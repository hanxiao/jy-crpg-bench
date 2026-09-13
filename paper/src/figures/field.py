"""The field the paper is generated from, loaded one way by every generator.

`catalog_snapshot.json` is the published catalogue of the final sweep as
fetched. Two further records complete it: `recovered_sessions.json`, one row
per session that the live catalogue no longer lists, read from the save the
game wrote and the keypress timeline by recover_sessions.py, and
`catalog_backup_20260911T174413Z.json`, the catalogue as it stood before it
was cleared for the final sweep. `aliases.json` maps variant spellings a run
was created under to the model, and every generator lists them under the
model; the declared name is kept on the row as `declared`. The field is the
set of models in the final sweep; sessions of other models stay out of it.
Service probes are dropped. The default budget is read from bench/broker.py.
Every preserved save in slots/ is decoded by slots.py, and the rung it alone
carries, the scenes the hermit's conversation opens, is attached to its row.
`replay_events.json`, written by replay_scan.py from the published replay
videos, carries the events the game keeps only on screen: the conversation
with the hermit, the compass in the item screen, a fight, its verdict, and
the companion's prompt answered. A rung is credited from whichever record
carries it, and a model is credited with every rung any of its sessions
reached.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slots as _slots

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "catalog_snapshot.json")
RECOVERED = os.path.join(HERE, "recovered_sessions.json")
BACKUP = os.path.join(HERE, "catalog_backup_20260911T174413Z.json")
EARLIER = os.path.join(HERE, "catalog_snapshot_20min.json")
ALIASES = json.load(open(os.path.join(HERE, "aliases.json"), encoding="utf-8"))
SLOTS = _slots.load()
EVENTS = json.load(open(os.path.join(HERE, "replay_events.json"), encoding="utf-8"))
_broker = open(os.path.join(HERE, "..", "..", "..", "bench", "broker.py"), encoding="utf-8").read()
DEFAULT_BUDGET = int(re.search(r'"QUNXIA_RUN_SECONDS", "(\d+)"', _broker).group(1))


def _rows(path):
    out = []
    for r in json.load(open(path, encoding="utf-8")):
        if r["agent"].startswith("probe-"):
            continue
        r = dict(r)
        r["declared"] = r["agent"]
        r["agent"] = ALIASES.get(r["agent"], r["agent"])
        sl = SLOTS.get(r["id"])
        if sl is not None:
            # save-gated: a session that wrote no save left the world closed
            r["world_opened"] = sl["world_opened"] if sl["saved"] else False
        r["replay"] = EVENTS.get(r["id"])
        out.append(r)
    return out


def load_runs(path=SNAPSHOT, dedup=True):
    rows = _rows(path)
    if path == SNAPSHOT:
        field = {r["agent"] for r in rows}
        seen = {r["id"] for r in rows}
        extra = _rows(RECOVERED) if os.path.exists(RECOVERED) else []
        for r in _rows(BACKUP) if os.path.exists(BACKUP) else []:
            # The backup rows were recorded before the benchmark preserved the
            # save, so their save-gated readings came from live memory reads
            # that later proved unreliable; they are kept as no reading.
            for k in ("saved_at", "first_saved_at", "world_map_at"):
                r.pop(k, None)
            r["compass"] = None
            r["books"] = None
            r["team_size"] = None
            r["source"] = "catalogue backup of 2026-09-11 17:44 UTC, before the clear"
            extra.append(r)
        for r in extra:
            if r["id"] in seen or (r["agent"] not in field and not is_random(r["agent"])):
                continue
            seen.add(r["id"])
            rows.append(r)
    return best_per_model(rows) if dedup else rows


def best_per_model(rows):
    """One session per model: the one that reached the most rungs. A model run
    more than once is reported by its best session, and on a tie by the most
    recent; ties beyond that break towards more actions, then the run id, so
    the choice is deterministic."""
    best = {}
    for r in rows:
        key = r["agent"]
        cur = best.get(key)
        rank = (rungs_reached(r), (r.get("started") or 0), (r.get("actions") or 0), r.get("id") or "")
        if cur is None or rank > cur[0]:
            best[key] = (rank, r)
    return [v[1] for v in best.values()]


def played(rows, budget=DEFAULT_BUDGET):
    return [r for r in rows if r["budget"] == budget and (r["actions"] or 0) > 0]


def is_random(agent):
    return agent.lower().startswith("random")


def random_rows(rows, budget=DEFAULT_BUDGET):
    """The random floor: at the default budget when it was run there, else
    every random run there is. The ratio is per action, so the budget only
    matters for the budget section, which says which it used."""
    at = [r for r in played(rows, budget) if is_random(r["agent"])]
    return at or [r for r in rows if is_random(r["agent"]) and (r["actions"] or 0) > 0]


def aliased(rows):
    """(declared, listed) pairs for the rows whose name was corrected."""
    return sorted({(r["declared"], r["agent"]) for r in rows if r["declared"] != r["agent"]})


DEFINITION = ("reached\nworld map", "picked up\nan item", "spoke with\nthe hermit",
              "holds the\ncompass", "recruited\ncompanion",
              "entered\na fight", "fought to\nthe end",
              "gained\nexperience", "reached\nlevel 2", "one of the\nfourteen")
SHORT = ("map", "item", "hermit", "compass", "party", "fight", "fought out", "exp", "lv 2", "book")
OPENING = 5     # the first five close the opening without a fight
MAP = DEFINITION.index("reached\nworld map")


def on_map(row):
    """Whether the run is credited with the world map."""
    return rungs_of(row)[MAP] is True


def rungs_of(row):
    """(reached | not reached | None for no reading) per rung, from whichever
    record carries the event. The bag and character records are read from
    emulator memory, the party and the world position from the save the game
    writes, and the events the game keeps only on screen from the published
    replay (see replay_scan.py). A rung with no record behind it is None; a
    run that wrote no save did not reach the save-gated rungs, since the game
    offers its save only from the world map, which every one of them sits
    beyond. Two readings follow the game's own rules: a session whose bag no
    record carries takes the item rung from the message the game draws when
    an item enters the bag, and a session whose replay shows no fight gained
    no experience, reached no level and holds no book, since victories pay
    experience and every book sits behind a fight."""
    slot = row.get("slot_saved")
    saved = "saved_at" in row or "world_map_at" in row or slot is not None
    ev = row.get("replay")

    def seen(name):
        return bool(ev and ev.get(name) and ev[name]["seconds"] > 0)

    recruited = bool(ev and ev.get("recruited_minute") is not None)
    no_fight = ev is not None and not seen("battle")
    known = [
        True if saved else row.get("bigmap") is not None,
        row.get("picked_item") is not None or bool(ev and ev.get("obtained")),
        ev is not None,
        ev is not None or saved or row.get("compass") is not None,
        ev is not None or saved or row.get("team_size") is not None,
        ev is not None,
        ev is not None or row.get("exp") is not None,
        row.get("exp") is not None or no_fight,
        row.get("level") is not None or no_fight,
        (True if saved else row.get("books") is not None) or no_fight,
    ]
    got = [
        (row.get("saved_at") is not None
         or row.get("world_map_at") is not None
         or slot is True) if saved
        else bool(row.get("bigmap")) and row.get("exit_secs") is not None,
        bool(row.get("picked_item")) or seen("obtained"),
        seen("hermit"),
        bool(row.get("compass")) or seen("compass"),
        (row.get("team_size") or 0) > 1 or recruited,
        seen("battle"),
        seen("defeat") or (row.get("exp") or 0) > 0,
        (row.get("exp") or 0) > 0,
        (row.get("level") or 0) > 1,
        (row.get("books") or 0) > 0,
    ]
    return [(g if k else None) for g, k in zip(got, known)]


def rungs_reached(row):
    return sum(1 for v in rungs_of(row) if v is True)


def crossing_actions(row):
    """Actions the session took to reach the world map: the count the service
    recorded from the first black frame, else the same count read from the
    replay, for a session credited with the world map; None otherwise."""
    if row.get("exit_acts") is not None:
        return row["exit_acts"]
    ev = row.get("replay") or {}
    if on_map(row) and ev.get("crossing_actions") is not None:
        return ev["crossing_actions"]
    return None


def model_rows(rows):
    """One row per model: the milestones any of its sessions reached, with the
    number of sessions behind it, per milestone the count of sessions that
    reached it, that carry a reading and that were played, and the actions
    each crossing took to reach the world map. A milestone nobody has a
    reading for is None."""
    by = {}
    for r in rows:
        by.setdefault(r["agent"], []).append(r)
    out = []
    for agent, rs in by.items():
        cols = list(zip(*[rungs_of(r) for r in rs]))
        rungs = [True if any(c is True for c in col)
                 else (False if any(c is not None for c in col) else None) for col in cols]
        counts = [(sum(1 for c in col if c is True), sum(1 for c in col if c is not None), len(col))
                  for col in cols]
        crossings = sorted(a for a in (crossing_actions(r) for r in rs) if a is not None)
        out.append({"agent": agent, "sessions": len(rs), "ids": [r["id"] for r in rs],
                    "rungs": rungs, "reached": sum(1 for v in rungs if v is True),
                    "counts": counts, "crossings": crossings,
                    "map_actions": min(crossings) if crossings else None})
    return out
