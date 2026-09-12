"""Session records for the runs the live catalogue no longer lists.

The catalogue was cleared before the final sweep, and the sessions played on
the evening of 2026-09-11 left no row behind. Each of them did leave the save
the game wrote (slots/<id>.grp, .idx, preserved by the service) and its
keypress timeline (timelines/<id>.json). This script reads both with the same
decoder the service uses and writes recovered_sessions.json, one row per
session in the shape of a catalogue row, so field.py can list every session a
model played. Fields no artefact carries are null.

    python3 figures/recover_sessions.py > figures/recovered_sessions.json
"""
import json
import os
import statistics as st
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "server"))
import save_state  # noqa: E402

BUDGET = 3600            # the service default when these sessions ran
IDLE_GAP = 9.5 * 60      # the inactivity rule then in force ended a session after ten minutes


def decode(path):
    grp = open(path + ".grp", "rb").read()
    idx = open(path + ".idx", "rb").read()
    return save_state.from_archive(grp, idx)


def signature(s):
    p = s["position"]
    return (s["team"][0]["name"] if s["team"] else None, p["x"], p["y"], p["sub_x"], p["sub_y"])


SEED = decode(os.path.join(HERE, "slots", "seed"))
SEED_SIG = signature(SEED)
SEED_BAG = (sum(SEED["bag"].values()), len(SEED["bag"]))

rows = []
for entry in json.load(open(os.path.join(HERE, "recovered_index.json"), encoding="utf-8")):
    rid = entry["id"]
    t = json.load(open(os.path.join(HERE, "timelines", rid + ".json"), encoding="utf-8"))
    if t["id"] != rid:
        sys.exit(f"timeline {rid} carries another id")
    marks = t["marks"]
    speed = t["speed"]
    played = round(t["seconds"] * speed)
    gap_end = t["seconds"] * speed - (marks[-1]["t"] * speed if marks else 0)
    if played >= BUDGET - 90:
        reason = "time"
    elif gap_end >= IDLE_GAP:
        reason = "idle"
    else:
        reason = "stopped"
    ended = datetime.fromisoformat(entry["uploaded"].replace("Z", "+00:00")).timestamp()
    s = decode(os.path.join(HERE, "slots", rid))
    saved = signature(s) != SEED_SIG
    bag = s["bag"]
    lead = s["team"][0] if s["team"] else {}
    keys = {}
    for m in marks:
        for k, _ in m["keys"]:
            keys[k] = keys.get(k, 0) + 1
    gaps = [(b["t"] - a["t"]) * speed for a, b in zip(marks, marks[1:])]
    curve = t.get("curve") or []
    row = {
        "id": rid, "agent": t["agent"], "started": ended - played, "played": played,
        "budget": BUDGET, "actions": len(marks), "reason": reason,
        "key_events": sum(keys.values()), "keys": keys, "distinct_keys": len(keys),
        "gap_p50": round(st.median(gaps), 2) if gaps else None,
        "meaningful": (curve[-1][1] / curve[-1][0]) if curve and curve[-1][0] else None,
        "reads": None, "ttfa": None, "help_langs": {}, "usage": None, "scenes": None,
        # the save the game wrote, decoded like every other archive
        "slot_saved": saved,
        "saved_at": None, "first_saved_at": None, "world_map_at": None,
        "bigmap": None, "exit_secs": None, "exit_acts": None,
        "compass": bool(bag.get(save_state.COMPASS_ID)) if saved else None,
        "team_size": s["team_size"] if saved else None,
        "books": s["books"] if saved else None,
        "picked_item": ((sum(bag.values()), len(bag)) != SEED_BAG) if saved else None,
        "level": lead.get("level") if saved else None,
        "skills": lead.get("skills") if saved else None,
        "exp": lead.get("exp") if saved else None,
        "hp": lead.get("hp") if saved else None,
        "position": {"x": s["position"]["x"], "y": s["position"]["y"]} if saved else None,
        "video_url": "https://storage.googleapis.com/jy-crpg-bench-runs/" + entry["video"],
        "timeline_url": f"runs/{rid}.json",
        "source": "save slot and timeline; the catalogue row was cleared before the final sweep",
    }
    rows.append(row)

rows.sort(key=lambda r: r["started"])
json.dump(rows, sys.stdout, indent=1, ensure_ascii=False)
print()
