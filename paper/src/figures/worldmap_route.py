"""A model's walk on the world map, read from its replay and placed on the
rendered world map of worldmap.py.

    python worldmap_route.py <session id> [<minutes>]

Every frame from the first black frame of the replay (the crossing) to the
given minute of play, 60 by default, is placed on the rendered world map (server/measure) at the offset
of highest normalised cross-correlation, over the frame without the status
strip and without any dialogue box or menu. The world map always scrolls to
keep the hero at one screen position, so his tile is the offset of the frame
plus HERO, the screen point that the compass reading of a replay fixes. A
match is searched within MAX_JUMP px of the last placed frame and, when that
fails (after a scene or a loaded save), over the whole map at a quarter of the
resolution, where a match must reach GLOBAL_NCC. Frames inside a scene, a fight or a menu do not match the map and
are skipped. The output, routes/world-<session>.json, holds one row per placed
frame: map pixel x and y, the game coordinates, the minute of play and the
correlation.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "human"))
import field  # noqa: E402
from anchored_route import fps_of, frames  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "server"))
from measure.routes import WorldMap, WorldTracker  # noqa: E402  the service places frames with the same code
from measure import worldmap as measure_worldmap  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
W0, H0 = 320, 200
OUT = os.path.join(HERE, "routes")
GAME = os.path.join(HERE, "..", "..", "..", "game")
CACHE = os.path.join(HERE, "worldmap-cache")   # derived from the game files, not tracked


def track(video, t0, t1, speed):
    """The hero's tiles on the world map in a video from t0 to t1 seconds: one
    row (px, py, x, y, minute of play, correlation) per placed frame; speed is
    the replay speed, 1 for a recording in real time."""
    fps = fps_of(video)
    if not os.path.exists(os.path.join(CACHE, "worldmap.json")):
        measure_worldmap.build_cache(GAME, CACHE)
    t = WorldTracker(WorldMap(CACHE))
    for i, f in enumerate(frames(video, t1)):
        if i / fps >= t0:
            t.feed(f, i / fps * speed / 60.0)
    return t.points


def main():
    sid = sys.argv[1]
    minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    row = next(r for r in field.load_runs(dedup=False, keep_excluded=True) if r["id"] == sid)
    ev = json.load(open(os.path.join(HERE, "replay_events.json"), encoding="utf-8"))[sid]
    speed = json.load(open(os.path.join(HERE, "timelines", sid + ".json"), encoding="utf-8"))["speed"]
    video = os.path.join(HERE, "videos", sid + ".mp4")
    if not os.path.exists(video):
        import urllib.request
        os.makedirs(os.path.dirname(video), exist_ok=True)
        urllib.request.urlretrieve(row["video_url"], video)
    rows = track(video, ev["first_black_second"], minutes * 60 / speed, speed)
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"world-{sid}.json")
    json.dump({"session": sid, "agent": row["agent"], "minutes": minutes,
               "columns": ["px", "py", "x", "y", "minute", "ncc"], "rows": rows}, open(out, "w"))
    print(sid, row["agent"], "placed", len(rows), "wrote", out)


if __name__ == "__main__":
    main()
