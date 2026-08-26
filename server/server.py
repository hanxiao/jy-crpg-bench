#!/usr/bin/env python3
"""Headless 金庸群俠傳 for the browser.

Runs the DOS game through DOSBox Pure with no display, and streams the VGA
framebuffer to a canvas as deflated 16x10 tile deltas. Keyboard input comes
back over the same socket. No audio.
"""
import asyncio
import base64
import collections
import ctypes
import hashlib
import io
import json
import os
import pathlib
import sys
import threading
import time
import traceback
import zlib

from aiohttp import WSMsgType, web
from PIL import Image

from prompt import system_prompt

ROOT = pathlib.Path(__file__).resolve().parent
LIB = ctypes.CDLL(str(ROOT / "libqunxia.so"))
CORE = os.environ.get("QUNXIA_CORE", str(ROOT.parent / "cores" / "dosbox_pure_libretro.so"))
GAME = os.environ.get("QUNXIA_GAME", str(ROOT.parent / "game" / "PLAY.BAT"))
SAVES = os.environ.get("QUNXIA_SAVES", str(ROOT.parent / "saves"))
PORT = int(os.environ.get("PORT", "8080"))
SEND_HZ = float(os.environ.get("QUNXIA_SEND_HZ", "20"))

LIB.core_set_option.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
LIB.core_init.argtypes = [ctypes.c_char_p] * 3
LIB.core_init.restype = ctypes.c_bool
LIB.core_key.argtypes = [ctypes.c_int, ctypes.c_bool]
LIB.core_fps.restype = ctypes.c_double
LIB.core_frame_serial.restype = ctypes.c_uint64
LIB.core_last_error.restype = ctypes.c_char_p
LIB.fb_encode_delta.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
LIB.fb_encode_delta.restype = ctypes.c_int
LIB.core_frame_hash.restype = ctypes.c_uint64
LIB.core_reset.restype = None
LIB.fb_reset.restype = None
LIB.fb_snapshot.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int,
                            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
LIB.fb_snapshot.restype = ctypes.c_int
LIB.core_release_all_keys.restype = None
LIB.core_save_state.argtypes = [ctypes.c_char_p]
LIB.core_save_state.restype = ctypes.c_bool
LIB.core_load_state.argtypes = [ctypes.c_char_p]
LIB.core_load_state.restype = ctypes.c_bool

BUF = ctypes.create_string_buffer(4 << 20)

# Key name -> RETROK. Same vocabulary as the native runner.
KEYS = {
    "up": 273, "down": 274, "right": 275, "left": 276,
    "enter": 13, "return": 13, "ok": 13, "space": 32,
    "esc": 27, "escape": 27, "cancel": 27,
    "tab": 9, "backspace": 8, "delete": 127,
    "shift": 304, "ctrl": 306, "alt": 308,
    "home": 278, "end": 279, "pageup": 280, "pagedown": 281,
}
for _i, _c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    KEYS[_c] = 97 + _i
for _d in range(10):
    KEYS[str(_d)] = 48 + _d
for _f in range(1, 13):
    KEYS[f"f{_f}"] = 281 + _f
for _k, _v in {";": 59, "'": 39, ",": 44, ".": 46, "/": 47, "-": 45, "=": 61,
               "[": 91, "]": 93, "\\": 92, "`": 96}.items():
    KEYS[_k] = _v
for _n in range(10):                      # numpad; the game accepts these for movement
    KEYS[f"kp{_n}"] = 256 + _n
KEYS["kpenter"] = 271
# The four movement axes are screen diagonals. Verified byte-identical to the
# arrows, so these are aliases that say what actually happens on screen.
for _alias, _code in {"upright": 273, "ne": 273,      # == up    == kp9
                      "downleft": 274, "sw": 274,     # == down  == kp1
                      "downright": 275, "se": 275,    # == right == kp3
                      "upleft": 276, "nw": 276}.items():  # == left == kp7
    KEYS[_alias] = _code

# Native resolution only, so the largest frame the core produces is 640x400.
SNAP = ctypes.create_string_buffer(640 * 400 * 3 + 4096)
api_lock = asyncio.Lock()     # one action at a time; the game is single-player
paused = threading.Event()    # held while the core is rebooted, so retro_reset
                              # is never called underneath a running retro_run

clients: set[web.WebSocketResponse] = set()
stats = {"frames": 0, "sent": 0, "bytes": 0, "tiles": 0, "dropped": 0,
         "pump_errors": 0, "last_error": "", "pump_ticks": 0, "pump_stage": "init",
         "queued": 0}
SEND_TIMEOUT = float(os.environ.get("QUNXIA_SEND_TIMEOUT", "3"))
# Recording. Tile deltas are what the stream already produces, so a recording is
# just those kept with timestamps, plus the keys that caused them.
IDLE_AFTER = 3.0          # no action for this long and the tail is idle
IDLE_TAIL = 30.0          # of which only the last this much is kept
KEYFRAME_EVERY = 30.0     # so pruning can always start from a whole picture
REC_MAX_BYTES = 12 << 20
LOCK_TIMEOUT = float(os.environ.get("QUNXIA_LOCK_TIMEOUT", "30"))
# Reset restores this rather than rebooting. It puts the agent in the opening
# room with a character already made, because creating one means driving the
# 注音 IME, which is a puzzle about input methods and not about the game.
START_STATE = os.environ.get("QUNXIA_START_STATE", str(ROOT.parent / "saves" / "start.state"))

# Everything anyone does to this session, so the page can show who is doing
# what. The game is shared, so this doubles as "why did the screen just move".
history: collections.deque = collections.deque(maxlen=300)
_seq = [0]
# Counted per game, so a reset starts a fresh session rather than continuing one.
session = {"started": time.time(), "actions": 0, "by_api": 0, "by_web": 0}
agents: collections.Counter = collections.Counter()
rec: dict = {"started": time.time(), "events": [], "bytes": 0, "last_key": 0.0,
             "last_activity": time.time(), "actor": ""}
THUMB_W = 150
THUMB_KEEP = 40          # only the newest entries carry an image, to bound memory


def make_thumb():
    """Small WebP of the current screen, for the activity panel."""
    w = ctypes.c_int(0)
    h = ctypes.c_int(0)
    n = LIB.fb_snapshot(SNAP, len(SNAP), 1, ctypes.byref(w), ctypes.byref(h))
    if n <= 0:
        return None
    img = Image.frombytes("RGB", (w.value, h.value), SNAP.raw[:n])
    img = img.resize((THUMB_W, max(1, round(THUMB_W * h.value / w.value))), Image.NEAREST)
    out = io.BytesIO()
    img.save(out, "WEBP", quality=72, method=0)
    return "data:image/webp;base64," + base64.b64encode(out.getvalue()).decode()


def log_action(src, verb, target, detail="", ok=True, thumb=False):
    _seq[0] += 1
    entry = {"id": _seq[0], "at": time.time(), "src": src, "verb": verb,
             "target": str(target)[:60], "detail": str(detail)[:60], "ok": ok}
    if thumb:
        try:
            entry["thumb"] = make_thumb()
        except Exception:
            pass
        # drop images from older entries so the buffer stays small
        withimg = [e for e in history if e.get("thumb")]
        for e in withimg[:max(0, len(withimg) - THUMB_KEEP + 1)]:
            e.pop("thumb", None)
    if verb in ("KEY", "KEYS", "TEXT", "WAIT"):
        rec_note_activity()
        session["actions"] += 1
        session["by_web" if src == "web" else "by_api"] += 1
        agents[src] += 1
    history.append(entry)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return entry
    asyncio.create_task(broadcast_log(entry))
    return entry


async def _send_one(ws, data, text):
    """One send, bounded. A peer that vanished without closing the TCP
    connection blocks forever once its window fills, so every send needs a
    deadline of its own."""
    try:
        async with asyncio.timeout(SEND_TIMEOUT):
            if text:
                await ws.send_str(data)
            else:
                await ws.send_bytes(data)
        return ws, True
    except Exception:
        return ws, False


async def fanout(data, text=False):
    """Send to every client at once and drop the ones that fail.

    Sending serially meant a single stuck client stalled the broadcast for
    everyone, which is how streaming died while the emulator kept running.
    """
    targets = []
    for ws in list(clients):
        if ws.closed:
            clients.discard(ws)
        else:
            targets.append(ws)
    if not targets:
        return
    for ws, ok in await asyncio.gather(*(_send_one(ws, data, text) for ws in targets)):
        if not ok:
            clients.discard(ws)
            stats["dropped"] += 1


async def broadcast_log(entry):
    await fanout(json.dumps({"t": "log", "e": [entry], "s": session_summary()}), text=True)


def emulate():
    """Own thread. ctypes drops the GIL for each call, so asyncio keeps running."""
    budget = 1.0 / max(1.0, LIB.core_fps())
    nxt = time.perf_counter()
    while True:
        if paused.is_set():
            time.sleep(0.02)
            nxt = time.perf_counter()
            continue
        LIB.core_run_frame()
        stats["frames"] += 1
        nxt += budget
        delay = nxt - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        elif delay < -0.25:
            nxt = time.perf_counter()


async def pump():
    """Encode a delta and fan it out, only when something actually changed.

    The body is guarded because a task created with create_task dies silently
    on an unhandled exception, and a dead pump looks exactly like a working
    server with a frozen picture.
    """
    period = 1.0 / SEND_HZ
    last_serial = -1
    last_key_at = 0.0
    while True:
        try:
            await asyncio.sleep(period)
            stats["pump_ticks"] += 1
            now = time.time()
            # A whole picture at intervals, so a pruned recording always has
            # somewhere to start replaying from.
            force = now - last_key_at >= KEYFRAME_EVERY
            serial = LIB.core_frame_serial()
            if serial == last_serial and not force:
                continue
            last_serial = serial
            stats["pump_stage"] = "encode"
            n = LIB.fb_encode_delta(BUF, len(BUF), 1 if force else 0)
            if n <= 0:
                continue
            count = int.from_bytes(BUF.raw[11:13], "little")
            if count == 0 and not force:
                continue
            if force:
                last_key_at = now
            stats["pump_stage"] = "compress"
            payload = zlib.compress(BUF.raw[:n], 6)
            rec_add("f", payload, keyframe=force)
            if not clients:
                stats["pump_stage"] = "idle"
                continue
            stats["sent"] += 1
            stats["bytes"] += len(payload)
            stats["tiles"] += count
            stats["pump_stage"] = "fanout"
            await fanout(payload)
            stats["pump_stage"] = "idle"
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            stats["pump_errors"] += 1
            stats["last_error"] = f"{type(exc).__name__}: {exc}"
            print("pump error:", repr(exc), file=sys.stderr, flush=True)
            traceback.print_exc()
            await asyncio.sleep(0.5)


def rec_note_activity():
    rec["last_activity"] = time.time()


def rec_add(kind, payload=None, key=None, down=None, keyframe=False):
    now = time.time()
    ev = {"t": round(now - rec["started"], 3)}
    if kind == "f":
        ev["d"] = base64.b64encode(payload).decode()
        if keyframe:
            ev["k"] = 1
        rec["bytes"] += len(payload)
    else:
        ev["key"] = key
        ev["down"] = bool(down)
        if rec["actor"]:
            ev["who"] = rec["actor"]
    rec["events"].append(ev)
    rec_prune(now)


def rec_prune(now):
    """Two bounds. A long idle tail keeps only its last IDLE_TAIL seconds, so an
    untouched game does not grow forever while still showing its own animation.
    And the whole thing is capped, dropping from the front to the oldest
    keyframe that fits, because deltas cannot be replayed from the middle."""
    idle_for = now - rec["last_activity"]
    if idle_for > IDLE_AFTER:
        cutoff = round(now - rec["started"] - IDLE_TAIL, 3)
        head, tail = [], []
        for ev in rec["events"]:
            (tail if ev["t"] >= cutoff else head).append(ev)
        # only trailing idle frames are droppable; anything before the idle
        # stretch began is real history
        idle_began = round(now - rec["started"] - idle_for, 3)
        keep = [e for e in head if e["t"] <= idle_began] + tail
        if len(keep) < len(rec["events"]):
            rec["events"] = keep

    if rec["bytes"] > REC_MAX_BYTES:
        for i, ev in enumerate(rec["events"]):
            if ev.get("k") and i > 0:
                dropped = rec["events"][:i]
                rec["bytes"] -= sum(len(e.get("d", "")) * 3 // 4 for e in dropped)
                rec["events"] = rec["events"][i:]
                break


def rec_reset():
    rec.update(started=time.time(), events=[], bytes=0, last_key=0.0,
               last_activity=time.time())


def session_summary():
    return {"started_at": session["started"],
            "uptime_s": round(time.time() - session["started"], 1),
            "actions": session["actions"],
            "by_api": session["by_api"], "by_web": session["by_web"],
            "agents": dict(agents.most_common(8))}


async def reap():
    """Drop clients that closed without a handshake. Without this they linger,
    are counted, and are sent every frame."""
    while True:
        await asyncio.sleep(15)
        for ws in list(clients):
            if ws.closed:
                clients.discard(ws)


async def send_keyframe(ws):
    n = LIB.fb_encode_delta(BUF, len(BUF), 1)
    if n > 0:
        await ws.send_bytes(zlib.compress(BUF.raw[:n], 6))


async def ws_handler(request):
    ws = web.WebSocketResponse(max_msg_size=0, heartbeat=30)
    await ws.prepare(request)
    clients.add(ws)
    await send_keyframe(ws)
    await ws.send_str(json.dumps({"t": "log", "e": list(history)[-80:],
                                  "s": session_summary()}))
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            d = msg.json()
            t = d.get("t")
            if t == "key":
                name = str(d.get("k", "")).lower()
                code = KEYS.get(name)
                if code:
                    down = bool(d.get("down"))
                    rec["actor"] = "web"
                    LIB.core_key(code, down)
                    key_event(name, down)
                    if down:                      # keyup would just double every line
                        log_action("web", "KEY", name)
            elif t == "tap":
                name = str(d.get("k", "")).lower()
                code = KEYS.get(name)
                if code:
                    rec["actor"] = "web"
                    log_action("web", "KEY", name)
                    LIB.core_key(code, True)
                    key_event(name, True)
                    await asyncio.sleep(0.06)
                    LIB.core_key(code, False)
                    key_event(name, False)
            elif t == "keyframe":
                await send_keyframe(ws)
    finally:
        clients.discard(ws)
    return ws


def snapshot(fmt="png"):
    """The screen at native size.

    PNG by default: WebP is smaller and equally lossless, but PNG is what
    vision stacks handle most reliably, and being read correctly matters more
    here than the bytes. ?format=webp is there when size does matter.
    """
    w = ctypes.c_int(0)
    h = ctypes.c_int(0)
    n = LIB.fb_snapshot(SNAP, len(SNAP), 1, ctypes.byref(w), ctypes.byref(h))
    if n <= 0:
        return None, 0, 0, ""
    img = Image.frombytes("RGB", (w.value, h.value), SNAP.raw[:n])
    out = io.BytesIO()
    if fmt == "webp":
        img.save(out, "WEBP", lossless=True, method=4)
        mime = "image/webp"
    else:
        img.save(out, "PNG", optimize=True)
        mime = "image/png"
    return out.getvalue(), w.value, h.value, mime


async def settle(baseline, react=30, stable=9, maxframes=120):
    """Wait for the game to react, then for the picture to hold still.

    Three ways to be done. The picture stops changing; or it starts cycling,
    which is what a blinking cursor or an idle sprite loop does and which never
    goes still; or nothing happened at all within the react budget. Without the
    cycle test every animated screen ran to maxframes, and that wait is held
    under the action lock, so it set the floor on how fast several agents can
    take turns.
    """
    ft = 1.0 / max(1.0, LIB.core_fps())
    reacted = react == 0
    last, runs, n = baseline, 0, 0
    seen: dict[int, int] = {}
    while n < maxframes:
        await asyncio.sleep(ft)
        n += 1
        h = LIB.core_frame_hash()
        if not reacted:
            if h != baseline:
                reacted, runs, last = True, 0, h
                seen = {h: n}
            elif n >= react:
                break
            continue
        if h == last:
            runs += 1
            if n >= 6 and runs >= stable:
                break
        else:
            runs = 0
            last = h
            first = seen.get(h)
            if first is not None and n - first >= stable:
                break                      # animation loop, it will never settle
            seen.setdefault(h, n)
    return n, reacted


def key_event(name, down):
    """Tell browsers a key is physically down, so a held key stays lit for as
    long as it is held instead of blinking once when the action finishes."""
    if name:
        rec_add("k", key=name, down=down)
        asyncio.create_task(fanout(json.dumps({"t": "key", "k": name, "down": down}),
                                   text=True))


async def tap(code, hold_frames, name=None):
    ft = 1.0 / max(1.0, LIB.core_fps())
    key_event(name, True)
    LIB.core_key(code, True)
    try:
        await asyncio.sleep(ft * max(1, hold_frames))
    finally:
        LIB.core_key(code, False)
        key_event(name, False)
    await asyncio.sleep(ft * 2)


def held_note(steps):
    """Longest single press in this action, in seconds, when worth showing."""
    fps = max(1.0, LIB.core_fps())
    longest = max((v for k, v, *_ in steps if k != "wait"), default=0) / fps
    return f"{longest:.1f}s" if longest >= 0.25 else ""


async def run_action(request, steps, note, verb="KEY"):
    """steps: list of (retrok, hold_frames) or ("wait", seconds).

    Deliberately does not return a screenshot. Encoding a PNG for every
    keypress cost real CPU on a shared-core box and most of those images were
    never looked at. Ask for /api/screen when you actually want to see.

    One action runs at a time so the game stays coherent when several agents
    act on it, but a caller waiting behind others is told so instead of being
    left to hang.
    """
    stats["queued"] += 1
    try:
        await asyncio.wait_for(api_lock.acquire(), timeout=LOCK_TIMEOUT)
    except asyncio.TimeoutError:
        return web.json_response(
            {"ok": False, "error": "busy", "queued": stats["queued"],
             "hint": "another agent holds the game; retry"}, status=503)
    finally:
        stats["queued"] -= 1

    try:
        # Logged before the keys are sent, not after: the panel should show an
        # action starting, not report it once it is already over.
        rec["actor"] = actor(request)
        log_action(rec["actor"], verb, note, detail=held_note(steps))
        baseline = LIB.core_frame_hash()
        for step in steps:
            kind, val = step[0], step[1]
            if kind == "wait":
                await asyncio.sleep(val)
            else:
                await tap(kind, val, step[2] if len(step) > 2 else None)
        waited, changed = await settle(baseline)
    finally:
        api_lock.release()

    return web.json_response({
        "ok": True, "action": note, "changed": changed,
        "width": LIB.core_width(), "height": LIB.core_height(),
        "frame": LIB.core_frame_serial(), "settled_frames": waited,
    })


async def body_of(request):
    try:
        return await request.json()
    except Exception:
        return {}


def keycode(name):
    return KEYS.get(str(name).strip().lower())


# Readable stand-in names, in the register of the game, so an agent that did
# not introduce itself is still something you can point at in the log.
_ADJ = ("swift", "jade", "iron", "azure", "silent", "crimson", "golden", "misty",
        "lone", "wandering", "ancient", "white", "shadow", "drunken", "nine", "cloud")
_NOUN = ("crane", "tiger", "dragon", "sparrow", "blade", "monk", "fox", "phoenix",
         "serpent", "willow", "peak", "lotus", "sabre", "pilgrim", "heron", "bell")


def anon_name(seed: str) -> str:
    h = hashlib.blake2s(seed.encode(), digest_size=4).digest()
    return f"{_ADJ[h[0] % len(_ADJ)]}-{_NOUN[h[1] % len(_NOUN)]}-{h[2]:02x}"


def actor(request):
    """Who is acting.

    An agent should name itself with an X-Agent header. When it does not, fall
    back to a short stable id derived from its address and client string, so
    two anonymous agents are still told apart instead of both showing as "api".
    """
    given = request.headers.get("X-Agent") or request.query.get("agent")
    if given:
        clean = "".join(c for c in given if c.isalnum() or c in "-_.")[:16]
        if clean:
            return clean
    peer = request.remote or "?"
    ua = request.headers.get("User-Agent", "")
    return anon_name(f"{peer}|{ua}")


async def api_key(request):
    d = await body_of(request)
    code = keycode(d.get("key", ""))
    if not code:
        return web.json_response({"ok": False, "error": "unknown key"}, status=400)
    hold = int(d.get("hold", 4))
    times = max(1, min(int(d.get("times", 1)), 100))
    name = str(d.get("key")).strip().lower()
    steps = []
    for i in range(times):
        steps.append((code, hold, name))
        if i != times - 1:
            steps.append(("wait", 0.08))
    return await run_action(request, steps, name + (f" x{times}" if times > 1 else ""))


async def api_keys(request):
    d = await body_of(request)
    names = d.get("keys") or []
    codes = [keycode(k) for k in names]
    if not names or any(c is None for c in codes):
        return web.json_response({"ok": False, "error": "unknown key in list"}, status=400)
    hold = int(d.get("hold", 4))
    steps = []
    for i, c in enumerate(codes):
        steps.append((c, hold, str(names[i]).strip().lower()))
        if i != len(codes) - 1:
            steps.append(("wait", 0.08))
    return await run_action(request, steps, " ".join(map(str, names)), verb="KEYS")


async def api_wait(request):
    d = await body_of(request)
    ms = max(0, min(int(d.get("ms", 1000)), 60000))
    return await run_action(request, [("wait", ms / 1000)], f"{ms}ms", verb="WAIT")


async def api_screen(request):
    """The only way to look at the screen. JSON, or ?format=png|webp for bytes."""
    fmt = request.query.get("format", "")
    log_action(actor(request), "GET", "screen", thumb=True)
    data, w, h, mime = snapshot("webp" if fmt == "webp" else "png")
    if not data:
        return web.json_response({"ok": False, "error": "no frame"}, status=503)
    if fmt in ("png", "webp"):
        return web.Response(body=data, content_type=mime)
    return web.json_response({
        "ok": True, "width": LIB.core_width(), "height": LIB.core_height(),
        "frame": LIB.core_frame_serial(), "image_width": w, "image_height": h,
        "image": f"data:{mime};base64," + base64.b64encode(data).decode(),
    })


def base_url(request):
    forwarded = request.headers.get("X-Forwarded-Proto")
    scheme = forwarded or request.scheme
    return f"{scheme}://{request.host}"


async def api_reset(request):
    """Hidden. Reboots the emulated machine back to the title screen and wipes
    the activity log. Unlisted in /api/help and 404s unless the token matches,
    so a visitor who stumbles on the path cannot wipe someone's game."""
    want = os.environ.get("QUNXIA_RESET_TOKEN")
    got = request.query.get("token") or request.headers.get("X-Reset-Token")
    if not want or got != want:
        raise web.HTTPNotFound()

    restored = False
    async with api_lock:
        paused.set()
        await asyncio.sleep(0.1)          # let the in-flight frame finish
        try:
            LIB.core_release_all_keys()
            if os.path.exists(START_STATE):
                restored = bool(LIB.core_load_state(START_STATE.encode()))
            if not restored:
                LIB.core_reset()           # no start state, fall back to a reboot
            LIB.fb_reset()
        finally:
            paused.clear()
        history.clear()
        _seq[0] = 0
        session.update(started=time.time(), actions=0, by_api=0, by_web=0)
        agents.clear()
        rec_reset()
        await asyncio.sleep(0.4 if restored else 1.5)

    await fanout(json.dumps({"t": "clear"}), text=True)
    for ws in list(clients):
        try:
            async with asyncio.timeout(SEND_TIMEOUT):
                await send_keyframe(ws)
        except Exception:
            clients.discard(ws)
    log_action("api", "RESET", "restored start state" if restored else "rebooted to title")
    return web.json_response({"ok": True, "reset": True, "restored": restored})


async def api_snapshot(request):
    """Hidden. Writes the current position as the state /api/reset restores."""
    want = os.environ.get("QUNXIA_RESET_TOKEN")
    got = request.query.get("token") or request.headers.get("X-Reset-Token")
    if not want or got != want:
        raise web.HTTPNotFound()
    async with api_lock:
        os.makedirs(os.path.dirname(START_STATE), exist_ok=True)
        ok = bool(LIB.core_save_state(START_STATE.encode()))
    size = os.path.getsize(START_STATE) if ok and os.path.exists(START_STATE) else 0
    log_action("api", "RESET", "saved start state" if ok else "start state failed", ok=ok)
    return web.json_response({"ok": ok, "path": START_STATE, "bytes": size})


async def api_recording(_request):
    """The session so far as tile deltas and key presses, for playback."""
    return web.json_response({
        "started": rec["started"],
        "duration": round(time.time() - rec["started"], 2),
        "events": rec["events"],
        "bytes": rec["bytes"],
    })


async def api_history(_request):
    return web.json_response({"history": list(history)})


async def api_help(request):
    # Not logged: the page fetches this on every load to fill the copy box, so
    # logging it fills the panel with entries nobody performed.
    lang = request.query.get("lang", "en")
    core_only = request.query.get("part") == "core"
    return web.Response(text=system_prompt(base_url(request), lang, core_only),
                        content_type="text/plain", charset="utf-8")


async def index(_request):
    return web.FileResponse(ROOT / "index.html")


async def status(_request):
    return web.json_response({
        "width": LIB.core_width(), "height": LIB.core_height(),
        "fps": round(LIB.core_fps(), 3), "frame": LIB.core_frame_serial(),
        "clients": len(clients), "session": session_summary(), **stats,
    })


def main():
    os.makedirs(SAVES, exist_ok=True)
    # Measured on this class of VM: 77000 cycles leaves only 1.75x headroom over
    # the 70.09 fps the core needs, which a shared-core instance cannot hold once
    # burst credits run out. 26800 (486DX2-66, period-correct for a 1996 game)
    # runs 6.7x faster than needed, so ~15% of a core.
    for k, v in {
        "dosbox_pure_cycles": os.environ.get("QUNXIA_CYCLES", "26800"),
        "dosbox_pure_sblaster_type": "none",   # no audio is streamed; do not synthesise it
        "dosbox_pure_midi": "disabled",
    }.items():
        LIB.core_set_option(k.encode(), v.encode())
    if not LIB.core_init(CORE.encode(), GAME.encode(), SAVES.encode()):
        raise SystemExit("core_init failed: " + LIB.core_last_error().decode())
    threading.Thread(target=emulate, daemon=True).start()

    app = web.Application()
    app.add_routes([
        web.get("/", index),
        web.get("/ws", ws_handler),
        web.get("/status", status),
        web.get("/api/screen", api_screen),
        web.get("/api/help", api_help),
        web.get("/api/history", api_history),
        web.get("/api/recording", api_recording),
        web.post("/api/reset", api_reset),
        web.post("/api/snapshot", api_snapshot),
        web.post("/api/key", api_key),
        web.post("/api/keys", api_keys),
        web.post("/api/wait", api_wait),
    ])
    # on_startup handlers are awaited, so the pump has to be detached as a task
    # rather than returned, or startup blocks on a loop that never ends.
    async def _spawn_pump(a):
        a["pump"] = asyncio.create_task(pump())
        a["reaper"] = asyncio.create_task(reap())
    app.on_startup.append(_spawn_pump)
    web.run_app(app, host="0.0.0.0", port=PORT, access_log=None)


if __name__ == "__main__":
    main()
