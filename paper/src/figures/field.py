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
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "catalog_snapshot.json")
RECOVERED = os.path.join(HERE, "recovered_sessions.json")
BACKUP = os.path.join(HERE, "catalog_backup_20260911T174413Z.json")
EARLIER = os.path.join(HERE, "catalog_snapshot_20min.json")
ALIASES = json.load(open(os.path.join(HERE, "aliases.json"), encoding="utf-8"))
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


DEFINITION = ("acted", "picked\nsomething up", "reached\nworld map",
              "holds the\ncompass", "recruited\na companion",
              "gained\nexperience", "reached\nlevel 2", "holds one\nof fourteen")
SHORT = ("acted", "item", "map", "compass", "party", "exp", "lv 2", "book")
OPENING = 5     # the first five close the opening without a fight


def rungs_of(row):
    """(reached | not reached | None for no reading) per rung, as the game
    records them. The world-map rung is the game's own account of the party on
    the overworld: a save the game wrote there, or the live reading of its
    world square changing, whichever the run carries. A run recorded before the
    benchmark read either field is credited only from the screen with a
    corroborating fade, a legacy path the paper does not report."""
    slot = row.get("slot_saved")
    saved = "saved_at" in row or "world_map_at" in row or slot is not None
    # For an instrumented run the compass, party and book rungs are read from
    # the save the game writes, and the game offers that save only from the
    # world map, which every one of these rungs sits beyond. So a run that
    # wrote no save did not reach them: their absence is measured, not unknown.
    # Only a run from before the benchmark read these at all is unmeasured.
    known = [
        True,
        row.get("picked_item") is not None,
        True if saved else row.get("bigmap") is not None,
        True if saved else row.get("compass") is not None,
        True if saved else row.get("team_size") is not None,
        row.get("exp") is not None,
        row.get("level") is not None,
        True if saved else row.get("books") is not None,
    ]
    got = [
        (row.get("key_events") if row.get("key_events") is not None
         else row["actions"]) > 0,
        bool(row.get("picked_item")),
        (row.get("saved_at") is not None
         or row.get("world_map_at") is not None
         or slot is True) if saved
        else bool(row.get("bigmap")) and row.get("exit_secs") is not None,
        bool(row.get("compass")),
        (row.get("team_size") or 0) > 1,
        (row.get("exp") or 0) > 0,
        (row.get("level") or 0) > 1,
        (row.get("books") or 0) > 0,
    ]
    return [(g if k else None) for g, k in zip(got, known)]


def rungs_reached(row):
    return sum(1 for v in rungs_of(row) if v is True)
