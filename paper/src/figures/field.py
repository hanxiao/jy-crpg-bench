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
Service probes are dropped. The field budget is 60 minutes.
Every preserved save in slots/ is decoded by slots.py, and what it alone
carries is attached to its row: the scenes the hermit's conversation opens,
and the level and experience of the leader. The catalogue's own level and
experience come from a live read of a copy of the character records that the
game does not update during play, so they are not used.
`replay_events.json`, written by replay_scan.py from the published replay
videos, carries the events the game keeps only on screen: the conversation
with the hermit, the compass in the item screen, a fight, its verdict, a
fight won, the experience and level it pays, and the companion's prompt
answered. A rung is credited from whichever record
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
# The budget of the field this paper reports. The broker's default has since
# moved to four hours; the field is selected by this value, not by that default.
DEFAULT_BUDGET = 3600
# The catalogue at the four-hour budget, every attempt including retries and
# interrupted runs; long_submissions.json says which sessions count.
LONG = os.path.join(HERE, "catalog_snapshot_240min.json")
LONG_BUDGET = 14400
# Four-hour sessions the paper leaves out: a declared name that names no model
# of the paper, and a session at another thinking level.
LONG_EXCLUDED = ("claude-opus-4-5-high", "gpt-6-astramax")
HACK_SESSION = "3eb8f81b3592"    # the four-hour session whose harness transcript shows it reading earlier timelines


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
            if sl["saved"]:
                r["save_level"], r["save_exp"] = sl["level"], sl["exp"]
        r["replay"] = EVENTS.get(r["id"])
        out.append(r)
    return out


# Models left out of the paper's field: a version with two later versions of
# its line in the field. Their sessions stay in the public catalogue.
EXCLUDED = ("gemini-3.6-flash",)


def load_runs(path=SNAPSHOT, dedup=True, keep_excluded=False):
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
    if not keep_excluded:
        rows = [r for r in rows if r["agent"] not in EXCLUDED]
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


HUMAN = os.path.join(HERE, "human_sessions.json")
HUMAN_KEYS = ("map", "item", "scene", "hermit", "compass", "companion", "fight", "fought", "exp", "level2", "book")
HUMAN_CLASSES = (("speedrun", "human speedrun"), ("playthrough", "human playthrough"))


def human_videos():
    """The published videos of human players the paper reads, as recorded in
    human_sessions.json: for each, the class, the minute of every milestone
    from the start of play (None when the video ends before it) and the
    video-estimated tile steps plus screen changes to the world map."""
    return json.load(open(HUMAN, encoding="utf-8")) if os.path.exists(HUMAN) else []


def human_rows():
    """One reference row per class of human video: milestone shares and
    video-estimated steps to the world map. Human videos have no input log,
    so their step counts must not occupy the model-only cross_keys field."""
    out = []
    for cls, label in HUMAN_CLASSES:
        vs = [v for v in human_videos() if v["class"] == cls]
        if not vs:
            continue
        cols = [(sum(1 for v in vs if v["milestones_min"].get(k) is not None), len(vs), len(vs)) for k in HUMAN_KEYS]
        crossings = sorted(v["steps_to_map"] for v in vs if v.get("steps_to_map") is not None)
        out.append({"agent": label, "sessions": len(vs), "ids": [v["id"] for v in vs],
                    "rungs": [c[0] > 0 for c in cols], "reached": sum(1 for c in cols if c[0] > 0),
                    "counts": cols, "cross_steps": crossings, "human": True})
    return out


def long_attempts():
    """All model attempts at the four-hour budget, including empty starts."""
    return [r for r in _rows(LONG) if r["budget"] == LONG_BUDGET and not is_random(r["agent"])]


def load_long():
    """The four-hour sessions that count, one per model, per the manifest."""
    import long_cohort
    return long_cohort.select(long_attempts())


def random_rows(rows, budget=DEFAULT_BUDGET):
    """The random floor: at the default budget when it was run there, else
    every random run there is. The ratio is per action, so the budget only
    matters for the budget section, which says which it used."""
    at = [r for r in played(rows, budget) if is_random(r["agent"])]
    return at or [r for r in rows if is_random(r["agent"]) and (r["actions"] or 0) > 0]


def aliased(rows):
    """(declared, listed) pairs for the rows whose name was corrected."""
    return sorted({(r["declared"], r["agent"]) for r in rows if r["declared"] != r["agent"]})


DEFINITION = ("reached\nworld map", "picked up\nan item", "entered\na location", "spoke with\nthe hermit",
              "held the\ncompass", "recruited a\nparty\nmember",
              "entered\na battle", "ended\na battle",
              "gained\nexperience", "reached\nlevel 2", "one of the\nfourteen")
SHORT = ("map", "item", "location", "hermit", "compass", "party", "battle", "ended", "exp", "lv 2", "book")
OPENING = 6     # the first six close the opening without a fight
HOME = "王居"   # the banner of the home scene, which does not count as a scene entered
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
    experience and every book sits behind a fight. Experience and level are
    read from the save and from the messages a won fight draws on the replay,
    never from the catalogue's live read (see the module docstring)."""
    slot = row.get("slot_saved")
    saved = "saved_at" in row or "world_map_at" in row or slot is not None
    ev = row.get("replay")

    def seen(name):
        return bool(ev and ev.get(name) and ev[name]["seconds"] > 0)

    recruited = bool(ev and ev.get("recruited_minute") is not None)
    gained = (row.get("save_exp") or 0) > 0 or seen("exp")
    no_fight = ev is not None and not seen("battle")
    scenes = (ev or {}).get("scenes")
    known = [
        True if saved else row.get("bigmap") is not None,
        bool(ev and ev.get("obtained")),
        scenes is not None,
        ev is not None,
        ev is not None or saved or row.get("compass") is not None,
        ev is not None or saved or row.get("team_size") is not None,
        ev is not None,
        ev is not None or "save_exp" in row,
        ev is not None or "save_exp" in row,
        ev is not None or "save_level" in row,
        (True if saved else row.get("books") is not None) or no_fight,
    ]
    got = [
        (row.get("saved_at") is not None
         or row.get("world_map_at") is not None
         or slot is True) if saved
        else bool(row.get("bigmap")) and row.get("exit_secs") is not None,
        seen("obtained"),
        bool(scenes and any(x["name"] != HOME for x in scenes["entries"])),
        seen("hermit"),
        bool(row.get("compass")) or seen("compass"),
        (row.get("team_size") or 0) > 1 or recruited,
        seen("battle"),
        seen("defeat") or seen("won") or gained,
        gained,
        (row.get("save_level") or 0) > 1 or seen("level"),
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


def crossing_keys(row):
    """Model keypresses before reaching the world map: every key of the
    actions up to the crossing, from the input log. Human video-estimated
    steps have a different unit and are stored separately by human_rows."""
    n = crossing_actions(row)
    if n is None:
        return None
    t = json.load(open(os.path.join(HERE, "timelines", row["id"] + ".json"), encoding="utf-8"))
    return sum(len(m["keys"]) for m in t["marks"][:n])


def crossing_order(m):
    """Sort key for the crossing panel: the mean keypresses to the world map
    over the sessions that crossed, fewest first, then the name."""
    c = m["cross_keys"]
    return (sum(c) / len(c) if c else float("inf"), m["agent"].lower())


def ladder_order(m):
    """Sort key for the model rows of the milestone panel and the effort
    table: the milestones reached, most first, then the summed share of
    sessions that reached them, then the name."""
    share = sum(c[0] / c[2] for c in m["counts"] if c[2])
    return (-m["reached"], -share, m["agent"].lower())


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
        cross_keys = sorted(k for k in (crossing_keys(r) for r in rs) if k is not None)
        out.append({"agent": agent, "sessions": len(rs), "ids": [r["id"] for r in rs],
                    "rungs": rungs, "reached": sum(1 for v in rungs if v is True),
                    "counts": counts, "crossings": crossings, "cross_keys": cross_keys,
                    "map_actions": min(crossings) if crossings else None})
    return out


CONFIRM = ("space", "enter")


def battles(row):
    """The battles of a session, read from the replay: each run of battle-card
    readings less than three minutes apart is one battle, which ends at the
    first defeat or battle-won message after it began, or stays open to the
    last key. Per battle: the minutes it began and ended, the outcome, the
    party (two when a recruitment came before it), and the actions and keys
    the model sent while it lasted."""
    e = row.get("replay")
    if not e or not e["battle"]["seconds"]:
        return []
    tl = json.load(open(os.path.join(HERE, "timelines", row["id"] + ".json"), encoding="utf-8"))
    sp = tl["speed"]
    marks = [(m["t"] * sp / 60, m) for m in tl["marks"]]
    runs = []
    for m in e["battle"]["minutes"]:
        if runs and m - runs[-1][-1] < 3:
            runs[-1].append(m)
        else:
            runs.append([m])
    ends = sorted([(m, "lost") for m in e["defeat"]["minutes"]] + [(m, "won") for m in e["won"]["minutes"]])
    out = []
    for run in runs:
        start = run[0]
        end, outcome = next(((m, o) for m, o in ends if m >= start), (marks[-1][0], "open"))
        inside = [m for t, m in marks if start - 0.3 <= t <= end]
        keys = [k for m in inside for k, _ in m["keys"]]
        rec = e.get("recruited_minute")
        out.append({"start": start, "end": end, "outcome": outcome,
                    "party": 2 if rec is not None and rec < start else 1,
                    "actions": len(inside), "keys": len(keys),
                    "confirm": sum(k in CONFIRM for k in keys) / len(keys) if keys else 0.0})
    return out


def minutes_of_play(row):
    """Minute of every action of a session, from its keypress timeline."""
    t = json.load(open(os.path.join(HERE, "timelines", row["id"] + ".json"), encoding="utf-8"))
    return [m["t"] * t["speed"] / 60 for m in t["marks"]]


def _crossing_minute(row):
    if not on_map(row):
        return None
    if row.get("exit_secs") is not None:
        return row["exit_secs"] / 60
    e = row.get("replay") or {}
    b = e.get("first_black_second")
    if b is None:
        return None
    t = json.load(open(os.path.join(HERE, "timelines", row["id"] + ".json"), encoding="utf-8"))
    return b * t["speed"] / 60


def _first(name):
    return lambda row: ((row.get("replay") or {}).get(name) or {}).get("first_minute")


# The chain of steps every playthrough passes in order, each with the minute a
# session first passed it, or None.
CHAIN = (("leave\nhouse", _crossing_minute),
         ("enter\nlocation", lambda row: ((row.get("replay") or {}).get("scenes") or {}).get("first_minute")),
         ("reach\nhermit", _first("hermit")),
         ("enter\nbattle", _first("battle")),
         ("win\nbattle", _first("won")),
         ("hold\nbook", lambda row: None))


def chain(rows):
    """Per step of CHAIN: the sessions at risk (those that passed the step
    before), and for each the minutes from the step before to passing this one
    (passed) or to its last key (stuck)."""
    out, prev = [], [(r, 0.0) for r in rows]
    for name, when in CHAIN:
        passed, stuck = [], []
        for r, t0 in prev:
            t = when(r)
            if t is not None:
                passed.append((r, t, t - t0))
            else:
                ms = minutes_of_play(r)
                stuck.append((r, (ms[-1] if ms else t0) - t0))
        out.append({"step": name, "at_risk": len(prev), "passed": [(r, d) for r, _, d in passed], "stuck": stuck})
        prev = [(r, t) for r, t, _ in passed]
    return out


def passes_after(step, minutes):
    """Passes, and hours at risk, once a session had spent `minutes` before the
    step without passing it."""
    n = sum(1 for _, d in step["passed"] if d >= minutes)
    h = (sum(max(0.0, d - minutes) for _, d in step["passed"]) + sum(max(0.0, d - minutes) for _, d in step["stuck"])) / 60
    return n, h
