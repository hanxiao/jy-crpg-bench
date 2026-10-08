"""One session measured end to end: the events, the milestones, the chain of
steps and the two routes, from frames of a published video or of a live game.

The clock is the replay's own: video seconds for a published video, and play
seconds divided by LIVE_SPEED for a live game, so a live session reads exactly
as its replay at that speed would.
"""
import json
import math
import subprocess

import numpy as np

from . import draw
from .events import HOLD, Scanner, to_gray, is_black
from .ladder import STEPS, chain_minutes, service_rungs
from .routes import HouseTracker, WorldTracker

LIVE_SPEED = 8.0
VERSION = 3          # 2: dialogue, saves and loads; 3: those three as rungs 12 to 14


class SessionMeasure:
    """Feed frames in order with their clock; read `result` at any time."""

    def __init__(self, speed, fps, world=None, house=True, fast=False):
        self.speed = float(speed)
        # the frames that span HOLD seconds of play at `fps` frames per clock second
        self.scanner = Scanner(math.ceil(HOLD * fps / self.speed - 1e-9))
        self.house = HouseTracker(fast=fast) if house else None
        self.world = WorldTracker(world, fast=fast) if world is not None else None
        self.marks = []

    def minute(self, clock):
        return clock * self.speed / 60

    def feed(self, rgb, clock, routes=True, gray=None):
        """One frame. A published video passes the luma it stores as `gray`;
        a live game passes its RGB frame alone."""
        if gray is None:
            gray = to_gray(rgb)
        black = is_black(gray)
        self.scanner.feed(gray, clock, black)
        if not routes or black:
            return
        if self.scanner.first_black is None:
            if self.house is not None:
                self.house.feed(rgb, self.minute(clock))
        elif self.world is not None:
            self.world.feed(rgb, self.minute(clock))

    def mark(self, clock, keys):
        """An action at `clock`: its keys, as [[name, hold seconds], ...]."""
        self.marks.append({"t": clock, "keys": keys})

    def replay(self, marks=None):
        ev = self.scanner.summary(self.speed, self.marks if marks is None else marks)
        for n, v in ev.items():
            if isinstance(v, dict) and "candidates" in v:
                v.pop("candidates")
        return ev

    def result(self, memory=None, marks=None):
        """The measure block of a catalogue entry. `memory` holds what the
        service read from the emulator (books, compass, the minute of the
        first book)."""
        row = dict(memory or {})
        row["replay"] = self.replay(marks)
        rungs = service_rungs(row)
        chain = chain_minutes(row, self.speed)
        use = self.marks if marks is None else marks
        black = row["replay"]["first_black_second"]
        return {"version": VERSION,
                "crossing_keys": crossing_keys(use, black),
                "rungs": rungs,
                "reached": sum(1 for v in rungs if v is True),
                "chain": [chain[s] for s in STEPS],
                "events": row["replay"],
                "house": self.house.path() if self.house else [],
                "world": [p[:5] for p in self.world.points] if self.world else []}

    def pictures(self, world_map, budget_minutes, events=None):
        """PNG bytes of the house route and the world-map route (None when the
        path is too short to draw)."""
        house = draw.house(self.house.path(), budget_minutes) if self.house and len(self.house.points) >= 2 else None
        worldp = None
        if self.world is not None and len(self.world.points) >= 2:
            worldp = draw.world(self.world.points, world_map, budget_minutes, marks=world_marks(self.world.points, events))
        return house, worldp


def counters(ev):
    """The conversations of a reading without the minute of each, which the
    live index and the catalogue have no room for."""
    d = ev.get("dialogue") or {}
    return {"count": d.get("count", 0), "distinct": d.get("distinct", 0), "first_minute": d.get("first_minute")}


def crossing_keys(marks, first_black):
    """Keys pressed before the first black frame, the exit onto the world map."""
    if first_black is None or not marks:
        return None
    return sum(len(m["keys"]) for m in marks if m["t"] <= first_black)


def world_marks(points, events, names=("hermit", "compass", "battle", "won", "defeat")):
    """Numbered marks at the last world-map point before each location entered
    and each first event: (px, py, number)."""
    if not events or not points:
        return []
    when = []
    for e in (events.get("scenes") or {}).get("entries", []):
        when.append(e["minute"])
    for n in names:
        m = (events.get(n) or {}).get("first_minute")
        if m is not None:
            when.append(m)
    out, k = [], 0
    for m in sorted(set(when)):
        before = [p for p in points if p[4] <= m]
        if not before:
            continue
        k += 1
        out.append((before[-1][0], before[-1][1], k))
    return out


def video_frames(path):
    """(gray, RGB) game frames of a published video, and its frame rate. The
    gray is the luma the video stores, which the events are read from; the
    RGB, rebuilt from subsampled chroma, places the routes."""
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    a, b = o.split("/") if "/" in o else (o, "1")
    fps = float(a) / float(b)

    def pipe(fmt):
        return subprocess.Popen(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path,
                                 "-vf", "scale=320:232,crop=320:200:0:0", "-f", "rawvideo", "-pix_fmt", fmt, "-"],
                                stdout=subprocess.PIPE)

    def gen():
        pg, pc = pipe("gray"), pipe("rgb24")
        ng, nc = 320 * 200, 320 * 200 * 3
        while True:
            bg, bc = pg.stdout.read(ng), pc.stdout.read(nc)
            if len(bg) < ng or len(bc) < nc:
                break
            yield (np.frombuffer(bg, np.uint8).reshape(200, 320).astype(np.float32),
                   np.frombuffer(bc, np.uint8).reshape(200, 320, 3))
        for p in (pg, pc):
            p.stdout.close()
            p.wait()
    return fps, gen()


def measure_video(path, timeline, world=None, memory=None):
    """The measure block of a published session: every frame of its video."""
    speed = timeline["speed"] if timeline else 8.0
    fps, frames = video_frames(path)
    m = SessionMeasure(speed, fps, world=world)
    for i, (g, f) in enumerate(frames):
        m.feed(f, i / fps, gray=g)
    marks = timeline["marks"] if timeline else None
    return m, m.result(memory, marks)


if __name__ == "__main__":
    import sys
    tl = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    _, res = measure_video(sys.argv[1], tl)
    print(json.dumps({k: v for k, v in res.items() if k not in ("house", "world")}, ensure_ascii=False)[:2000])
