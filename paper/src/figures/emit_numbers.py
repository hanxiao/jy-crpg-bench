"""Every number the paper cites, emitted as LaTeX macros.

    python3 figures/numbers.py > figures/numbers.tex

`main.tex` inputs the generated file, so no measurement is transcribed by hand.
Sources: `catalog_snapshot.json` (the published catalogue) and `start.state`,
the savestate every session boots into, committed here alongside the snapshot
(the broker reuses a present start state, so this is exactly the state the
catalogue's runs booted from). The script checks internal consistency and
stops on a disagreement, and it never emits a number it did not compute.
"""

import json
import math
import os
import re
import statistics as st
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "catalog_snapshot.json")
START_STATE = os.path.join(HERE, "start.state")

CHAR_SZ = 182
NAME, LEVEL, EXP, HP, MAXHP, MP, MAXMP = 8, 30, 32, 34, 36, 82, 84
ANCHOR = "程靈素".encode("big5")
CHECK = (("胡斐", 1), ("苗人鳳", 3))
RECORDS = 320

VENDORS = ("claude", "gpt", "gemini", "qwen", "glm", "grok", "deepseek")
DIAG = ("kp7", "kp9", "kp1", "kp3")
ARROWS = ("up", "down", "left", "right")

lines = []
checked = []


def fam(agent):
    low = agent.lower()
    for pre in ("codex-cli--", "vista-codex-", "vista-", "codex-"):
        low = low.replace(pre, "")
    low = low.replace("--pi", "").replace("-codex", "")
    if low.startswith("random"):
        return "random"
    return next((v for v in VENDORS if low.startswith(v)), "other")


def emit(name, value, note="", fmt=None):
    """Define \\name. Floats keep three decimals below 10, one above,
    unless `fmt` says otherwise."""
    if fmt is not None:
        text = fmt % value
    elif isinstance(value, float):
        text = f"{value:.3f}" if abs(value) < 10 else f"{value:.1f}"
    else:
        text = str(value)
    if not re.fullmatch(r"[0-9A-Za-z.\-+%/ ]*", text):
        sys.exit(f"emit {name}: unsupported characters in {text!r}")
    lines.append((f"% {note}".rstrip() if note else "", f"\\newcommand{{\\{name}}}{{{text}}}"))


def ratio(k, n):
    if n <= 0:
        sys.exit("ratio over an empty denominator")
    if abs(k / n - round(k / n * 1000) / 1000) > 0.006:
        sys.exit(f"ratio {k}/{n} disagrees with the published figure")
    return k / n


def wil(k, n, z=1.96):
    p = ratio(k, n)
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, ctr - half), p, min(1.0, ctr + half)


# ------------------------------------------------------------------ field sets
import field
raw = json.load(open(SNAPSHOT, encoding="utf-8"))
probes = [r for r in raw if r["agent"].startswith("probe-")]
rows = field.load_runs(dedup=False)
BUDGET = field.DEFAULT_BUDGET
ALL = field.played(rows)
never = [r for r in rows if (r["actions"] or 0) == 0]
other_budget = [r for r in rows if r["budget"] != BUDGET]
MODELS = [r for r in ALL if fam(r["agent"]) != "random"]
RANDOM = field.random_rows(rows)
if not MODELS or not RANDOM:
    sys.exit("no scored sessions or no random floor in the snapshot")
# every session a model of the field played at this budget; the random floor
# is reported on its own, so every count below runs over the models
PLAY = MODELS
UNION = field.model_rows(MODELS)
RUNION = field.model_rows(RANDOM)

emit("NsessionsTotal", len(raw), "catalogue entries in the snapshot")
emit("Nsessions", len(MODELS), "model sessions at the default budget that played")
emit("LsessionsMin", min(m["sessions"] for m in UNION), "fewest sessions a model played")
emit("LsessionsMax", max(m["sessions"] for m in UNION), "most sessions a model played")
emit("NsessionsAll", len(ALL), "sessions at the default budget that played, the floor included")
emit("Nmodels", len(MODELS), "model sessions")
emit("NrandomRuns", len(RANDOM), "random-baseline sessions")
emit("Nvendors", len({fam(r["agent"]) for r in MODELS}), "vendors in the field")
emit("Nlabels", len({r["agent"] for r in rows}), "distinct agent labels")
emit("NlabelsPlay", len({r["agent"] for r in PLAY}),
     "distinct agent labels among the scored sessions")
emit("NmodelLabels", len({r["agent"] for r in PLAY if fam(r["agent"]) != "random"}),
     "distinct model labels among the scored sessions")


def base(agent):
    """The model name once the client prefixes an operator declared are gone,
    so runs of one model through two clients count as one model."""
    low = agent.lower()
    for pre in ("codex-cli--", "vista-codex-", "vista-", "codex-"):
        low = low.replace(pre, "")
    return low.replace("--pi", "").replace("-codex", "")


emit("NmodelsDistinct", len({base(r["agent"]) for r in MODELS}),
     "distinct model names among the scored sessions")
emit("Nnever", len(never), "sessions that never sent a key")
emit("NotherBudget", len(other_budget), "sessions at another playtime")
emit("Nprobes", len(probes), "service probes, excluded")
emit("Nbudget", BUDGET, "default playtime, seconds")
emit("NbudgetMin", BUDGET // 60, "default playtime, minutes")
_records = [r for r in field.load_runs(dedup=False) if r["budget"] == BUDGET]
emit("Naliased", sum(1 for r in _records if r["declared"] != r["agent"]),
     "sessions on record created under a variant spelling of the model name")
_pairs = [f"\\texttt{{{d}}} as \\texttt{{{m}}}" for d, m in field.aliased(_records)]
lines.append(("% the runs created under a name that was not the model, declared as listed",
              "\\newcommand{\\aliaslist}{" + (" and ".join(_pairs) if _pairs else "none") + "}"))
emit("Nidle", sum(1 for r in PLAY if r["reason"] == "idle"), "reported sessions ended by the inactivity rule then in force")
emit("Ntime", sum(1 for r in PLAY if r["reason"] == "time"), "reported sessions that played to their budget")

# A model run more than once is reported by its longest session (field.py);
# the sessions that gives way to it stay in the snapshot and are counted here.
_every = [r for r in field.load_runs(dedup=False) if r["budget"] == BUDGET and fam(r["agent"]) != "random"]
_kept = {r["id"] for r in MODELS}
_dropped = [r for r in _every if r["id"] not in _kept]
emit("NrepeatModels", len({r["agent"] for r in _dropped}), "models with more than one session")
emit("NrepeatSessions", len(_dropped), "sessions that give way to a longer one of the same model")
emit("NrepeatNever", sum(1 for r in _dropped if (r["actions"] or 0) == 0),
     "of those, sessions that never sent a key")
emit("NsessionsRaw", len(_every), "model sessions at the default budget on record")
emit("NsessionsPlayed", sum(1 for r in _every if (r.get("actions") or 0) > 0),
     "model sessions at the default budget that sent a key")
_per = {}
for r in _every:
    if (r.get("actions") or 0) > 0:
        _per[r["agent"]] = _per.get(r["agent"], 0) + 1
emit("NsessionsMaxPerModel", max(_per.values()), "most sessions any one model played")

# ------------------------------------------------------------------- behaviour
acts = [r["actions"] for r in PLAY]
emit("EactsTotal", sum(acts))
emit("EactsModels", sum(r["actions"] for r in MODELS))
emit("EactsRandom", sum(r["actions"] for r in RANDOM))
emit("EactsMedian", st.median(acts))
emit("EactsMin", min(acts))
emit("EactsMax", max(acts))
emit("Eaps", sum(acts) / sum(r["played"] for r in PLAY), "pooled actions per second")
emit("Ereads", sum(r["reads"] for r in MODELS if r.get("reads") is not None), "screen reads by model sessions")
# how often a model looks and how many keys it sends per look, against the
# milestones its session reached: rank correlations over the model sessions


def _rank(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    ranks = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2
        i = j + 1
    return ranks


def _spearman(x, y):
    rx, ry = _rank(x), _rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return num / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


_cad = [r for r in MODELS if r["actions"]]
_look = [r for r in _cad if r.get("reads") is not None]
_rk = _spearman([r["key_events"] / r["actions"] for r in _cad], [field.rungs_reached(r) for r in _cad])
_rr = _spearman([r["reads"] / r["actions"] for r in _look], [field.rungs_reached(r) for r in _look])
_th = [r for r in _cad if r.get("gap_p50") is not None]
_rt = _spearman([r["gap_p50"] for r in _th], [field.rungs_reached(r) for r in _th])
if abs(_rt) >= 0.3:
    sys.exit("the prose says think time does not set the order")
lines.append(("% rank correlation of median think time with milestones", "\\newcommand{\\CrhoThink}{%.2f}" % _rt))
if abs(_rk) >= 0.3 or abs(_rr) >= 0.3:
    sys.exit("the prose says the milestones barely follow keys per action or reads per action")
emit("NcadenceSessions", len(_cad), "model sessions in the cadence correlation")
emit("NlookSessions", len(_look), "of them with a count of screen reads")
emit("ClookMedian", st.median(r["reads"] / r["actions"] for r in _look), "median screen reads per action", fmt="%.2f")
emit("CrhoKeys", _rk, "rank correlation of keys per action with milestones", fmt="%.2f")
emit("CrhoReads", _rr, "rank correlation of reads per action with milestones", fmt="%.2f")

hist = {}
for r in PLAY:
    for k, v in (r.get("keys") or {}).items():
        hist[k] = hist.get(k, 0) + v
tot = sum(hist.values())
diag = sum(v for k, v in hist.items() if k in DIAG)
arr = sum(v for k, v in hist.items() if k in ARROWS)
emit("EkeysTotal", tot, "key events submitted")
emit("EkeysDistinct", len(hist), "distinct keys submitted")
emit("EshareDiag", diag / tot, "share on the four isometric axes")
emit("EshareArrow", arr / tot, "share on the arrow keys")
emit("EkeysEnter", hist.get("enter", 0))
emit("EkeysSpace", hist.get("space", 0))

# the screen-change ratio is known only for sessions read to their end
RATED = [r for r in PLAY if r.get("meaningful") is not None]
best = max(RATED, key=lambda r: r["meaningful"])
# Behavioural styles are read from sessions that played: a run the idle rule
# ended after a handful of keys has no ratio worth naming.
ACTIVE = [r for r in MODELS if r["actions"] >= 30 and r.get("meaningful") is not None]
emit("Nactive", len(ACTIVE), "model sessions with at least thirty actions")
worst = min(ACTIVE, key=lambda r: r["meaningful"])
lo_b, p_b, hi_b = wil(round(best["meaningful"] * best["actions"]), best["actions"])
lo_w, p_w, hi_w = wil(round(worst["meaningful"] * worst["actions"]), worst["actions"])
emit("Qbest", p_b)
emit("QbestLow", lo_b)
emit("QbestHigh", hi_b)
emit("QbestN", best["actions"])
emit("QbestLabel", best["agent"])
emit("Qworst", p_w)
emit("QworstLow", lo_w)
emit("QworstHigh", hi_w)
emit("QworstN", worst["actions"])
emit("QworstLabel", worst["agent"])
if worst.get("ttfa") is not None and worst.get("reads") is not None:
    emit("QworstStart", worst["ttfa"] / 60.0, "minutes before its first key", fmt="%.1f")
    emit("QworstReads", 100.0 * worst["reads"] / worst["actions"],
         "screen reads per hundred actions of the lowest-ratio run", fmt="%.0f")

rk = sum(round(r["meaningful"] * r["actions"]) for r in RANDOM)
rn = sum(r["actions"] for r in RANDOM)
lo_r, p_r, hi_r = wil(rk, rn)
emit("Qrandom", p_r)
emit("QrandomLow", lo_r)
emit("QrandomHigh", hi_r)
emit("QrandomN", rn)
emit("QrandomKeys", RANDOM[0]["distinct_keys"])
emit("QrandomBudgetMin", RANDOM[0]["budget"] // 60, "budget the random floor ran at, minutes")
emit("QrandomAtDefault", int(RANDOM[0]["budget"] == BUDGET), "1 when the floor ran at the default budget")
sub = [r for r in ACTIVE if r["meaningful"] < p_r]
emit("NbelowFloor", len(sub), "active model sessions under the random floor")
_low = min((r["meaningful"] for r in sub), default=worst["meaningful"])
emit("QunderVsRandom", _low / p_r)
emit("QunderTimes", p_r / _low if _low else 0.0,
     "how many times below the random floor the lowest run sits", fmt="%.1f")
emit("QworstOverRandom", worst["meaningful"] / p_r,
     "the lowest active ratio as a multiple of the random floor", fmt="%.1f")
emit("QrandomGap", st.median(r["gap_p50"] for r in RANDOM),
     "median inter-action gap of the random baseline, seconds", fmt="%.1f")
# the random policy as bench/random_baseline.py draws it, and the check that every
# random session on record replays the seeded sequence key for key
_BENCH = os.path.join(HERE, "..", "..", "..", "bench")
sys.path.insert(0, _BENCH)
import random_baseline as _rb  # noqa: E402
import check_random_run as _crr  # noqa: E402
_rsrc = open(os.path.join(_BENCH, "random_baseline.py"), encoding="utf-8").read()
_rseed = int(re.search(r'"--seed", type=int, default=(\d+)', _rsrc).group(1))
_rpace = float(re.search(r'"--pace", type=float, default=([0-9.]+)', _rsrc).group(1))
emit("QrandomSeed", _rseed, "the seed of the random baseline")
emit("QrandomPace", _rpace, "its mean seconds between actions", fmt="%.1f")
emit("QrandomMoveShare", 100.0 * sum(1 for k in _rb.ACTIONS if k in DIAG) / len(_rb.ACTIONS),
     "share of its draws that are a diagonal movement key, percent", fmt="%.0f")
emit("QrandomEnterShare", 100.0 * _rb.ACTIONS.count("enter") / len(_rb.ACTIONS),
     "share of its draws that are the confirm key, percent", fmt="%.0f")
if len(set(_rb.ACTIONS)) != RANDOM[0]["distinct_keys"]:
    sys.exit("the random policy draws from %d keys, the catalogue counted %d" % (len(set(_rb.ACTIONS)), RANDOM[0]["distinct_keys"]))
for _r in RANDOM:
    _tl = json.load(open(os.path.join(HERE, "timelines", _r["id"] + ".json"), encoding="utf-8"))
    _sent = [k for m in _tl["marks"] for k, _ in m.get("keys", [])]
    if _sent != _crr.intended(_rseed, len(_sent), _rpace):
        sys.exit("random session %s does not replay the seeded sequence" % _r["id"])
if len({tuple(field.rungs_of(r)) for r in RANDOM}) != 1:
    sys.exit("the prose says the random sessions agree on every milestone")

# The two model sessions that deliberate longest between actions, so the
# prose can name them and their pace without typing either.
_slow = sorted((r for r in ACTIVE if r.get("gap_p50") is not None),
               key=lambda r: -r["gap_p50"])[:2]
emit("QslowA", _slow[0]["agent"])
emit("QslowB", _slow[1]["agent"])
emit("QslowGap", min(r["gap_p50"] for r in _slow),
     "the shorter of their median think times, seconds", fmt="%.0f")
emit("QslowActs", max(r["actions"] for r in _slow),
     "the larger of their action counts")

# ---------------------------------------------------------------- machine state
# the leader's level and experience, from the save the game wrote
read = [r for r in PLAY if "save_level" in r]
emit("Sread", len(read), "sessions whose save carries the leader's character sheet")
_EXP = field.DEFINITION.index("gained\nexperience")
_LV2 = field.DEFINITION.index("reached\nlevel 2")
_gainers = [r for r in PLAY if field.rungs_of(r)[_EXP] is True]
# the live copy of the character records keeps the values the session started with
if any(r.get("save_exp", 0) > 0 and (r.get("exp"), r.get("level")) != (0, 1) for r in PLAY) or not any(r.get("save_exp", 0) > 0 for r in PLAY):
    sys.exit("the prose says the live character record kept its start values where the save shows experience")
emit("SexpAny", len(_gainers), "hour sessions in which the party gained experience")
emit("SlevelTwo", sum(1 for r in PLAY if field.rungs_of(r)[_LV2] is True), "hour sessions that reached level 2")

_on_map = field.on_map
crossed = [r for r in PLAY if _on_map(r)]
_live = [r for r in PLAY if r.get("level") is not None]   # sessions with a live record
cross = [r for r in _live if r.get("bigmap") is True]
fade = [r for r in PLAY if r.get("exit_secs") is not None]
both = [r for r in _live if r.get("bigmap") is True and r.get("exit_secs") is not None]
emit("Smap", len(crossed), "sessions credited with the world map by the save the game wrote")
emit("SmapScreen", len(cross), "sessions whose screen latched the world-map signature")
# sessions that carry both a save reading and a screen fingerprint, where the
# two can be compared
_both = [r for r in PLAY if ("saved_at" in r or r.get("slot_saved") is not None) and r.get("bigmap") is not None]
emit("SmapBoth", sum(1 for r in _both if _on_map(r)), "crossings carrying both a save and a fingerprint reading")
emit("SmapAgree", sum(1 for r in _both if _on_map(r) and r.get("bigmap") is True), "of those, crossings the fingerprint also shows")
emit("SmapSaveOnly", sum(1 for r in _both if _on_map(r) and r.get("bigmap") is False),
     "crossings the save credits that the screen fingerprint missed")
emit("SmapScreenOnlyBoth", sum(1 for r in _both if not _on_map(r) and r.get("bigmap") is True),
     "fingerprints with no save behind them, among sessions carrying both")
emit("SmapScreenOnly", sum(1 for r in cross if not _on_map(r)),
     "screen latches with no save behind them")
emit("Sstayed", len(PLAY) - len(crossed),
     "scored sessions that never reached the world map")

# The crossing timed by the game: the first save it writes on the world map,
# measured from the start of the session. Attempts recur every two minutes, so
# this clock trails the crossing by at most that.
_saved = [r for r in crossed if r.get("first_saved_at") is not None and r.get("started") is not None]
_save_min = [(r["first_saved_at"] - r["started"]) / 60.0 for r in _saved]
if _save_min:
    emit("SsaveN", len(_saved), "crossings carrying the time of the first save")
    emit("SsaveMedian", st.median(_save_min), "minutes into the session, median", fmt="%.0f")
    emit("SsaveFirst", min(_save_min), fmt="%.0f")
    emit("SsaveLast", max(_save_min), fmt="%.0f")

# The steady-traversal example the behaviour section names: among the model
# sessions that acted at least as often as the median, the one whose actions
# changed the screen most often. Read from the catalogue, never typed.
_median_acts = st.median(r["actions"] for r in ACTIVE)
_steady = max((r for r in ACTIVE if r["actions"] >= _median_acts),
              key=lambda r: r["meaningful"], default=None)
if _steady:
    emit("Qsteady", round(_steady["meaningful"], 3), "ratio of the steady-traversal run")
    emit("QsteadyOsc", round(_steady.get("oscillation") or 0.0, 3), "its oscillation rate")
    emit("QsteadyN", _steady["actions"], "its action count")
    emit("QsteadyLabel", _steady["agent"], "its label")
emit("SmapFade", len(both), "of those, corroborated by a black frame")
emit("SmapSolo", len(cross) - len(both))
emit("SmapUnread", sum(1 for r in PLAY if r.get("bigmap") is None))
emit("SexitMedian", st.median(r["exit_secs"] for r in fade) / 60.0, "minutes", fmt="%.1f")
emit("SexitFirst", min(r["exit_secs"] for r in fade) / 60.0, fmt="%.1f")
emit("SexitLast", max(r["exit_secs"] for r in fade) / 60.0, fmt="%.1f")
_ck = [k for k in (field.crossing_keys(r) for r in MODELS) if k is not None]
emit("SexitActs", st.median(_ck), "median keypresses before a crossing", fmt="%.0f")
emit("SexitVendors", len({fam(r["agent"]) for r in fade}),
     "vendor families with a corroborated crossing")

# The game's own rungs, now that the field carries them.
def _known(key):
    return [r for r in PLAY if r.get(key) is not None]
emit("Sitem", sum(1 for r in _known("picked_item") if r["picked_item"]), "sessions that picked something up")
emit("SnoItem", sum(1 for r in _known("picked_item") if not r["picked_item"]), "sessions that never picked anything up")
emit("SitemKnown", len(_known("picked_item")))
emit("Scompass", sum(1 for r in _known("compass") if r["compass"]), "sessions holding the compass")
emit("Sopened", sum(1 for r in _known("world_opened") if r["world_opened"]),
     "sessions whose save shows the scenes the hermit opens")
emit("SopenedKnown", len(_known("world_opened")))
_COMPASS = field.DEFINITION.index("held the\ncompass")
_holders = sorted((r for r in PLAY if field.rungs_of(r)[_COMPASS] is True), key=lambda r: r["agent"])
lines.append(("% the models holding the compass, by label",
              "\\newcommand{\\ScompassLabel}{" + (" and ".join(
                  "\\texttt{%s}" % a for a in sorted({r["agent"] for r in _holders})) if _holders else "none") + "}"))
_timed = [r for r in _holders if r.get("first_saved_at") is not None and r.get("exit_acts") is not None]
if _timed:
    emit("ScompassSaveMin", (_timed[0]["first_saved_at"] - _timed[0]["started"]) / 60.0,
         "minutes into the session when the compass holder's first save landed", fmt="%.0f")
    emit("ScompassExitActs", _timed[0]["exit_acts"],
         "actions the compass holder had taken at its crossing")
emit("ScompassKnown", len(_known("compass")))
emit("Ssaved", sum(1 for r in PLAY if r.get("saved_at") or r.get("slot_saved")), "sessions whose save the game wrote")
emit("Steam", sum(1 for r in _known("team_size") if r["team_size"] > 1), "sessions with a companion")
emit("SteamKnown", len(_known("team_size")))
emit("Sbooks", sum(1 for r in _known("books") if r["books"] > 0), "sessions holding a book")
emit("SbooksKnown", len(_known("books")))
emit("Sdone", sum(1 for r in PLAY if r.get("completion_secs") is not None), "sessions that completed")
_map = field.on_map
emit("SleftNoItem", sum(1 for r in PLAY if _map(r) and r.get("picked_item") is False),
     "sessions that reached the map without the chest")
emit("SitemNoLeft", sum(1 for r in PLAY if r.get("picked_item") and not _map(r)),
     "sessions that searched the chest without reaching the map")
emit("Sboth", sum(1 for r in PLAY if r.get("picked_item") and _map(r)), "sessions that did both")
emit("QrandomRungs", max((m["reached"] for m in RUNION), default=0),
     "rungs the random floor reached, over its sessions")

# ------------------------------------------------------------ the ladder by model
emit("Lrungs", len(field.DEFINITION), "rungs on the ladder")
emit("Lopening", field.OPENING, "rungs of the opening")
emit("Lmodels", len(UNION), "models on the ladder")
_LNAMES = {"Lmap": "reached\nworld map", "Litem": "picked up\nan item", "Lscene": "entered\na location", "Lhermit": "spoke with\nthe hermit",
           "Lcompass": "held the\ncompass", "Lparty": "recruited a\nparty\nmember", "Lfight": "entered\na battle",
           "Lfought": "ended\na battle", "Lexp": "gained\nexperience", "Llevel": "reached\nlevel 2",
           "Lbook": "one of the\nfourteen"}
for _n, _d in _LNAMES.items():
    _i = field.DEFINITION.index(_d)
    emit(_n, sum(1 for m in UNION if m["rungs"][_i] is True), "models credited with rung %d" % (_i + 1))
_ITEM = field.DEFINITION.index("picked up\nan item")
emit("LnoItem", sum(1 for m in UNION if m["rungs"][_ITEM] is False), "models that never picked anything up")
_SCENE = field.DEFINITION.index("entered\na location")
emit("LnoScene", sum(1 for m in UNION if m["rungs"][_SCENE] is False), "models that never entered a scene beyond the home")


def _scenes(r):
    return ((r.get("replay") or {}).get("scenes") or {})


def _distinct(r):
    return _scenes(r).get("distinct") or 0

def emit_label(name, agent, note=""):
    lines.append((f"% {note}".rstrip() if note else "", f"\\newcommand{{\\{name}}}{{\\texttt{{{agent}}}}}"))


_top = max(UNION, key=lambda m: (m["reached"], m["agent"]))
lines.append(("% the model with the most rungs", "\\newcommand{\\LtopLabel}{\\texttt{%s}}" % _top["agent"]))
emit("Ltop", _top["reached"], "rungs it reached")
emit("LtopSessions", _top["sessions"], "sessions it played")
_second = sorted(UNION, key=lambda m: (-m["reached"], m["agent"]))[1]
_second_agent = _second["agent"]
emit_label("LsecondLabel", _second_agent)
emit("Lsecond", _second["reached"], "milestones the second model reached")
emit("LsecondSessions", _second["sessions"], "its sessions")
# the keypresses each crossing took, per model: the spread within a model against the spread between them
_cross = {m["agent"]: m["cross_keys"] for m in UNION}
if any(not c for c in _cross.values()):
    sys.exit("every model reached the world map, so every model needs a crossing count")
_within, _wlabel = max((max(c) / min(c), a) for a, c in _cross.items() if len(c) >= 2)
_means = {a: sum(c) / len(c) for a, c in _cross.items()}
_between = max(_means.values()) / min(_means.values())
if _within <= _between:
    sys.exit("the prose says the count varies more within a model than between models; it does not")
lines.append(("% the model whose crossings differ the most", "\\newcommand{\\LspreadLabel}{\\texttt{%s}}" % _wlabel))
emit("LspreadRatio", _within, "factor between its slowest and fastest crossing", fmt="%.0f")
emit("LbetweenRatio", _between, "factor between the largest and smallest model mean", fmt="%.0f")
# the narrowest range of crossings, over the models that crossed in more than one session
_steady = min((a for a, c in _cross.items() if len(c) >= 2), key=lambda a: max(_cross[a]) / min(_cross[a]))
_steady_m = next(m for m in UNION if m["agent"] == _steady)
if len(_cross[_steady]) != _steady_m["sessions"]:
    sys.exit("the prose says the model with the narrowest range crossed in every session; it did not")
emit_label("LsteadyLabel", _steady, "the model whose crossings vary least")
emit("LsteadyMin", min(_cross[_steady]), "fewest keypresses it took to the world map")
emit("LsteadyMax", max(_cross[_steady]), "most keypresses it took")
emit("LsteadySessions", _steady_m["sessions"], "its sessions")
# reliability across sessions: the crossing and the hermit
_HERMIT = field.DEFINITION.index("spoke with\nthe hermit")
_bymodel = {}
for r in MODELS:
    _bymodel.setdefault(r["agent"], []).append(r)
emit("LcrossSessions", sum(1 for r in MODELS if field.on_map(r)), "model sessions credited with the world map")
emit("LcrossEvery", sum(1 for rs in _bymodel.values() if all(field.on_map(r) for r in rs)),
     "models that crossed in every session they played")
_h = {a: (sum(1 for r in rs if field.rungs_of(r)[_HERMIT] is True), len(rs)) for a, rs in _bymodel.items()}
_every = [a for a, v in _h.items() if v[0] == v[1]]
if len(_every) != 1:
    sys.exit("the prose names one model that reached the hermit in every session: %s" % _every)
_every_a = _every[0]
_others = {a: v for a, v in _h.items() if a != _every_a and v[0] > 0}
if max(v[0] / v[1] for v in _others.values()) != 0.5:
    sys.exit("the prose says the other models reached the hermit in at most half of their sessions")
emit("LhermitOthers", len(_others), "other models that reached the hermit")
_both = [r for r in MODELS if r.get("exit_acts") is not None and (r.get("replay") or {}).get("crossing_actions") is not None]
if any(r["exit_acts"] != r["replay"]["crossing_actions"] for r in _both):
    sys.exit("the replay crossing count disagrees with the service count on some session")
emit("LcrossAgree", len(_both), "sessions carrying both crossing counts, which agree on every one")
_hermit_models = sorted(m["agent"] for m in UNION if m["rungs"][_HERMIT] is True)
lines.append(("% the models that spoke with the hermit", "\\newcommand{\\LhermitLabels}{" +
              (", ".join("\\texttt{%s}" % a for a in _hermit_models[:-1]) + " and \\texttt{%s}" % _hermit_models[-1]
               if len(_hermit_models) > 1 else "".join("\\texttt{%s}" % a for a in _hermit_models)) + "}"))
emit("QrandomSaved", sum(1 for r in RANDOM if r.get("saved_at")), "random runs that wrote a save")
emit("Susage", sum(1 for r in PLAY if r.get("usage")), "sessions with a usage report")
emit("Shelp", sum(1 for r in PLAY if r.get("help_langs")), "sessions that fetched the brief from the session")

# The earlier field at the previous default, kept for the record.
_old = field.load_runs(field.EARLIER)
_old_play = field.played(_old, 1200)
_old_models = [r for r in _old_play if fam(r["agent"]) != "random"]
emit("NoldSessions", len(_old_play), "scored sessions of the earlier twenty-minute field")
emit("NoldBudgetMin", 20)
emit("NoldModels", len({base(r["agent"]) for r in _old_models}))
emit("NoldLabels", len({r["agent"] for r in _old_models}))
emit("NoldVendors", len({fam(r["agent"]) for r in _old_models}))
emit("SoldMapFade", sum(1 for r in _old_play if r.get("bigmap") is True and r.get("exit_secs") is not None),
     "earlier sessions with a corroborated world-map crossing")
emit("SoldExpAny", sum(1 for r in _old_play if (r.get("exp") or 0) > 0))

# ---------------------------------------------------- shipped character records
mem = open(START_STATE, "rb").read()
base = None
i = mem.find(ANCHOR)
while i != -1:
    b = i - NAME - 2 * CHAR_SZ
    if b >= 0 and all(
            mem[b + c * CHAR_SZ + NAME:b + c * CHAR_SZ + NAME + 10].split(b"\0")[0]
            == n.encode("big5") for n, c in CHECK):
        base = b
        break
    i = mem.find(ANCHOR, i + 1)
if base is None:
    sys.exit("character array not located in start.state; refusing to cite it")

overflow = []
named = 0
for k in range(RECORDS):
    rec = mem[base + k * CHAR_SZ: base + (k + 1) * CHAR_SZ]
    if len(rec) < CHAR_SZ:
        sys.exit(f"record {k} is short: the stride is not {CHAR_SZ}")
    if rec[NAME:NAME + 10].split(b"\0")[0]:
        named += 1
    hp, mx = struct.unpack_from("<hh", rec, HP)
    mp, mm = struct.unpack_from("<hh", rec, MP)
    if hp > mx or mp > mm:
        overflow.append(k)
import slots as _slots
_named, _start, _after = _slots.scenes()
emit("Mscenes", _named, "named scenes in the scene table")
emit("MscenesOpenStart", _start, "scenes open at the start")
emit("MscenesOpenHermit", _after, "scenes open once the hermit has spoken")
emit("MscenesClosedHermit", _named - _after, "scenes still closed after him")
emit("Mrecords", RECORDS, "character records addressed")
emit("MrecordBytes", CHAR_SZ)
emit("Mblock", RECORDS * CHAR_SZ, "bytes of that block")
emit("Mnamed", named, "records carrying a name")
emit("Moverflow", len(overflow), "records exceeding hp/maxHp or mp/maxMp")

# The action space, read from the server's own key table rather than restated,
# so the paper cannot claim a vocabulary the API does not accept.
_keys = {}
_ktext = open(os.path.join(HERE, "..", "..", "..", "server", "server.py"),
              encoding="utf-8").read()
_ns: dict = {}
_block = _ktext[_ktext.index("KEYS = {"):_ktext.index("# Native resolution only")]
exec(compile(_block, "keys", "exec"), _ns)
_keys = _ns["KEYS"]
emit("MkeyNames", len(_keys), "key names the API accepts")
# the action protocol, read from the server so the paper cannot drift from it
emit("MmaxKeys", int(re.search(r"^MAX_KEYS_PER_ACTION = (\d+)", _ktext, re.M).group(1)), "keys an action may carry")
emit("MsettleReact", int(re.search(r"def settle\(baseline, react=(\d+)", _ktext).group(1)), "frames allowed for the game to react")
emit("MsettleStable", int(re.search(r"^DEFAULT_STABLE_FRAMES = (\d+)", _ktext, re.M).group(1)), "identical frames that count as settled")
emit("MsettleMax", int(re.search(r"^DEFAULT_SETTLE_MAX_FRAMES = (\d+)", _ktext, re.M).group(1)), "frames after which the wait ends regardless")
emit("MkeyCodes", len(set(_keys.values())), "distinct scancodes behind them")


# ------------------------------------------------------------ replay patterns
# Read from the published keypress timelines of the scored sessions, committed
# in figures/timelines/<id>.json beside the snapshot. A mark's time is on the
# replay clock, so a minute here is the minute shown in the strip of the video.
TIMELINES = os.path.join(HERE, "timelines")
CONFIRM = ("enter", "space")


def timeline(r):
    path = os.path.join(TIMELINES, r["id"] + ".json")
    if not os.path.exists(path):
        sys.exit(f"no timeline for {r['agent']} ({r['id']}); fetch runs/{r['id']}.json")
    t = json.load(open(path, encoding="utf-8"))
    if t["id"] != r["id"] or len(t["marks"]) != r["actions"]:
        sys.exit(f"timeline of {r['agent']} disagrees with the catalogue")
    return t


def minutes(t, m):
    return m["t"] * t["speed"] / 60.0


def confirm_runs(t):
    """Stretches of three or more consecutive actions made only of confirm keys:
    a conversation pressed through line by line."""
    out, cur = [], []
    for m in t["marks"]:
        ks = [k for k, _ in m["keys"]]
        if ks and all(k in CONFIRM for k in ks):
            cur.append(m)
        else:
            if len(cur) >= 3:
                out.append(cur)
            cur = []
    if len(cur) >= 3:
        out.append(cur)
    return out


TL = {r["id"]: timeline(r) for r in PLAY}

# the crossing that took most actions, against the median crossing
_crossed = [r for r in PLAY if r.get("exit_acts") is not None]
_slowest = max(_crossed, key=field.crossing_keys)
emit("PexitActsMax", field.crossing_keys(_slowest), "keypresses the slowest crossing took")
emit_label("PexitActsMaxLabel", _slowest["agent"])
emit("PexitMinMax", _slowest["exit_secs"] / 60.0, "minute of that crossing", fmt="%.0f")
_noconfirm = [r for r in PLAY if not any((r.get("keys") or {}).get(k) for k in CONFIRM)]
emit("PnoConfirm", len(_noconfirm), "sessions that never pressed enter or space")
if len(_noconfirm) != 1 or _slowest["id"] != _noconfirm[0]["id"]:
    sys.exit("the prose calls the slowest crossing the one session that never confirmed; it no longer is")

# the session that crossed and then never entered a scene, the home included
_orbit = [r for r in _crossed if not _scenes(r).get("entries")]
_orb = max(_orbit, key=lambda r: r["actions"] - r["exit_acts"])
emit_label("PorbitLabel", _orb["agent"])
emit("PorbitExitMin", _orb["exit_secs"] / 60.0, "minute it crossed", fmt="%.0f")
emit("PorbitActs", _orb["actions"] - _orb["exit_acts"], "actions it took on the world map afterwards")
emit("PorbitMin", (_orb["played"] - _orb["exit_secs"]) / 60.0, "minutes it spent there", fmt="%.0f")

# breadth: distinct scenes entered beyond the home, from the name banners on the replay
_wide = max(PLAY, key=lambda r: (_distinct(r), r["actions"]))
emit("PscenesMax", _distinct(_wide), "distinct scenes the widest-ranging session entered")
emit_label("PscenesMaxLabel", _wide["agent"])
emit("PscenesThree", sum(1 for r in PLAY if _distinct(r) >= 3), "sessions that entered three or more distinct scenes")

# the prose says every model but the top two entered only an inn or the house of the hermit
_HERMIT_HOUSE = "南賢居"
for _r in MODELS:
    if _r["agent"] not in (_top["agent"], _second_agent):
        for _x in _scenes(_r).get("entries", []):
            if _x["name"] != field.HOME and _x["name"] != _HERMIT_HOUSE and not _x["name"].endswith("客棧"):
                sys.exit(f"{_r['agent']} entered {_x['name']}, which is neither an inn nor the house of the hermit; the prose no longer holds")

# the compass holder: the conversation and the compass reads
_holder = max((r for r in PLAY if field.rungs_of(r)[_COMPASS] is True), key=lambda r: (_distinct(r), r["actions"]))
if _distinct(_holder) != _distinct(_wide):
    sys.exit("the prose calls the widest-ranging session a compass holder; it no longer is")
_ht = TL[_holder["id"]]


def opens_items(m):
    """The item screen opened in one action: escape, then the menu walked
    down to the items and confirmed."""
    ks = [k for k, _ in m["keys"]]
    return any(ks[i] in ("esc", "escape") and ks[i + 1:i + 3] == ["down", "down"] and ks[i + 3] in ("enter", "space")
               for i in range(len(ks) - 3))


emit("PholderMenuOpens", sum(1 for m in _ht["marks"] if opens_items(m)), "times it opened the item screen")
if not _holder["replay"]["compass"]["seconds"]:
    sys.exit("the prose says the widest-ranging session read its coordinates from the compass")

# Events read from the published replays (replay_events.json), by minute of
# the session clock shown in the strip of the video.
EV = {r["id"]: (r, r["replay"]) for r in PLAY if r.get("replay")}


def _first(ev, name):
    return ev[name]["first_minute"]


_every_ids = {r["id"] for r in _bymodel[_every_a]}
if _every_a != _second_agent:
    sys.exit("the prose says the second model reached the hermit in every session")
_hermit_every = sorted(_first(e, "hermit") for i, (r, e) in EV.items() if i in _every_ids and e["hermit"]["seconds"])
emit("PhermitSessions", sum(1 for r, e in EV.values() if e["hermit"]["seconds"]), "sessions that reached the hermit")
emit("PhermitEveryFirst", min(_hermit_every), "earliest minute the second model reached the hermit", fmt="%.0f")
emit("PhermitEveryLast", max(_hermit_every), "latest", fmt="%.0f")

# the battles: every one began in the house of Yan Ji; alone at level one the hero lost
# it or stalled in it; the one win came after recruiting Tian Boguang
_YANJI, _TIAN = "閻基居", "田伯光居"
_all_fights = [(r, e) for r, e in EV.values() if e["battle"]["seconds"]]
emit("PfightSessions", len(_all_fights), "sessions that entered a battle")
for r, e in _all_fights:
    _before = [x["name"] for x in e["scenes"]["entries"] if x["minute"] <= _first(e, "battle")]
    if not _before or _before[-1] != _YANJI:
        sys.exit("the prose says every battle began in the house of Yan Ji; %s did not" % r["id"])
    if e.get("recruited_minute") is not None and e["recruited_minute"] < _first(e, "battle"):
        sys.exit("the prose says the hero fought the first battle alone; %s had recruited before it" % r["id"])
_CK, _FK = field.DEFINITION.index("held the\ncompass"), field.DEFINITION.index("entered\na battle")
_both_models = sorted(m["agent"] for m in UNION if m["rungs"][_CK] is True and m["rungs"][_FK] is True)
if _both_models != sorted([_top["agent"], _second_agent]):
    sys.exit("the prose says two models took the compass and entered a battle: %s" % _both_models)
_wins = [(r, e) for r, e in _all_fights if e["won"]["seconds"]]
if len(_wins) != 1 or _wins[0][0]["agent"] != _top["agent"]:
    sys.exit("the prose describes one won battle, by the top model: %s" % [r["id"] for r, e in _wins])
_wr, _we = _wins[0]
if field.rungs_reached(_wr) != _top["reached"]:
    sys.exit("the prose says the top model reached all its milestones in the session that won")
_EXPK, _LVK = field.DEFINITION.index("gained\nexperience"), field.DEFINITION.index("reached\nlevel 2")
if not (field.rungs_of(_wr)[_EXPK] and field.rungs_of(_wr)[_LVK]) or _first(_we, "exp") != _first(_we, "won") or _first(_we, "level") != _first(_we, "won"):
    sys.exit("the prose says the win paid experience and the second level at once")
if any(field.rungs_of(r)[_EXPK] for r in PLAY if r["id"] != _wr["id"]):
    sys.exit("the prose says no other session gained experience")
# its route: lost alone, walked to Tian Boguang, recruited him, returned to Yan Ji and won
_yj = [x["minute"] for x in _we["scenes"]["entries"] if x["name"] == _YANJI]
_tb = [x["minute"] for x in _we["scenes"]["entries"] if x["name"] == _TIAN]
_rec = _we.get("recruited_minute")
if not (len(_yj) >= 2 and _tb and _rec is not None
        and _yj[0] < _first(_we, "battle") < _first(_we, "defeat") < _tb[0] < _rec < _yj[1] < _first(_we, "won")):
    sys.exit("the prose orders the winning session: Yan Ji, defeat, Tian Boguang, recruitment, Yan Ji again, win")
emit("PtopDefeatMin", _first(_we, "defeat"), "minute the winning session lost its first battle", fmt="%.0f")
emit("PrecruitMin", _rec, "minute it answered yes to Tian Boguang", fmt="%.0f")
emit("PreturnMin", _yj[1], "minute it entered the house of Yan Ji again", fmt="%.0f")
emit("PwonMin", _first(_we, "won"), "minute of the battle-won banner", fmt="%.0f")
_recruits = [(r, e) for r, e in EV.values() if e.get("recruited_minute") is not None]
# the second model's battles: one lost, one left open when its keys stopped
_sf = [(r, e) for r, e in _all_fights if r["agent"] == _second_agent]
if len(_all_fights) != len(_sf) + 1:
    sys.exit("the prose attributes every battle to the two models")
_sl = [(r, e) for r, e in _sf if e["defeat"]["seconds"]]
_so = [(r, e) for r, e in _sf if not e["defeat"]["seconds"] and not e["won"]["seconds"]]
if len(_sl) != 1 or len(_so) != 1:
    sys.exit("the prose describes one lost and one open battle of the second model")
emit("PsecondDefeatMin", _first(_sl[0][1], "defeat"), "minute its lost battle ended", fmt="%.0f")
_st = TL[_so[0][0]["id"]]
emit("PbattleLastMin", minutes(_st, _st["marks"][-1]), "minute of the open battle's last key", fmt="%.0f")
_tian2 = [r for r in _bymodel[_second_agent] if any(x["name"] == _TIAN for x in _scenes(r).get("entries", []))]
if any((r["replay"] or {}).get("recruited_minute") is not None and _TIAN in [x["name"] for x in _scenes(r)["entries"]] for r in _tian2):
    sys.exit("the prose says the second model entered the house of Tian Boguang without recruiting him")
emit("PsecondTianSessions", len(_tian2), "sessions of the second model that entered the house of Tian Boguang")

# Appendix: every battle on record (both budgets), checked by eye against the replay
import save_state as _ss  # noqa: E402  (on the path through slots.py)
_BT = [(r, b) for r in PLAY + field.load_long() for b in field.battles(r)]
_baud = json.load(open(os.path.join(HERE, "battles_audit.json"), encoding="utf-8"))["checked"]
if sorted((a["session"], a["began_minute"]) for a in _baud) != sorted((r["id"], b["start"]) for r, b in _BT) \
        or any(a["opponent"] != "閻基" for a in _baud):
    sys.exit("battles_audit.json must list every battle, each against Yan Ji")
_alone = [b for r, b in _BT if b["party"] == 1]
_won = [(r, b) for r, b in _BT if b["outcome"] == "won"]
if sorted(b["outcome"] for b in _alone) != ["lost"] * (len(_alone) - 1) + ["open"] or len(_won) != 1 or _won[0][1]["party"] != 2:
    sys.exit("the appendix says the hero alone lost every battle but one left open, and the one win had two in the party")
emit("Nbattles", len(_BT), "battles on record")
emit("NbattlesAlone", len(_alone), "battles the hero fought alone")
emit("NbattlesAloneLost", sum(b["outcome"] == "lost" for b in _alone), "of them lost")
_wr, _wb = _won[0]
_team = _ss.from_archive(open(os.path.join(HERE, "slots", _wr["id"] + ".grp"), "rb").read(),
                         open(os.path.join(HERE, "slots", _wr["id"] + ".idx"), "rb").read())["team"]
_tian = [m for m in _team if m["name"] == "田伯光"]
if len(_team) != 2 or not _tian:
    sys.exit("the appendix says the winning party was the hero and Tian Boguang")
emit("PtianLevel", _tian[0]["level"], "Tian Boguang's level in the save")
emit("PtianHealth", _tian[0]["maxhp"], "his health")
emit("PwinConfirm", 100 * _wb["confirm"], "percent of keys in the won battle that confirm", fmt="%.0f")
# after a defeat: the winning session returned to the battle, no other session did
_after = {}
for r in PLAY + field.load_long():
    for bt in field.battles(r):
        if bt["outcome"] == "lost":
            _after[r["id"]] = (r, bt, [x for x in field.battles(r) if x["start"] > bt["end"]])
if not _after[_wr["id"]][2] or any(later for sid, (_, _, later) in _after.items() if sid != _wr["id"]):
    sys.exit("the prose says only the winning session returned to a battle it had lost")
_moved = [(r, bt) for sid, (r, bt, later) in _after.items() if sid != _wr["id"]]
emit("NlostNoReturn", len(_moved), "other sessions that lost a battle and never fought again")
emit("PnoReturnLeftMin", max(r["budget"] / 60 - bt["end"] for r, bt in _moved), "the most budget one of them had left, minutes", fmt="%.0f")
# the other recruitments fought no battle afterwards
for r in PLAY + field.load_long():
    rm = (r.get("replay") or {}).get("recruited_minute")
    if rm is not None and r["id"] != _wr["id"] and any(b["start"] > rm for b in field.battles(r)):
        sys.exit("the appendix says the other recruitments were followed by no battle")
_tm = json.load(open(os.path.join(HERE, "templates", "templates.json"), encoding="utf-8"))
emit("ReplayThreshold", _tm["threshold"], "match threshold of the replay scan", fmt="%.1f")
import replay_scan as _rs  # noqa: E402
emit("ReplayHold", _rs.HOLD, "seconds of play a panel must stay above the threshold", fmt="%.1f")
_speeds = {round(json.load(open(os.path.join(HERE, "timelines", k + ".json"), encoding="utf-8"))["speed"])
           for k in field.EVENTS if os.path.exists(os.path.join(HERE, "timelines", k + ".json"))}
_need = {v: math.ceil(_rs.HOLD * 20 / v - 1e-9) for v in _speeds}
if _need != {8: 2, 24: 1}:
    sys.exit("the prose names two frames at 8 times speed and one at 24 times; the replays give %s" % _need)
_HELD = ("hermit", "compass", "battle", "defeat", "prompt")
_MSGS = ("obtained", "won", "exp", "level")
_miss = max(e[n]["max"] for _, e in EV.values() for n in _HELD if e[n]["seconds"] == 0 and e[n]["max"] is not None)
emit("ReplayMissMax", _miss, "highest score of a held panel in any session without it", fmt="%.2f")
_msg_miss = max(e[n]["max"] for _, e in EV.values() for n in _MSGS if e[n]["seconds"] == 0 and e[n]["max"] is not None)
emit("ReplayMsgMissMax", _msg_miss, "highest score of a single-frame message in any session without it", fmt="%.2f")
# the first reading of every panel in the hour sessions, checked by eye (panel_audit.json)
_audit = json.load(open(os.path.join(HERE, "panel_audit.json"), encoding="utf-8"))["checked"]
_first = {(r["id"], n, [c for c in e[n]["candidates"] if c[1] > _tm["threshold"]][0][0])
          for r, e in EV.values() if not field.is_random(r["agent"])
          for n in ("hermit", "compass", "battle", "defeat", "prompt", "won", "exp", "level") if e[n]["seconds"]}
if {(a["session"], a["panel"], a["video_second"]) for a in _audit if a["shows_panel"]} != _first:
    sys.exit("panel_audit.json does not cover every first panel reading of the hour sessions; check the new ones by eye")
emit("NpanelAudited", len(_first), "first panel readings checked by eye")
# every yes-or-no prompt on the replays was answered by a key of the model, not by the save attempt
for _sid, _e in field.EVENTS.items():
    _tp = os.path.join(HERE, "timelines", _sid + ".json")
    if not _e["prompt"]["seconds"] or not os.path.exists(_tp):
        continue
    _marks = json.load(open(_tp, encoding="utf-8"))["marks"]
    for _sec, _v in _e["prompt"]["candidates"]:
        if _v > _tm["threshold"] and not any(_sec <= m["t"] <= _sec + 3 for m in _marks):
            sys.exit("a yes-or-no prompt on %s at video second %s was left without a key of the model" % (_sid, _sec))
# the item milestone read from the obtained message where no record carries the bag
# the item milestone is the item message; every bag reading that shows a new item agrees
if any(not (r.get("replay") or {}).get("obtained") for r in ALL):
    sys.exit("a session has no scan for the item message")
_ob_bag = [r for r in ALL if r.get("picked_item")]
if any(not r["replay"]["obtained"]["seconds"] for r in _ob_bag):
    sys.exit("a bag reading shows a new item that the item message does not")
emit("PobtainedBag", len(_ob_bag), "sessions whose inventory shows a new item, all with the item message")
# the threshold margin: every reading is the same for any threshold between the
# highest score of a frame without the event and the lowest best score of a session with it
_hitmin = min(e[n]["max"] for _, e in EV.values() for n in _HELD if e[n]["seconds"] > 0)
_msg_hit = min((e[n]["max"], n) for _, e in EV.values() for n in _MSGS if e[n]["seconds"] > 0)
if not (_miss < _tm["threshold"] <= _hitmin and _msg_miss < _tm["threshold"] <= _msg_hit[0]):
    sys.exit("the threshold does not sit between the highest miss and the lowest hit")
if _msg_hit[1] != "obtained":
    sys.exit("the prose says the lowest message hit is an item message")
emit("ReplayHitMin", _hitmin, "lowest best score of a session with a held panel", fmt="%.2f")
emit("ReplayMsgHitMin", _msg_hit[0], "lowest best score of a session with a message", fmt="%.2f")
# the replay readings against the state records where both exist
def _seen(r, n):
    e = r.get("replay") or {}
    return bool(e.get(n) and e[n]["seconds"] > 0)
_cb = [r for r in ALL if r.get("replay") and r.get("compass") is not None]
if any(_seen(r, "compass") != bool(r["compass"]) for r in _cb):
    sys.exit("the compass panel disagrees with a bag reading")
emit("PcompassBoth", len(_cb), "sessions with both a bag reading and a replay")
emit("PcompassBag", sum(1 for r in _cb if r["compass"]), "of them whose bag holds the compass, all with the coordinate line on the replay")
_hb = [r for r in ALL if r.get("replay") and r.get("world_opened") is not None]
if any(r["world_opened"] and not _seen(r, "hermit") for r in _hb):
    sys.exit("a save shows the scenes the hermit opens but the replay shows no portrait")
emit("PhermitBoth", len(_hb), "sessions with a preserved save and a replay")
emit("PhermitOpened", sum(1 for r in _hb if r["world_opened"]), "of them whose save shows the scenes the hermit opens, all with his portrait on the replay")
# the model left out of the field, and its sessions in the catalogue
if len(field.EXCLUDED) != 1:
    sys.exit("the appendix names one excluded model")
_excl = field.played([r for r in field.load_runs(dedup=False, keep_excluded=True) if r["agent"] in field.EXCLUDED])
if not _excl:
    sys.exit("the excluded model has no session at the default budget; drop the sentence")
lines.append(("% the model left out of the field", "\\newcommand{\\LexcludedLabel}{\\texttt{%s}}" % field.EXCLUDED[0]))
emit("NexcludedSessions", len(_excl), "its sessions at the default budget in the catalogue")
emit("NidleSessions", sum(1 for r in PLAY if r.get("reason") == "idle"),
     "sessions ended by the ten-minute idle rule the field ran with")
# when the field ran
import datetime as _dt
_HOURLY = ALL
_days = sorted(_dt.datetime.fromtimestamp(r["started"], _dt.timezone.utc).date() for r in _HOURLY if r.get("started"))
if len(_days) != len(_HOURLY):
    sys.exit("a session carries no start time")
if _days[0].year != _days[-1].year or _days[0].month != _days[-1].month:
    sys.exit("the field spans more than one month; the date macro assumes one")
lines.append(("% the days the field ran, UTC", "\\newcommand{\\FieldDates}{%d to %d %s}" % (_days[0].day, _days[-1].day, _days[-1].strftime("%B %Y"))))

# the conversations with the hermit held by sessions that never took the
# compass: the confirm run overlapping the hermit's portrait on screen
_HERMIT = field.DEFINITION.index("spoke with\nthe hermit")
_talks = []
for r in PLAY:
    e = r.get("replay")
    if not e or not e["hermit"]["seconds"] or field.rungs_of(r)[_COMPASS] is True:
        continue
    t = TL[r["id"]]
    lo, hi = min(e["hermit"]["minutes"]) - 1, max(e["hermit"]["minutes"]) + 1
    runs = [c for c in confirm_runs(t) if minutes(t, c[-1]) >= lo and minutes(t, c[0]) <= hi]
    if not runs:
        continue
    c = max(runs, key=lambda c: sum(len(m["keys"]) for m in c))
    n = sum(len(m["keys"]) for m in c)
    _talks.append((r, n, minutes(t, c[-1]) - minutes(t, c[0]), minutes(t, c[0]), minutes(t, c[-1])))
if not _talks:
    sys.exit("no conversation with the hermit outside the compass holder; the prose describes two")
_slow = max(_talks, key=lambda x: x[2])
_fast = min(_talks, key=lambda x: x[2] / x[1])
emit_label("PtalkSlowLabel", _slow[0]["agent"])
emit("PtalkSlowPresses", _slow[1], "confirm presses of the slowest conversation with the hermit")
emit("PtalkSlowMin", _slow[2], "minutes it took", fmt="%.0f")
emit("PtalkSlowPace", 60.0 * _slow[2] / _slow[1], "seconds a press", fmt="%.0f")
emit("PtalkSlowEndMin", _slow[4], "minute it ended", fmt="%.0f")
emit("PtalkSlowLeftMin", _slow[0]["budget"] / 60.0 - _slow[4], "minutes of budget left then", fmt="%.0f")
emit_label("PtalkFastLabel", _fast[0]["agent"])
emit("PtalkFastPresses", _fast[1], "confirm presses of the fastest conversation")
emit("PtalkFastMin", _fast[2], "minutes it took", fmt="%.0f")
emit("PtalkFastStartMin", _fast[3], "minute it began", fmt="%.0f")
if _slow[0]["id"] == _fast[0]["id"]:
    sys.exit("the prose contrasts two conversations; the slowest and fastest are the same session")

# blind batching: the longest key list any action carried
_lens = {r["id"]: max(len(m["keys"]) for m in TL[r["id"]]["marks"]) for r in PLAY}
_bid = max(_lens, key=_lens.get)
_br = next(r for r in PLAY if r["id"] == _bid)
emit("PbatchMaxKeys", _lens[_bid], "keys in the longest single action")
emit_label("PbatchLabel", _br["agent"])
emit("PbatchKeysPerAction", _br["key_events"] / _br["actions"], "its keys per action", fmt="%.0f")
emit("PbatchBig", sum(1 for m in TL[_bid]["marks"] if len(m["keys"]) >= 50), "its actions of fifty keys or more")
if not _br.get("saved_at") or _br.get("bigmap"):
    sys.exit("the prose says the batching session was credited by the save alone; it no longer is")

# ------------------------------------------------------- the four-hour sessions
import long_cohort
LONG_ATTEMPTS = field.long_attempts()
LONG_MANIFEST = long_cohort.validate(LONG_ATTEMPTS)
LONG = field.load_long()
_long_models = {r["agent"] for r in LONG}
_field_models = {r["agent"] for r in PLAY}
_compatible_models = {r["agent"] for r in LONG_ATTEMPTS if r["declared"] not in field.LONG_EXCLUDED}
_pending_models = sorted(_compatible_models - _long_models)
emit("NlongAttempts", len(LONG_ATTEMPTS), "attempts at the four-hour budget on record")
emit("NlongSessions", len(LONG), "four-hour sessions that count")
emit("NlongModels", len(_long_models), "models with a four-hour session that counts")
emit("NlongWithheld", len(LONG_ATTEMPTS) - len(LONG), "attempts that do not count")
emit("NlongPendingModels", len(_pending_models), "models with a four-hour attempt and no session that counts")
emit("NlongFieldModels", len(_long_models & _field_models), "of them evaluated at the hour")
emit("NlongFieldSessions", sum(r["agent"] in _field_models for r in LONG))
emit("NlongBudgetMin", field.LONG_BUDGET // 60, "requested wall-clock budget")
emit("NlongWindowMin", LONG_MANIFEST["last_key_window_seconds"] // 60, "the last key must fall within this many final minutes")
emit("NlongMinLastMin", (field.LONG_BUDGET - LONG_MANIFEST["last_key_window_seconds"]) // 60)
emit("NlongAliased", sum(r["declared"] != r["agent"] for r in LONG))
emit("NlongExcluded", len(long_cohort.entries_of(LONG_MANIFEST, "incompatible_config")), "attempts declared under names that identify no model of the paper")
emit("NlongStartup", len(long_cohort.entries_of(LONG_MANIFEST, "startup_only")), "attempts of one or two actions")
emit("NlongZero", len(long_cohort.entries_of(LONG_MANIFEST, "no_actions")), "attempts with no action")
emit("NlongProtocol", len(long_cohort.entries_of(LONG_MANIFEST, "protocol_violation")), "attempts whose harness read earlier sessions")
emit("NlongEarly", len(long_cohort.entries_of(LONG_MANIFEST, "stopped_early")), "attempts whose last key came before the final minutes")
if len(long_cohort.entries_of(LONG_MANIFEST, "protocol_violation")) != 1:
    sys.exit("the prose says one attempt read the timelines of earlier sessions")
if sum(len(long_cohort.entries_of(LONG_MANIFEST, s)) for s in
       ("no_actions", "startup_only", "stopped_early", "incompatible_config", "protocol_violation")) != len(LONG_ATTEMPTS) - len(LONG):
    sys.exit("the attempts that do not count do not add up to the manifest")
_hack = [r for r in LONG_ATTEMPTS if r["id"] == field.HACK_SESSION]
_CK, _RK = field.DEFINITION.index("held the\ncompass"), field.DEFINITION.index("recruited a\nparty\nmember")
if len(_hack) != 1 or _hack[0]["agent"] != "gemini-3.8-flash" or field.rungs_of(_hack[0])[_CK] is not True or field.rungs_of(_hack[0])[_RK] is not True:
    sys.exit("the prose says the attempt that read earlier sessions is gemini-3.8-flash and held the compass and a companion")
emit_label("LlongHackLabel", "gemini-3.8-flash", "the model whose attempt read the timelines of earlier sessions")
# from the harness transcript of that attempt, which is not in the release: among
# the sequences it read was a session of gpt-6-astra
emit_label("LlongHackReadLabel", "gpt-6-astra", "a model whose timeline that attempt read")


def _join(names):
    names = ["\\texttt{%s}" % a for a in names]
    return (", ".join(names[:-1]) + " and " + names[-1]) if len(names) > 1 else "".join(names)


lines.append(("% models with a four-hour attempt and no session that counts",
              "\\newcommand{\\LlongPendingLabels}{" + _join(_pending_models) + "}"))
for macro, rung in (("NlongMap", "reached\nworld map"), ("NlongItem", "picked up\nan item"),
                   ("NlongScene", "entered\na location"), ("NlongHermit", "spoke with\nthe hermit"),
                   ("NlongCompass", "held the\ncompass"), ("NlongCompanion", "recruited a\nparty\nmember"),
                   ("NlongFight", "entered\na battle"), ("NlongExp", "gained\nexperience"),
                   ("NlongBook", "one of the\nfourteen")):
    k = field.DEFINITION.index(rung)
    emit(macro, sum(field.rungs_of(r)[k] is True for r in LONG), "among the four-hour sessions that count")
_last = {r["id"]: long_cohort.last_key_seconds(r) / 60 for r in LONG}
emit("LlongLastMin", min(_last.values()), "earliest last key, minutes", fmt="%.1f")
emit("LlongLastMax", max(_last.values()), "latest last key, minutes", fmt="%.1f")
_lcross = [r["exit_secs"] / 60 for r in LONG if field.on_map(r)]
if not _lcross or any(r.get("exit_secs") is None for r in LONG if field.on_map(r)):
    sys.exit("a selected crossing has no service time")
emit("LlongCrossFirst", min(_lcross), "earliest crossing, minutes", fmt="%.1f")
emit("LlongCrossLast", max(_lcross), "latest crossing, minutes", fmt="%.1f")
emit("NlongCrossLate", sum(t > BUDGET / 60 for t in _lcross))
# the filters: leaving the house, reaching the hermit, winning after a defeat.
# A four-hour session passes a filter early or not at all.
import emit_long as _el  # noqa: E402


def _marks_min(r):
    t = json.load(open(os.path.join(HERE, "timelines", r["id"] + ".json"), encoding="utf-8"))
    return [m["t"] * t["speed"] / 60 for m in t["marks"]]


def _after(r, t0):
    ms = [m for m in _marks_min(r) if m >= t0]
    return (ms[-1] - t0 if ms else 0.0), len(ms)


_stay = [r for r in LONG if not field.on_map(r)]
if len(_stay) != 1:
    sys.exit("the prose says one four-hour session never left the house")
emit("PfOneStuckMin", _after(_stay[0], 0)[0], "minutes the session that never left played", fmt="%.0f")
_crossed = [r for r in LONG if field.on_map(r)]
_hpass = [r for r in _crossed if r["replay"]["hermit"]["seconds"]]
_hstuck = [r for r in _crossed if not r["replay"]["hermit"]["seconds"]]
if len(_hpass) != 1:
    sys.exit("the prose says one four-hour session reached the hermit")
emit("PfTwoPassMin", _hpass[0]["replay"]["hermit"]["first_minute"] - _hpass[0]["exit_secs"] / 60, "minutes from its crossing to the hermit", fmt="%.0f")
emit("NfTwoStuck", len(_hstuck), "four-hour sessions that left the house and never reached the hermit")
_hs = [_after(r, r["exit_secs"] / 60) for r in _hstuck]
emit("PfTwoStuckMinLo", min(m for m, _ in _hs), "fewest minutes one of them spent on the world map", fmt="%.0f")
emit("PfTwoStuckMinHi", max(m for m, _ in _hs), "most minutes", fmt="%.0f")
emit("PfTwoStuckActs", max(a for _, a in _hs), "most actions", fmt="%d")
_lost4 = [(r, bt) for r in LONG for bt in field.battles(r) if bt["outcome"] == "lost"]
if len(_lost4) != 1 or any(field.battles(r)[-1] != bt for r, bt in _lost4):
    sys.exit("the prose says one four-hour session lost a battle and never fought again")
_f3 = _after(_lost4[0][0], _lost4[0][1]["end"])
emit("PfThreeMin", _f3[0], "minutes it played after the defeat", fmt="%.0f")
emit("PfThreeActs", _f3[1], "actions it sent after the defeat", fmt="%d")
# the filters over every model session, hour and four-hour (figures/filters.py)
_CH = field.chain([r for r in PLAY if not field.is_random(r["agent"])] + LONG)
_FW = 30
emit("Nchain", _CH[0]["at_risk"], "model sessions followed along the chain")
emit("FilterWait", _FW, "minutes before a step after which a filter is passed by no session")
_st = {s["step"].replace("\n", " "): s for s in _CH}
_hs, _ws = _st["reach hermit"], _st["win battle"]
for _s in (_hs, _ws):
    if field.passes_after(_s, _FW)[0]:
        sys.exit("the prose says no session passes %s after %d minutes before it" % (_s["step"], _FW))
for _s in (_st["leave house"], _st["enter location"]):
    if not field.passes_after(_s, _FW)[0]:
        sys.exit("the prose says sessions still pass %s after %d minutes" % (_s["step"], _FW))
emit("NhermitRisk", _hs["at_risk"], "sessions that entered a location")
emit("NhermitPass", len(_hs["passed"]), "of them that reached the hermit")
emit("PhermitPassMax", max(d for _, d in _hs["passed"]), "the longest any took to reach him, minutes", fmt="%.0f")
emit("PhermitLateHours", field.passes_after(_hs, _FW)[1], "hours of play before the hermit past the wait, with no pass", fmt="%.0f")
emit("NwinRisk", _ws["at_risk"], "sessions that entered a battle")
emit("PwinLateHours", field.passes_after(_ws, _FW)[1], "hours of play before a win past the wait, with no pass", fmt="%.0f")
if len(_ws["passed"]) != 1:
    sys.exit("the prose says one session won a battle")
_hl = [r for r, d in _hs["stuck"] if d > _FW]
emit("NhermitLate", len(_hl), "sessions that played past the wait without reaching the hermit")
_wl = [r for r, d in _ws["stuck"] if d > _FW]
if len(_wl) != 1 or _wl[0] is not _lost4[0][0]:
    sys.exit("the prose says the one session that played past the wait after its first battle is the four-hour one that lost")
emit("NwinShort", len(_ws["stuck"]) - len(_wl), "sessions whose last key came within the wait after their first battle")

# after the first hour the four-hour sessions add only items and locations
for r in LONG:
    for col, name in _el.COLUMNS:
        m = (r["exit_secs"] / 60 if r.get("exit_secs") is not None else None) if name == "crossing" else _el.first_minute(r["replay"], name)
        if m is not None and m > BUDGET / 60 and col not in ("Item", "Location"):
            sys.exit("the prose says the four-hour sessions add only items and locations after the first hour")
# the four-hour sessions that go beyond the opening, by milestone
_LK = {k: field.DEFINITION.index(k) for k in ("spoke with\nthe hermit", "held the\ncompass", "entered\na battle", "ended\na battle", "gained\nexperience", "one of the\nfourteen")}
_beyond = [r for r in LONG if field.rungs_of(r)[_LK["spoke with\nthe hermit"]] is True]
for rung in ("gained\nexperience", "one of the\nfourteen"):
    if any(field.rungs_of(r)[_LK[rung]] is True for r in LONG):
        sys.exit("the prose says no four-hour session that counts reached " + rung.replace("\n", " "))
if len(_beyond) != 1 or _beyond[0]["agent"] != "claude-opus-5.5":
    sys.exit("the prose says one four-hour session, of claude-opus-5.5, goes beyond the opening: %s" % [r["agent"] for r in _beyond])
_sp, = _beyond
_spe = _sp["replay"]
if not (_spe.get("defeat") or {}).get("minutes"):
    sys.exit("the prose says the four-hour session beyond the opening lost its battle")
# every milestone it reached has its first reading inside the first hour
_at = {"hermit": _spe["hermit"]["first_minute"], "compass": _spe["compass"]["first_minute"],
       "battle": _spe["battle"]["first_minute"], "defeat": _spe["defeat"]["first_minute"],
       "location": min((x["minute"] for x in _spe["scenes"]["entries"] if x["name"] != field.HOME), default=None),
       "map": _sp["exit_secs"] / 60 if _sp.get("exit_secs") is not None else None}
if any(m is None or m > BUDGET / 60 for m in _at.values()) or _spe.get("recruited_minute") is not None \
        or any(_spe[n]["seconds"] for n in ("won", "exp", "level")) \
        or field.rungs_reached(_sp) != 7:
    sys.exit("the prose says the four-hour session beyond the opening reached nothing new after its first hour: %s" % _at)
emit_label("LlongBeyondLabel", _sp["agent"], "the model of the four-hour session beyond the opening")
emit("PlongBeyondLastMin", long_cohort.last_key_seconds(_sp) / 60, "minute of its last key", fmt="%.0f")
emit("PlongBeyondHermitMin", _spe["hermit"]["minutes"][0], fmt="%.0f")
emit("PlongBeyondCompassMin", _spe["compass"]["minutes"][0], fmt="%.0f")
emit("PlongBeyondBattleMin", _spe["battle"]["minutes"][0], fmt="%.0f")
emit("PlongBeyondDefeatMin", _spe["defeat"]["minutes"][0], fmt="%.0f")
if field.HACK_SESSION in {r["id"] for r in LONG}:
    sys.exit("the attempt that read earlier sessions must not count")
_ldays = sorted(_dt.datetime.fromtimestamp(r["started"], _dt.timezone.utc).date() for r in LONG)
if _ldays[0].month != _ldays[-1].month:
    sys.exit("the four-hour sessions span more than one month; the date macro assumes one")
lines.append(("% the days the four-hour sessions that count ran, UTC", "\\newcommand{\\LongDates}{%s}" % (
    "%d %s" % (_ldays[0].day, _ldays[0].strftime("%B %Y")) if _ldays[0] == _ldays[-1]
    else "%d to %d %s" % (_ldays[0].day, _ldays[-1].day, _ldays[-1].strftime("%B %Y")))))

# ------------------------------------------------------- human reference videos
HUMAN = field.human_videos()
if HUMAN:
    sys.path.insert(0, os.path.join(HERE, "human"))
    import gate as _gate  # noqa: E402
    emit("HumanRoomGate", _gate.OG, "the least match of the opening room that admits a capture", fmt="%.2f")
    _classes = {cls: [v for v in HUMAN if v["class"] == cls] for cls, _ in field.HUMAN_CLASSES}
    emit("NhumanVideos", len(HUMAN), "published videos of human players the paper reads")
    emit("NhumanSpeedruns", len(_classes["speedrun"]))
    emit("NhumanPlaythroughs", len(_classes["playthrough"]))

    def _vals(vs, key):
        return [v["milestones_min"][key] for v in vs if v["milestones_min"].get(key) is not None]

    for cls, tag in (("speedrun", "Speed"), ("playthrough", "Play")):
        vs = _classes[cls]
        if not vs:
            continue
        for key, name in (("map", "Map"), ("hermit", "Hermit"), ("fight", "Fight"), ("book", "Book")):
            vals = _vals(vs, key)
            if vals:
                emit(f"Lhuman{tag}{name}First", min(vals), f"{cls}: earliest minute of {key}", fmt="%.1f" if key == "map" else "%.0f")
                emit(f"Lhuman{tag}{name}Last", max(vals), f"{cls}: latest minute of {key}", fmt="%.1f" if key == "map" else "%.0f")
        steps = [v["steps_to_map"] for v in vs if v.get("steps_to_map") is not None]
        emit(f"Lhuman{tag}StepsMin", min(steps))
        emit(f"Lhuman{tag}StepsMax", max(steps))
        emit(f"Nhuman{tag}Compass", len(_vals(vs, "compass")), f"{cls} videos in which the compass is taken")
        emit(f"Nhuman{tag}Book", len(_vals(vs, "book")), f"{cls} videos that reach a book")
        done = [v["completion_min"] for v in vs if v.get("completion_min") is not None]
        if done:
            emit(f"Nhuman{tag}Complete", len(done), f"{cls} videos that finish the game")
            emit(f"Lhuman{tag}CompletionMin", min(done), fmt="%.0f")
            emit(f"Lhuman{tag}CompletionMax", max(done), fmt="%.0f")
    # every human reference holds a book, and the abstract gives the latest
    if any(v["milestones_min"].get("book") is None for v in HUMAN):
        sys.exit("the abstract says every human reference holds a book")
    emit("LhumanBookLast", max(v["milestones_min"]["book"] for v in HUMAN), "latest minute any human reference holds its first book", fmt="%.0f")
    if any(field.rungs_of(r)[field.DEFINITION.index("one of the\nfourteen")] is True for r in MODELS + LONG):
        sys.exit("the abstract says no model session holds a book")
_hour_rungs = {k for r in MODELS for k, v in enumerate(field.rungs_of(r)) if v is True}
_long_rungs = {k for r in LONG for k, v in enumerate(field.rungs_of(r)) if v is True}
if not _long_rungs <= _hour_rungs:
    sys.exit("the abstract says the four-hour sessions reach no milestone the hour sessions do not")
# per model: what three more hours add, for the models that played both budgets
def _union(rs):
    return {k for r in rs for k, v in enumerate(field.rungs_of(r)) if v is True}
_both_budgets = sorted({r["agent"] for r in LONG} & {r["agent"] for r in MODELS})
_gain = {a: _union([r for r in LONG if r["agent"] == a]) - _union([r for r in MODELS if r["agent"] == a]) for a in _both_budgets}
_gainers = {a: g for a, g in _gain.items() if g}
if len(_gainers) != 1 or sum(len(g) for g in _gainers.values()) != 1:
    sys.exit("the conclusion says four hours add one milestone to one of the models that played both budgets: %s" % _gainers)
emit("NbothBudgets", len(_both_budgets), "models with sessions that count at both budgets")

print("% generated by figures/numbers.py from catalog_snapshot.json and start.state")
print("% regenerate before editing any number in the paper")
for comment, body in lines:
    if comment:
        print(comment)
    print(body)
print("% --- derived strings used by the results table -------------------------")
print("% each row: agent & second & first & keys &"
      " screen-changing decisions/n & ratio\\ci{n} & in-going & map & end")
keep = ("agent", "played", "ttfa", "actions", "reads", "meaningful",
        "distinct_keys", "bigmap", "exit_secs", "level", "exp", "reason", "id")
rows_sorted = sorted(PLAY, key=lambda r: (fam(r["agent"]), -r["actions"]))
print("% rows below are sorted by vendor then actions")
counts = {}
for r in rows_sorted:
    k = round((r["meaningful"] or 0) * r["actions"])
    lo, p, hi = wil(k, r["actions"])
    name = r["agent"]
    counts[name] = counts.get(name, 0) + 1
    tag = f"{name}" if fam(name) == "random" or counts[name] == 1 else ""
    print(f"% {name:26s} n={r['actions']:4d} k={k:4d} ratio={p:.3f}"
          f"[{lo:.3f},{hi:.3f}] map={r.get('bigmap')} level={r.get('level')} "
          f"exp={r.get('exp')} ttfa={r['ttfa']} reason={r['reason']}")
print("% --- repetition of a label appears in the catalogue ----------------------------")
seen = {}
for r in PLAY:
    seen.setdefault(r["agent"], []).append(round((r["meaningful"] or 0) * r["actions"]) / r["actions"])
for a, vs in seen.items():
    if len(vs) > 1:
        print(f"% repeated {a}: {vs} spread={max(vs)-min(vs):.3f}")
