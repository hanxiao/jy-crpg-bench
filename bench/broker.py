#!/usr/bin/env python3
"""Benchmark front door.

Spawns one isolated game process per agent and routes to it. That is all it
does: the run's clock, its teardown, its video and its catalogue entry all
belong to the session process itself (see server/warden.py), so this holds no
state worth losing and a node that dies takes only its own runs with it.

There is no catalogue here and no web page. The published catalogue is a JSON
object in the bucket, read directly by a static site.
"""
import asyncio
import hmac
import json
import os
import pathlib
import shutil
import socket
import subprocess
import time
import uuid
import sys

import aiohttp
from aiohttp import web

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
SERVER = REPO / "server" / "server.py"
sys.path.insert(0, str(REPO / "server"))
from health import clock, read_json, write_json, failure
from storage import validate_recording_directory
RECORDING_DIR = pathlib.Path(os.environ.get("QUNXIA_RECORDING_DIR", str(REPO / "recordings")))
PYTHON = os.environ.get("QUNXIA_PYTHON", str(REPO / ".venv" / "bin" / "python"))
RESULT_DIR = pathlib.Path(os.environ.get("QUNXIA_RESULT_DIR", "/tmp/qunxia-results"))
LOCAL = pathlib.Path(os.environ.get("QUNXIA_LOCAL_PUBLIC", "/tmp/qunxia-public"))
VIDEO_DIR = pathlib.Path(os.environ.get("QUNXIA_VIDEO_DIR", "/tmp/qunxia-videos"))
GCS_BUCKET = os.environ.get("QUNXIA_GCS_BUCKET", "")
PUBLIC_BASE = os.environ.get("QUNXIA_PUBLIC_BASE", "")
SITE = os.environ.get("QUNXIA_SITE", "https://hanxiao.io/jy-crpg-bench/")
RUN_SECONDS = int(os.environ.get("QUNXIA_RUN_SECONDS", "1200"))     # 20 minutes
# A caller may ask for a longer game. Bounded at a day: past that the recording
# hits its own size cap and the early history is dropped anyway.
MAX_MINUTES = int(os.environ.get("QUNXIA_MAX_MINUTES", "1440"))
# An agent that has not acted in this long is wedged, not thinking.
IDLE_LIMIT = int(os.environ.get("QUNXIA_IDLE_LIMIT", "600"))        # 10 minutes
BOOT_WAIT = float(os.environ.get("QUNXIA_BOOT_WAIT", "18"))
# Measured on 8 vCPU / 8Gi: 32 concurrent runs all held a full 70.09 fps with
# flat 1.13s action latency, and the container then OOMed at 33, killing every
# live run with it. CPU was never the limit; memory was, at roughly 123MB of
# game copy per run. This refuses the extra run instead of losing the others.
MAX_SESSIONS = int(os.environ.get("QUNXIA_MAX_SESSIONS", "24"))
# Every session gets its own copy of the game directory and its own libretro
# save directory. DOSBox Pure mounts the directory holding the content as a
# writable C:, and the skill tells agents to use the in-game save menu, so a
# shared directory would let one run's savegame land on another's. Measured at
# 123MB and 0.14s per copy, which is worth not having to reason about it.
GAME = os.environ.get("QUNXIA_GAME", str(REPO / "game" / "PLAY.BAT"))
WORK = pathlib.Path(os.environ.get("QUNXIA_WORK_DIR", "/tmp/qunxia-work"))
# How often the public snapshot of what is running is written to the bucket.
# Visitors read that file, never this service: a launch-day crowd polling here
# would be competing for CPU with the emulators it came to watch.
LIVE_EVERY = float(os.environ.get("QUNXIA_LIVE_EVERY", "4"))
SHOT_EVERY = float(os.environ.get("QUNXIA_SHOT_EVERY", "4"))
# A run is played by one agent but can be watched by many. Past this many
# sockets the extra viewers fall back to the published thumbnail, so a popular
# run is never slowed by its own audience.
MAX_WATCHERS = int(os.environ.get("QUNXIA_MAX_WATCHERS", "12"))
# How long to hold an agent's final call while its video renders and uploads.
# The run is over either way; this only decides whether the agent is handed the
# link or has to go and find it in the catalogue.
VIDEO_WAIT = float(os.environ.get("QUNXIA_VIDEO_WAIT", "300"))

# The catalogue page is static and served from another origin, so the two
# endpoints it reads have to say so.
CORS = {"Access-Control-Allow-Origin": "*"}
LIVE_HERO_FIELDS = (
    "level", "exp", "hp", "maxhp", "skills", "items",
    "inventory_distinct", "picked_item",
)
LIVE_TIMING_FIELDS = (
    "ttfa", "gap_p50", "gap_p95", "reads",
    "decision_calls", "key_events", "input_frames", "wait_calls",
)

sessions: dict[str, dict] = {}


def live_hero(summary):
    """The machine-state fields intentionally published to live.json."""
    return {key: summary.get(key) for key in LIVE_HERO_FIELDS}


def live_timing(summary):
    return {key: summary.get(key) for key in LIVE_TIMING_FIELDS}


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


_bucket_cache = []


def bucket():
    if not GCS_BUCKET:
        return None
    if not _bucket_cache:
        from google.cloud import storage
        _bucket_cache.append(storage.Client().bucket(GCS_BUCKET))
    return _bucket_cache[0]


def put(name, data, mime, max_age):
    b = bucket()
    if b is None:
        # object names carry slashes; on a filesystem those are directories
        out = LOCAL / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return
    blob = b.blob(name)
    blob.cache_control = f"public, max-age={max_age}"
    blob.upload_from_string(data, content_type=mime)


def drop(name):
    b = bucket()
    try:
        if b is None:
            (LOCAL / name).unlink(missing_ok=True)
        else:
            b.blob(name).delete()
    except Exception:
        pass


CATALOG_OBJECT = "catalog.json"


def merge_usage_into_catalog(sid, usage):
    """Attach an agent's usage to the run's catalogue entry.

    The entry is written by the session process (server/warden.py); this runs
    in the broker, so like the warden's append it is a generation-conditioned
    read-modify-write with retries rather than last-write-wins. Returns True
    when the entry was found and updated, False when the run is not in the
    catalogue yet (or has rolled off its cap) - the caller decides what a
    False means in context.
    """
    b = bucket()
    if b is None:
        local = pathlib.Path(os.environ.get("QUNXIA_CATALOG",
                                            "/tmp/qunxia-catalog.json"))
        runs = json.loads(local.read_text()) if local.exists() else []
        entry = next((r for r in runs if r.get("id") == sid), None)
        if entry is None:
            return False
        entry["usage"] = usage
        local.write_text(json.dumps(runs, indent=1))
        return True
    from google.api_core.exceptions import PreconditionFailed
    for attempt in range(12):
        blob = b.get_blob(CATALOG_OBJECT)
        if blob is None:
            return False
        gen = blob.generation
        try:
            runs = json.loads(blob.download_as_bytes())
        except Exception:
            runs = []
        entry = next((r for r in runs if r.get("id") == sid), None)
        if entry is None:
            return False
        entry["usage"] = usage
        try:
            blob.upload_from_string(
                json.dumps(runs), content_type="application/json",
                if_generation_match=gen)
        except PreconditionFailed:
            time.sleep(0.3 * (attempt + 1))
            continue
        return True
    raise RuntimeError("catalogue is too contended to update")


_results: dict[str, dict] = {}


def result_of(sid):
    """The session process writes this the moment it calls its own run over.

    The file is written twice: once with the summary while the video renders,
    and again with the video up. The second write is complete, and it is the
    process's last - it exits on the same tick - so a result seen complete is
    remembered. The hot loops ask for it several times a second for as long as
    the container lives, and a finished run's file will not change under them,
    so re-reading and re-parsing it on every ask would be pure waste."""
    cached = _results.get(sid)
    if cached is not None:
        return cached
    f = RESULT_DIR / f"{sid}.json"
    if not f.exists():
        return None
    try:
        result = json.loads(f.read_text())
    except Exception:
        return None
    if result.get("complete"):
        _results[sid] = result
    return result


async def wait_published(sid, res):
    """The run writes its summary the moment it ends, then rewrites it once the
    video is up. Wait for the second write so the agent's last reply carries a
    link rather than a null."""
    if res.get("complete") or res.get("valid") is False or res.get("video_url") or res.get("error"):
        return res
    deadline = time.time() + VIDEO_WAIT
    while time.time() < deadline:
        await asyncio.sleep(2)
        later = result_of(sid)
        if later and (later.get("complete") or later.get("valid") is False or later.get("video_url") or later.get("error")):
            return later
    return res


async def wait_healthy(port, timeout=90, proc=None):
    async with aiohttp.ClientSession() as http:
        for _ in range(int(timeout * 2)):
            # A game process that has already exited will not bind; polling a
            # dead port until the deadline would burn a minute of wall time
            # (and the caller's slot) on a failure that is decided.
            if proc is not None and proc.poll() is not None:
                return False
            try:
                async with http.get(f"http://127.0.0.1:{port}/status",
                                    timeout=aiohttp.ClientTimeout(total=3)) as r:
                    if r.status == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
    return False


def make_workdir(sid):
    """A private, writable game directory for one run."""
    root = WORK / sid
    shutil.rmtree(root, ignore_errors=True)
    (root / "saves").mkdir(parents=True, exist_ok=True)
    src = pathlib.Path(GAME).parent
    shutil.copytree(src, root / "game", dirs_exist_ok=True)
    return root / "game" / pathlib.Path(GAME).name, root / "saves"


def running_count():
    return sum(1 for s in sessions.values()
               if s["proc"].poll() is None and not result_of(s["id"]))


async def start_session(agent, budget, publish=True):
    live = running_count()
    if live >= MAX_SESSIONS:
        raise web.HTTPServiceUnavailable(
            text=json.dumps({
                "ok": False, "error": "at capacity",
                "running": live, "capacity": MAX_SESSIONS,
                "hint": "every machine is busy. Wait and POST /session again; "
                        "nothing is queued, so retry rather than hold."}),
            content_type="application/json", headers=CORS)
    sid = uuid.uuid4().hex[:12]
    port = free_port()
    # Two secrets, two readers. The URL token travels in the session's
    # base_url, so the agent that plays the run holds it; the reset token
    # stays inside the broker - for its own bootstrap and the operator's
    # backdoor - and is never in an address an agent can be seen holding.
    token = uuid.uuid4().hex
    reset_token = uuid.uuid4().hex
    loop = asyncio.get_running_loop()
    game, saves = await loop.run_in_executor(None, make_workdir, sid)
    env = dict(os.environ)
    env.update(PORT=str(port),
               QUNXIA_GAME=str(game),
               QUNXIA_SAVES=str(saves),
               QUNXIA_HEALTH_DIR=str(WORK / sid / "health"),
               QUNXIA_DIAGNOSTIC_DIR=str(RESULT_DIR / f"{sid}.diagnostics"),
               QUNXIA_RECORDING_DIR=str(RECORDING_DIR),
               QUNXIA_RECORDING_FILE=str(RECORDING_DIR / sid / "recording.jsonl"),
               QUNXIA_SEND_HZ="15",
               QUNXIA_RESET_TOKEN=reset_token,
               QUNXIA_BENCH="1",
               QUNXIA_PUBLISH="1" if publish else "0",
               QUNXIA_BENCH_AGENT=agent,
               QUNXIA_BENCH_SID=sid,
               QUNXIA_BENCH_BUDGET=str(budget),
               QUNXIA_BENCH_IDLE=str(IDLE_LIMIT),
               QUNXIA_RESULT_DIR=str(RESULT_DIR),
               QUNXIA_BENCH_SITE=SITE)
    proc = subprocess.Popen([PYTHON, str(SERVER)], env=env, cwd=str(REPO / "server"))
    sess = {"id": sid, "agent": agent, "port": port, "token": token,
            "proc": proc, "work": WORK / sid, "budget": budget,
            "started": time.time(), "ends_at": time.time() + budget, "started_clock": clock()}
    sessions[sid] = sess

    if not await wait_healthy(port, proc=proc):
        await asyncio.to_thread(stop_worker, proc)
        await asyncio.to_thread(archive_health, sess, 'startup_failed')
        shutil.rmtree(WORK / sid, ignore_errors=True)
        raise web.HTTPBadGateway(
            text=json.dumps({"ok": False, "error": "session did not start"}),
            content_type="application/json")

    # Start every run in the opening room rather than at the title screen.
    # Creating a character means driving the 注音 IME, which measures knowledge
    # of input methods and not play, and it is where runs used to die. A
    # savestate will not load into a machine that is still booting, so retry.
    await asyncio.sleep(BOOT_WAIT)
    sess["spawned"] = False
    async with aiohttp.ClientSession() as http:
        for _ in range(20):
            try:
                async with http.post(f"http://127.0.0.1:{port}/api/reset",
                                     params={"token": reset_token},
                                     timeout=aiohttp.ClientTimeout(total=120)) as r:
                    if (await r.json()).get("restored"):
                        sess["spawned"] = True
                        break
            except Exception as exc:
                sess["error"] = f"spawn: {exc}"
            await asyncio.sleep(2)

    # A run that did not start in the game is not a benchmark run: it begins at
    # the DOS boot screen and measures nothing. Refuse it loudly instead of
    # handing the agent a broken game, which is what happened for an hour when
    # the bootstrap failed and every session silently started at the title.
    if not sess["spawned"]:
        await asyncio.to_thread(stop_worker, proc)
        await asyncio.to_thread(archive_health, sess, 'spawn_failed')
        shutil.rmtree(WORK / sid, ignore_errors=True)
        sessions.pop(sid, None)
        print(f"session {sid} refused: start state would not load", flush=True)
        raise web.HTTPServiceUnavailable(
            text=json.dumps({
                "ok": False, "error": "the game is not ready",
                "hint": "the starting savestate is being rebuilt; try again in "
                        "a few minutes"}),
            content_type="application/json", headers=CORS)

    sess["ends_at"] = time.time() + budget            # clock starts once playable
    return sess


def ended_payload(sess, res):
    """The run published its own summary; pass it back rather than guessing."""
    if not res:
        res = failure("worker_exited_without_result")
    if res.get("valid") is False:
        return dict(res, agent=sess["agent"])
    keep = ("reason", "why", "actions", "played", "aps", "video_url", "error", "valid")
    return dict({k: res[k] for k in keep if res and k in res},
                ok=True, ended=True, agent=sess["agent"],
                message="This benchmark run has ended. Stop playing.",
                catalog_url=SITE)


# ------------------------------------------------------------------ http

def public_scheme(request):
    """The scheme the front door reached this service on.

    Cloud Run terminates TLS in front of us, so request.url.scheme is http;
    the front door reports the public one in X-Forwarded-Proto. Every proxy
    on the path appends its own observation, so the innermost - the last -
    value is the front door's, and a value a client prepends cannot rewrite
    the URLs this service issues into http, where a redirect turns a POST
    into a GET."""
    for value in reversed(request.headers.get("X-Forwarded-Proto", "").split(",")):
        value = value.strip().lower()
        if value in ("http", "https"):
            return value
    return request.url.scheme


def public_origin(request):
    """The origin the client reached this service at.

    The host is the one the front door presented the request under; Cloud
    Run rejects hosts the service does not serve, so it names an address
    this service owns. A client-supplied X-Forwarded-Host is ignored: this
    service hands out play addresses that carry the run's token in their
    path, and a caller must not be able to point that credential at a host
    of their own choosing."""
    return f"{public_scheme(request)}://{request.host}"


def canonical_agent_name(name):
    """The one rule for the names runs are listed under.

    The name round-trips through the usage report's X-Agent header and
    header values are latin-1, so a name that cannot survive that
    round-trip could never be reported; it must not be accepted in the
    first place. The pi launcher applies this same transform to
    QUNXIA_BENCH_AGENT, so a report always carries the name the session
    was created under, whatever the operator pasted in."""
    return "".join(
        c for c in str(name).strip()
        if c.isascii() and (c.isalnum() or c in "-_."))[:40]


async def api_new(request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    agent = canonical_agent_name(
        body.get("agent") or request.query.get("agent") or "")
    if request.app.get("booting"):
        return web.json_response(
            {"ok": False, "error": "still authoring the opening savestate",
             "hint": "this happens once per cold start; retry in a minute"},
            status=503, headers=CORS)
    if not agent:
        return web.json_response(
            {"ok": False, "error": "name yourself first",
             "hint": 'POST {"agent": "<the model you are>"} - the name is what '
                     'the catalogue lists this run under'}, status=400)
    try:
        minutes = int(body.get("minutes") or request.query.get("minutes")
                      or RUN_SECONDS // 60)
    except (TypeError, ValueError):
        minutes = RUN_SECONDS // 60
    minutes = max(1, min(minutes, MAX_MINUTES))
    # A caller can ask to stay out of the catalogue. Smoke tests were landing
    # on the public board, one of them at the top of it.
    publish = body.get("publish", request.query.get("publish")) not in (
        False, "false", "0", 0)
    sess = await start_session(agent, minutes * 60, publish)
    # The URL is the credential: the session's token rides in its path, so
    # this is the only address that can send input to the run. The address
    # without it is what the board links to its viewers, and there only
    # watching is possible.
    base = public_origin(request) + f"/s/{sess['id']}/t/{sess['token']}"
    return web.json_response({
        "ok": True, "session": sess["id"], "agent": agent,
        "base_url": base, "help_url": base + "/api/help",
        "seconds": sess["budget"], "minutes": minutes,
        "max_minutes": MAX_MINUTES, "ends_at": sess["ends_at"],
        "idle_limit": IDLE_LIMIT,
        "spawned_in_game": sess.get("spawned", False),
        "catalog_url": SITE,
        "message": f"You are in the game as '{agent}'. You have "
                   f"{minutes} minutes. Read {base}/api/help, then "
                   f"play with {base}/api/... . Keep acting: if no action "
                   f"arrives for {IDLE_LIMIT // 60} minutes the run is stopped "
                   f"early and listed as idle.",
    })


async def proxy(request):
    sid = request.match_info["sid"]
    sess = sessions.get(sid)
    if not sess:
        raise web.HTTPNotFound(
            text=json.dumps({"ok": False, "error": "no such session",
                             "hint": "POST /session to start one"}),
            content_type="application/json")

    # The URL is the credential. The session's own address carries its token
    # in the path, and that is full access. An address without it is a
    # spectator address - the board links its viewers there - and it may
    # watch, not play.
    tail = request.match_info.get("tail", "")
    parts = tail.split("/")
    # The token gates play access; compare it in constant time, for the same
    # reason a password is never compared with ==.
    authenticated = (len(parts) >= 3 and parts[0] == "t"
                     and hmac.compare_digest(parts[1],
                                             sess.get("token") or ""))
    if authenticated:
        tail = "/".join(parts[2:])

    # Usage is a broker endpoint, not a session one: it lands on the
    # catalogue, which the session process does not own. It is answered
    # before the 410 below on purpose - the report arrives after the run is
    # over - and only through the session's own address, since the run's
    # agent name is public and a name check alone would not keep a
    # stranger's report out.
    if request.method == "POST" and tail == "usage":
        if not authenticated:
            return web.json_response(
                {"ok": False, "error": "usage reports are filed through "
                                       "the session's own address",
                 "hint": "the base_url from POST /session carries it"},
                status=403, headers=CORS)
        return await api_usage(request)

    if not authenticated and request.method not in ("GET", "HEAD"):
        return web.json_response(
            {"ok": False, "error": "this address watches; it does not play",
             "hint": "the base_url from POST /session carries play access "
                     "in its path"},
            status=403, headers=CORS)

    res = result_of(sid)
    if res or sess["proc"].poll() is not None:
        if res:
            res = await wait_published(sid, res)
        return web.json_response(ended_payload(sess, res), status=410)

    url = f"http://127.0.0.1:{sess['port']}/{tail}"

    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await spectate(request, sess, url)

    data = await request.read()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}
    # The record attributes every action to the session's own agent, not to
    # whatever the client claims: the catalogue, the video and the replay
    # must name the same model, and no stranger may write a name into the
    # run's record.
    headers["X-Agent"] = sess["agent"]
    # The session server builds the public URLs of its own help page from
    # these two headers. This proxy is the only path to the server, so it
    # states what it knows - replacing anything the client sent - and the
    # server can trust what arrives.
    headers["X-Forwarded-Host"] = request.host
    headers["X-Forwarded-Proto"] = public_scheme(request)
    out = None
    try:
        http = request.app["http"]
        async with http.request(request.method, url, params=request.query,
                                data=data or None, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=180)) as r:
            out = web.StreamResponse(status=r.status, headers={'Content-Type':r.headers.get('Content-Type','application/octet-stream')})
            out.headers['X-Bench-Remaining'] = str(max(0, int(sess['ends_at'] - time.time())))
            await out.prepare(request)
            async for chunk in r.content.iter_chunked(64 << 10):
                await out.write(chunk)
            await out.write_eof()
            return out
    except Exception as exc:
        if out is not None and out.prepared:
            if request.transport:
                request.transport.close()
            return out
        # The process may have published and exited between the two checks.
        res = result_of(sid)
        if res:
            return web.json_response(
                ended_payload(sess, await wait_published(sid, res)), status=410)
        raise web.HTTPBadGateway(
            text=json.dumps({"ok": False, "error": str(exc)}),
            content_type="application/json")


async def open_http(app):
    """One connector for the life of the broker. The proxy hands every agent
    action and every spectator's page through it; a fresh ClientSession per
    request would build and tear down a pool of sockets for each one."""
    app["http"] = aiohttp.ClientSession()


async def close_http(app):
    await app["http"].close()


async def spectate(request, sess, url):
    """Watch a run in progress. Anything the viewer sends is dropped rather
    than forwarded, so a spectator cannot touch the game even with a hand
    written socket - read only is a property of this proxy, not of the page."""
    if sess.get("watchers", 0) >= MAX_WATCHERS:
        return web.json_response(
            {"ok": False, "error": "too many watchers", "watchers": MAX_WATCHERS,
             "hint": "this run is already being watched by as many sockets as "
                     "it will carry; the published thumbnail still updates"},
            status=503, headers=CORS)
    # Take the slot before the handshake: prepare() awaits, and a check and
    # an increment on either side of an await are not atomic.
    sess["watchers"] = sess.get("watchers", 0) + 1
    ws = web.WebSocketResponse(max_msg_size=4096, heartbeat=30, compress=False)
    try:
        await ws.prepare(request)
    except Exception:
        sess["watchers"] = max(0, sess["watchers"] - 1)
        raise
    try:
        http = request.app["http"]
        async with http.ws_connect(url, max_msg_size=2 << 20, heartbeat=30, compress=0) as up:
            async def downstream():
                async for m in up:
                    if m.type == aiohttp.WSMsgType.BINARY:
                        await ws.send_bytes(m.data)
                    elif m.type == aiohttp.WSMsgType.TEXT:
                        await ws.send_str(m.data)
            pump = asyncio.create_task(downstream())
            try:
                async for _ in ws:
                    pass                      # deliberately ignored
            finally:
                pump.cancel()
    except Exception:
        pass
    finally:
        sess["watchers"] = max(0, sess["watchers"] - 1)
        await ws.close()
    return ws


# A usage report is a handful of numbers. Anything bigger is not a report.
USAGE_LIMIT = 64 << 10


def _validate_usage(body):
    """The report is published verbatim onto the public board, so keep it to
    what a usage actually is, and nothing else. None when it is not one."""
    if not isinstance(body, dict):
        return None

    def tokens(key):
        value = body.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        if value < 0 or value > 10**9:
            return None
        return value

    usage = {k: tokens(k) for k in
             ("input", "output", "cacheRead", "cacheWrite", "totalTokens")}
    if any(v is None for v in usage.values()):
        return None
    cost = body.get("cost", 0)
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) \
            or not 0 <= cost <= 10**6:
        return None
    turns = body.get("turns", 0)
    if isinstance(turns, bool) or not isinstance(turns, int) \
            or not 0 <= turns <= 100000:
        return None
    usage.update(cost=round(float(cost), 6), turns=turns)
    model = body.get("model")
    if isinstance(model, str) and model:
        usage["model"] = "".join(c for c in model if c.isprintable())[:200]
    return usage


async def api_usage(request):
    """Report the run's model usage, measured by the agent's harness.

    This is the provider's meter relayed by the harness that ran the model -
    not a claim by the model, which is why the board may publish it at all.
    It is filed through the session's own token address, so the proxy's
    check lands it here, on the broker's catalogue, and no stranger's
    address can file one. The report lands on the run's catalogue entry:
    immediately if the entry is there, otherwise on the next sweep tick that
    finds it (the session process appends the entry while it finalizes, which
    can outlive the agent's last reply by minutes).
    """
    sid = request.match_info["sid"]
    sess = sessions.get(sid)
    if not sess:
        raise web.HTTPNotFound(
            text=json.dumps({"ok": False, "error": "no such session",
                             "hint": "usage reports land on a run while it "
                                     "is finishing or just after it"}),
            content_type="application/json", headers=CORS)
    if request.headers.get("X-Agent") != sess["agent"]:
        return web.json_response({
            "ok": False, "error": "X-Agent must name this run's agent",
            "hint": "send the same name the session was created under"},
            status=403, headers=CORS)
    raw = await request.read()
    if len(raw) > USAGE_LIMIT:
        raise web.HTTPPayloadTooLarge(
            text=json.dumps({"ok": False,
                             "error": "a usage report is at most 64KB"}),
            content_type="application/json", headers=CORS)
    try:
        usage = _validate_usage(json.loads(raw or b"{}"))
    except (ValueError, TypeError):
        usage = None
    if usage is None:
        return web.json_response({
            "ok": False, "error": "a usage report needs input, output, "
                                  "cacheRead, cacheWrite and totalTokens "
                                  "as non-negative integers",
            "hint": "the harness's meter, not the model's estimate"},
            status=400, headers=CORS)
    try:
        merged = await asyncio.get_running_loop().run_in_executor(
            None, merge_usage_into_catalog, sid, usage)
    except Exception as exc:
        print(f"usage merge for {sid}: {exc}", flush=True)
        merged = False
    if merged:
        sess.pop("usage", None)
        return web.json_response({"ok": True, "merged": True}, headers=CORS)
    # The entry is not in the catalogue yet. Keep the report on the session
    # and let the sweep attach it once the entry lands; the deadline below
    # bounds a run whose entry never will.
    sess["usage"] = usage
    sess["usage_since"] = time.time()
    return web.json_response({
        "ok": True, "merged": False,
        "note": "the run's entry is not in the catalogue yet; the report "
                "will be attached when it lands"},
        status=202, headers=CORS)


async def api_sessions(_request):
    now = time.time()
    return web.json_response(
        {"capacity": MAX_SESSIONS, "running": [
            {"id": s["id"], "agent": s["agent"],
             "started": s["started"], "watchers": s.get("watchers", 0),
             "actions": s.get("live_actions", 0), "budget": s.get("budget"),
             "meaningful": s.get("live_meaningful", 0),
             "scenes": s.get("live_scenes", 1),
             "frontier": s.get("live_frontier"),
             **(s.get("live_world") or {}),
             **(s.get("live_hero") or {}),
             **s.get("live_timing", {}),
             "uptime": round(s.get("live_uptime", 0)),
             "remaining": max(0, round(s["ends_at"] - now))}
            for s in sessions.values()
            if s["proc"].poll() is None and not result_of(s["id"])]},
        headers=CORS)


async def video_file(request):
    """Only used when no bucket is configured, ie local development."""
    name = pathlib.Path(request.match_info["name"]).name
    path = VIDEO_DIR / name
    if not path.exists():
        raise web.HTTPNotFound()
    return web.FileResponse(path)


async def api_catalog(_request):
    """The published catalogue lives in the bucket; this is the local mirror
    so the static page can be developed without one."""
    if GCS_BUCKET:
        raise web.HTTPFound(
            f"https://storage.googleapis.com/{GCS_BUCKET}/catalog.json")
    f = pathlib.Path(os.environ.get("QUNXIA_CATALOG", "/tmp/qunxia-catalog.json"))
    runs = json.loads(f.read_text()) if f.exists() else []
    return web.json_response({"runs": runs}, headers=CORS)


async def health(_request):
    return web.json_response({
        "ok": not _request.app.get("bootstrap_failed"),
        "booting": bool(_request.app.get("booting")),
        "running": running_count(), "capacity": MAX_SESSIONS,
        "budget": RUN_SECONDS, "max_minutes": MAX_MINUTES,
        "idle_limit": IDLE_LIMIT, "site": SITE},
        headers=CORS)


async def index(_request):
    """No dashboard here. The site is static and lives elsewhere."""
    raise web.HTTPFound(SITE)


def live_payload():
    now = time.time()
    return {"t": round(now, 1), "capacity": MAX_SESSIONS,
            "max_minutes": MAX_MINUTES, "max_watchers": MAX_WATCHERS,
            "running": [
                {"id": s["id"], "agent": s["agent"], "started": s["started"],
                 "actions": s.get("live_actions", 0),
                 "meaningful": s.get("live_meaningful", 0),
                     "scenes": s.get("live_scenes", 1),
                 "frontier": s.get("live_frontier"),
                 **(s.get("live_world") or {}),
                 **(s.get("live_hero") or {}),
                 "keys": s.get("live_keys", {}),
                 **s.get("live_timing", {}),
                 "uptime": round(s.get("live_uptime", 0)),
                 "budget": s.get("budget"),
                 "watchers": s.get("watchers", 0),
                 "shot": s.get("shot_at", 0),
                 "remaining": max(0, round(s["ends_at"] - now))}
                for s in sessions.values()
                if s["proc"].poll() is None and not result_of(s["id"])]}


def stop_worker(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def archive_health(sess, reason=None):
    """Keep bounded evidence outside the work directory before reclaiming it.

    A killed or unresponsive worker cannot write its own incident. The broker
    retains the last heartbeat/fault and exit status in that case as well.
    """
    work = sess.get('work')
    if not work or not (work / 'health').exists():
        return
    destination = RESULT_DIR / f"{sess['id']}.diagnostics"
    try:
        for name in ('heartbeat.json', 'failure.json'):
            value = read_json(work / 'health' / name)
            if value is not None:
                write_json(destination / name, value)
        write_json(destination / 'worker.json', dict(
            pid=sess['proc'].pid, exit_code=sess['proc'].poll(), reason=reason))
    except OSError as exc:
        print(f"diagnostic archive {sess['id']}: {exc}", flush=True)


async def fail_worker(sess, reason):
    # Reap before writing, so a dying worker cannot overwrite this result.
    await asyncio.to_thread(stop_worker, sess['proc'])
    await asyncio.to_thread(archive_health, sess, reason)
    result = result_of(sess['id'])
    if result and result.get('valid') is True:
        result.update(complete=True, error=(result.get('error') or '') + f' artifact finalization failed: {reason}')
    else:
        result = dict(failure(reason), id=sess['id'], agent=sess['agent'], complete=True)
    write_json(RESULT_DIR / f"{sess['id']}.json", result)


async def check_workers():
    jobs = []
    now = clock()
    timeout = float(os.environ.get('QUNXIA_STALL_SECONDS', '15'))
    for sess in list(sessions.values()):
        proc = sess['proc']
        result = result_of(sess['id'])
        if result and result.get('complete'):
            continue
        state = read_json(sess['work'] / 'health/heartbeat.json')
        fault = read_json(sess['work'] / 'health/failure.json')
        reason = fault.get('reason') if fault else None
        if not reason and proc.poll() is not None:
            if result and result.get('valid'):
                result.update(complete=True, error='artifact generation did not finish')
                write_json(RESULT_DIR / f"{sess['id']}.json", result)
                continue
            reason = 'worker_exited_without_result'
        if not reason and state and state.get('pid') == proc.pid:
            if now - state.get('at', 0) > timeout:
                reason = 'worker_unresponsive'
            elif state.get('phase') == 'finalizing' and now - state.get('phase_at', 0) > 300:
                reason = 'finalization_stalled'
            elif state.get('failure'):
                reason = state['failure']['reason']
        elif not reason and now - sess['started_clock'] > 30:
            reason = 'missing_worker_heartbeat'
        if reason:
            jobs.append(fail_worker(sess, reason))
    if jobs:
        await asyncio.gather(*jobs)


async def monitor_workers():
    while True:
        try:
            await check_workers()
        except Exception as exc:
            print(f'worker monitor: {exc}', flush=True)
        await asyncio.sleep(.5)


async def sweep(app):
    """Housekeeping, on the broker's own clock rather than any caller's.

    Three jobs. It reclaims a finished run's 123MB game copy once the process
    that owned it is gone, which that process cannot do while it is still
    holding those files open. It refreshes the live action counts. And it
    publishes both the counts and a thumbnail per running run to the bucket,
    so the public page reads a static file that scales on its own instead of
    polling this service, which shares its CPU with every emulator.
    """
    loop = asyncio.get_running_loop()
    tick, last_live, last_shot, last_sig = 0, 0.0, 0.0, None
    # One session for the life of the sweep, not a new one per tick: a
    # fresh session and its connector would otherwise be built and torn
    # down every second even when no run is active.
    http = aiohttp.ClientSession()

    async def live_status(port):
        try:
            async with http.get(f"http://127.0.0.1:{port}/status",
                                timeout=aiohttp.ClientTimeout(total=3)) as r:
                return (await r.json()).get("session", {})
        except Exception:
            return None

    async def thumbnail(s, now):
        try:
            async with http.get(
                    f"http://127.0.0.1:{s['port']}/api/screen",
                    params={"format": "jpeg", "spectate": "1"},
                    timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    img = await r.read()
                    await loop.run_in_executor(
                        None, put, f"live/{s['id']}.jpg", img, "image/jpeg", 4)
                    s["shot_at"] = round(now)
        except Exception as exc:
            if not s.get("shot_warned"):
                s["shot_warned"] = True
                print(f"thumbnail failed for {s['id']}: {exc}", flush=True)

    try:
        while True:
            await asyncio.sleep(1)
            tick += 1
            now = time.time()
            running = [s for s in sessions.values()
                       if s["proc"].poll() is None and not result_of(s["id"])]

            # Poll every running worker concurrently: one hung worker must not
            # stall the counts, the publish, or the reclaim below for all the
            # others in the pool (24 by default, 3s + 8s per stalled fetch).
            for s, d in zip(running, await asyncio.gather(
                    *(live_status(s["port"]) for s in running))):
                if d is None:
                    continue
                s["live_actions"] = d.get("actions", 0)
                s["live_uptime"] = d.get("uptime_s", 0)
                s["live_meaningful"] = d.get("meaningful", 0)
                s["live_scenes"] = d.get("scenes", 1)
                s["live_world"] = {k: d.get(k) for k in
                                   ("bigmap", "exit_acts", "exit_secs")}
                s["live_hero"] = live_hero(d)
                s["live_frontier"] = d.get("frontier")
                s["live_keys"] = d.get("keys", {})
                s["live_timing"] = live_timing(d)

            if running and now - last_shot >= SHOT_EVERY:
                last_shot = now
                await asyncio.gather(*(thumbnail(s, now) for s in running))

            # written while anything runs, and once more after the last one stops
            sig = tuple(sorted(s["id"] for s in running))
            if running and now - last_live >= LIVE_EVERY or sig != last_sig:
                last_live, last_sig = now, sig
                try:
                    await loop.run_in_executor(
                        None, put, "live.json",
                        json.dumps(live_payload()).encode(), "application/json", 3)
                except Exception as exc:
                    print(f"live publish failed: {exc}", flush=True)

            # A usage report waits here while the session process finalizes:
            # it writes its result before it appends the catalogue entry, so a
            # missing result means a guaranteed miss - only then is the
            # catalogue round-trip worth paying, once a second per pending run.
            for s in list(sessions.values()):
                if s.get("usage") is None or result_of(s["id"]) is None:
                    continue
                if now - s.get("usage_since", 0) > 600:
                    # The entry never landed; stop paying for a run the
                    # catalogue does not have.
                    s.pop("usage", None)
                    s.pop("usage_since", None)
                    continue
                try:
                    merged = await loop.run_in_executor(
                        None, merge_usage_into_catalog, s["id"], s["usage"])
                except Exception as exc:
                    merged = False
                    print(f"usage merge for {s['id']}: {exc}", flush=True)
                if merged:
                    s.pop("usage", None)
                    s.pop("usage_since", None)

            if tick % 30:
                continue
            for s in list(sessions.values()):
                work = s.get("work")
                if work and s["proc"].poll() is not None and work.exists():
                    await loop.run_in_executor(None, archive_health, s)
                    await loop.run_in_executor(
                        None, lambda w=work: shutil.rmtree(w, ignore_errors=True))
                    # its thumbnail is nothing but storage cost once the run is over
                    await loop.run_in_executor(None, drop, f"live/{s['id']}.jpg")
                    print(f"reclaimed {work}", flush=True)
    finally:
        await http.close()


async def spawn_sweep(app):
    # a restart leaves a stale live.json describing runs that died with the
    # container; clear it before anything reads it
    try:
        await asyncio.get_running_loop().run_in_executor(
            None, put, "live.json", json.dumps(live_payload()).encode(),
            "application/json", 3)
    except Exception as exc:
        print(f"live reset failed: {exc}", flush=True)
    app["sweep"] = asyncio.create_task(sweep(app))
    app["monitor"] = asyncio.create_task(monitor_workers())


async def ensure_start_state(app):
    """The savestate is tied to the core build, so it cannot be shipped in the
    image. Author it here, once, on whatever machine this is.

    Deliberately not awaited from on_startup. Authoring means playing the
    opening through, which takes minutes, and an aiohttp startup handler runs
    before the socket is listening: Cloud Run's startup probe gives four
    minutes, saw nothing on the port, and killed the instance mid-bootstrap,
    over and over. So the port opens first and this runs behind it, with
    /session refusing until it lands."""
    state = pathlib.Path(os.environ.get(
        "QUNXIA_START_STATE", str(REPO / "saves" / "start.state")))
    if state.exists():
        print(f"start state present: {state}", flush=True)
        app["booting"] = False
        return
    print("no start state, playing the opening once to make one", flush=True)
    app["booting"] = True
    # The opening is played by a script that can lose its way: a slower machine
    # burns its budget mid-scene and gives up. One failure used to mean the
    # container refused every session for as long as it lived, which is how
    # this went down. Try again instead.
    for attempt in range(1, 4):
        try:
            await author_start_state(state, attempt)
        except Exception as exc:
            print(f"bootstrap attempt {attempt} failed: {exc}", flush=True)
        if state.exists():
            break
        await asyncio.sleep(2)
    app["booting"] = False
    ok = state.exists()
    print(f"start state ready: {ok}", flush=True)
    app["bootstrap_failed"] = not ok
    return


async def author_start_state(state, attempt):
    print(f"  opening attempt {attempt}", flush=True)
    port, token = free_port(), uuid.uuid4().hex
    env = dict(os.environ)
    env.update(PORT=str(port), QUNXIA_RESET_TOKEN=token,
               QUNXIA_START_STATE=str(state))
    env.pop("QUNXIA_BENCH", None)              # the authoring run is not a run
    proc = subprocess.Popen([PYTHON, str(SERVER)], env=env, cwd=str(REPO / "server"),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not await wait_healthy(port):
            raise RuntimeError("worker did not start")
        from bootstrap import build
        await asyncio.get_running_loop().run_in_executor(
            None, lambda: build(f"http://127.0.0.1:{port}", token))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


async def boot_in_background(app):
    app["booting"] = True
    app["bootstrap"] = asyncio.create_task(ensure_start_state(app))


def main():
    validate_recording_directory(RECORDING_DIR)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg") is None:
        print("warning: ffmpeg not on PATH, runs will not render", flush=True)
    web.run_app(build_app(), host="0.0.0.0",
                port=int(os.environ.get("PORT", "8080")), access_log=None)


def build_app():
    app = web.Application(client_max_size=64 << 20)
    app.add_routes([
        web.get("/", index),
        web.get("/health", health),
        web.post("/session", api_new),
        web.get("/api/sessions", api_sessions),
        web.get("/api/catalog", api_catalog),
        web.get("/videos/{name}", video_file),
        # Usage has no route of its own: the catch-all answers it after the
        # token check, so only the session's own address can file a report.
        web.route("*", "/s/{sid}/{tail:.*}", proxy),
    ])
    app.on_startup.append(boot_in_background)
    app.on_startup.append(spawn_sweep)
    app.on_startup.append(open_http)
    app.on_cleanup.append(close_http)
    return app


if __name__ == "__main__":
    main()
