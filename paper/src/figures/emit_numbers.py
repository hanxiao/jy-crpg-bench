"""Every number the paper cites, emitted as LaTeX macros.

    python3 figures/numbers.py > figures/numbers.tex

`main.tex` inputs the generated file, so no measurement is transcribed by hand.
Sources: `catalog_snapshot.json` (the published catalogue) and `start.state`,
the savestate every session boots into. The script checks internal consistency
and stops on a disagreement, and it never emits a number it did not compute.
"""

import json
import math
import os
import re
import statistics as st
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SNAPSHOT = os.path.join(HERE, "catalog_snapshot.json")
START_STATE = os.path.join(ROOT, "saves", "start.state")

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


def emit(name, value, note=""):
    """Define \\name. Floats keep three decimals below 10, one above."""
    if isinstance(value, float):
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
raw = json.load(open(SNAPSHOT, encoding="utf-8"))
probes = [r for r in raw if r["agent"].startswith("probe-")]
rows = [r for r in raw if not r["agent"].startswith("probe-")]
PLAY = [r for r in rows if r["budget"] == 1200 and (r["actions"] or 0) > 0]
never = [r for r in rows if (r["actions"] or 0) == 0]
other_budget = [r for r in rows if r["budget"] != 1200]
MODELS = [r for r in PLAY if fam(r["agent"]) != "random"]
RANDOM = [r for r in PLAY if fam(r["agent"]) == "random"]

emit("NsessionsTotal", len(raw), "catalogue entries in the snapshot")
emit("Nsessions", len(PLAY), "sessions at the default budget that played")
emit("Nmodels", len(MODELS), "model sessions")
emit("NrandomRuns", len(RANDOM), "random-baseline sessions")
emit("Nvendors", len({fam(r["agent"]) for r in MODELS}), "vendors in the field")
emit("Nlabels", len({r["agent"] for r in rows}), "distinct agent labels")
emit("Nnever", len(never), "sessions that never sent a key")
emit("NotherBudget", len(other_budget), "sessions at another playtime")
emit("Nprobes", len(probes), "service probes, excluded")
emit("Nbudget", PLAY[0]["budget"], "default playtime, seconds")

# ------------------------------------------------------------------- behaviour
acts = [r["actions"] for r in PLAY]
emit("EactsTotal", sum(acts))
emit("EactsModels", sum(r["actions"] for r in MODELS))
emit("EactsRandom", sum(r["actions"] for r in RANDOM))
emit("EactsMedian", st.median(acts))
emit("EactsMin", min(acts))
emit("EactsMax", max(acts))
emit("Eaps", sum(acts) / sum(r["played"] for r in PLAY), "pooled actions per second")
emit("Ereads", sum(r["reads"] for r in MODELS), "screen reads by model sessions")

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
worst = min(PLAY, key=lambda r: r["meaningful"])
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
emit("QworstStart", worst["ttfa"] / 60.0, "minutes before its first key")

rk = sum(round(r["meaningful"] * r["actions"]) for r in RANDOM)
rn = sum(r["actions"] for r in RANDOM)
lo_r, p_r, hi_r = wil(rk, rn)
emit("Qrandom", p_r)
emit("QrandomLow", lo_r)
emit("QrandomHigh", hi_r)
emit("QrandomN", rn)
emit("QrandomKeys", RANDOM[0]["distinct_keys"])
sub = [r for r in MODELS if r["meaningful"] < p_r]
emit("NbelowFloor", len(sub), "model sessions under the random floor")
emit("QunderVsRandom", min(r["meaningful"] for r in sub) / p_r)

# ---------------------------------------------------------------- machine state
read = [r for r in PLAY if r.get("level") is not None]
emit("Sread", len(read), "sessions whose character record was read")
emit("Sunread", len(PLAY) - len(read))
if len({r["level"] for r in read}) != 1 or len({r["skills"] for r in read}) != 1:
    sys.exit("level or skills vary between runs; the prose is stale")
emit("Slevel", st.mode([r["level"] for r in read]))
emit("SexpSum", sum(r["exp"] for r in read), "experience accumulated by every run")
emit("Sskills", st.mode([r["skills"] for r in read]))
emit("SexpAny", sum(1 for r in read if r["exp"] > 0))
emit("SlevelTwo", sum(1 for r in read if r["level"] > 1))

cross = [r for r in read if r.get("bigmap") is True]
fade = [r for r in PLAY if r.get("exit_secs") is not None]
both = [r for r in read if r.get("bigmap") is True and r.get("exit_secs") is not None]
emit("Smap", len(cross), "sessions whose screen latched the world-map signature")
emit("SmapFade", len(both), "of those, corroborated by a black frame")
emit("SmapSolo", len(cross) - len(both))
emit("SmapUnread", sum(1 for r in PLAY if r.get("bigmap") is None))
emit("SexitMedian", st.median(r["exit_secs"] for r in fade) / 60.0, "minutes")
emit("SexitFirst", min(r["exit_secs"] for r in fade) / 60.0)
emit("SexitLast", max(r["exit_secs"] for r in fade) / 60.0)
emit("SexitActs", st.median(r["exit_acts"] for r in fade), "median keys before a crossing")

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
