"""The paper's measurement of a session, as it is played.

A thread samples the game frame RATE times a second of play and feeds it to
measure.session.SessionMeasure with the clock the session's replay at
LIVE_SPEED would have, so a live session and its published video read alike.
Routes are placed at most ROUTE_EVERY seconds apart; the events on every
sample. Every action is marked with its keys, which the recruitment reading
needs. Nothing here is visible to the agent of a scored run: the server
withholds it with the rest of the run's own numbers.
"""
import json
import os
import pathlib
import threading
import time

import numpy as np

from measure.routes import WorldMap
from measure.session import LIVE_SPEED, SessionMeasure

RATE = float(os.environ.get("QUNXIA_MEASURE_RATE", "10"))
ROUTE_EVERY = float(os.environ.get("QUNXIA_MEASURE_ROUTE_EVERY", "1"))
PICTURE_EVERY = 20.0
CACHE = pathlib.Path(os.environ.get(
    "QUNXIA_WORLDMAP_CACHE", pathlib.Path(__file__).resolve().parent / "measure" / "cache"))


def world_map():
    """The rendered world map, or None where its cache was not built."""
    if (CACHE / "worldmap.json").exists():
        return WorldMap(CACHE)
    return None


class LiveMeasure:
    def __init__(self, grab, played, budget_minutes, world=None):
        """`grab()` returns the current RGB frame (200 x 320 x 3) or None;
        `played()` the seconds of play so far, or None before play starts."""
        self.grab, self.played = grab, played
        self.budget_minutes = budget_minutes
        self.world_map = world
        # coarse-to-fine placement: within a few pixels of the exact search at a
        # quarter of its cost, which the emulator on the same host needs
        self.m = SessionMeasure(LIVE_SPEED, RATE * LIVE_SPEED, world=world, fast=True)
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.book_minute = None
        self._pictures = (0.0, None, None)
        self.thread = threading.Thread(target=self.loop, name="measure", daemon=True)

    def start(self):
        self.thread.start()
        return self

    def loop(self):
        last_route = 0.0
        while not self.stop.is_set():
            t0 = time.monotonic()
            try:
                p = self.played()
                f = self.grab() if p is not None else None
                if f is not None:
                    route = t0 - last_route >= ROUTE_EVERY
                    with self.lock:
                        self.m.feed(f, p / LIVE_SPEED, routes=route)
                    if route:
                        last_route = t0
            except Exception as exc:          # a bad frame must not end the reading
                print(f"measure: {type(exc).__name__}: {exc}", flush=True)
            self.stop.wait(max(0.0, 1.0 / RATE - (time.monotonic() - t0)))

    def mark(self, keys, holds):
        """An action: its key names and the frames each was held."""
        p = self.played()
        if p is None:
            return
        with self.lock:
            self.m.mark(p / LIVE_SPEED, [[k, round(h / 70.0, 3)] for k, h in zip(keys, holds)])

    def note_books(self, books):
        if books and self.book_minute is None and self.played() is not None:
            self.book_minute = round(self.played() / 60, 1)

    def result(self, memory=None):
        memory = dict(memory or {})
        memory["book_minute"] = self.book_minute
        with self.lock:
            return self.m.result(memory)

    def summary(self, memory=None):
        """The milestones, the chain and the first minute of every event,
        without the routes: what the live index and the status carry."""
        r = self.result(memory)
        ev = r["events"]
        return {"version": r["version"], "rungs": r["rungs"], "reached": r["reached"], "chain": r["chain"],
                "first": {n: (ev.get(n) or {}).get("first_minute") for n in
                          ("hermit", "compass", "battle", "defeat", "prompt", "obtained", "won", "exp", "level")},
                "scenes": [[e["minute"], e["name"]] for e in ev["scenes"]["entries"]],
                "crossing_actions": ev["crossing_actions"], "crossing_keys": r["crossing_keys"],
                "recruited_minute": ev["recruited_minute"],
                "house_points": len(r["house"]), "world_points": len(r["world"])}

    def pictures(self, force=False):
        """PNG bytes of the house route and the world-map route, redrawn at
        most every PICTURE_EVERY seconds."""
        at, house, world = self._pictures
        if force or time.monotonic() - at >= PICTURE_EVERY:
            with self.lock:
                events = self.m.replay()
                house, world = self.m.pictures(self.world_map, self.budget_minutes, events)
            self._pictures = (time.monotonic(), house, world)
        return house, world

    def routes_json(self):
        r = self.result()
        return json.dumps({"columns_house": ["x", "y", "minute"], "house": r["house"],
                           "columns_world": ["px", "py", "x", "y", "minute"], "world": r["world"]})

    def close(self):
        self.stop.set()
