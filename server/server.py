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
import hmac
import io
import json
import math
import struct
import os
import pathlib
import re
import sys
import threading
import time
import traceback
import zlib

from aiohttp import WSMsgType, web
from PIL import Image

import warden
from state_reader import decode_inventory, inventory_gained

from prompt import system_prompt
from health import Health, EnvironmentFailure
from input_wait import InputBudget, current_budget
from peers import Peer
from recording_store import RecordingStore
from recording import RecordingAPI
from storage import validate_recording_directory

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
LIB.core_key_before_deadline.argtypes = [ctypes.c_int, ctypes.c_bool, ctypes.c_double]
LIB.core_key_before_deadline.restype = ctypes.c_bool
LIB.core_fps.restype = ctypes.c_double
LIB.core_frame_serial.restype = ctypes.c_uint64
LIB.core_ticks.restype = ctypes.c_uint64
LIB.core_last_error.restype = ctypes.c_char_p
LIB.fb_encode_delta.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
LIB.fb_encode_delta.restype = ctypes.c_int
LIB.core_frame_hash.restype = ctypes.c_uint64
LIB.fb_luma.restype = ctypes.c_int
LIB.core_state_peek.argtypes = [ctypes.POINTER(ctypes.c_size_t), ctypes.c_int,
                                ctypes.POINTER(ctypes.c_int16)]
LIB.core_state_peek.restype = ctypes.c_int
LIB.core_state_size.restype = ctypes.c_size_t
LIB.core_state_copy.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
LIB.core_state_copy.restype = ctypes.c_int
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

health = None
recording_store = recording_api = None
recording_blocked = False

class RecordingUnavailable(RuntimeError):
    pass

peers = {}
emulator_stop = threading.Event()
BUF = ctypes.create_string_buffer(4 << 20)

# Key name -> RETROK. Same vocabulary as the native runner.
# One key, several accepted spellings. Counted under whatever the agent
# happened to type, a single key split across two entries in the histogram,
# and since both spellings draw the same icon it read as a duplicated row.
# The table lives in warden so the two counters cannot disagree.
def canon(name):
    return warden.ALIAS.get(name, name)


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
api_lock = None     # one action at a time; the game is single-player
paused = threading.Event()    # held while the core is rebooted, so retro_reset
                              # is never called underneath a running retro_run
paused_ack = threading.Event()

clients: set[web.WebSocketResponse] = set()
stats = {"frames": 0, "sent": 0, "bytes": 0, "tiles": 0, "dropped": 0,
         "pump_errors": 0, "last_error": "", "pump_ticks": 0, "pump_stage": "init",
         "queued": 0}
SEND_TIMEOUT = float(os.environ.get("QUNXIA_SEND_TIMEOUT", "3"))
# Recording. Tile deltas are what the stream already produces, so a recording is
# just those kept with timestamps, plus the keys that caused them.
KEYFRAME_EVERY = 30.0     # periodic complete frames in the disk recording
# A benchmark run wants the whole session, not a rolling tail.
LOCK_TIMEOUT = float(os.environ.get("QUNXIA_LOCK_TIMEOUT", "30"))
# Four frames can fit inside one slow game-loop redraw, so a short keydown and
# keyup may be consumed together without producing a map step. Ten frames are
# still well below the game's held-key repeat delay, but reliably span a loop
# iteration. Measure all tap phases against emulated frames rather than wall
# time so host scheduling cannot shorten a pulse.
DEFAULT_TAP_FRAMES = 10
KEY_RELEASE_FRAMES = 2
BETWEEN_TAPS_FRAMES = 6
DEFAULT_STABLE_FRAMES = 9
DEFAULT_SETTLE_MAX_FRAMES = 120
MAX_STABLE_FRAMES = 600
MAX_HOLD_FRAMES = 1200
MAX_GAP_FRAMES = 600
MAX_KEYS_PER_ACTION = 100
MAX_ACTION_FRAMES = 2800
MAX_WAIT_MS = 60000
MAX_HISTORY_LIMIT = 300
# Reset restores this rather than rebooting. It puts the agent in the opening
# room with a character already made, because creating one means driving the
# 注音 IME, which is a puzzle about input methods and not about the game.
START_STATE = os.environ.get("QUNXIA_START_STATE", str(ROOT.parent / "saves" / "start.state"))
STATE_DIR = os.environ.get("QUNXIA_STATE_DIR", str(ROOT.parent / "saves" / "states"))

# Everything anyone does to this session, so the page can show who is doing
# what. The game is shared, so this doubles as "why did the screen just move".
history: collections.deque = collections.deque(maxlen=300)
_seq = [0]
# Counted per game, so a reset starts a fresh session rather than continuing one.
session = {"started": time.time(), "actions": 0, "key_events": 0,
           "input_frames": 0, "wait_calls": 0, "by_api": 0, "by_web": 0}
# Every distinct place the agent has stood. The camera is locked to the
# character, so each tile of ground it reaches paints a different picture;
# walking back over old ground repeats one. Counting distinct pictures counts
# ground covered, and going in circles adds nothing, which is the point.
# Behavioural counters, following definitions from the game-agent benchmark
# literature so the numbers mean the same thing elsewhere:
#   screen-changing decision ratio - whether successive decision-result frames
#     differ. This is not a uniform environment-step metric because one
#     decision may contain several keys or a held key.
#   repetition rate        - AgentQuest (arXiv 2404.06411), repeated actions
#     over steps taken.
#   progress vs steps      - TextQuests (2507.23701) and BALROG (2411.13543)
#     both report progress as a curve against step count, not a single number.
beh = {"meaningful": 0, "oscillation": 0, "last": None, "prev": None,
       }
keyhist: dict = {}

# Where the character actually is, read out of the emulated machine rather than
# guessed from the picture. DOSBox Pure exposes no memory regions, so this
# serialises and reads two shorts out of the image: 3.6 ms, once per action,
# against the 312 ms that second of emulation costs anyway.
#
# The two offsets were found by walking and watching: both move by one per
# diagonal step and stop dead at walls, and outdoors kp7 moves one while kp9
# moves the other, so they are genuinely two axes. The savestate layout is
# fixed by the core build and the opening state, both of which ship here.
# A savestate's layout belongs to the core build that wrote it, so these
# cannot be constants: offsets found on one machine read as garbage on
# another, which is exactly what happened when offsets found on macOS were
# shipped to a Linux container. They are calibrated by /api/calibrate on
# whatever machine authors the opening state, and read back from beside it.
_POS_ARGS = (ctypes.c_size_t * 2)(0, 0)
_POS_OUT = (ctypes.c_int16 * 2)()



# A scene change blacks the screen out. Measured: the opening room reads 92,
# and a transition drops it near zero, so the threshold is nowhere near
# anything the game draws normally.
DARK = 12

# ---------------------------------------------------------------- game stats
#
# The game's own character records, read out of a serialised machine. This only
# ever serialises - it never loads a state back, which is the operation that
# crashed DOS - so it is safe to do while an agent is playing.
#
# The layout is the save file's, taken from the hojy reimplementation and
# checked against the game's own shipped RANGER.GRP: 320 records of 182 bytes,
# and across all 320 only two break hp <= maxHp or mp <= maxMp.
CHAR_SZ = 182
CHAR_ANCHOR = ("程靈素", 2)          # this NPC's name occurs once in the image
CHAR_CHECK = (("胡斐", 1), ("苗人鳳", 3))
# Byte offsets inside one record.
C_NAME, C_LEVEL, C_EXP, C_HP, C_MAXHP = 8, 30, 32, 34, 36
C_STAMINA, C_MP, C_MAXMP = 42, 82, 84
C_ATTACK, C_INTEGRITY, C_REPUTATION, C_POTENTIAL = 86, 112, 118, 120
C_SKILLS = 126

hero = {"base": None, "buf": None, "cap": 0, "read": 0, "found": False,
         "level": None, "exp": None, "hp": None, "maxhp": None,
         "skills": None, "items": None, "reputation": None, "potential": None,
         "inventory_distinct": None, "picked_item": None,
         "inventory_baseline": None}


def _state_bytes():
    if hero["buf"] is None:
        cap = LIB.core_state_size()
        if not cap:
            return None
        hero["cap"] = cap
        hero["buf"] = ctypes.create_string_buffer(cap)
    n = LIB.core_state_copy(hero["buf"], hero["cap"])
    return hero["buf"].raw[:n] if n > 0 else None


def _locate(mem):
    """Where the character array sits in this image.

    Anchored on a name and confirmed by two neighbours at the right stride.
    A first hit is not enough: these names appear more than once, and the
    serialised layout moves between runs.
    """
    pat = CHAR_ANCHOR[0].encode("big5")
    i = mem.find(pat)
    while i != -1:
        base = i - C_NAME - CHAR_ANCHOR[1] * CHAR_SZ
        if base >= 0 and all(
                mem[base + cid * CHAR_SZ + C_NAME:
                    base + cid * CHAR_SZ + C_NAME + 10].split(b"\0")[0]
                == nm.encode("big5") for nm, cid in CHAR_CHECK):
            return base
        i = mem.find(pat, i + 1)
    return None


def read_stats():
    """Read the protagonist and public inventory from the emulated machine."""
    mem = _state_bytes()
    if mem is None:
        return
    base = hero["base"]
    at = base + CHAR_ANCHOR[1] * CHAR_SZ + C_NAME if base is not None else None
    if at is None or mem[at:at + 6] != CHAR_ANCHOR[0].encode("big5"):
        base = _locate(mem)          # moved, or never found
        hero["base"] = base
    if base is None:
        return
    b = mem[base: base + CHAR_SZ]
    hero["found"] = True
    hero["level"] = struct.unpack_from("<h", b, C_LEVEL)[0]
    hero["exp"] = struct.unpack_from("<H", b, C_EXP)[0]
    hero["hp"] = struct.unpack_from("<h", b, C_HP)[0]
    hero["maxhp"] = struct.unpack_from("<h", b, C_MAXHP)[0]
    hero["reputation"] = struct.unpack_from("<h", b, C_REPUTATION)[0]
    hero["potential"] = struct.unpack_from("<h", b, C_POTENTIAL)[0]
    hero["skills"] = sum(1 for v in struct.unpack_from("<10h", b, C_SKILLS) if v > 0)
    # The four values at offset 166 are role-local seed/AI slots, not the
    # player's inventory, so deliberately do not score or publish them.
    inventory = decode_inventory(mem, base)
    if inventory is not None:
        hero["inventory_distinct"] = len(inventory)
        opening = hero["inventory_baseline"]
        if opening is None:
            hero["inventory_baseline"] = dict(inventory)
            hero["picked_item"] = False
        elif inventory_gained(opening, inventory):
            hero["picked_item"] = True


# Off by default, and it stays off until there is a way to find the
# coordinates that does not involve reloading a savestate into a running
# machine. Doing that crashed DOS outright in the container - the session came
# back showing DOSBox Pure's "DOS Crashed" menu and stopped responding to keys
# - which is far too high a price for one column. Distance then reports as
# unmeasured, which the page already draws as a dash rather than a nought.
CALIBRATE = os.environ.get("QUNXIA_CALIBRATE") == "1"

world = {"scenes": 1, "banked": 0, "origin": None, "far": 0, "ok": False,
         "dark": False, "miss": 0, "tried": False,
         "bigmap": False, "exit_acts": None, "exit_secs": None,
         "checked_refs": False}


def position():
    """(x, y) in the game's own coordinates, or None if this read is no good.

    Mid-transition the coordinates are briefly nonsense - measured at
    (-13145, 27812) one action after a scene change, while the new scene was
    still loading. That is a reason to skip a sample, not to give up: only the
    core refusing to serialise at all disables the metric, because that will
    not fix itself."""
    if not world["ok"]:
        return None
    if LIB.core_state_peek(_POS_ARGS, 2, _POS_OUT) != 0:
        world["ok"] = False
        return None
    x, y = _POS_OUT[0], _POS_OUT[1]
    if not (0 <= x < 1200 and 0 <= y < 1200):
        # One of these is a scene still loading. A run of them means the
        # offsets are not what this build put there, and reporting a distance
        # of nought from that would be a lie rather than a gap.
        world["miss"] += 1
        if world["miss"] >= 8:
            world["ok"] = False
            print("position reads keep coming back wrong; giving up on them",
                  flush=True)
        return None
    world["miss"] = 0
    return x, y


# "Reached the world map", as a latch. The reference is a fingerprint of the
# big map captured just outside the spawn compound's exit by the offline
# harness - which is exactly where every run's first big-map entry lands,
# because every run starts in the same home. Validated for separability:
# frames on the map near spawn sit 0-4 cells from the reference, indoor
# frames sit 16+ away, and the threshold of 8 splits the gap.
import base64 as _b64
BIGMAP_REFS = [_b64.b64decode("AwMDAwMDAwMDAgIDAwMDAwICAgMCAgICAwICAgEAAQMCAgICAgICAgEAAQMDAwMCAgICAgEAAgMDAwMDAgEBAQEBAgMDAwMDAQEBAQEBAgMDAwMDAQEBAQEBAQICAgMD")]
BIGMAP_DIST = 8


def _fp_dist(a, b):
    return sum(1 for x, y in zip(a, b) if abs(x - y) > 1)


def looks_like_bigmap(fp):
    return fp is not None and any(_fp_dist(fp, r) <= BIGMAP_DIST
                                  for r in BIGMAP_REFS)


def enter_scene():
    """Count the transition and start the next scene.

    The scene count must not depend on position calibration: it was guarded by
    the position origin once, and with calibration off that guard made the
    counter structurally stuck at one - a run could cross a real fade and
    still read scenes=1. Caught by the positive control, not in the field.
    Distance banking still needs the origin; the count never did."""
    world["scenes"] += 1
    if world["origin"] is not None:
        world["banked"] += world["far"]
    world["origin"], world["far"] = None, 0
    # the first exit is the first real quality signal a run can give: how many
    # actions and how much clock it took to get out of the spawn scene at all
    if world["scenes"] == 2 and world["exit_acts"] is None:
        world["exit_acts"] = session["actions"]
        world["exit_secs"] = round(time.time() - session["started"], 1)
        if warden.ON and warden.run["playable"]:
            world["exit_secs"] = round(time.time() - warden.run["playable"], 1)


def note_move():
    """How much ground this action covered, and whether it changed scene.

    Distance is measured from where the character entered the current scene and
    kept only as a maximum, so walking back and forth cannot inflate it. That
    is exactly how the old screen-based count went wrong.

    The origin is deliberately not set from the frame the fade was seen on: the
    new scene is still loading then and its coordinates have not landed. It is
    picked up on the next action instead, which costs one step of distance and
    is worth it for a number that is not nonsense."""
    if world["dark"]:
        world["dark"] = False
        enter_scene()
        return
    p = position()
    if p is None:
        return
    o = world["origin"]
    if o is None:
        world["origin"], world["far"] = p, 0
        return
    # Chebyshev, not Manhattan: a step here is diagonal, moving both axes at
    # once, so Manhattan would call one step two tiles. This counts steps.
    d = max(abs(p[0] - o[0]), abs(p[1] - o[1]))
    # A step moves one tile, so a jump is the floor changing under you: a scene
    # change whose fade went unseen. Counted as one rather than allowed to
    # register as a huge distance.
    if d > world["far"] + 8:
        enter_scene()
        world["origin"], world["far"] = p, 0
        return
    world["far"] = max(world["far"], d)
curve: list = []          # (action index, meaningful) sampled as the run goes
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


def log_action(src, verb, target, detail="", ok=True, thumb=False,
               key_events=None, input_frames=0, wait_call=False):
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
        if key_events is None:
            key_events = 1 if verb in ("KEY", "TEXT") else 0
        session["key_events"] += key_events
        session["input_frames"] += input_frames
        session["wait_calls"] += int(wait_call or verb == "WAIT")
        session["by_web" if src == "web" else "by_api"] += 1
        agents[src] += 1
    history.append(entry)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return entry
    asyncio.create_task(broadcast_log(entry))
    return entry


def drop_peer(ws):
    clients.discard(ws)
    if peers.pop(ws, None) is not None:
        stats["dropped"] += 1


async def fanout(data, text=False):
    for ws in list(clients):
        peer = peers.get(ws)
        if ws.closed or peer is None:
            clients.discard(ws)
        else:
            peer.put(data, text)


async def broadcast_log(entry):
    await fanout(json.dumps({"t": "log", "e": [entry], "s": session_summary()}), text=True)


def emulate():
    """Own thread. ctypes drops the GIL for each call, so asyncio keeps running."""
    budget = 1.0 / max(1.0, LIB.core_fps())
    nxt = time.perf_counter()
    while not emulator_stop.is_set():
        if paused.is_set():
            paused_ack.set()
            time.sleep(0.02)
            nxt = time.perf_counter()
            continue
        paused_ack.clear()
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
            if recording_blocked:
                continue
            stats["pump_ticks"] += 1
            now = time.time()
            # Periodic complete frames preserve standalone replay boundaries.
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
    elif kind == "a":
        ev["act"] = key
        ev["label"] = down
        if rec["actor"]:
            ev["who"] = rec["actor"]
    else:
        ev["key"] = key
        ev["down"] = bool(down)
        if rec["actor"]:
            ev["who"] = rec["actor"]
    if recording_store:
        try:
            ok = recording_store.append(ev)
        except (OSError, BufferError) as exc:
            recording_store.error = str(exc)
            ok = False
        if not ok:
            block_recording()
            raise RecordingUnavailable(recording_store.error)
        rec["bytes"] = recording_store.committed_size


def block_recording():
    global recording_blocked
    recording_blocked = True
    paused.set()
    if warden.ON:
        health.fail("recording_failed")


def rec_reset():
    if recording_store:
        try:
            recording_store.reset(time.time())
        except OSError as exc:
            recording_store.error = str(exc)
            block_recording()
            raise RecordingUnavailable(str(exc)) from exc
        finally:
            rec.update(started=recording_store.started, events=[], bytes=recording_store.committed_size,
                       last_key=0.0, last_activity=time.time())
    else:
        rec.update(started=time.time(), events=[], bytes=0, last_key=0.0, last_activity=time.time())


# The camera is locked to the character, so the character sits at a fixed spot
# in the frame and the background is what says where you are. That patch is
# blanked before hashing: the sprite faces whichever way it last walked, which
# made one tile facing north-west a different place from the same tile facing
# south-east, so retracing your steps scored as new ground. Measured by
# diffing a frame against itself after a step out and a step back: the only
# pixels that moved were x 132-157, y 58-109 of 320x200. Held as fractions
# because the framebuffer is not promised at that size.
SPRITE = (120 / 320, 46 / 200, 170 / 320, 122 / 200)

# There is deliberately no mask for the menu. It is a panel down the left, and
# whether it tips the hash depends on how bright the scene behind it is, so it
# does inflate a screen-identity count. But it is x 20-61 in the opening room
# and x 20-160 on the world map: its width follows its contents, which follow
# where you are. A mask big enough for both would blank half the frame and
# take the background with it. That is what killed counting distinct places,
# not this one overlay - see the note on note_screen below.


def fingerprint():
    """A coarse signature of what is on screen, ignoring the character
    standing in front of it. Equal fingerprints mean the screen did not
    react; unequal ones do not mean you moved."""
    w = ctypes.c_int(0)
    h = ctypes.c_int(0)
    n = LIB.fb_snapshot(SNAP, len(SNAP), 1, ctypes.byref(w), ctypes.byref(h))
    if n <= 0:
        return None
    img = Image.frombytes("RGB", (w.value, h.value), SNAP.raw[:n]).convert("L")
    x0, y0, x1, y1 = SPRITE
    img.paste(0, (int(x0 * img.width), int(y0 * img.height),
                  int(x1 * img.width), int(y1 * img.height)))
    small = img.resize((12, 8), Image.BILINEAR)
    return bytes(v >> 5 for v in small.getdata())      # 8 levels of grey


# There was a dialogue detector here. It looked for a bright band across the
# lower rows and never once fired, on any run. Measured against 582 frames of
# real play: the brightest cell that region ever reaches is 5 of 7, and the
# test wanted 6. It was not mistuned by a little, it was outside the game's
# range in that part of the screen, so every run reported nought dialogue
# advances and that nought looked like a finding.
#
# Removed rather than retuned: picking a new threshold needs a frame known to
# hold a dialogue box to check against, and guessing one would just be the
# same mistake with a different number.


def note_bigmap(fp):
    """Latch when the screen is the world map.

    Negative control at runtime: the very first fingerprint of a session is
    the spawn interior, and if that matches the big-map reference the
    calibration cannot be trusted, so the latch disables itself for the run
    rather than report a false crossing."""
    if world["bigmap"] or fp is None:
        return
    if not world["checked_refs"]:
        world["checked_refs"] = True
        if looks_like_bigmap(fp):
            world["bigmap"] = None          # miscalibrated: report unmeasured
            print("bigmap reference matches the spawn interior; flag disabled",
                  flush=True)
            return
    # A later interior view can resemble the coarse reference even when the
    # opening negative control did not. Require at least one detected full-black
    # boundary before accepting the world-map fingerprint.
    if (world["bigmap"] is False and world["scenes"] >= 2
            and looks_like_bigmap(fp)):
        world["bigmap"] = True


def note_screen():
    """What the screen did in response to the last action.

    This deliberately does not try to say *where* the character is. It used to:
    it counted distinct fingerprints and called them places visited. Two
    things that are not places kept landing in that count. The character
    faces the way it walked, so retracing six steps scored three new places -
    fixable, and fixed, by blanking the sprite. The menu is the one that
    cannot be fixed: it is a panel whose width follows its contents, x 20-61
    indoors and x 20-160 outdoors, so no fixed mask covers it and a mask that
    did would blank the background the count depends on. Identifying a
    position from the framebuffer needs the game's own coordinates, not
    better heuristics on pixels, so the count is gone rather than
    approximated. What is left below only asks whether the screen reacted,
    which a hash can answer honestly.
    """
    fp = fingerprint()
    if fp is None:
        return
    note_bigmap(fp)
    before = beh["last"]
    if before is not None and fp != before:
        beh["meaningful"] += 1
    # A -> B -> A is the oscillation the literature calls out as the signature
    # of an agent that is busy without getting anywhere.
    if beh["prev"] is not None and fp == beh["prev"] and fp != before:
        beh["oscillation"] += 1
    beh["prev"], beh["last"] = before, fp
    if not curve or session["actions"] - curve[-1][0] >= 5:
        curve.append((session["actions"], beh["meaningful"]))
        del curve[:-400]


def session_summary():
    return {"started_at": session["started"],
            "uptime_s": round(time.time() - session["started"], 1),
            "actions": session["actions"],
            "decision_calls": session["actions"],
            "key_events": session["key_events"],
            "input_frames": session["input_frames"],
            "wait_calls": session["wait_calls"],
            "meaningful": beh["meaningful"],
            "oscillation": beh["oscillation"],
            "scenes": world["scenes"],
            "bigmap": world["bigmap"],
            "exit_acts": world["exit_acts"], "exit_secs": world["exit_secs"],
            "level": hero["level"], "exp": hero["exp"],
            "hp": hero["hp"], "maxhp": hero["maxhp"],
            "skills": hero["skills"], "items": hero["items"],
            "inventory_distinct": hero["inventory_distinct"],
            "picked_item": hero["picked_item"],
            "reputation": hero["reputation"], "potential": hero["potential"],
            "frontier": (world["banked"] + world["far"]) if world["ok"] else None,
            # the key histogram, so a card can draw its bars while the run is
            # still going rather than only once it has finished
            "keys": dict(sorted(keyhist.items(), key=lambda kv: -kv[1])[:12]),
            "by_api": session["by_api"], "by_web": session["by_web"],
            "agents": dict(agents.most_common(8)),
            **warden.timing()}


async def reap():
    """Drop clients that closed without a handshake. Without this they linger,
    are counted, and are sent every frame."""
    while True:
        await asyncio.sleep(15)
        for ws in list(clients):
            if ws.closed:
                clients.discard(ws)


async def send_keyframe(ws):
    # Encoding changes the shared delta baseline. Persist and broadcast that
    # full frame before any later delta is allowed to use it.
    n = LIB.fb_encode_delta(BUF, len(BUF), 1)
    if n > 0:
        payload = zlib.compress(BUF.raw[:n], 6)
        rec_add("f", payload, keyframe=True)
        await fanout(payload)


async def ws_handler(request):
    ws = web.WebSocketResponse(max_msg_size=4096, heartbeat=30, compress=False)
    await ws.prepare(request)
    clients.add(ws)
    peers[ws] = Peer(ws, SEND_TIMEOUT, drop_peer)
    try:
        await send_keyframe(ws)
    except BaseException:
        peers[ws].drop()
        raise
    peers[ws].put(json.dumps({"t": "log", "e": list(history)[-80:],
                                  "s": session_summary(), "c": list(curve)}), text=True)
    # code -> (name, core tick at keydown). Browser automation can emit keydown
    # and keyup within one emulated frame, so remember when each press reached
    # the core and fence short pulses on release.
    holding: dict[int, tuple[str, int]] = {}
    lock_held = False
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                d = msg.json()
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            t = d.get("t")
            if recording_blocked and not (t == "key" and not d.get("down")):
                continue
            if warden.ON and t in ("key", "tap"):
                continue
            if t == "key":
                name = str(d.get("k", "")).lower()
                code = KEYS.get(name)
                if code:
                    down = bool(d.get("down"))
                    if down and code not in holding:
                        if not lock_held:
                            lock_held = await acquire_action_lock()
                        if not lock_held:
                            log_action("web", "KEY", name, detail="busy", ok=False)
                            continue
                        try:
                            rec["actor"] = "web"
                            if await press_web_key(name, code, holding):
                                log_action("web", "KEY", name)
                        except BaseException:
                            if not holding and lock_held:
                                action_lock().release()
                                lock_held = False
                            raise
                    elif not down:
                        rec["actor"] = "web"
                        await release_web_key(name, code, holding)
                        if not holding and lock_held:
                            action_lock().release()
                            lock_held = False
            elif t == "tap":
                name = str(d.get("k", "")).lower()
                code = KEYS.get(name)
                if code and code not in holding:
                    borrowed = lock_held
                    if borrowed or await acquire_action_lock():
                        try:
                            rec["actor"] = "web"
                            log_action("web", "KEY", name)
                            await tap(code, DEFAULT_TAP_FRAMES, name)
                        finally:
                            if not borrowed:
                                action_lock().release()
                    else:
                        log_action("web", "KEY", name, detail="busy", ok=False)
            elif t == "keyframe":
                await send_keyframe(ws)
    finally:
        for code, (name, _) in list(holding.items()):
            LIB.core_key(code, False)
            try:
                key_event(name, False)
            except RecordingUnavailable:
                pass
        holding.clear()
        if lock_held:
            action_lock().release()
        peer = peers.get(ws)
        if peer:
            peer.drop()
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
    elif fmt == "jpeg":
        # only for catalogue thumbnails: shown about 320px wide and fetched by
        # every visitor, so bytes on the wire matter far more than fidelity
        img = img.resize((256, max(1, round(256 * h.value / w.value))), Image.BILINEAR)
        img.save(out, "JPEG", quality=52, optimize=True)
        mime = "image/jpeg"
    else:
        img.save(out, "PNG", optimize=True)
        mime = "image/png"
    return out.getvalue(), w.value, h.value, mime


async def settle(baseline, react=30, stable=DEFAULT_STABLE_FRAMES,
                 maxframes=DEFAULT_SETTLE_MAX_FRAMES):
    """Wait for the game to react, then for the picture to hold still.

    Three ways to be done. The picture stops changing; or it starts cycling,
    which is what a blinking cursor or an idle sprite loop does and which never
    goes still; or nothing happened at all within the react budget. Without the
    cycle test every animated screen ran to maxframes, and that wait is held
    under the action lock, so it set the floor on how fast several agents can
    take turns.
    """
    # A full reaction window can precede the requested stable run.
    maxframes = max(maxframes, react + stable)
    ft = 1.0 / max(1.0, LIB.core_fps())
    reacted = react == 0
    last, runs, n = baseline, 0, 0
    seen: dict[int, int] = {}
    while n < maxframes:
        await wait_core_frames(1)
        n += 1
        # A fully black frame can be brief and gone by the time this returns, so
        # record only that visible signal here. A luma sample is about a microsecond.
        if LIB.fb_luma() < DARK:
            world["dark"] = True
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


async def pause_emulator():
    """Stop between emulated frames before calling reset/serialize APIs."""
    paused.set()
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 2.0
    while not paused_ack.is_set():
        if loop.time() >= deadline:
            resume_emulator()
            if health:
                health.fail("pause_stalled")
            raise EnvironmentFailure("emulator did not pause")
        await asyncio.sleep(0.005)


def resume_emulator():
    if recording_blocked:
        return
    paused.clear()
    # Do not let a following pause observe the acknowledgement from this one.
    paused_ack.clear()


async def acquire_action_lock():
    """Acquire the one-player lease shared by REST and browser input."""
    stats["queued"] += 1
    try:
        await asyncio.wait_for(action_lock().acquire(), timeout=LOCK_TIMEOUT)
        return True
    except asyncio.TimeoutError:
        return False
    finally:
        stats["queued"] -= 1


def action_lock():
    if api_lock is None:
        raise RuntimeError("action lock is not initialized")
    return api_lock


async def press_web_key(name, code, holding):
    """Press a browser key once and remember the core tick it reached."""
    if code in holding:
        return False
    input_stage("keydown", key=name)
    send_key_down(code)
    holding[code] = (name, LIB.core_ticks())
    key_event(name, True)
    return True


async def release_web_key(name, code, holding):
    """Release a browser key after it has spanned enough emulated frames.

    Human holds that already exceed the minimum stop immediately. Very short
    taps are extended only to ``DEFAULT_TAP_FRAMES`` and followed by the normal
    release fence, making automated browser keypresses as reliable as the REST
    API without changing long-hold behaviour.
    """
    pressed = holding.get(code)
    if pressed is None:
        return False
    pressed_name, pressed_at = pressed
    elapsed = max(0, LIB.core_ticks() - pressed_at)
    remaining = max(0, DEFAULT_TAP_FRAMES - elapsed)
    budget = InputBudget(remaining + KEY_RELEASE_FRAMES, LIB.core_fps(), health,
                         check_runtime=check_input_runtime)
    token = current_budget.set(budget)
    try:
        try:
            if remaining:
                input_stage("browser_hold", key=pressed_name or name)
                await wait_core_frames(remaining)
        finally:
            # Cancellation or a dropped socket must never strand a movement key.
            LIB.core_key(code, False)
            holding.pop(code, None)
            key_event(pressed_name or name, False)
        input_stage("release", key=pressed_name or name)
        await wait_core_frames(KEY_RELEASE_FRAMES)
        budget.check()
        return True
    finally:
        current_budget.reset(token)
        if health:
            health.set_input()


def check_input_runtime(allow_finished=False):
    if recording_blocked:
        raise RecordingUnavailable(recording_store.error or "recording storage is paused")
    if not allow_finished and warden.ON:
        warden.check_time()
        if warden.run["done"]:
            raise web.HTTPGone(text=json.dumps(warden.ended_payload()), content_type="application/json")


def input_stage(stage, **details):
    budget = current_budget.get()
    if budget:
        budget.stage(stage, **details)
    elif health:
        health.set_input(stage=stage, **details)


def send_key_down(code):
    budget = current_budget.get()
    check_input_runtime()
    if budget:
        budget.check()
    deadline = budget.deadline if budget else 0
    if warden.ON and warden.run["deadline"] is not None:
        deadline = min(deadline, warden.run["deadline"]) if deadline else warden.run["deadline"]
    if deadline:
        if not LIB.core_key_before_deadline(code, True, deadline):
            check_input_runtime()
            if budget:
                budget.fail("input_frame_timeout")
            raise EnvironmentFailure("input_frame_timeout")
    else:
        LIB.core_key(code, True)


async def wait_core_frames(frames, allow_finished=False):
    """Keep the same absolute frame target while a slow core makes progress."""
    budget = current_budget.get() or InputBudget(
        max(1, int(frames)), LIB.core_fps(), health,
        check_runtime=lambda: check_input_runtime(allow_finished))
    await budget.wait(frames, LIB.core_ticks)


def key_event(name, down):
    """Tell browsers a key is physically down, so a held key stays lit for as
    long as it is held instead of blinking once when the action finishes."""
    if name:
        rec_add("k", key=name, down=down)
        asyncio.create_task(fanout(json.dumps({"t": "key", "k": name, "down": down}),
                                   text=True))


async def tap(code, hold_frames, name=None):
    pressed = False
    try:
        input_stage("keydown", key=name)
        send_key_down(code)
        pressed = True
        key_event(name, True)
        input_stage("hold", key=name)
        await wait_core_frames(hold_frames)
    finally:
        if pressed:
            LIB.core_key(code, False)
            key_event(name, False)
    input_stage("release", key=name)
    await wait_core_frames(KEY_RELEASE_FRAMES)


def held_note(steps):
    """Longest single press in this action, in seconds, when worth showing."""
    fps = max(1.0, LIB.core_fps())
    longest = max((v for k, v, *_ in steps if k not in ("wait", "frames")), default=0) / fps
    return f"{longest:.1f}s" if longest >= 0.25 else ""


async def run_action(request, steps, note, verb="KEY"):
    """Steps are key taps, ``("wait", seconds)`` or ``("frames", count)``.

    By default it does not return a screenshot. Encoding a PNG for every
    keypress cost real CPU on a shared-core box and most were never read. With
    ``?image=1`` the settled frame is captured before this action releases its
    lease, so the observation cannot belong to another controller.

    One action runs at a time so the game stays coherent when several agents
    act on it, but a caller waiting behind others is told so instead of being
    left to hang.
    """
    if warden.ON:
        warden.check_time()
        done = warden.ended_payload()
        if done:
            return web.json_response(done, status=410)
    try:
        settle_args = settle_options(request)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)

    if not await acquire_action_lock():
        return web.json_response(
            {"ok": False, "error": "busy", "queued": stats["queued"],
             "hint": "another agent holds the game; retry"}, status=503)

    image = None
    image_w = image_h = 0
    image_mime = ""
    image_error = ""
    will_calibrate = CALIBRATE and not world["ok"] and not world["tried"]
    calibration_frames = (280 + 4 * (DEFAULT_TAP_FRAMES + KEY_RELEASE_FRAMES
                          + DEFAULT_SETTLE_MAX_FRAMES)) if will_calibrate else 0
    budget = InputBudget(
        sum(step[1] + (KEY_RELEASE_FRAMES if len(step) > 2 else 0)
            for step in steps if step[0] != "wait")
        + max(settle_args["maxframes"], settle_args["react"] + settle_args["stable"])
        + calibration_frames,
        LIB.core_fps(), health,
        wall_seconds=sum(step[1] for step in steps if step[0] == "wait"),
        check_runtime=check_input_runtime)
    token = current_budget.set(budget)
    try:
        budget.check()
        # Logged before the keys are sent, not after: the panel should show an
        # action starting, not report it once it is already over.
        if warden.ON and warden.run["done"]:
            return web.json_response(warden.ended_payload(), status=410)
        # Key/frame totals describe the submitted request, including steps
        # that may not finish if execution is interrupted.
        rec["actor"] = actor(request)
        key_steps = [step for step in steps if len(step) > 2]
        input_frames = sum(int(step[1]) for step in key_steps)
        log_action(rec["actor"], verb, note, detail=held_note(steps),
                   key_events=len(key_steps), input_frames=input_frames,
                   wait_call=not key_steps)
        rec_add("a", key=session["actions"], down=f"{verb} {note}"[:32])
        if warden.ON:
            # Only key steps carry a name at index 2; "wait" and "frames" are
            # pairs. Filtering by kind broke the moment a new pause kind was
            # added, so key off the shape instead.
            warden.note_action([step[2] for step in key_steps], note,
                               input_frames=input_frames)
        # counted here rather than only in the warden, so a run that is still
        # going can show its own key distribution
        for _s in steps:
            if len(_s) > 2:
                _k = canon(_s[2])
                keyhist[_k] = keyhist.get(_k, 0) + 1
        if will_calibrate:
            input_stage("calibration")
            world["tried"] = True
            await calibrate_lazily()
            # Calibration and input waits consume the same fixed run budget.
        budget.action_seq = session["actions"]
        baseline = LIB.core_frame_hash()
        for index, step in enumerate(steps):
            budget.check()
            input_stage("step", step_index=index)
            kind, val = step[0], step[1]
            if kind == "wait":
                input_stage("wait")
                await budget.wait_seconds(val)
            elif kind == "frames":
                input_stage("gap", step_index=index)
                await wait_core_frames(val)
            else:
                await tap(kind, val, step[2] if len(step) > 2 else None)
        input_stage("settle")
        waited, changed = await settle(baseline, **settle_args)
        note_move()
        note_screen()
        # Inventory can increase and be consumed between sparse samples.  The
        # read is ~1.2 ms against hundreds of ms per action, so sample every
        # action and latch gains relative to the opening state.
        try:
            read_stats()
        except Exception as exc:
            print(f"stat read failed: {exc!r}", flush=True)
        if warden.ON:
            warden.run["meaningful"] = beh["meaningful"]
            warden.run["oscillation"] = beh["oscillation"]
            warden.run["scenes"] = world["scenes"]
            warden.run["bigmap"] = world["bigmap"]
            warden.run["exit_acts"] = world["exit_acts"]
            warden.run["exit_secs"] = world["exit_secs"]
            for k in ("level", "exp", "hp", "maxhp", "skills", "items",
                      "reputation", "potential", "inventory_distinct",
                      "picked_item"):
                warden.run[k] = hero[k]
            warden.run["frontier"] = ((world["banked"] + world["far"])
                                      if world["ok"] else None)
            warden.run["curve"] = list(curve)
        if wants_image(request):
            # A look inside the action is still a look: keep the read count
            # comparable with agents that call /api/screen separately.
            if warden.ON:
                warden.note_read()
            try:
                image, image_w, image_h, image_mime = snapshot("png")
                if not image:
                    image_error = "no frame"
            except Exception as exc:
                image_error = f"{type(exc).__name__}: {exc}"
        budget.check()
    finally:
        current_budget.reset(token)
        if health:
            health.set_input()
        action_lock().release()

    result = {
        "ok": True, "action": note, "changed": changed,
        "width": LIB.core_width(), "height": LIB.core_height(),
        "frame": LIB.core_frame_serial(), "settled_frames": waited,
    }
    if image:
        result.update({
            "image_width": image_w, "image_height": image_h,
            "image": f"data:{image_mime};base64," + base64.b64encode(image).decode(),
        })
    if image_error:
        result["image_error"] = image_error
    return web.json_response(result)


async def body_of(request):
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def bounded_int(value, name, default, minimum, maximum):
    """Parse an integer without silently accepting fractions or booleans."""
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    if isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise ValueError(f"{name} must be an integer")
        value = int(value)
    elif not isinstance(value, int):
        try:
            value = int(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{name} must be an integer") from None
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def settle_options(request):
    """Validated headless equivalents of the native API settle controls."""
    q = request.query
    react = bounded_int(q.get("react"), "react", 30, 0, 2000)
    stable = bounded_int(q.get("stable"), "stable", DEFAULT_STABLE_FRAMES,
                         1, MAX_STABLE_FRAMES)
    maxframes = bounded_int(q.get("maxsettle"), "maxsettle",
                            DEFAULT_SETTLE_MAX_FRAMES, 1, 2000)
    return {"react": react, "stable": stable, "maxframes": max(maxframes, react)}


def wants_image(request):
    return str(request.query.get("image", "0")).lower() in ("1", "true", "yes")


def validate_action_frames(count, hold, gap):
    total = count * (hold + KEY_RELEASE_FRAMES) + max(0, count - 1) * gap
    if total > MAX_ACTION_FRAMES:
        raise ValueError(
            f"action is too long ({total} frames; maximum {MAX_ACTION_FRAMES})"
        )


def keycode(name):
    return KEYS.get(str(name).strip().lower())


def state_path(body):
    raw = body.get("name")
    if raw is None:
        slot = bounded_int(body.get("slot"), "slot", 1, 1, 99)
        raw = f"slot{slot}"
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("state name must be a non-empty string")
    clean = "".join(c if c.isalnum() or c in "-_" else "_" for c in raw.strip())[:64]
    if not clean or clean in (".", ".."):
        raise ValueError("invalid state name")
    return pathlib.Path(STATE_DIR) / f"{clean}.state", clean


def attach_snapshot(result):
    data, w, h, mime = snapshot("png")
    if data:
        result.update({
            "width": LIB.core_width(), "height": LIB.core_height(),
            "frame": LIB.core_frame_serial(),
            "image_width": w, "image_height": h,
            "image": f"data:{mime};base64," + base64.b64encode(data).decode(),
        })
    else:
        result["image_error"] = "no frame"
    return result


def core_error(fallback):
    try:
        raw = LIB.core_last_error()
        if raw:
            return raw.decode(errors="replace")
    except Exception:
        pass
    return fallback


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

    An agent should name itself with an X-Agent header. The name is held to
    the broker's canonical rule - 40 ASCII letters, digits and -_. - so that
    what the record, the catalogue and the video show all agree on who
    played. When no name is given, fall back to a short stable id derived
    from the address and client string, so two anonymous agents are still
    told apart instead of both showing as "api".
    """
    given = request.headers.get("X-Agent") or request.query.get("agent")
    if given:
        clean = "".join(c for c in given
                        if c.isascii() and (c.isalnum() or c in "-_."))[:40]
        if clean:
            return clean
    peer = request.remote or "?"
    ua = request.headers.get("User-Agent", "")
    return anon_name(f"{peer}|{ua}")


async def api_key(request):
    d = await body_of(request)
    if d is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    code = keycode(d.get("key", ""))
    if not code:
        return web.json_response({"ok": False, "error": "unknown key"}, status=400)
    try:
        hold = bounded_int(d.get("hold"), "hold", DEFAULT_TAP_FRAMES,
                           1, MAX_HOLD_FRAMES)
        times = bounded_int(d.get("times"), "times", 1,
                            1, MAX_KEYS_PER_ACTION)
        gap = bounded_int(d.get("gap"), "gap", BETWEEN_TAPS_FRAMES,
                          0, MAX_GAP_FRAMES)
        validate_action_frames(times, hold, gap)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    name = str(d.get("key")).strip().lower()
    steps = []
    for i in range(times):
        steps.append((code, hold, name))
        if i != times - 1 and gap:
            steps.append(("frames", gap))
    return await run_action(request, steps, name + (f" x{times}" if times > 1 else ""))


async def api_keys(request):
    d = await body_of(request)
    if d is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    names = d.get("keys") or []
    if not isinstance(names, list) or not 1 <= len(names) <= MAX_KEYS_PER_ACTION:
        return web.json_response(
            {"ok": False,
             "error": f"keys must contain between 1 and {MAX_KEYS_PER_ACTION} entries"},
            status=400,
        )
    codes = [keycode(k) for k in names]
    if any(c is None for c in codes):
        return web.json_response({"ok": False, "error": "unknown key in list"}, status=400)
    try:
        hold = bounded_int(d.get("hold"), "hold", DEFAULT_TAP_FRAMES,
                           1, MAX_HOLD_FRAMES)
        gap = bounded_int(d.get("gap"), "gap", BETWEEN_TAPS_FRAMES,
                          0, MAX_GAP_FRAMES)
        validate_action_frames(len(names), hold, gap)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    steps = []
    for i, c in enumerate(codes):
        steps.append((c, hold, str(names[i]).strip().lower()))
        if i != len(codes) - 1 and gap:
            steps.append(("frames", gap))
    return await run_action(request, steps, " ".join(map(str, names)), verb="KEYS")


async def api_wait(request):
    d = await body_of(request)
    if d is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    try:
        ms = bounded_int(d.get("ms"), "ms", 1000, 0, MAX_WAIT_MS)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    return await run_action(request, [("wait", ms / 1000)], f"{ms}ms", verb="WAIT")


async def api_screen(request):
    """The only way to look at the screen. JSON, or ?format=png|webp|jpeg.

    ?spectate=1 is a look that is not the player's: it publishes a thumbnail
    for the catalogue. It must not count as a read against the agent, nor
    appear in its action log, or watching a run would change its numbers.
    """
    fmt = request.query.get("format", "")
    watching = request.query.get("spectate") == "1"
    if warden.ON and not watching:
        ended = warden.ended_payload()
        if ended:
            # A look after the run is over is answered the way an action is:
            # the end signal rides on every tool the agent can still call, not
            # only the ones that send keys.
            return web.json_response(ended, status=410)
        warden.note_read()
    if not watching:
        log_action(actor(request), "GET", "screen", thumb=True)
    data, w, h, mime = snapshot(fmt if fmt in ("webp", "jpeg") else "png")
    if not data:
        return web.json_response({"ok": False, "error": "no frame"}, status=503)
    if fmt in ("png", "webp", "jpeg"):
        return web.Response(body=data, content_type=mime)
    return web.json_response({
        "ok": True, "width": LIB.core_width(), "height": LIB.core_height(),
        "frame": LIB.core_frame_serial(), "image_width": w, "image_height": h,
        "image": f"data:{mime};base64," + base64.b64encode(data).decode(),
    })


# A host this server will put in a URL: a name, a name with a port, and
# nothing else. It keeps a malformed or hostile X-Forwarded-Host from
# rewriting the help page's URLs into a scheme or a path of someone's
# choosing.
_TRUSTED_HOST = re.compile(r"[A-Za-z0-9._-]+(:[0-9]{1,5})?")


def base_url(request):
    """The origin this server is reached at, for the URLs in the help page.

    The benchmark proxy fronts each session server on the loopback interface
    and reports the public origin in X-Forwarded-Host and X-Forwarded-Proto.
    It is the only path to the server and it overwrites whatever the client
    sent, so those values are trusted here; a direct caller - local
    development - falls back to its own host. In benchmark mode the origin
    gains the session's own address, because the API is only reachable under
    /s/<session>: the help page must name an address the reader can reach.
    """
    host = request.host
    forwarded = request.headers.get("X-Forwarded-Host", "").split(",")[0]
    if _TRUSTED_HOST.fullmatch(forwarded):
        host = forwarded
    scheme = request.scheme
    for value in request.headers.get("X-Forwarded-Proto", "").split(","):
        value = value.strip().lower()
        if value in ("http", "https"):
            scheme = value
            break
    base = f"{scheme}://{host}"
    sid = os.environ.get("QUNXIA_BENCH_SID", "")
    if os.environ.get("QUNXIA_BENCH") == "1" and sid:
        base = f"{base.rstrip('/')}/s/{sid}"
    return base


async def api_key_names(_request):
    return web.json_response({"keys": sorted(KEYS)})


async def api_slots(_request):
    if warden.ON:
        # A scored run has no out-of-band rewind. Hidden, like reset.
        raise web.HTTPNotFound()
    root = pathlib.Path(STATE_DIR)
    slots = []
    if root.exists():
        for path in sorted(root.glob("*.state")):
            try:
                stat = path.stat()
            except OSError:
                continue
            slots.append({
                "name": path.stem, "bytes": stat.st_size,
                "modified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
            })
    return web.json_response({"slots": slots})


async def api_save(request):
    if warden.ON:
        # A scored run has no out-of-band rewind. Hidden, like reset.
        raise web.HTTPNotFound()
    body = await body_of(request)
    if body is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    try:
        path, name = state_path(body)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    if not await acquire_action_lock():
        return web.json_response({"ok": False, "error": "busy"}, status=503)
    ok = False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        await pause_emulator()
        try:
            LIB.core_release_all_keys()
            ok = bool(LIB.core_save_state(str(path).encode()))
            result = {"ok": ok, "slot": name}
            if not ok:
                result["error"] = core_error("save failed")
            if wants_image(request):
                try:
                    attach_snapshot(result)
                except Exception as exc:
                    result["image_error"] = f"{type(exc).__name__}: {exc}"
        finally:
            resume_emulator()
    except Exception as exc:
        result = {"ok": False, "slot": name, "error": str(exc)}
    finally:
        action_lock().release()
    log_action(actor(request), "SAVE", name, ok=ok)
    return web.json_response(result, status=200 if result.get("ok") else 500)


async def api_load(request):
    if warden.ON:
        # A scored run has no out-of-band rewind. Hidden, like reset.
        raise web.HTTPNotFound()
    body = await body_of(request)
    if body is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    try:
        path, name = state_path(body)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    if not path.is_file():
        return web.json_response({"ok": False, "error": "no such slot"}, status=404)
    if not await acquire_action_lock():
        return web.json_response({"ok": False, "error": "busy"}, status=503)
    ok = False
    try:
        await pause_emulator()
        try:
            LIB.core_release_all_keys()
            ok = bool(LIB.core_load_state(str(path).encode()))
            if ok:
                LIB.fb_reset()
        finally:
            resume_emulator()
        if ok:
            await wait_core_frames(2)
        result = {"ok": ok, "slot": name}
        if not ok:
            result["error"] = core_error("load failed")
        if wants_image(request):
            try:
                attach_snapshot(result)
            except Exception as exc:
                result["image_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        result = {"ok": False, "slot": name, "error": str(exc)}
    finally:
        action_lock().release()
    log_action(actor(request), "LOAD", name, ok=ok)
    if ok:
        await fanout(json.dumps({"t": "clear"}), text=True)
        # One keyframe, recorded once and fanned out to every viewer, as
        # api_reset does; send_keyframe no longer targets a single socket.
        await send_keyframe(None)
    return web.json_response(result, status=200 if result.get("ok") else 500)


async def api_reset(request):
    """Hidden. Reboots the emulated machine back to the title screen and wipes
    the activity log. Unlisted in /api/help and 404s unless the token matches,
    so a visitor who stumbles on the path cannot wipe someone's game."""
    want = os.environ.get("QUNXIA_RESET_TOKEN")
    got = request.query.get("token") or request.headers.get("X-Reset-Token")
    # Constant time, for the same reason a password is never compared with ==:
    # a short-circuiting comparison leaks how much of a guessed token was
    # right. Both sides are byte-encoded first: compare_digest rejects
    # non-ASCII strings outright, and a 500 is not the answer this endpoint
    # gives a wrong token.
    if not want or not hmac.compare_digest(
            (got or "").encode("utf-8"), want.encode("utf-8")):
        raise web.HTTPNotFound()

    restored = False
    async with action_lock():
        await pause_emulator()
        try:
            LIB.core_release_all_keys()
            have_state = os.path.exists(START_STATE)
            if have_state:
                restored = bool(LIB.core_load_state(START_STATE.encode()))
            # Only reboot when there is no state to restore. Rebooting on a
            # failed load turns a caller that retries into a reboot loop, and
            # the machine never finishes starting.
            if not restored and not have_state:
                LIB.core_reset()
            LIB.fb_reset()
        finally:
            resume_emulator()
        history.clear()
        _seq[0] = 0
        session.update(started=time.time(), actions=0, key_events=0,
                       input_frames=0, wait_calls=0, by_api=0, by_web=0)
        keyhist.clear()
        curve.clear()
        beh.update(meaningful=0, oscillation=0, last=None, prev=None)
        world.update(scenes=1, banked=0, origin=None, far=0, ok=False,
                     dark=False, miss=0, tried=False, bigmap=False,
                     exit_acts=None, exit_secs=None, checked_refs=False)
        hero.update(base=None, found=False, level=None, exp=None, hp=None,
                    maxhp=None, skills=None, items=None, reputation=None,
                    potential=None, inventory_distinct=None, picked_item=None,
                    inventory_baseline=None)
        agents.clear()
        rec_reset()
        await asyncio.sleep(0.4 if restored else 1.5)
        note_screen()                  # seed the opening-frame negative control
        try:
            read_stats()                  # establish the opening inventory
        except Exception as exc:
            print(f"opening stat read failed: {exc!r}", flush=True)
        if warden.ON and warden.run["playable"] is None:
            warden.playable_now()          # the clock starts when play can

    await fanout(json.dumps({"t": "clear"}), text=True)
    await send_keyframe(None)
    log_action("api", "RESET", "restored start state" if restored else "rebooted to title")
    return web.json_response({"ok": True, "reset": True, "restored": restored})


async def api_snapshot(request):
    """Hidden. Writes the current position as the state /api/reset restores."""
    want = os.environ.get("QUNXIA_RESET_TOKEN")
    got = request.query.get("token") or request.headers.get("X-Reset-Token")
    if not want or not hmac.compare_digest(
            (got or "").encode("utf-8"), want.encode("utf-8")):
        raise web.HTTPNotFound()
    async with action_lock():
        await pause_emulator()
        try:
            os.makedirs(os.path.dirname(START_STATE), exist_ok=True)
            LIB.core_release_all_keys()
            ok = bool(LIB.core_save_state(START_STATE.encode()))
        finally:
            resume_emulator()
    size = os.path.getsize(START_STATE) if ok and os.path.exists(START_STATE) else 0
    log_action("api", "RESET", "saved start state" if ok else "start state failed", ok=ok)
    return web.json_response({"ok": ok, "path": START_STATE, "bytes": size})


async def calibrate():
    """Find where this savestate keeps the character's coordinates.

    Walks two steps out and two back from the opening state and looks for
    shorts that went 0,+1,+2,+1,0 with it. A clock or a frame counter only ever
    climbs, so the walk back is what tells a coordinate from a counter.

    This runs per session rather than once per image. The offsets are not a
    property of the build: the same coordinates were measured two bytes apart
    on two runs on the same machine, so the serialised layout shifts with
    whatever else the machine is doing. Within one session it holds, and the
    walk is done and undone on the first action, within the fixed run budget.
    """
    cap = LIB.core_state_size()
    if not cap:
        return None, "core will not say how big its state is"
    buf = ctypes.create_string_buffer(cap)

    async def shot():
        n = LIB.core_state_copy(buf, cap)
        if n <= 0:
            raise RuntimeError("serialize failed")
        return buf.raw[:n]

    # No lock here: the only caller already holds it, on the first action.
    # The load is a guarantee, not a requirement: this runs before the agent
    # has done anything, so the machine is already sitting at the opening. If
    # it will not load, walk from here rather than refuse to calibrate.
    if not LIB.core_load_state(START_STATE.encode()):
        print("calibration: start state would not reload, walking from here",
              flush=True)
    await wait_core_frames(140)
    states = [await shot()]
    for name in ("kp3", "kp3", "kp7", "kp7"):
        base = LIB.core_frame_hash()
        await tap(KEYS[name], DEFAULT_TAP_FRAMES, name)
        await settle(base)
        states.append(await shot())
    LIB.core_load_state(START_STATE.encode())
    await wait_core_frames(140)

    n = min(len(x) for x in states)
    want_up = [0, 1, 2, 1, 0]
    hits = set()
    for off in range(0, n - 1, 2):
        vals = [int.from_bytes(s[off:off + 2], "little", signed=True) for s in states]
        d = [v - vals[0] for v in vals]
        if d == want_up or d == [-x for x in want_up]:
            hits.add(off)
    # A diagonal step moves both coordinates, so the pair wanted here is two
    # candidates close together whose values are small enough to be tiles.
    # Requiring them to be strictly adjacent was too strict: the machine puts
    # other things between them.
    def val(o):
        return int.from_bytes(states[0][o:o + 2], "little", signed=True)
    tiles = sorted(o for o in hits if 0 <= val(o) < 1200)
    pairs = [(a, b) for i, a in enumerate(tiles) for b in tiles[i + 1:]
             if 0 < b - a <= 8]
    chosen = pairs[0] if pairs else None
    if not chosen:
        return None, f"{len(hits)} candidates, no usable pair"
    _POS_ARGS[0], _POS_ARGS[1] = chosen
    world["ok"] = True
    world["miss"] = 0
    return chosen, f"{len(hits)} candidates, {len(pairs)} pairs"


async def api_recording(request):
    if recording_api:
        return await recording_api.handle(request)
    return web.json_response({"started": rec["started"], "duration": 0, "events": [], "bytes": 0})


async def api_history(request):
    try:
        limit = bounded_int(request.query.get("limit"), "limit", 100,
                            0, MAX_HISTORY_LIMIT)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    items = list(history)
    return web.json_response({"history": items[-limit:] if limit else []})


async def api_help(request):
    # Not logged: the page fetches this on every load to fill the copy box, so
    # logging it fills the panel with entries nobody performed.
    lang = request.query.get("lang", "en")
    core_only = request.query.get("part") == "core"
    return web.Response(text=system_prompt(base_url(request), lang, core_only,
                                           benchmark=warden.ON),
                        content_type="text/plain", charset="utf-8")


async def recording_script(_request):
    return web.FileResponse(ROOT / "recording.js")


async def index(_request):
    return web.FileResponse(ROOT / "index.html")


async def status(_request):
    return web.json_response({
        "width": LIB.core_width(), "height": LIB.core_height(),
        "fps": round(LIB.core_fps(), 3), "frame": LIB.core_frame_serial(),
        "clients": len(clients), "session": session_summary(), **stats,
        **(health.snapshot() if health else {}),
        "recording": {"cache_bytes": 0, "pending_bytes": recording_store.pending_bytes if recording_store else 0,
                      "error": recording_store.error if recording_store else ""},
    })


@web.middleware
async def json_errors(request, handler):
    """Whatever goes wrong, an agent gets JSON it can read.

    An unhandled exception used to come back as an HTML 500, which a caller
    cannot parse and which reads as the service being down rather than as one
    bad request.
    """
    try:
        if recording_blocked and request.method == "POST" and request.path.startswith("/api/"):
            raise RecordingUnavailable(recording_store.error)
        if health:
            health.check()
        return await handler(request)
    except web.HTTPException:
        raise
    except RecordingUnavailable as exc:
        return web.json_response({"ok": False, "error": "recording_unavailable", "message": str(exc)}, status=503)
    except EnvironmentFailure as exc:
        if health:
            health.fail(str(exc))
        return web.json_response(health.fault, status=503)
    except Exception as exc:
        traceback.print_exc()
        if warden.ON:
            # "errors" starts as None, unmeasured, and becomes a count only
            # once a request has actually failed under the benchmark.
            warden.run["errors"] = (warden.run["errors"] or 0) + 1
        stats["last_error"] = f"{type(exc).__name__}: {exc}"
        return web.json_response(
            {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
            status=500)


async def startup(app):
    """Create the action lock on the serving loop and detach the workers."""
    global api_lock
    api_lock = asyncio.Lock()
    app["pump"] = asyncio.create_task(pump())
    app["reaper"] = asyncio.create_task(reap())
    if health:
        app["heartbeat"] = asyncio.create_task(pulse_health())
        health.set_phase("running")
    if warden.ON:
        app["warden"] = asyncio.create_task(warden.warden(
            rec, health, api_lock,
            lambda n: wait_core_frames(n, allow_finished=True),
            recording_api.snapshot))


async def calibrate_lazily():
    """Locate the coordinates on the first action rather than at startup.

    Startup was the wrong place twice over: an aiohttp startup handler runs
    before the socket listens, so waiting there made the session unreachable;
    and racing the session's own load of the opening state produced a stream of
    failed unserialise calls. By the first keypress the machine is definitely
    running, and this walk ends by reloading the opening state, so the agent
    The offsets are not baked into the image because the serialised layout is
    not stable across machines, or even across runs on one machine.
    """
    for attempt in range(2):
        try:
            pos, why = await calibrate()
        except Exception as exc:
            pos, why = None, repr(exc)
        if pos:
            print(f"position offsets {hex(pos[0])},{hex(pos[1])} ({why})",
                  flush=True)
            return
        print(f"calibration attempt {attempt + 1} found nothing ({why})",
              flush=True)
        await asyncio.sleep(1.0)
    print("no position offsets; exploration will not be reported", flush=True)


async def pulse_health():
    global recording_blocked
    while True:
        health.pulse()
        if recording_blocked and recording_store.flush():
            recording_blocked = False
            LIB.fb_reset()
            resume_emulator()
        await asyncio.sleep(.25)


async def cleanup(app):
    for task in app.values():
        if isinstance(task, asyncio.Task):
            task.cancel()
    await asyncio.gather(*(t for t in app.values() if isinstance(t, asyncio.Task)), return_exceptions=True)
    for peer in list(peers.values()):
        peer.drop()
    emulator_stop.set()
    if health:
        LIB.core_shutdown()
        health.stop()
    if recording_api:
        recording_api.close()
        recording_store.close()


def main():
    global health, recording_store, recording_api
    directory = os.environ.get("QUNXIA_RECORDING_DIR", str(ROOT.parent / "recordings"))
    validate_recording_directory(directory)
    path = pathlib.Path(os.environ.get("QUNXIA_RECORDING_FILE", str(pathlib.Path(directory) / f"{PORT}.jsonl")))
    validate_recording_directory(path.parent)
    recording_store = RecordingStore(path)
    recording_api = RecordingAPI(recording_store)
    rec.update(started=recording_store.started, events=[], bytes=recording_store.committed_size)
    health = Health(LIB.core_ticks, paused.is_set, os.environ.get("QUNXIA_HEALTH_DIR", str(pathlib.Path(SAVES) / ".health")))
    health.start()
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

    app = web.Application(middlewares=[json_errors])
    app.add_routes([
        web.get("/", index),
        web.get("/recording.js", recording_script),
        web.get("/ws", ws_handler),
        web.get("/status", status),
        web.get("/api/screen", api_screen),
        web.get("/api/help", api_help),
        web.get("/api/keys", api_key_names),
        web.get("/api/slots", api_slots),
        web.get("/api/history", api_history),
        web.get("/api/recording", api_recording),
        web.post("/api/reset", api_reset),
        web.post("/api/snapshot", api_snapshot),
        web.post("/api/key", api_key),
        web.post("/api/keys", api_keys),
        web.post("/api/wait", api_wait),
        web.post("/api/save", api_save),
        web.post("/api/load", api_load),
    ])
    # Startup handlers are awaited, so the workers are detached tasks rather
    # than returned, or startup would block on loops that never end.
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    web.run_app(app, host="0.0.0.0", port=PORT, access_log=None)


if __name__ == "__main__":
    main()
