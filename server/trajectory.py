"""Action and trajectory analysis for a JSONL recording.

The recording remains the source of truth.  This module only reads it and
returns measurements that can be compared between windows of one run or
between runs.  A recording can be useful without calibrated coordinates:
action timing, pauses, reversals, and screen response are still reported, but
the position section is explicitly marked as unmeasured.
"""
from collections import defaultdict
import json
import math
from pathlib import Path


PAUSE_SECONDS = 5.0
MAX_LINE = 4 << 20

_DIRECTION = {
    "up": (1, -1), "down": (-1, 1), "left": (-1, -1), "right": (1, 1),
    "kp1": (-1, 1), "kp2": (0, 1), "kp3": (1, 1), "kp4": (-1, 0),
    "kp6": (1, 0), "kp7": (-1, -1), "kp8": (0, -1), "kp9": (1, -1),
    "upright": (1, -1), "ne": (1, -1),
    "downright": (1, 1), "se": (1, 1),
    "downleft": (-1, 1), "sw": (-1, 1),
    "upleft": (-1, -1), "nw": (-1, -1),
}


def _number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def _action_name(event):
    value = event.get("act")
    if isinstance(value, str) and value:
        return value
    label = event.get("label")
    if isinstance(label, str) and label:
        return label.split(" ", 1)[0]
    return None


def _direction(event):
    target = event.get("on") or event.get("key")
    if not isinstance(target, str):
        label = event.get("label")
        target = label.split(" ", 1)[-1] if isinstance(label, str) else ""
    # KEYS actions can carry a sequence such as ``kp9 enter``. Only the
    # directional token contributes to route reversals; confirmation keys do
    # not erase the movement direction.
    return next((_DIRECTION[token] for token in target.lower().split()
                 if token in _DIRECTION), None)


def _window(rows):
    if not rows:
        return {"actions": 0, "elapsed_s": 0.0, "actions_per_min": 0.0,
                "screen_change_ratio": None, "long_pauses": 0,
                "reverse_steps": 0, "position_samples": 0,
                "distance": None, "frontier_gain": None,
                "frontier_regressions": None}
    first, last = rows[0], rows[-1]
    elapsed = max(0.0, last["t"] - first["t"])
    gaps = [b["t"] - a["t"] for a, b in zip(rows, rows[1:])]
    changes = [row["screen_changed"] for row in rows
               if row["screen_changed"] is not None]
    positions = [(row["x"], row["y"]) for row in rows
                 if row["x"] is not None and row["y"] is not None]
    # Missing samples and scene changes break the path; never count a scene
    # transition or bridge an unobserved segment as walked distance.
    segments = [max(abs(b["x"] - a["x"]), abs(b["y"] - a["y"]))
                for a, b in zip(rows, rows[1:])
                if all(row[axis] is not None for row in (a, b) for axis in ("x", "y"))
                and a.get("scene") is not None and a["scene"] == b.get("scene")]
    distance = sum(segments) if segments else None
    frontiers = [row["frontier"] for row in rows if row["frontier"] is not None]
    gain = regressions = None
    if len(frontiers) >= 2:
        gain = max(0, frontiers[-1] - frontiers[0])
        regressions = sum(b < a for a, b in zip(frontiers, frontiers[1:]))
    return {
        "actions": len(rows),
        "elapsed_s": round(elapsed, 3),
        "actions_per_min": round(len(rows) * 60 / elapsed, 3) if elapsed else 0.0,
        "screen_change_ratio": (round(sum(changes) / len(changes), 3)
                                 if changes else None),
        "long_pauses": sum(gap >= PAUSE_SECONDS for gap in gaps),
        "reverse_steps": sum(row["reverse"] for row in rows),
        "position_samples": len(positions),
        "distance": distance,
        "frontier_gain": gain,
        "frontier_regressions": regressions,
    }


def summarize(events, *, window_size=25):
    """Summarize parsed recording events without loading frame payloads."""
    actions = []
    observations = []
    previous_direction = None
    for event in events:
        if not isinstance(event, dict):
            continue
        timestamp = _number(event.get("t"))
        if timestamp is None or timestamp < 0:
            continue
        if event.get("trajectory") is True:
            action = event.get("action")
            if type(action) is int and action > 0:
                observations.append({
                    "action": action,
                    "t": timestamp,
                    "action_t": _number(event.get("action_t")),
                    "scene": event.get("scene"),
                    "x": event.get("x") if type(event.get("x")) is int else None,
                    "y": event.get("y") if type(event.get("y")) is int else None,
                    "frontier": _number(event.get("frontier")),
                    "screen_changed": (event.get("screen_changed")
                                       if type(event.get("screen_changed")) is bool else None),
                })
            continue
        name = _action_name(event)
        if name not in ("KEY", "KEYS", "WAIT", "TEXT"):
            continue
        direction = _direction(event)
        reverse = bool(direction and previous_direction
                       and direction[0] == -previous_direction[0]
                       and direction[1] == -previous_direction[1])
        if direction:
            previous_direction = direction
        actions.append({"number": len(actions) + 1, "t": timestamp,
                        "name": name, "reverse": reverse})

    rows = []
    for action in actions:
        row = dict(action)
        observation = {}
        # Prefer the full recording timestamp because the worker-local action
        # counter starts over after a restart. A small tolerance covers the
        # marker's historical three-decimal timestamp rounding.
        timed = [(abs(action["t"] - item["action_t"]), item)
                 for item in observations if item["action_t"] is not None]
        if timed:
            distance, candidate = min(timed, key=lambda pair: pair[0])
            if distance <= 0.02:
                observation = candidate
                observations.remove(candidate)
        if not observation:
            for candidate in list(observations):
                if candidate["action"] == action["number"] and candidate["action_t"] is None:
                    observation = candidate
                    observations.remove(candidate)
                    break
        row.update({"scene": observation.get("scene"), "x": observation.get("x"), "y": observation.get("y"),
                    "frontier": observation.get("frontier"),
                    "screen_changed": observation.get("screen_changed")})
        rows.append(row)
    overall = _window(rows)
    windows = [_window(rows[start:start + window_size])
               for start in range(0, len(rows), window_size)]
    coordinate_samples = sum(row["x"] is not None and row["y"] is not None
                             for row in rows)
    return {
        "version": 1,
        "status": "measured" if coordinate_samples else "position-unmeasured",
        "actions": rows,
        "summary": overall,
        "windows": windows,
        "window_size": window_size,
        "position_samples": coordinate_samples,
        "analysis": {
            "smoothness_comparison": (
                "Compare later windows with earlier windows using pause, reverse, "
                "screen_change_ratio, and frontier/distance fields; missing "
                "coordinates are not treated as zero."
            )
        },
    }


def read_events(path):
    """Read a recording while rejecting oversized or incomplete lines."""
    with Path(path).open("rb") as stream:
        for line in iter(lambda: stream.readline(MAX_LINE + 1), b""):
            if len(line) > MAX_LINE:
                raise ValueError("recording event is too large")
            if not line.endswith(b"\n"):
                raise ValueError("recording has an incomplete trailing event")
            yield json.loads(line)


def analyze(path, *, window_size=25):
    return summarize(read_events(path), window_size=window_size)
