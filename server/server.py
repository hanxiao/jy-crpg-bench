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
import uuid
import zlib

from aiohttp import WSMsgType, web
from PIL import Image

import warden
from state_reader import decode_inventory, inventory_gained
import save_state
from activity import ActivityStore
from saved_history import SavedHistory
from video_export import VideoExports

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
HOST = os.environ.get("QUNXIA_HOST", "0.0.0.0")
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

# Key name -> RETROK. The same vocabulary as the native runner's Control
# API (Sources/QunXia/Keys.swift, RetroKey.table) - the README's "the API
# accepts the full DOS keyboard" line is that table, so a name it accepts
# is a name the headless one accepts too. test_api pins the two together.
# One key, several accepted spellings. Counted under whatever the agent
# happened to type, a single key split across two entries in the histogram,
# and since both spellings draw the same icon it read as a duplicated row.
# The spelling table lives in warden so the two counters cannot disagree.
def canon(name):
    return warden.ALIAS.get(name, name)


KEYS = {
    "up": 273, "down": 274, "right": 275, "left": 276,
    "enter": 13, "return": 13, "ok": 13, "confirm": 13, "space": 32,
    "esc": 27, "escape": 27, "cancel": 27, "back": 27, "pause": 19,
    "tab": 9, "backspace": 8, "delete": 127, "insert": 277,
    "shift": 304, "lshift": 304, "rshift": 303,
    "ctrl": 306, "lctrl": 306, "rctrl": 305,
    "alt": 308, "lalt": 308, "ralt": 307,
    "numlock": 300, "capslock": 301, "scrolllock": 302,
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
# The native Control API spells the same eleven keys by word; accept both.
for _k, _v in {"semicolon": 59, "quote": 39, "comma": 44, "period": 46,
               "slash": 47, "minus": 45, "equals": 61, "leftbracket": 91,
               "backslash": 92, "rightbracket": 93, "backquote": 96}.items():
    KEYS[_k] = _v
for _n in range(10):                      # numpad; the game accepts these for movement
    KEYS[f"kp{_n}"] = 256 + _n
KEYS["kpenter"] = 271
# Numpad operators, under the names the native Control API gives them.
KEYS.update({"kpplus": 270, "kpminus": 269, "kpmultiply": 268,
             "kpdivide": 267, "kpperiod": 266})
# The game answers yes/no prompts by letter; the native API also names
# them by word.
KEYS["yes"], KEYS["no"] = 121, 110
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
         # Whoever last took the one-player lease. A caller that waits out
         # LOCK_TIMEOUT and gets a 503 is otherwise left guessing whether it
         # queued behind another agent or behind a browser leaning on a key.
         "queued": 0, "holder": ""}
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
# Measured floor, 24 taps per point against a key whose effect is certain:
# 1 frame lands 0-29% of the time, 2 frames 33-67%, 3 frames 79-88%, 4 frames
# 96-100%, 5 frames and up 100%. Below five the game and the caller disagree
# about whether a key was pressed, which is worse for an agent than a refusal,
# so a shorter hold is a bad request rather than an unreliable one.
MIN_HOLD_FRAMES = 5
KEY_RELEASE_FRAMES = 2
BETWEEN_TAPS_FRAMES = 6
DEFAULT_STABLE_FRAMES = 9
DEFAULT_SETTLE_MAX_FRAMES = 120
MAX_STABLE_FRAMES = 600
MAX_SETTLE_FRAMES = 2000
MAX_HOLD_FRAMES = 1200
MAX_KEYS_PER_ACTION = 100
MAX_ACTION_FRAMES = 2800
MAX_HISTORY_LIMIT = 300
# Raw-bytes encodings for GET /screen; "" is the default JSON reply. PNG is the
# one an agent is told about, because it is the one every runner can produce
# and the one vision stacks read most reliably. WebP and JPEG are here for the
# browser client and the catalogue thumbnails, which pay for bytes on a wire.
SCREEN_FORMATS = ("", "png", "webp", "jpeg")
# Reset restores this rather than rebooting. It puts the agent in the opening
# room with a character already made, because creating one means driving the
# 注音 IME, which is a puzzle about input methods and not about the game.
START_STATE = os.environ.get("QUNXIA_START_STATE", str(ROOT.parent / "saves" / "start.state"))
STATE_DIR = os.environ.get("QUNXIA_STATE_DIR", str(ROOT.parent / "saves" / "states"))
# Long-lived play is opt-in. A scored run must never read or update a previous
# interactive checkpoint, even if its launcher inherited these variables.
RESUME_STATE = "" if warden.ON else os.environ.get("QUNXIA_RESUME_STATE", "")


def _checkpoint_setting(name, default, parse):
    # A typo in an operator's environment should end in one sentence naming
    # the variable, not in a traceback from import time.
    value = os.environ.get(name, default)
    try:
        return parse(value)
    except ValueError:
        raise SystemExit(f"{name} must be a number, not {value!r}") from None


AUTOSAVE_SECONDS = _checkpoint_setting("QUNXIA_AUTOSAVE_SECONDS", "30", float) if RESUME_STATE else 0
# 1500 frames is where bench/repro.py (BOOT_MIN_FRAMES) finds the title
# parked at the pinned cycle setting; a restore before that lands mid-boot.
RESUME_WARMUP_FRAMES = _checkpoint_setting("QUNXIA_RESUME_WARMUP_FRAMES", "1500", int) if RESUME_STATE else 0
checkpoint = {"enabled": bool(RESUME_STATE), "state": "warming" if RESUME_STATE else "disabled",
              "restored": False, "saves": 0, "last_saved": None, "error": None}

# Everything anyone does to this session, so the page can show who is doing
# what. The game is shared, so this doubles as "why did the screen just move".
history: collections.deque = collections.deque(maxlen=300)
_seq = [0]
activity_store = None


def restore_activity():
    global activity_store
    # Persistent UI history is explicitly opt-in and never enters formal runs.
    if warden.ON or os.environ.get("QUNXIA_PERSIST_HISTORY", "0") != "1":
        return
    store = ActivityStore(pathlib.Path(SAVES) / "activity.json")
    try:
        entries = store.load()
    except (OSError, ValueError) as exc:
        # Preserve malformed/unreadable snapshots for inspection, not overwrite.
        print(f"activity history disabled: {exc}", flush=True)
        return
    history.extend(entries)
    _seq[0] = entries[-1]["id"] if entries else 0
    activity_store = store


def persist_activity():
    if activity_store is not None:
        try:
            activity_store.save(history)
        except (OSError, ValueError) as exc:
            print(f"activity history write failed: {exc}", flush=True)

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
# How long a reply may wait for a black screen to lift. A scene change blacks
# the screen out and draws the new scene a moment later; the caller wants the
# new scene, so an action holds its reply through the black, bounded so a
# screen that stays black is still answered.
TRANSITION_FRAMES = 300

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
CHAR_ANCHOR = save_state.CHAR_ANCHOR
# Byte offsets inside one record.
C_NAME, C_LEVEL, C_EXP, C_HP, C_MAXHP = 8, 30, 32, 34, 36
C_STAMINA, C_MP, C_MAXMP = 42, 82, 84
C_ATTACK, C_INTEGRITY, C_REPUTATION, C_POTENTIAL = 86, 112, 118, 120
C_SKILLS = 126

hero = {"base": None, "buf": None, "cap": 0, "read": 0, "found": False,
         "level": None, "exp": None, "hp": None, "maxhp": None,
         "skills": None, "items": None, "reputation": None, "potential": None,
         "inventory_distinct": None, "picked_item": None,
         "inventory_baseline": None,
         # The game's own semantics, read from the working copy: how many of
         # the fourteen books are held, and which. This is the score the
         # benchmark is for, and no agent can reach it.
         "books": None, "book_ids": None, "items_total": None,
         # The compass the hermit's cabinet holds, read from the same bag:
         # the first gated event of the opening.
         "compass": None,
         # Played seconds at the first read that found all fourteen held: the
         # completion event the benchmark times. Latched once, never cleared.
         "completion_secs": None,
         # The party and the world square the running game keeps, read beside
         # the character records; moved_on_map says the last action changed the
         # square, which only walking on the world map does, and world_map_at is
         # the played time of the first such change.
         "world_x": None, "world_y": None, "party_size": None,
         "moved_on_map": False, "world_map_at": None}


# --------------------------------------------------- the game's own save slot
#
# The game writes its save slots as `R<n>.GRP` into the directory it was
# mounted from, so a save the game performs itself is readable from here. That
# archive is the only place the party roster and the world square are true:
# the copies of those in a machine image are the ones the game loaded when the
# run began, and they do not follow the player.
#
# The game only offers 存檔 from the world map, and it says so itself: the menu
# has six rows there and four inside a scene. The attempt below opens the menu,
# counts its rows, and backs out again when saving is not on offer, so it never
# guesses from pixels what the game will accept.
#
# None of this is reachable from the Control API. An agent that could save
# could also load, and a run that can rewind is not a measurement.
GAME_DIR = pathlib.Path(GAME).parent
SNAPSHOT_SLOT = min(3, max(1, int(os.environ.get("QUNXIA_SNAPSHOT_SLOT", "3"))))
# How often to try, in seconds. A try that finds a scene costs two taps.
# Zero switches it off, which is what the broker does for the worker that
# authors the start state: that one is being driven through the opening by a
# script, not played, and a key of ours in the middle of it would derail the
# replay and leave the benchmark without an origin.
SNAPSHOT_EVERY = float(os.environ.get("QUNXIA_SNAPSHOT_EVERY", "120"))
# Idle before trying, so the macro never lands between an agent's own keys.
SNAPSHOT_IDLE = 2.0
WORLD_MENU_ROWS = 6         # 醫療 解毒 物品 狀態 離隊 系統
SYSTEM_ROW = 5              # 系統 is the sixth
SAVE_ROW = 1                # 讀檔 存檔 離開: 存檔 is the second

# How much budget is left when a scored run gets its last save. The agent is
# still playing then, which is the point: after this there is no more chance
# to catch the party on the world map.
SNAPSHOT_LAST_CALL = float(os.environ.get("QUNXIA_SNAPSHOT_LAST_CALL", "25"))

snap = {"at": None, "first_at": None, "tries": 0, "saves": 0, "why": "not tried yet",
        "archive": None, "last_action": time.time(), "last_call": False}


def archive_paths(slot=None):
    n = SNAPSHOT_SLOT if slot is None else slot
    return GAME_DIR / f"R{n}.GRP", GAME_DIR / f"R{n}.IDX"


def archive_stamp():
    """Enough of the slot file to tell a fresh write from the old one."""
    grp, _ = archive_paths()
    try:
        st = grp.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def read_archive():
    """The slot the game last wrote, decoded, or None."""
    grp, idx = archive_paths()
    try:
        return save_state.from_archive(grp.read_bytes(), idx.read_bytes())
    except OSError:
        return None


# The menu panel's left border is a column of white pixels at a fixed x, and
# the panel grows by exactly one row height per entry: measured at 122 pixels
# for the six-row world-map menu and 82 for the four-row one a scene offers,
# both starting at y 23. Its width follows its contents and its right border
# moves with it, so the left border is the one thing that stays put.
MENU_X = 21
MENU_TOP = (15, 30)
MENU_ROW_H = 20
MENU_PAD = 2


def menu_rows():
    """How many rows the game's menu panel has, or 0 when none is open."""
    w = ctypes.c_int(0)
    h = ctypes.c_int(0)
    n = LIB.fb_snapshot(SNAP, len(SNAP), 1, ctypes.byref(w), ctypes.byref(h))
    if n <= 0 or w.value <= MENU_X:
        return 0
    px = Image.frombytes("RGB", (w.value, h.value), SNAP.raw[:n]).load()
    best = top = run = start = 0
    for y in range(h.value):
        if min(px[MENU_X, y]) >= 250:
            if run == 0:
                start = y
            run += 1
            if run > best:
                best, top = run, start
        else:
            run = 0
    if best < MENU_ROW_H * 2 or not MENU_TOP[0] <= top <= MENU_TOP[1]:
        return 0
    return round((best - MENU_PAD) / MENU_ROW_H)


async def meta_tap(code, times=1):
    """A key the benchmark presses for itself.

    Deliberately outside the session accounting: these are not the agent's
    actions and must not appear in its action count, its key histogram, or its
    behavioural ratios.
    """
    for _ in range(times):
        try:
            LIB.core_key(code, True)
            await wait_core_frames(DEFAULT_TAP_FRAMES)
        finally:
            LIB.core_key(code, False)
        await wait_core_frames(24)      # let the panel redraw before reading it


async def close_menus(limit=4):
    """Escape until nothing is open. One escape too many reopens the menu, so
    this asks the screen rather than pressing a fixed number of times."""
    for _ in range(limit):
        if menu_rows() == 0:
            return True
        await meta_tap(KEYS["escape"])
    return menu_rows() == 0


async def game_snapshot(reason=""):
    """Have the game save itself, then read what it wrote.

    Returns (summary, why). The summary is None whenever the game did not
    write, which is the usual outcome inside a scene.
    """
    if not await acquire_action_lock("snapshot", timeout=0.05):
        return None, "busy"
    snap["tries"] += 1
    try:
        if menu_rows():
            # the player left a menu open; an escape now would close it under them
            return None, "a menu is open"
        await meta_tap(KEYS["escape"])
        rows = menu_rows()
        if rows != WORLD_MENU_ROWS:
            # Not the world map: a scene's menu, or none. Close it and give up.
            # This is where the party spends most of a run, so the attempt costs
            # a scene an escape it did not ask for; the read that answers the
            # model waits on the same lock this holds, so the model never sees
            # the menu, and the game state is put back before it looks again.
            await close_menus()
            return None, (f"the menu offered {rows} rows, not {WORLD_MENU_ROWS}"
                          "; the game only saves from the world map")
        if stats["queued"]:
            # Somebody wants to play. The save is worth a few of the run's
            # seconds, but never seconds an agent is waiting on.
            await close_menus()
            return None, "yielded to a waiting caller"
        await meta_tap(KEYS["down"], SYSTEM_ROW)
        await meta_tap(KEYS["enter"])
        await meta_tap(KEYS["down"], SAVE_ROW)
        await meta_tap(KEYS["enter"])
        await meta_tap(KEYS["down"], SNAPSHOT_SLOT - 1)
        before = archive_stamp()
        await meta_tap(KEYS["enter"])
        # The game writes the file a moment after it says 請稍候; wait for the
        # file itself rather than for a number of frames.
        written = False
        for _ in range(40):
            await wait_core_frames(20)
            if archive_stamp() not in (None, before):
                written = True
                break
        await close_menus()
        if not written:
            return None, "the slot file did not change"
        summary = read_archive()
        if summary is None:
            return None, "the slot the game wrote would not decode"
        summary["saved_at"] = time.time()
        summary["reason"] = reason
        absorb_archive(summary)
        snap["archive"] = summary
        snap["at"] = summary["saved_at"]
        if snap["first_at"] is None:
            # the first save the game wrote is the first time the party stood
            # on the world map: the crossing, timed by the game and not the screen
            snap["first_at"] = snap["at"]
        snap["saves"] += 1
        if warden.ON:
            warden.run["team_size"] = summary["team_size"]
            warden.run["team_level"] = summary["team_level"]
            warden.run["saved_at"] = snap["at"]
            warden.run["first_saved_at"] = snap["first_at"]
        return summary, ""
    finally:
        action_lock().release()
        stats["holder"] = ""


async def snapshotter():
    """Have the game save itself now and then, and once before time is up.

    Every attempt waits for a gap: nobody queued for the lock, and the agent
    idle since its last action, so a key of ours never lands inside one of
    its own. An attempt that finds a scene costs two taps and puts the screen
    back exactly as it was; one that finds the world map costs a few seconds
    and leaves a save behind.
    """
    if SNAPSHOT_EVERY <= 0:
        return
    while True:
        await asyncio.sleep(5)
        if paused.is_set():
            continue
        if warden.ON and (warden.run["playable"] is None or warden.run["done"]):
            continue
        if not session["actions"]:
            # Nothing has played yet, so there is nothing to record and the
            # opening is the one moment a stray key would be most confusing.
            continue
        left = warden.timing().get("remaining") if warden.ON else None
        # The run's last save: near the end of the budget, whether or not one
        # is due, because after this there is no more world map to catch.
        last_call = left is not None and left <= SNAPSHOT_LAST_CALL
        if last_call:
            if snap["last_call"]:
                continue
        elif snap["at"] and time.time() - snap["at"] < SNAPSHOT_EVERY:
            continue
        if time.time() - snap["last_action"] < SNAPSHOT_IDLE:
            continue
        if stats["queued"]:                # somebody is waiting to play
            continue
        try:
            summary, why = await game_snapshot("last call" if last_call
                                              else "periodic")
        except Exception as exc:                       # never kill the task
            summary, why = None, f"{type(exc).__name__}: {exc}"
        snap["why"] = why or "saved"
        if last_call and why != "busy":
            snap["last_call"] = True
        if summary is None:
            # Nothing was written, so back off the same interval rather than
            # retrying every five seconds from inside a scene.
            snap["at"] = time.time()


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
    return save_state.locate_characters(mem)


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
        hero["items_total"] = sum(inventory.values())
        # The fourteen novels end the game. They count whether they sit in the
        # shared bag or in the protagonist's own four carried slots.
        carried = save_state.decode_character(
            mem[base:base + save_state.CHAR_BYTES], 0) or {}
        held = save_state.books_held(inventory, [carried] if carried else [])
        # A rung, once reached, is kept. The live bag is decoded from a memory
        # image whose character array is found by a name search, and on some
        # core builds a later read can land on the wrong copy and come back
        # short; the save the game writes, folded in by absorb_archive, is the
        # reliable source, and neither it nor a good live read is undone by a
        # bad one. Books and the compass only ever climb.
        if len(held) > (hero["books"] or 0):
            hero["books"] = len(held)
            hero["book_ids"] = held
        if inventory.get(save_state.COMPASS_ID, 0) > 0:
            hero["compass"] = True
        latch_completion()

        opening = hero["inventory_baseline"]
        if opening is None:
            hero["inventory_baseline"] = dict(inventory)
            hero["picked_item"] = False
        elif inventory_gained(opening, inventory):
            hero["picked_item"] = True
    live = save_state.read_live(mem, base)
    if live is None:
        hero["moved_on_map"] = False
        return
    was = (hero["world_x"], hero["world_y"])
    moved = was != (None, None) and was != (live["x"], live["y"])
    hero["moved_on_map"] = moved
    hero["world_x"], hero["world_y"] = live["x"], live["y"]
    hero["party_size"] = len(live["party"])
    if moved and hero["world_map_at"] is None:
        hero["world_map_at"] = played_now()


def played_now(now=None):
    """Seconds of play so far: from the playable moment under the warden,
    from the session start otherwise."""
    now = time.time() if now is None else now
    start = (warden.run["playable"] if warden.ON and warden.run["playable"]
             else session["started"])
    return round(now - start, 1)


def absorb_archive(summary):
    """Fold the bag the game itself wrote into the live reading.

    The bag beside the character records is the game's own working copy, but
    an item a script hands over was seen to reach it late, after the next
    save or scene change, while the archive the game writes carries it at
    once. Where the archive says more than the live copy, the archive wins;
    nothing here can take a rung away.
    """
    bag = summary.get("bag") or {}
    if bag.get(save_state.COMPASS_ID, 0) > 0:
        hero["compass"] = True
    elif hero["compass"] is None:
        # The save's bag is the reliable source, so its absence is a real
        # reading, not a missed one: the rung is measured and not reached,
        # which the ladder draws as a filled miss rather than an empty cell.
        # A later save that carries the compass still latches it to True.
        hero["compass"] = False
    hero["books"] = max(hero["books"] or 0, summary.get("books") or 0)
    opening = hero["inventory_baseline"]
    if opening is not None and bag and inventory_gained(opening, bag):
        hero["picked_item"] = True
    latch_completion()


def latch_completion(now=None):
    """Record the played time at which the fourteenth book was first seen.

    The archive records every book held, so the count of books is what
    carries the ladder to the ending; this turns the first read at fourteen
    into the completion time the benchmark ranks by. The clock is the run's
    playable moment under the warden and the session start otherwise.
    """
    if hero["completion_secs"] is not None or (hero["books"] or 0) < len(save_state.BOOK_IDS):
        return None
    hero["completion_secs"] = played_now(now)
    return hero["completion_secs"]


# Off by default, and it stays off until there is a way to find the
# coordinates that does not involve reloading a savestate into a running
# machine. Doing that crashed DOS outright in the container - the session came
# back showing DOSBox Pure's "DOS Crashed" menu and stopped responding to keys
# - which is far too high a price for one column. Distance then reports as
# unmeasured, which the page already draws as a dash rather than a nought.
CALIBRATE = os.environ.get("QUNXIA_CALIBRATE") == "1" and not RESUME_STATE

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
    sample = {"scene": world["scenes"],
              "frontier": (world["banked"] + world["far"])
              if world["ok"] else None,
              "x": None, "y": None}
    if world["dark"]:
        world["dark"] = False
        enter_scene()
        sample["scene"] = world["scenes"]
        sample["frontier"] = ((world["banked"] + world["far"])
                               if world["ok"] else None)
        return sample
    p = position()
    if p is None:
        return sample
    sample["x"], sample["y"] = p
    o = world["origin"]
    if o is None:
        world["origin"], world["far"] = p, 0
        sample["frontier"] = world["banked"]
        return sample
    # Chebyshev, not Manhattan: a step here is diagonal, moving both axes at
    # once, so Manhattan would call one step two tiles. This counts steps.
    d = max(abs(p[0] - o[0]), abs(p[1] - o[1]))
    # A step moves one tile, so a jump is the floor changing under you: a scene
    # change whose fade went unseen. Counted as one rather than allowed to
    # register as a huge distance.
    if d > world["far"] + 8:
        enter_scene()
        world["origin"], world["far"] = p, 0
        sample["scene"] = world["scenes"]
        sample["frontier"] = world["banked"]
        return sample
    world["far"] = max(world["far"], d)
    sample["frontier"] = world["banked"] + world["far"]
    return sample
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


def disk_history_enabled():
    return (not warden.ON and recording_store is not None
            and os.environ.get("QUNXIA_PERSIST_HISTORY", "0") == "1")


def record_activity(entry):
    # The JSONL retains every marker; the deque and activity.json are only a
    # small reconnect cache. GETs must survive after their cache entries age out.
    if not disk_history_enabled() or entry["verb"] not in ("GET", "KEY", "KEYS", "WAIT", "TEXT"):
        return
    event = {"t": round(entry["at"] - rec["started"], 3),
             "act": entry["verb"], "who": entry["src"], "on": entry["target"],
             "detail": entry["detail"], "ok": entry["ok"], "history": 1}
    if entry.get("thumb"):
        event["thumb"] = entry["thumb"]
    try:
        ok = recording_store.append(event)
    except (OSError, BufferError) as exc:
        recording_store.error = str(exc)
        ok = False
    if not ok:
        block_recording()
        raise RecordingUnavailable(recording_store.error)
    rec["bytes"] = recording_store.committed_size


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
        snap["last_action"] = time.time()   # the save macro waits for a gap
        if key_events is None:
            key_events = 1 if verb in ("KEY", "TEXT") else 0
        session["key_events"] += key_events
        session["input_frames"] += input_frames
        session["wait_calls"] += int(wait_call or verb == "WAIT")
        session["by_web" if src == "web" else "by_api"] += 1
        agents[src] += 1
    record_activity(entry)
    history.append(entry)
    persist_activity()
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


def record_trajectory(sample, screen_changed, action_at=None):
    """Persist the post-action observation beside the raw input marker.

    The action marker is written before input is sent. This second event is
    written after settling, so an offline reader can join the two by
    ``action`` and distinguish what was requested from what the game showed.
    Coordinates are optional: resumed workers may not have calibrated offsets.
    Missing coordinates stay null and are never interpreted as zero distance.
    """
    if not recording_store:
        return
    sample = sample or {}
    event = {"t": round(time.time() - rec["started"], 3),
             "trajectory": True, "action": session["actions"],
             "scene": sample.get("scene", world["scenes"]),
             "frontier": sample.get("frontier"),
             "screen_changed": bool(screen_changed)}
    if type(action_at) in (int, float) and math.isfinite(action_at):
        # The per-worker action counter resets after a restart; this timestamp
        # lets an offline reader join the observation to the older marker.
        event["action_t"] = action_at
    if type(sample.get("x")) is int and type(sample.get("y")) is int:
        event["x"], event["y"] = sample["x"], sample["y"]
    try:
        ok = recording_store.append(event)
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
    changed = before is not None and fp != before
    if changed:
        beh["meaningful"] += 1
    # A -> B -> A is the oscillation the literature calls out as the signature
    # of an agent that is busy without getting anywhere.
    if beh["prev"] is not None and fp == beh["prev"] and fp != before:
        beh["oscillation"] += 1
    beh["prev"], beh["last"] = before, fp
    if not curve or session["actions"] - curve[-1][0] >= 5:
        curve.append((session["actions"], beh["meaningful"]))
        del curve[:-400]
    return changed


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
            "items_total": hero["items_total"],
            "books": hero["books"],
            "compass": hero["compass"],
            "completion_secs": hero["completion_secs"],
            "party_size": hero["party_size"], "world_map_at": hero["world_map_at"],
            # From the game's own save slot: the party and the world square are
            # true only there. Books and items stay on the live reading above,
            # which is fresher than the last save.
            "team_size": (snap["archive"] or {}).get("team_size"),
            "team_level": (snap["archive"] or {}).get("team_level"),
            "team": (snap["archive"] or {}).get("team"),
            "saved_at": snap["at"], "first_saved_at": snap["first_at"],
            "saved_why": snap["why"],
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
    peers[ws].put(json.dumps({"t": "log", "e": list(history),
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
            if checkpoint["enabled"] and checkpoint["state"] != "ready" and t in ("key", "tap"):
                continue
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
                            lock_held = await acquire_action_lock(f"browser holding {name}")
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
                    if borrowed or await acquire_action_lock(f"browser tapping {name}"):
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
                 maxframes=DEFAULT_SETTLE_MAX_FRAMES, depth=0):
    """Wait for the game to react, then for the picture to hold still, and
    through a scene transition, so the picture the caller gets is the one to
    act on.

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
    if depth == 0 and LIB.fb_luma() < DARK:
        # The screen is black: a scene is changing. Wait for it to be drawn,
        # then for it to hold still, once; a screen that stays black is
        # returned as it is.
        waited = 0
        while waited < TRANSITION_FRAMES and LIB.fb_luma() < DARK:
            await wait_core_frames(1)
            waited += 1
            world["dark"] = True
        n += waited
        if LIB.fb_luma() >= DARK:
            more, _ = await settle(LIB.core_frame_hash(), react=react, stable=stable,
                                   maxframes=maxframes, depth=1)
            n += more
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


async def acquire_action_lock(holder="", timeout=None):
    """Acquire the one-player lease shared by REST and browser input.

    `timeout` is for callers that would rather not take a turn at all than
    wait for one: the save macro gives up instantly so an agent never queues
    behind the benchmark's own housekeeping.
    """
    stats["queued"] += 1
    try:
        await asyncio.wait_for(action_lock().acquire(),
                               timeout=LOCK_TIMEOUT if timeout is None else timeout)
        stats["holder"] = holder
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
    if budget:
        budget.check()
    else:
        check_input_runtime()
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

    if not await acquire_action_lock(f"{actor(request)} {verb} {note}"[:60]):
        return web.json_response(
            {"ok": False, "error": "busy", "queued": stats["queued"],
             "holder": stats["holder"],
             "hint": f"{stats['holder'] or 'another controller'} holds the game; "
                     "a browser keeps the lease for as long as its key is down"},
            status=503)

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
        action_entry = log_action(rec["actor"], verb, note, detail=held_note(steps),
                                  key_events=len(key_steps), input_frames=input_frames,
                                  wait_call=not key_steps)
        if not disk_history_enabled():
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
        trajectory = note_move()
        screen_changed = note_screen()
        action_at = (action_entry.get("at") - rec["started"]
                     if isinstance(action_entry, dict)
                     and type(action_entry.get("at")) in (int, float)
                     else None)
        record_trajectory(trajectory, screen_changed, action_at=action_at)
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
                      "picked_item", "items_total", "books", "compass",
                      "completion_secs", "party_size", "world_map_at"):
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

    # The response says what was done and names the frame that followed, and
    # nothing about what the screen did: a hash or a "changed" flag flips on
    # an idle animation as readily as on a step, and a model that trusted one
    # counted steps it never took. What happened is read from the picture.
    result = {"ok": True, "action": note, **core_fields()}
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


def only(body, *known):
    """Refuse a body field this call does not read.

    Ignoring it silently is the failure this API is built to avoid: the caller
    is told 200 and the game does something else. ``{"frames": 70}`` on a wait
    that measures milliseconds is a request that never happened, and the
    agent has no way to find that out.
    """
    unknown = sorted(set(body) - set(known))
    if unknown:
        raise ValueError(
            f"unknown field{'s' if len(unknown) > 1 else ''}: "
            f"{', '.join(unknown)}; this call takes {', '.join(known)}")
    return body


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
    react = bounded_int(q.get("react"), "react", 30, 0, MAX_SETTLE_FRAMES)
    stable = bounded_int(q.get("stable"), "stable", DEFAULT_STABLE_FRAMES,
                         1, MAX_STABLE_FRAMES)
    maxframes = bounded_int(q.get("maxsettle"), "maxsettle",
                            DEFAULT_SETTLE_MAX_FRAMES, 1, MAX_SETTLE_FRAMES)
    return {"react": react, "stable": stable, "maxframes": max(maxframes, react)}


def wants_image(request):
    return str(request.query.get("image", "0")).lower() in ("1", "true", "yes")


def core_fields():
    """The description of the machine that every reply carries.

    The same set the native runner returns, so one agent loop can read either
    without knowing which it is talking to. ``frame`` names the picture. No
    hash of the screen and no "changed" flag: both flip on an idle animation
    as readily as on a step, and an agent that trusted them counted steps it
    never took. Emulated-frame counters and the session's own numbers are not
    here either: they belong to the board, not to the agent playing.
    """
    return {
        "width": LIB.core_width(), "height": LIB.core_height(),
        "frame": LIB.core_frame_serial(),
    }


def validate_action_frames(count, hold, gap):
    total = count * (hold + KEY_RELEASE_FRAMES) + max(0, count - 1) * gap
    if total > MAX_ACTION_FRAMES:
        raise ValueError(
            f"action is too long ({total} frames; maximum {MAX_ACTION_FRAMES})"
        )


def keycode(name):
    return KEYS.get(str(name).strip().lower())


# What a save with no name of its own is called. The window's own quick save
# writes here too, so ⌘S and a nameless POST mean the same slot.
QUICK_STATE = "slot1"


def state_path(body):
    raw = body.get("name", QUICK_STATE)
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
    """Press one key or several in order: ``{"key": "kp3"}`` or
    ``{"key": ["kp9", "enter"]}``, with an optional ``hold`` in emulated
    frames for every key. There is no other action call: a repeat is a list
    of the same key, and there is no "let the game run" because an action
    already returns when the screen has settled, a scene transition included.
    """
    d = await body_of(request)
    if d is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    try:
        only(d, "key", "hold")
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    raw = d.get("key")
    names = raw if isinstance(raw, list) else [raw]
    if not 1 <= len(names) <= MAX_KEYS_PER_ACTION:
        return web.json_response(
            {"ok": False,
             "error": f"key must be one key name or a list of 1 to {MAX_KEYS_PER_ACTION}"},
            status=400)
    codes = [keycode(k) if isinstance(k, str) else None for k in names]
    if any(c is None for c in codes):
        bad = [str(k) for k, c in zip(names, codes) if c is None]
        return web.json_response({"ok": False, "error": "unknown key: " + ", ".join(bad),
                                  "hint": "GET /api/keys lists every name"}, status=400)
    try:
        hold = bounded_int(d.get("hold"), "hold", DEFAULT_TAP_FRAMES,
                           MIN_HOLD_FRAMES, MAX_HOLD_FRAMES)
        validate_action_frames(len(names), hold, BETWEEN_TAPS_FRAMES)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    names = [str(k).strip().lower() for k in names]
    steps = []
    for i, c in enumerate(codes):
        steps.append((c, hold, names[i]))
        if i != len(codes) - 1:
            steps.append(("frames", BETWEEN_TAPS_FRAMES))
    verb = "KEY" if len(names) == 1 else "KEYS"
    return await run_action(request, steps, " ".join(names), verb=verb)


async def api_screen(request):
    """The only way to look at the screen. JSON, or ?format=png|webp|jpeg.

    ?spectate=1 is a look that is not the player's: it publishes a thumbnail
    for the catalogue. It must not count as a read against the agent, nor
    appear in its action log, or watching a run would change its numbers.
    """
    fmt = request.query.get("format", "")
    if fmt not in SCREEN_FORMATS:
        return web.json_response(
            {"ok": False,
             "error": f"format must be one of {', '.join(f for f in SCREEN_FORMATS if f)}"
                      "; omit it for JSON with a base64 PNG"}, status=400)
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
    # The lock an action holds is the lock the benchmark's own save holds, so
    # a look waits like a key does and never shows a menu the player did not
    # open. A spectator's look takes the frame as it is.
    held = (not watching and api_lock is not None
            and await acquire_action_lock(f"{actor(request)} look"[:60]))
    try:
        data, w, h, mime = snapshot(fmt if fmt in ("webp", "jpeg") else "png")
    finally:
        if held:
            action_lock().release()
            stats["holder"] = ""
    if not data:
        return web.json_response({"ok": False, "error": "no frame"}, status=503)
    if fmt in ("png", "webp", "jpeg"):
        return web.Response(body=data, content_type=mime)
    return web.json_response({
        "ok": True, "image_width": w, "image_height": h,
        "image": f"data:{mime};base64," + base64.b64encode(data).decode(),
        **core_fields(),
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
    # Only the multiuser gateway sets this header, and a scored session never
    # sits behind that gateway, so a client's own value is ignored there.
    prefix = request.headers.get("X-Forwarded-Prefix", "").rstrip("/")
    if not warden.ON and re.fullmatch(r"/u/[A-Za-z0-9_-]{20,64}", prefix):
        return base + prefix
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
        path, name = state_path(only(body, "name"))
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    if not await acquire_action_lock("save"):
        return web.json_response({"ok": False, "error": "busy",
                                  "holder": stats["holder"]}, status=503)
    ok = False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        await pause_emulator()
        try:
            LIB.core_release_all_keys()
            ok = bool(LIB.core_save_state(str(path).encode()))
            result = {"ok": ok, "action": "save", "slot": name, **core_fields()}
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
        result = {"ok": False, "action": "save", "slot": name, "error": str(exc)}
    finally:
        action_lock().release()
    log_action(actor(request), "SAVE", name, ok=ok)
    return web.json_response(result, status=200 if result.get("ok") else 500)


async def checkpoint_core(path, *, saving):
    """Drain native work before releasing the pause, including cancellation."""
    try:
        await pause_emulator()
        def operation():
            LIB.core_release_all_keys()
            if saving:
                return bool(LIB.core_save_state(str(path).encode()))
            ok = bool(LIB.core_load_state(str(path).encode()))
            if ok:
                LIB.fb_reset()
            return ok

        task = asyncio.create_task(asyncio.to_thread(operation))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # A cancelled await cannot stop ctypes. Keep the lease and pause
            # until that call has actually returned.
            await task
            raise
    finally:
        resume_emulator()


async def save_checkpoint():
    if warden.ON or not RESUME_STATE or checkpoint["state"] != "ready":
        return False
    async with action_lock():
        # Keep the old checkpoint until execution is healthy on both sides
        # of serialization; the file itself is staged in its own directory.
        await wait_core_frames(2)
        path = pathlib.Path(RESUME_STATE)
        pending = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not await checkpoint_core(pending, saving=True):
                raise RuntimeError(core_error("checkpoint save failed"))
            await wait_core_frames(2)
            os.replace(pending, path)
            checkpoint.update(saves=checkpoint["saves"] + 1, last_saved=time.time(), error=None)
            return True
        finally:
            pending.unlink(missing_ok=True)


async def resume_and_autosave():
    if warden.ON or not RESUME_STATE:
        return
    try:
        async with action_lock():
            checkpoint["state"] = "warming"
            await wait_core_frames(RESUME_WARMUP_FRAMES)
            if LIB.core_width() <= 0 or LIB.core_height() <= 0:
                raise RuntimeError("the core has not produced a frame")
            path = pathlib.Path(RESUME_STATE)
            if path.exists():
                checkpoint["state"] = "restoring"
                if not await checkpoint_core(path, saving=False):
                    raise RuntimeError(core_error("checkpoint restore failed"))
                await wait_core_frames(2)
                checkpoint["restored"] = True
                await send_keyframe(None)
            checkpoint.update(state="ready", error=None)
    except Exception as exc:
        # Do not accept input or overwrite an unreadable previous session
        # with the newly booted machine. An operator must resolve the file.
        checkpoint.update(state="failed", error=str(exc))
        stats["last_error"] = "resume: " + str(exc)
        return
    while AUTOSAVE_SECONDS > 0:
        await asyncio.sleep(AUTOSAVE_SECONDS)
        try:
            await save_checkpoint()
        except Exception as exc:
            checkpoint["error"] = str(exc)
            stats["last_error"] = "autosave: " + str(exc)


async def api_load(request):
    if warden.ON:
        # A scored run has no out-of-band rewind. Hidden, like reset.
        raise web.HTTPNotFound()
    body = await body_of(request)
    if body is None:
        return web.json_response({"ok": False, "error": "JSON object required"}, status=400)
    try:
        path, name = state_path(only(body, "name"))
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)
    if not path.is_file():
        return web.json_response({"ok": False, "error": "no such slot"}, status=404)
    if not await acquire_action_lock("load"):
        return web.json_response({"ok": False, "error": "busy",
                                  "holder": stats["holder"]}, status=503)
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
        result = {"ok": ok, "action": "load", "slot": name, **core_fields()}
        if not ok:
            result["error"] = core_error("load failed")
        if wants_image(request):
            try:
                attach_snapshot(result)
            except Exception as exc:
                result["image_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        result = {"ok": False, "action": "load", "slot": name, "error": str(exc)}
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
        persist_activity()
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
                    items_total=None, books=None, compass=None,
                    completion_secs=None, inventory_baseline=None,
                    world_x=None, world_y=None, party_size=None,
                    moved_on_map=False, world_map_at=None)
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
        return await recording_api.handle(
            request, include_trajectory=include_trajectory(request))
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
    if warden.ON:
        warden.note_help(lang)      # which brief this run read, on the record
    return web.Response(text=system_prompt(base_url(request), lang, core_only,
                                           benchmark=warden.ON),
                        content_type="text/plain", charset="utf-8")


async def saved_history_script(_request):
    return web.FileResponse(ROOT / "saved-history.js", headers={"Cache-Control": "no-store"})


async def recording_script(_request):
    return web.FileResponse(ROOT / "recording.js")


async def video_export_script(_request):
    return web.FileResponse(ROOT / "video-export.js", headers={"Cache-Control": "no-store"})


async def replay_script(_request):
    return web.FileResponse(ROOT / "replay.js")


async def index(_request):
    # The benchmark deliberately has no saved-history endpoints. Let its
    # observer page choose the available live log without probing a 404.
    page = (ROOT / "index.html").read_text(encoding="utf-8").replace(
        'data-history-enabled="auto"',
        f'data-history-enabled="{str(not warden.ON).lower()}"')
    return web.Response(text=page, content_type="text/html",
                        headers={"Cache-Control": "no-store"})


async def progress(request):
    """The save slot, decoded, for the browser that reads it like a game.

    Separate from /status because it is bigger and nobody polls it: the panel
    fetches it when someone opens it, and again when the save time moves.
    """
    if withheld(request):
        return web.json_response({"ok": False, "error": "not while the run is scored"},
                                 status=404)
    archived = snap["archive"] or {}
    return web.json_response({
        "ok": True,
        "saved_at": snap["at"], "why": snap["why"], "slot": SNAPSHOT_SLOT,
        "detail": archived.get("detail"),
        # The live reading, which is fresher than the save for everything the
        # save is not the only source of.
        "live": {k: hero[k] for k in ("level", "exp", "hp", "maxhp", "skills",
                                      "books", "book_ids", "items_total",
                                      "inventory_distinct", "compass")},
    })


# What a scored run must not be able to read about itself. A model that can
# see its own score can play the score; the board and the operator see these,
# the agent never does.
SCORED_FIELDS = ("level", "exp", "hp", "maxhp", "skills", "reputation",
                 "potential", "inventory_distinct", "picked_item",
                 "items_total", "books", "compass", "completion_secs",
                 "party_size", "world_map_at",
                 "meaningful", "oscillation",
                 "scenes", "frontier", "bigmap", "exit_acts", "exit_secs",
                 "team_size", "team_level", "team", "saved_at", "first_saved_at",
                 "saved_why")


def operator(request):
    """True when the caller holds the token the broker keeps to itself."""
    want = os.environ.get("QUNXIA_RESET_TOKEN")
    got = request.query.get("token") or request.headers.get("X-Reset-Token")
    return bool(want) and hmac.compare_digest(
        (got or "").encode("utf-8"), want.encode("utf-8"))


def include_trajectory(request):
    """Only an explicitly authenticated operator may read recorded coordinates.

    Trajectory markers are written for offline analysis. They must stay out of
    every ordinary recording response, including interactive non-benchmark
    sessions where the benchmark warden is disabled.
    """
    return operator(request)


def withheld(request):
    """Whether this caller must not see what the run has achieved.

    A model that can watch its own score can play the score, so a scored run
    keeps these from everyone but the operator - while it is still being
    played. Once it is over there is nothing left to play for and the numbers
    are published anyway, so whoever is watching can read them.
    """
    return warden.ON and not warden.run["done"] and not operator(request)


async def status(_request):
    summary = session_summary()
    if withheld(_request):
        summary = {k: v for k, v in summary.items() if k not in SCORED_FIELDS}
    return web.json_response({
        "width": LIB.core_width(), "height": LIB.core_height(),
        "fps": round(LIB.core_fps(), 3), "frame": LIB.core_frame_serial(),
        "clients": len(clients), "session": summary, **stats,
        **(health.snapshot() if health else {}),
        "recording": {"cache_bytes": 0, "pending_bytes": recording_store.pending_bytes if recording_store else 0,
                      "error": recording_store.error if recording_store else ""},
        "checkpoint": dict(checkpoint),
    })


@web.middleware
async def json_errors(request, handler):
    """Whatever goes wrong, an agent gets JSON it can read.

    An unhandled exception used to come back as an HTML 500, which a caller
    cannot parse and which reads as the service being down rather than as one
    bad request.
    """
    try:
        if (checkpoint["enabled"] and checkpoint["state"] != "ready"
                and request.method == "POST" and request.path.startswith("/api/")):
            return web.json_response({"ok": False, "error": "session_not_ready",
                                      "checkpoint": dict(checkpoint)}, status=503)
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
    if RESUME_STATE:
        app["checkpoint"] = asyncio.create_task(resume_and_autosave())
    else:
        app["snapshotter"] = asyncio.create_task(snapshotter())
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
    saving = app.get("checkpoint")
    if saving:
        saving.cancel()
        await asyncio.gather(saving, return_exceptions=True)
        try:
            await asyncio.wait_for(save_checkpoint(), timeout=10)
        except Exception as exc:
            stats["last_error"] = "shutdown checkpoint: " + str(exc)
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
    if RESUME_STATE and (not math.isfinite(AUTOSAVE_SECONDS) or AUTOSAVE_SECONDS < 0
                         or RESUME_WARMUP_FRAMES < 1):
        raise SystemExit("checkpoint interval must be finite and non-negative; warmup frames must be positive")
    restore_activity()
    directory = os.environ.get("QUNXIA_RECORDING_DIR", str(ROOT.parent / "recordings"))
    validate_recording_directory(directory)
    path = pathlib.Path(os.environ.get("QUNXIA_RECORDING_FILE", str(pathlib.Path(directory) / f"{PORT}.jsonl")))
    validate_recording_directory(path.parent)
    recording_store = RecordingStore(path)
    recording_api = RecordingAPI(recording_store, archives=not warden.ON)
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
    app.router.add_get("/saved-history.js", saved_history_script)
    app.add_routes([
        web.get("/", index),
        web.get("/recording.js", recording_script),
        web.get("/replay.js", replay_script),
        web.get("/video-export.js", video_export_script),
        web.get("/ws", ws_handler),
        web.get("/status", status),
        web.get("/progress", progress),
        web.get("/api/screen", api_screen),
        web.get("/api/help", api_help),
        web.get("/api/keys", api_key_names),
        web.get("/api/slots", api_slots),
        web.get("/api/history", api_history),
        web.get("/api/recording", api_recording),
        web.post("/api/reset", api_reset),
        web.post("/api/snapshot", api_snapshot),
        web.post("/api/key", api_key),
        web.post("/api/save", api_save),
        web.post("/api/load", api_load),
    ])
    recording_api.install(app)
    # Startup handlers are awaited, so the workers are detached tasks rather
    # than returned, or startup would block on loops that never end.
    pin_provider = getattr(recording_api, "pin", None)
    SavedHistory(recording_store, pin_provider=pin_provider).install(app, enabled=not warden.ON)
    VideoExports(recording_store, pin_provider=pin_provider).install(app, enabled=not warden.ON)
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    web.run_app(app, host=HOST, port=PORT, access_log=None)


if __name__ == "__main__":
    main()
