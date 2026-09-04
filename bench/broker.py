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
import json
import os
import pathlib
import shutil
import socket
import subprocess
import time
import uuid

import aiohttp
from aiohttp import web

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
SERVER = REPO / "server" / "server.py"
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


def result_of(sid):
    """The session process writes this the moment it calls its own run over."""
    f = RESULT_DIR / f"{sid}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except Exception:
        return None


async def wait_published(sid, res):
    """The run writes its summary the moment it ends, then rewrites it once the
    video is up. Wait for the second write so the agent's last reply carries a
    link rather than a null."""
    if res.get("video_url") or res.get("error"):
        return res
    deadline = time.time() + VIDEO_WAIT
    while time.time() < deadline:
        await asyncio.sleep(2)
        later = result_of(sid)
        if later and (later.get("video_url") or later.get("error")):
            return later
    return res


async def wait_healthy(port, timeout=90):
    async with aiohttp.ClientSession() as http:
        for _ in range(int(timeout * 2)):
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
    token = uuid.uuid4().hex
    loop = asyncio.get_running_loop()
    game, saves = await loop.run_in_executor(None, make_workdir, sid)
    env = dict(os.environ)
    env.update(PORT=str(port),
               QUNXIA_GAME=str(game),
               QUNXIA_SAVES=str(saves),
               QUNXIA_REC_KEEP_ALL="1",
               # People do watch bench runs now, so the stream is not throttled
               # to the old "nobody is looking" rate. Measured at 5.9 MB/min of
               # recording at the effective 3 fps this yields; the cap below
               # bounds a long run, and 24 of these have to fit in RAM at once.
               QUNXIA_SEND_HZ="15",
               QUNXIA_REC_MAX_BYTES=str(160 << 20),
               QUNXIA_RESET_TOKEN=token,
               QUNXIA_BENCH="1",
               QUNXIA_PUBLISH="1" if publish else "0",
               QUNXIA_BENCH_AGENT=agent,
               QUNXIA_BENCH_SID=sid,
               QUNXIA_BENCH_BUDGET=str(budget),
               QUNXIA_BENCH_IDLE=str(IDLE_LIMIT),
               QUNXIA_RESULT_DIR=str(RESULT_DIR),
               QUNXIA_BENCH_SITE=SITE)
    proc = subprocess.Popen([PYTHON, str(SERVER)], env=env, cwd=str(REPO / "server"))
    sess = {"id": sid, "agent": agent, "port": port, "proc": proc,
            "work": WORK / sid, "budget": budget,
            "started": time.time(), "ends_at": time.time() + budget}
    sessions[sid] = sess

    if not await wait_healthy(port):
        proc.kill()
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
                                     params={"token": token},
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
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
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
    keep = ("reason", "why", "actions", "played", "aps", "video_url", "error")
    return dict({k: res[k] for k in keep if res and k in res},
                ok=True, ended=True, agent=sess["agent"],
                message="This benchmark run has ended. Stop playing.",
                catalog_url=SITE)


# ------------------------------------------------------------------ http

def public_origin(request):
    """Cloud Run terminates TLS in front of us, so request.url.scheme is http.
    Handing that back made agents POST to http, get 302'd to https, and have
    the redirect turn their POST into a GET."""
    proto = request.headers.get("X-Forwarded-Proto", "").split(",")[0].strip()
    host = request.headers.get("X-Forwarded-Host", "").split(",")[0].strip()
    return f"{proto or request.url.scheme}://{host or request.host}"


async def api_new(request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    agent = (body.get("agent") or request.query.get("agent") or "").strip()
    agent = "".join(c for c in agent if c.isalnum() or c in "-_.")[:40]
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
    base = public_origin(request) + f"/s/{sess['id']}"
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

    res = result_of(sid)
    if res or sess["proc"].poll() is not None:
        if res:
            res = await wait_published(sid, res)
        return web.json_response(ended_payload(sess, res), status=410)

    tail = request.match_info.get("tail", "")
    url = f"http://127.0.0.1:{sess['port']}/{tail}"

    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await spectate(request, sess, url)

    data = await request.read()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}
    headers.setdefault("X-Agent", sess["agent"])
    try:
        async with aiohttp.ClientSession() as http:
            async with http.request(request.method, url, params=request.query,
                                    data=data or None, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=180)) as r:
                out = web.Response(body=await r.read(), status=r.status,
                                   content_type=r.content_type)
                out.headers["X-Bench-Remaining"] = str(
                    max(0, int(sess["ends_at"] - time.time())))
                return out
    except Exception as exc:
        # The process may have published and exited between the two checks.
        res = result_of(sid)
        if res:
            return web.json_response(
                ended_payload(sess, await wait_published(sid, res)), status=410)
        raise web.HTTPBadGateway(
            text=json.dumps({"ok": False, "error": str(exc)}),
            content_type="application/json")


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
    ws = web.WebSocketResponse(max_msg_size=0, heartbeat=30)
    await ws.prepare(request)
    sess["watchers"] = sess.get("watchers", 0) + 1
    try:
        async with aiohttp.ClientSession() as http:
            async with http.ws_connect(url, max_msg_size=0, heartbeat=30) as up:
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
        sess["watchers"] = max(0, sess.get("watchers", 1) - 1)
        await ws.close()
    return ws


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
    while True:
        await asyncio.sleep(1)
        tick += 1
        now = time.time()
        running = [s for s in sessions.values()
                   if s["proc"].poll() is None and not result_of(s["id"])]

        async with aiohttp.ClientSession() as http:
            for s in running:
                try:
                    async with http.get(f"http://127.0.0.1:{s['port']}/status",
                                        timeout=aiohttp.ClientTimeout(total=3)) as r:
                        d = (await r.json()).get("session", {})
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
                except Exception:
                    pass

            if running and now - last_shot >= SHOT_EVERY:
                last_shot = now
                for s in running:
                    try:
                        async with http.get(
                                f"http://127.0.0.1:{s['port']}/api/screen",
                                params={"format": "jpeg", "spectate": "1"},
                                timeout=aiohttp.ClientTimeout(total=8)) as r:
                            if r.status == 200:
                                img = await r.read()
                                await loop.run_in_executor(
                                    None, put, f"live/{s['id']}.jpg", img,
                                    "image/jpeg", 4)
                                s["shot_at"] = round(now)
                    except Exception as exc:
                        if not s.get("shot_warned"):
                            s["shot_warned"] = True
                            print(f"thumbnail failed for {s['id']}: {exc}", flush=True)

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

        if tick % 30:
            continue
        for s in list(sessions.values()):
            work = s.get("work")
            if work and s["proc"].poll() is not None and work.exists():
                await loop.run_in_executor(
                    None, lambda w=work: shutil.rmtree(w, ignore_errors=True))
                # its thumbnail is nothing but storage cost once the run is over
                await loop.run_in_executor(None, drop, f"live/{s['id']}.jpg")
                print(f"reclaimed {work}", flush=True)


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
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg") is None:
        print("warning: ffmpeg not on PATH, runs will not render", flush=True)
    app = web.Application(client_max_size=64 << 20)
    app.add_routes([
        web.get("/", index),
        web.get("/health", health),
        web.post("/session", api_new),
        web.get("/api/sessions", api_sessions),
        web.get("/api/catalog", api_catalog),
        web.get("/videos/{name}", video_file),
        web.route("*", "/s/{sid}/{tail:.*}", proxy),
    ])
    app.on_startup.append(boot_in_background)
    app.on_startup.append(spawn_sweep)
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")),
                access_log=None)


if __name__ == "__main__":
    main()
