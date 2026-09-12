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

VENDORS = ("claude", "gpt", "gemini", "qwen", "glm", "grok")
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
rows = field.load_runs()
BUDGET = field.DEFAULT_BUDGET
ALL = field.played(rows)
never = [r for r in rows if (r["actions"] or 0) == 0]
other_budget = [r for r in rows if r["budget"] != BUDGET]
MODELS = [r for r in ALL if fam(r["agent"]) != "random"]
RANDOM = field.random_rows(rows)
if not MODELS or not RANDOM:
    sys.exit("no scored sessions or no random floor in the snapshot")
# "sessions" in the paper are model sessions; the random floor is reported
# on its own, so every count below runs over the models
PLAY = MODELS

emit("NsessionsTotal", len(raw), "catalogue entries in the snapshot")
emit("Nsessions", len(MODELS), "model sessions at the default budget that played")
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

best = max(PLAY, key=lambda r: r["meaningful"])
# Behavioural styles are read from sessions that played: a run the idle rule
# ended after a handful of keys has no ratio worth naming.
ACTIVE = [r for r in MODELS if r["actions"] >= 30]
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
read = [r for r in PLAY if r.get("level") is not None]
emit("Sread", len(read), "sessions whose character record was read")
emit("Sunread", len(PLAY) - len(read))
emit("SlevelKinds", len({r["level"] for r in read}), "distinct levels among read records")
emit("Slevel", st.mode([r["level"] for r in read]))
emit("SexpSum", sum(r["exp"] for r in read), "experience accumulated by every run")
emit("Sskills", st.mode([r["skills"] for r in read if r.get("skills") is not None]))
emit("SexpAny", sum(1 for r in read if r["exp"] > 0))
emit("SlevelTwo", sum(1 for r in read if r["level"] > 1))

_on_map = lambda r: field.rungs_of(r)[2] is True
crossed = [r for r in PLAY if _on_map(r)]
cross = [r for r in read if r.get("bigmap") is True]
fade = [r for r in PLAY if r.get("exit_secs") is not None]
both = [r for r in read if r.get("bigmap") is True and r.get("exit_secs") is not None]
emit("Smap", len(crossed), "sessions credited with the world map by the save the game wrote")
emit("SmapScreen", len(cross), "sessions whose screen latched the world-map signature")
emit("SmapSaveOnly", sum(1 for r in crossed if r.get("bigmap") is False),
     "crossings the save credits that the screen fingerprint missed")
emit("SmapWithScreen", sum(1 for r in crossed if r.get("bigmap") is not None),
     "crossings that also carry a fingerprint reading")
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
emit("SexitActs", st.median(r["exit_acts"] for r in fade), "median keys before a crossing", fmt="%.0f")
emit("SexitVendors", len({fam(r["agent"]) for r in fade}),
     "vendor families with a corroborated crossing")

# The game's own rungs, now that the field carries them.
def _known(key):
    return [r for r in PLAY if r.get(key) is not None]
emit("Sitem", sum(1 for r in _known("picked_item") if r["picked_item"]), "sessions that picked something up")
emit("SnoItem", sum(1 for r in _known("picked_item") if not r["picked_item"]), "sessions that never picked anything up")
emit("SitemKnown", len(_known("picked_item")))
emit("Scompass", sum(1 for r in _known("compass") if r["compass"]), "sessions holding the compass")
_holders = sorted((r for r in PLAY if r.get("compass")), key=lambda r: r["agent"])
lines.append(("% the sessions holding the compass, by label",
              "\\newcommand{\\ScompassLabel}{" + (" and ".join(
                  "\\texttt{%s}" % r["agent"] for r in _holders) if _holders else "none") + "}"))
if _holders and _holders[0].get("first_saved_at") is not None:
    emit("ScompassSaveMin", (_holders[0]["first_saved_at"] - _holders[0]["started"]) / 60.0,
         "minutes into the session when the compass holder's first save landed", fmt="%.0f")
    emit("ScompassExitActs", _holders[0].get("exit_acts") or 0,
         "actions the compass holder had taken at its crossing")
emit("ScompassKnown", len(_known("compass")))
emit("Ssaved", sum(1 for r in PLAY if r.get("saved_at") or r.get("slot_saved")), "sessions whose save the game wrote")
emit("Steam", sum(1 for r in _known("team_size") if r["team_size"] > 1), "sessions with a companion")
emit("SteamKnown", len(_known("team_size")))
emit("Sbooks", sum(1 for r in _known("books") if r["books"] > 0), "sessions holding a book")
emit("SbooksKnown", len(_known("books")))
emit("Sdone", sum(1 for r in PLAY if r.get("completion_secs") is not None), "sessions that completed")
_map = lambda r: field.rungs_of(r)[2] is True
emit("SleftNoItem", sum(1 for r in PLAY if _map(r) and r.get("picked_item") is False),
     "sessions that reached the map without the chest")
emit("SitemNoLeft", sum(1 for r in PLAY if r.get("picked_item") and not _map(r)),
     "sessions that searched the chest without reaching the map")
emit("Sboth", sum(1 for r in PLAY if r.get("picked_item") and _map(r)), "sessions that did both")
emit("QrandomRungs", max((field.rungs_reached(r) for r in RANDOM), default=0),
     "rungs the random floor reached")
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
emit("MkeyCodes", len(set(_keys.values())), "distinct scancodes behind them")


# ------------------------------------------------------------ replay patterns
# Read from the published keypress timelines of the scored sessions, committed
# in figures/timelines/<id>.json beside the snapshot. A mark's time is on the
# replay clock, so a minute here is the minute shown in the strip of the video.
TIMELINES = os.path.join(HERE, "timelines")
CONFIRM = ("enter", "space")


def emit_label(name, agent, note=""):
    lines.append((f"% {note}".rstrip() if note else "", f"\\newcommand{{\\{name}}}{{\\texttt{{{agent}}}}}"))


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
_slowest = max(_crossed, key=lambda r: r["exit_acts"])
emit("PexitActsMax", _slowest["exit_acts"], "actions the slowest crossing took")
emit_label("PexitActsMaxLabel", _slowest["agent"])
emit("PexitMinMax", _slowest["exit_secs"] / 60.0, "minute of that crossing", fmt="%.0f")
_noconfirm = [r for r in PLAY if not any((r.get("keys") or {}).get(k) for k in CONFIRM)]
emit("PnoConfirm", len(_noconfirm), "sessions that never pressed enter or space")
if len(_noconfirm) != 1 or _slowest["id"] != _noconfirm[0]["id"]:
    sys.exit("the prose calls the slowest crossing the one session that never confirmed; it no longer is")

# the session that crossed and then never entered a scene
_orbit = [r for r in _crossed if (r.get("scenes") or 0) <= 2]
_orb = max(_orbit, key=lambda r: r["actions"] - r["exit_acts"])
emit_label("PorbitLabel", _orb["agent"])
emit("PorbitExitMin", _orb["exit_secs"] / 60.0, "minute it crossed", fmt="%.0f")
emit("PorbitActs", _orb["actions"] - _orb["exit_acts"], "actions it took on the world map afterwards")
emit("PorbitMin", (_orb["played"] - _orb["exit_secs"]) / 60.0, "minutes it spent there", fmt="%.0f")

# breadth: scenes entered
_wide = max(PLAY, key=lambda r: r.get("scenes") or 0)
emit("PscenesMax", _wide["scenes"], "scenes the widest-ranging session entered")
emit_label("PscenesMaxLabel", _wide["agent"])
emit("PscenesThree", sum(1 for r in PLAY if (r.get("scenes") or 0) >= 3), "sessions that entered three or more scenes")

# the compass holder: the conversation and the compass reads
_holder = next(r for r in PLAY if r.get("compass"))
_ht = TL[_holder["id"]]
_hruns = confirm_runs(_ht)
_talk = max(_hruns, key=lambda c: sum(len(m["keys"]) for m in c))
emit("PtalkHolderPresses", sum(len(m["keys"]) for m in _talk), "confirm presses of its longest conversation")
_hmin = minutes(_ht, _talk[-1]) - minutes(_ht, _talk[0])
emit("PtalkHolderMin", _hmin, "minutes that conversation took", fmt="%.0f")
emit("PtalkHolderPace", 60.0 * _hmin / sum(len(m["keys"]) for m in _talk), "seconds a press", fmt="%.0f")


def opens_items(m):
    ks = [k for k, _ in m["keys"]]
    return any(ks[i:i + 4] == ["esc", "down", "down", "enter"] for i in range(len(ks) - 3))


emit("PholderMenuOpens", sum(1 for m in _ht["marks"] if opens_items(m)), "times it opened the item screen")
emit("PholderArrows", sum(v for k, v in (_holder.get("keys") or {}).items() if k in ARROWS), "arrow keys it pressed")

# Two sessions of the compass holder's model outside the reported field, named
# by id because the field does not carry them: the one whose replay shows the
# companion prompt answered, and the one that walked into the first fight.
RECRUIT_ID, BATTLE_ID = "40c05bfa3284", "0aaed52489f6"
_all = {r["id"]: r for r in field.load_runs(dedup=False)}
for _id in (RECRUIT_ID, BATTLE_ID):
    if _id not in _all or _all[_id]["agent"] != _holder["agent"]:
        sys.exit(f"session {_id} is not on record under the compass holder's model")
_rt = json.load(open(os.path.join(TIMELINES, RECRUIT_ID + ".json"), encoding="utf-8"))
_yes = [m for m in _rt["marks"] if any(k == "y" for k, _ in m["keys"])]
if len(_yes) != 1 or _all[RECRUIT_ID].get("team_size") is not None:
    sys.exit("the recruit session no longer reads as one answered prompt with no party reading")
emit("PrecruitMin", (_yes[0]["t"] * _rt["speed"] + (_all[RECRUIT_ID].get("ttfa") or 0)) / 60.0,
     "minute the companion prompt was answered", fmt="%.0f")
_bt = json.load(open(os.path.join(TIMELINES, BATTLE_ID + ".json"), encoding="utf-8"))
emit("PbattleMin", minutes(_bt, _bt["marks"][-1]), "minute of the last action of the session in the first fight", fmt="%.0f")
emit("PbattleActs", len(_bt["marks"]), "its actions")
if not _all[BATTLE_ID].get("compass"):
    sys.exit("the battle session is expected to hold the compass")

# the longest conversation held on the far side of the crossing by a session
# without the compass: the one that reached the hermit and ran out of time
_others = [r for r in PLAY if not r.get("compass") and r.get("exit_acts") is not None]
_best = None
for r in _others:
    for c in confirm_runs(TL[r["id"]]):
        if c[0]["n"] <= r["exit_acts"]:
            continue
        n = sum(len(m["keys"]) for m in c)
        if _best is None or n > _best[0]:
            _best = (n, r, c)
_n, _lr, _lc = _best
_lt = TL[_lr["id"]]
emit_label("PtalkLongLabel", _lr["agent"])
emit("PtalkLongPresses", _n, "confirm presses of the longest conversation without the compass")
_lmin = minutes(_lt, _lc[-1]) - minutes(_lt, _lc[0])
emit("PtalkLongMin", _lmin, "minutes it took", fmt="%.0f")
emit("PtalkLongPace", 60.0 * _lmin / _n, "seconds a press", fmt="%.0f")
emit("PtalkLongEndMin", minutes(_lt, _lc[-1]), "minute it ended", fmt="%.0f")
emit("PtalkLongLeftMin", _lr["budget"] / 60.0 - minutes(_lt, _lc[-1]), "minutes of budget left then", fmt="%.0f")

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
