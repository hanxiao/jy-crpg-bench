"""Self-terminating benchmark run.

One game server process is one benchmark run. The process that played the game
is the one that decides the run is over, renders it, publishes it, and exits -
nothing outside has to watch a clock on its behalf. That keeps teardown local
to whichever node happens to be running the session, so the fleet scales by
adding nodes rather than by making one supervisor bigger.

Off unless QUNXIA_BENCH is set, so the interactive server is unaffected.
"""
import asyncio
import json
import os
import pathlib
import sys
import time
from health import clock, write_json

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "bench"))

ON = os.environ.get("QUNXIA_BENCH") == "1"
AGENT = os.environ.get("QUNXIA_BENCH_AGENT", "agent")
SID = os.environ.get("QUNXIA_BENCH_SID", "")
BUDGET = int(os.environ.get("QUNXIA_BENCH_BUDGET", "1200"))
IDLE = int(os.environ.get("QUNXIA_BENCH_IDLE", "600"))
BUCKET = os.environ.get("QUNXIA_GCS_BUCKET", "")
# A run can ask not to be listed. Smoke tests were reaching the public
# catalogue and ranking above real runs, including one that recorded a crashed
# machine as a model that did nothing.
PUBLISH = os.environ.get("QUNXIA_PUBLISH", "1") != "0"
RESULTS = pathlib.Path(os.environ.get("QUNXIA_RESULT_DIR", "/tmp/qunxia-results"))
VIDEOS = pathlib.Path(os.environ.get("QUNXIA_VIDEO_DIR", "/tmp/qunxia-videos"))
# Where this backend serves its own files from, used only when there is no
# bucket, ie local development. Distinct from SITE, which is the published
# catalogue and is not this service at all.
PUBLIC_BASE = os.environ.get("QUNXIA_PUBLIC_BASE", "").rstrip("/")
SITE = os.environ.get("QUNXIA_BENCH_SITE", "https://hanxiao.io/jy-crpg-bench/")
CATALOG_OBJECT = "catalog.json"

# Filled in by the server as the agent plays. Kept here rather than in the
# proxy so the numbers survive however the run is fronted.
# The one table both counters use: the warden's own, and the server's live
# histogram through warden.ALIAS. Importing the other way round would drag the
# emulator in.
# Spelling -> the key it names. Two spellings are one key only when they
# drive the same scancode: lshift and shift are both 304, but rshift is its
# own 303 (as in the native table), so it keeps its own row. The on-screen
# diagonal aliases are the arrow scancodes under second names (ne and
# upright both drive 273, the same as up), so they merge into the arrow's
# row the way lshift merges into shift's; kp9 keeps its own 265.
ALIAS = {
    "esc": "escape", "cancel": "escape", "back": "escape",
    "return": "enter", "ok": "enter", "confirm": "enter",
    "yes": "y", "no": "n",
    "lshift": "shift", "lctrl": "ctrl", "lalt": "alt",
    "upright": "up", "ne": "up",
    "downleft": "down", "sw": "down",
    "downright": "right", "se": "right",
    "upleft": "left", "nw": "left",
    "quote": "'", "comma": ",", "minus": "-", "period": ".", "slash": "/",
    "semicolon": ";", "equals": "=", "leftbracket": "[", "backslash": "\\",
    "rightbracket": "]", "backquote": "`",
}

run = {"playable": None, "first": None, "last": None, "gaps": [], "keys": {},
       "deadline": None, "last_clock": None,
       # Request errors have no counter; the historical zero was a placeholder.
       "reads": 0, "errors": None, "actions": 0, "key_events": 0,
       "input_frames": 0, "wait_calls": 0,
       "meaningful": 0, "oscillation": 0, "curve": [],
       "scenes": 1, "frontier": 0,
       "bigmap": False, "exit_acts": None, "exit_secs": None,
       # the game's own character and shared-inventory values
       "level": None, "exp": None, "hp": None, "maxhp": None, "skills": None,
       "items": None, "reputation": None, "potential": None,
       "inventory_distinct": None, "picked_item": None,
       # Retained for metrics compatibility; the fixed deadline grants no credit.
       "credit": 0.0,
       "done": None, "result": None}


def playable_now():
    """Called once the savestate is in and the agent may act."""
    run["playable"] = time.time()
    run["deadline"] = clock() + BUDGET
    run["last_clock"] = clock()


def check_time():
    """End at the fixed monotonic deadline, also from inside an input action."""
    if run["deadline"] is not None and clock() >= run["deadline"] and not run["done"]:
        run["done"] = "time"


def note_action(keys, label="", input_frames=0):
    """Record a decision's submitted keys and requested held frames.

    A wait is still a decision call and therefore participates in timing, but
    it is recorded separately from key submissions. These totals are recorded
    before execution, so they also include steps an interrupted call may not
    finish; they are not measurements of executed keys or frames.
    """
    now = time.time()
    if run["last"] is not None:
        run["gaps"].append(now - run["last"])
    else:
        run["first"] = now
    run["last"] = now
    run["last_clock"] = clock()
    run["actions"] += 1
    if not keys:
        run["wait_calls"] += 1
    run["key_events"] += len(keys)
    run["input_frames"] += input_frames
    for k in keys or []:
        # under the name the key is known by, not the spelling that arrived
        k = ALIAS.get(k, k)
        run["keys"][k] = run["keys"].get(k, 0) + 1


def note_read():
    run["reads"] += 1


def ended_payload():
    """What an agent gets once its run is over. Present as soon as the run is
    called, so a late request is answered even while the video renders."""
    if not run["done"]:
        return None
    res = run["result"] or {}
    if not res:
        return {"ok": False, "ended": True, "valid": None, "message": "Run stopped; validating completion."}
    return {"ok": True, "ended": True,
            "message": "This benchmark run has ended. Stop playing.",
            "agent": AGENT, "reason": run["done"], "why": why_text(),
            "actions": run["actions"],
            "key_events": run["key_events"],
            "input_frames": run["input_frames"],
            "wait_calls": run["wait_calls"],
            "played_seconds": round((run["last"] or run["playable"] or 0)
                                    - (run["playable"] or 0)),
            "video_url": res.get("video_url"),
            "poster_url": res.get("poster_url"),
            "video_pending": res.get("video_url") is None,
            "catalog_url": SITE}


def human(sec):
    sec = int(sec or 0)
    if sec < 120:
        return f"{sec} seconds"
    m, s = divmod(sec, 60)
    return f"{m} {'minute' if m == 1 else 'minutes'}" + (f" {s}s" if s else "")


def why_text():
    if run["done"] == "time":
        return f"the full {human(BUDGET)} budget was used"
    idle = human(time.time() - (run["last"] or run["playable"] or time.time()))
    if run["done"] == "never started":
        return f"no action was ever sent - the run sat unplayed for {idle}"
    return (f"no action arrived for {idle}, so the run was stopped early. "
            f"Spending that long on one step is a failure, not thinking")


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(q * len(xs)))], 2)


def timing():
    """The clock figures a card can show while the run is still going.

    metrics() is only assembled at teardown, so a live card had dashes where a
    finished one had numbers even though the warden had been tracking these
    from the first keypress."""
    if not ON or run["playable"] is None:
        return {}
    gaps = run["gaps"]
    return {
        "ttfa": round(run["first"] - run["playable"], 2) if run["first"] else None,
        # the deadline is on this process's monotonic clock, so only this
        # process can say how much of it is left
        "remaining": round(max(0.0, run["deadline"] - clock()), 2)
                     if run["deadline"] is not None else None,
        "gap_p50": pct(gaps, 0.5), "gap_p95": pct(gaps, 0.95),
        "reads": run["reads"], "errors": run["errors"],
    }


def metrics():
    playable = run["playable"] or time.time()
    played = max(0.0, (run["last"] or playable) - playable)
    n, gaps = run["actions"], run["gaps"]
    return {
        "id": SID, "agent": AGENT, "started": playable,
        "played": round(played), "budget": BUDGET,
        # `actions` is retained for published-schema compatibility. It means
        # model decision/API calls, not uniform emulator steps.
        "actions": n, "decision_calls": n, "reason": run["done"] or "time",
        "key_events": run["key_events"],
        "input_frames": run["input_frames"],
        "wait_calls": run["wait_calls"],
        "ttfa": round(run["first"] - playable, 2) if run["first"] else None,
        "aps": round(n / played, 3) if played > 0.5 and n else 0.0,
        "gap_p50": pct(gaps, 0.5), "gap_p95": pct(gaps, 0.95),
        "gap_max": round(max(gaps), 2) if gaps else None,
        "reads": run["reads"], "errors": run["errors"],
        # Read out of the emulated machine, not guessed from the picture.
        # `scenes` is a legacy field name for full-black segmentation; it does
        # not identify actual scenes. Distance is kept as a maximum, so pacing
        # back and forth cannot inflate it.
        "scenes": run["scenes"],
        "frontier": run["frontier"],
        # The first-black proxy remains diagnostic; bigmap is the separately
        # calibrated world-map signal.
        "bigmap": run["bigmap"],
        "exit_acts": run["exit_acts"], "exit_secs": run["exit_secs"],
        # What the character actually became. Level barely moves in twenty
        # minutes, which is itself the finding.
        **{k: run[k] for k in ("level", "exp", "hp", "maxhp", "skills",
                               "items", "reputation", "potential",
                               "inventory_distinct", "picked_item")},
        # There is no count of distinct places here on purpose. It was
        # measured off the framebuffer and the framebuffer cannot answer it:
        # the menu is an overlay whose size follows where you are, so no fixed
        # mask covers it, and a screen it tips reads as somewhere new. A five
        # tile corridor was reporting ten. Repetition and longest-stall went
        # with it, since both were that same count divided by actions. The
        # metrics below only need to know whether the screen reacted.
        # Share of adjacent decision results whose final frames differ. This is
        # diagnostic, not a uniform environment step or proof of movement.
        "meaningful": round(run["meaningful"] / n, 3) if n else 0.0,
        "meaningful_count": run["meaningful"],
        # A -> B -> A oscillation, the failure mode GVGAI-LLM names explicitly.
        "oscillation": round(run["oscillation"] / n, 3) if n else 0.0,
        # Progress against decision-call count. Submitted keys and requested
        # held frames are reported separately as key_events and input_frames.
        "curve": run["curve"][-200:],
        "keys": dict(sorted(run["keys"].items(), key=lambda kv: -kv[1])),
        "distinct_keys": len(run["keys"]),
    }


# ------------------------------------------------------------------ publish

def _bucket():
    if not BUCKET or not PUBLISH:
        return None
    from google.cloud import storage
    return storage.Client().bucket(BUCKET)


def publish(path: pathlib.Path):
    b = _bucket()
    if b is None:
        return f"{PUBLIC_BASE}/videos/{path.name}" if PUBLIC_BASE else None
    blob = b.blob(path.name)
    kind = {".mp4": "video/mp4", ".jpg": "image/jpeg",
            ".json": "application/json"}.get(path.suffix, "application/octet-stream")
    # Carry the hint into the upload instead of patching it after: one API
    # call, and no window in which the object is public under default cache
    # hints. publish_bytes does the same.
    blob.cache_control = "public, max-age=31536000, immutable"
    blob.upload_from_filename(str(path), content_type=kind)
    return f"https://storage.googleapis.com/{BUCKET}/{path.name}"


def publish_bytes(name, data, mime, max_age=31536000):
    b = _bucket()
    if b is None:
        out = pathlib.Path(os.environ.get("QUNXIA_LOCAL_PUBLIC",
                                          "/tmp/qunxia-public")) / name
        out.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, pathlib.Path):
            import shutil
            shutil.copyfile(data, out)
        else:
            out.write_bytes(data)
        return
    blob = b.blob(name)
    blob.cache_control = f"public, max-age={max_age}"
    if isinstance(data, pathlib.Path):
        blob.upload_from_filename(str(data), content_type=mime)
    else:
        blob.upload_from_string(data, content_type=mime)


def append_catalog(entry):
    """Nodes finish independently, so the shared list is written with a
    generation precondition and retried rather than last-write-wins."""
    b = _bucket()
    if b is None:
        local = pathlib.Path(os.environ.get("QUNXIA_CATALOG",
                                            "/tmp/qunxia-catalog.json"))
        runs = json.loads(local.read_text()) if local.exists() else []
        # Same upsert-by-id and 500 cap as the shared object, so the dev
        # catalogue cannot drift from what the board actually serves.
        runs = [entry] + [r for r in runs if r.get("id") != entry["id"]]
        local.write_text(json.dumps(runs[:500], indent=1))
        return
    from google.api_core.exceptions import PreconditionFailed
    for attempt in range(12):
        # get_blob fetches the metadata, so generation is a real number.
        # b.blob() alone leaves it None, which omits the precondition entirely
        # and quietly turns concurrent appends into last-write-wins.
        blob = b.get_blob(CATALOG_OBJECT)
        if blob is None:
            blob, runs, gen = b.blob(CATALOG_OBJECT), [], 0
        else:
            gen = blob.generation
            try:
                runs = json.loads(blob.download_as_bytes())
            except Exception:
                # A failed or corrupt download is not an empty catalogue:
                # reading it as one would replace the public leaderboard
                # with this single entry, since the generation precondition
                # still passes. Retry like a write conflict; the broker's
                # usage merge makes the same distinction.
                time.sleep(0.3 * (attempt + 1))
                continue
        runs = [entry] + [r for r in runs if r.get("id") != entry["id"]]
        # Carry the hint into the write, as the broker's merge does: one
        # API call, and no window in which the catalogue sits public under
        # default cache hints.
        blob.cache_control = "public, max-age=15"
        try:
            blob.upload_from_string(json.dumps(runs[:500]),
                                    content_type="application/json",
                                    if_generation_match=gen)
            return
        except PreconditionFailed:
            time.sleep(0.3 * (attempt + 1))
    raise RuntimeError("catalogue is too contended to append to")


def write_result(res):
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / f"{SID}.json", res)


# ------------------------------------------------------------------ the loop

async def warden(rec, health, action_lock, wait_frames, recording_snapshot=None):
    """Ends the run on whichever comes first - the clock or a long silence -
    then publishes it and takes the process down with it."""
    while run["playable"] is None:
        await asyncio.sleep(1)
    while not run["done"]:
        check_time()
        if run["done"]:
            break
        now = clock()
        if now - run["last_clock"] >= IDLE:
            run["done"] = "idle" if run["last"] else "never started"
            break
        await asyncio.sleep(min(.25, max(.01, run["deadline"] - now)))

    async with action_lock:
        try:
            await wait_frames(2)
            health.check()
        except Exception as exc:
            health.fail("finalization_wait_failed", source="finalization",
                        exception_type=type(exc).__name__)
            return
        health.set_phase("finalizing")
    res = dict(metrics(), valid=True, complete=False, why=why_text(), video_url=None,
               rendered_artifacts_uploaded=False, error=None)
    run["result"] = res
    write_result(res)                      # answer late callers straight away
    events = None
    try:
        events = recording_snapshot() if recording_snapshot else list(rec["events"])
        from render import render
        VIDEOS.mkdir(parents=True, exist_ok=True)
        out = VIDEOS / f"{AGENT}-{SID}.mp4"
        loop = asyncio.get_running_loop()
        # Read a fixed committed prefix while the producer continues running.
        snap = dict(rec, events=events, duration=getattr(events, "duration", None))
        info = await loop.run_in_executor(None, lambda: render(snap, out, AGENT,
            timeline_extra=dict(agent=AGENT, id=SID, curve=run["curve"][-400:], keys=run["keys"])))
        timeline = info.pop("timeline", None)
        poster = info.pop("poster", None)
        res["video"] = {k: v for k, v in info.items() if k != "path"}
        res["video_url"] = await loop.run_in_executor(None, publish, out)
        # The still the card shows before the video is fetched. Without it a
        # thumbnail is a blank box until it scrolls into view, and on iOS
        # often after that too.
        if poster:
            res["poster_url"] = await loop.run_in_executor(
                None, publish, pathlib.Path(poster))
        # The scrubbable replay: a few KB describing what happened when, so the
        # page can drive the MP4 rather than ship the whole recording.
        if timeline is not None:
            await loop.run_in_executor(None, publish_bytes, f"runs/{SID}.json",
                                       pathlib.Path(timeline), "application/json")
            res["timeline_url"] = f"runs/{SID}.json"
        # Only successful uploads of every rendered artifact permit cleanup.
        # With no bucket or publication disabled, publish() returns a local
        # URL instead. The raw recording journal is never uploaded here.
        res["rendered_artifacts_uploaded"] = bool(PUBLISH and BUCKET)
    except Exception as exc:
        res["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if hasattr(events, "close"):
            events.close()
    # The entry only exists once finalization is done, so it must carry the
    # same complete flag the result file ends with.
    res["complete"] = True
    try:
        await asyncio.get_running_loop().run_in_executor(None, append_catalog, res)
    except Exception as exc:
        res["error"] = (res["error"] or "") + f" catalogue: {exc}"
    write_result(res)
    print(f"bench run {SID} finished: {res['reason']} "
          f"{res['actions']} actions -> {res.get('video_url')}", flush=True)
    await asyncio.sleep(1)                 # let the last reply flush
    os._exit(0)
