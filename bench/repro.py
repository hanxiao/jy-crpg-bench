"""Regenerate the canonical input script from the committed start state.

The paper's reproducibility statement is that a run regenerates
byte-identically: committed start state plus committed inputs, and the
frames follow.  This file is that claim made executable: it boots the real
core with no server and no browser, loads the committed start state,
replays a fixed input schedule frame by frame, and reports the signature
of the result.

  python3 bench/repro.py                 # one regeneration, signature to stdout
  python3 bench/repro.py --check bench/golden/repro-darwin.json

The signature carries the whole machine state after the script (sha256 of
the core's own savestate) plus sampled frame hashes, so any
nondeterminism anywhere in the pipeline - emulator, game, filesystem,
build - shows up as a difference.  The test in bench/test_repro.py
regenerates twice in fresh processes and requires the two, and on the
platform of the committed golden that, to agree.

Three invariants make the start state a well-defined origin, and all are
pinned here:

* The state may only be loaded while the game is running.  The core pauses
  its emulation thread at the load only outside its boot phase; a load
  mid-boot lands wherever the boot happens to be and is not
  reproducible.  The live server is always warm - its reset arrives after
  the title screen has parked - so the regeneration boots to the parked
  title first (boot_to_park).
* Every frame is paced at the core's native rate, exactly as the live
  server paces it.  The core runs its frames on its own thread, which
  samples the keyboard mid-frame; an unpaced loop races that thread, a
  key press then lands in whichever frame it happens to be in, and the
  result is no longer reproducible.  One frame per 1/fps wall clock
  leaves the thread idle between frames, so each press lands in exactly
  one frame and every count in the signature is exact.
* Once the game is running, how long it was parked must not matter: the
  load lands on the same machine state no matter when it arrives.

Nothing here needs the live service: CoreHost and the standard library
only.  Where the real core, game, or start state is absent (CI builds no
game) the check reports what is missing and exits 3.
"""
import argparse
import ctypes
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "server" / "libqunxia.so"
GAME = os.environ.get("QUNXIA_GAME", str(ROOT / "game" / "PLAY.BAT"))
START_STATE = os.environ.get("QUNXIA_START_STATE", str(ROOT / "saves" / "start.state"))
TRACKED_START_STATE = ROOT / "paper" / "src" / "figures" / "start.state"

# The boot shows static stretches of its own (a still frame mid-DOS-boot),
# so the parked check is only trusted after this many emulated frames; the
# cap bounds a boot that never parks (a crash parks too, on a black screen,
# which the colour check below rejects).
BOOT_MIN_FRAMES = 1500
BOOT_CAP = 3000
PARK_STABLE = 30


def core_path():
    env = os.environ.get("QUNXIA_CORE")
    if env:
        return env
    name = "dosbox_pure_libretro." + ("dylib" if platform.system() == "Darwin" else "so")
    for candidate in (ROOT / "Cores" / name, ROOT / "cores" / name,
                      ROOT / "vendor" / "dosbox-pure" / name):
        if candidate.exists():
            return str(candidate)
    return str(ROOT / "Cores" / name)


# libretro RETROK_*: printable keys keep their ASCII codes, the arrows are 273+.
RETROK = {"space": 32, "escape": 27, "tab": 9,
          "up": 273, "down": 274, "right": 275, "left": 276}

# canonical-v1: ten seconds of play at the game's native rate - walk the
# four ways, attack twice, open and close a menu.  Every key is released
# before the last frame.  (frame, key, down)
SCRIPT = [
    (0,   "up",     True),
    (60,  "up",     False),
    (64,  "right",  True),
    (88,  "right",  False),
    (92,  "down",   True),
    (112, "down",   False),
    (116, "left",   True),
    (136, "left",   False),
    (140, "space",  True),
    (143, "space",  False),
    (146, "space",  True),
    (149, "space",  False),
    (152, "up",     True),
    (200, "up",     False),
    (204, "tab",    True),
    (207, "tab",    False),
    (212, "escape", True),
    (215, "escape", False),
    (220, "down",   True),
    (250, "down",   False),
    (254, "right",  True),
    (296, "right",  False),
]
TOTAL = 300
SCRIPT_VERSION = "canonical-v1"


def load_library():
    lib = ctypes.CDLL(str(LIB))
    lib.core_set_option.argtypes = [ctypes.c_char_p] * 2
    lib.core_init.argtypes = [ctypes.c_char_p] * 3
    lib.core_init.restype = ctypes.c_bool
    lib.core_load_state.argtypes = [ctypes.c_char_p]
    lib.core_load_state.restype = ctypes.c_bool
    lib.core_save_state.argtypes = [ctypes.c_char_p]
    lib.core_save_state.restype = ctypes.c_bool
    lib.core_key.argtypes = [ctypes.c_int, ctypes.c_bool]
    lib.core_run_frame.argtypes = []
    lib.core_shutdown.argtypes = []
    lib.core_frame_hash.restype = ctypes.c_uint64
    lib.core_frame_serial.restype = ctypes.c_uint64
    lib.core_ticks.restype = ctypes.c_uint64
    lib.core_fps.restype = ctypes.c_double
    lib.core_last_error.restype = ctypes.c_char_p
    lib.core_pixels.restype = ctypes.c_void_p
    lib.core_pitch.restype = ctypes.c_int
    lib.core_width.restype = ctypes.c_int
    lib.core_height.restype = ctypes.c_int
    return lib


def boot_to_park(lib, fps, extra=0):
    """Paced frames until the title screen has parked; return the count.

    Paced the way the live server paces: one frame per 1/fps wall clock, so
    the core's emulation thread is idle between frames and every frame
    count is exact.  Parking means the same frame for PARK_STABLE
    consecutive frames after BOOT_MIN_FRAMES: the boot itself contains
    static stretches, and a crashed game parks too - on black, which is
    why a parked screen must also carry colour.  ``extra`` keeps the title
    up for more frames before returning, to prove the load does not depend
    on how long the game was running.
    """
    frames, prev, stable = 0, None, 0
    while frames < BOOT_CAP:
        lib.core_run_frame()
        frames += 1
        h = lib.core_frame_hash()
        stable = stable + 1 if h == prev else 0
        prev = h
        if frames >= BOOT_MIN_FRAMES and stable >= PARK_STABLE:
            break
        time.sleep(1.0 / fps)
    if frames < BOOT_MIN_FRAMES or stable < PARK_STABLE:
        raise SystemExit(f"the boot did not park within {BOOT_CAP} frames")
    pitch, width, height = lib.core_pitch(), lib.core_width(), lib.core_height()
    frame = ctypes.string_at(lib.core_pixels(), height * pitch)
    if len(set(frame[::97])) < 8:
        raise SystemExit("the parked screen carries no colour; the game "
                         "did not boot (a crash parks on black)")
    for _ in range(extra):
        lib.core_run_frame()
        frames += 1
        time.sleep(1.0 / fps)
    return frames


def regenerate(lib, core, game, start, extra=0):
    """Boot to the parked title, load the start state, replay SCRIPT.

    Every frame is paced at the core's native rate, exactly as the live
    server paces it: the core runs its frames on its own thread, which
    samples the keyboard mid-frame, so an unpaced loop races it - a key
    press then lands in whichever frame the thread happens to be in, and
    the result is no longer reproducible.  One frame per 1/fps wall clock
    leaves the thread idle between frames, so each press lands in exactly
    one frame and each count below is exact.  All frame counts are
    relative to the load.
    """
    saves = tempfile.mkdtemp(prefix="repro-saves-")
    try:
        # The same pins the live server uses (server/main).
        for key, value in (("dosbox_pure_cycles", "26800"),
                           ("dosbox_pure_sblaster_type", "none"),
                           ("dosbox_pure_midi", "disabled")):
            lib.core_set_option(key.encode(), value.encode())
        if not lib.core_init(core.encode(), game.encode(), saves.encode()):
            raise SystemExit("core_init failed: " + lib.core_last_error().decode())
        fps = float(lib.core_fps())
        boot_frames = boot_to_park(lib, fps, extra)
        if not lib.core_load_state(start.encode()):
            raise SystemExit("start state would not load: "
                             + lib.core_last_error().decode())
        serial0, ticks0 = lib.core_frame_serial(), lib.core_ticks()
        by_frame = {}
        for frame, key, down in SCRIPT:
            by_frame.setdefault(frame, []).append((RETROK[key], down))
        hashes = []
        for frame in range(TOTAL):
            for code, down in by_frame.get(frame, ()):
                lib.core_key(code, down)
            lib.core_run_frame()
            if (frame + 1) % 50 == 0:
                hashes.append(int(lib.core_frame_hash()))
            time.sleep(1.0 / fps)
        state = Path(saves) / "final.state"
        if not lib.core_save_state(str(state).encode()):
            raise SystemExit("save state failed: " + lib.core_last_error().decode())
        blob = state.read_bytes()
        return {
            "script": SCRIPT_VERSION,
            "platform": platform.system().lower(),
            "start_sha256": hashlib.sha256(Path(start).read_bytes()).hexdigest(),
            "boot_frames": boot_frames,
            "fps": round(fps, 3),
            "ticks_delta": int(lib.core_ticks() - ticks0),
            "serial_delta": int(lib.core_frame_serial() - serial0),
            "hashes": hashes,
            "state_sha256": hashlib.sha256(blob).hexdigest(),
            "state_bytes": len(blob),
        }
    finally:
        lib.core_shutdown()
        shutil.rmtree(saves, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", metavar="GOLDEN",
                        help="fail unless the signature matches this file")
    parser.add_argument("--extra", type=int, default=0,
                        help="title frames to keep parked before the load")
    args = parser.parse_args()

    missing = [str(p) for p in (LIB, GAME, START_STATE) if not Path(p).exists()]
    if missing:
        print("missing: " + ", ".join(missing), file=sys.stderr)
        sys.exit(3)
    if TRACKED_START_STATE.exists() and not Path(START_STATE).samefile(TRACKED_START_STATE):
        if hashlib.sha256(Path(START_STATE).read_bytes()).hexdigest() \
                != hashlib.sha256(TRACKED_START_STATE.read_bytes()).hexdigest():
            print("the start state differs from the committed copy", file=sys.stderr)
            sys.exit(3)

    signature = regenerate(load_library(), core_path(), GAME, START_STATE,
                           args.extra)
    if args.check:
        golden = json.loads(Path(args.check).read_text())
        if signature == golden:
            print("the canonical script regenerates the committed golden")
        else:
            for key in sorted(set(signature) | set(golden)):
                if signature.get(key) != golden.get(key):
                    print(f"  {key}:\n    regenerated {signature.get(key)!r}\n"
                          f"    golden      {golden.get(key)!r}")
            sys.exit(1)
    else:
        print(json.dumps(signature, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
