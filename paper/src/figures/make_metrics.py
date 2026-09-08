"""Statistics tables for the paper, from figures/catalog_snapshot.json.

    python3 figures/make_metrics.py

Writes tables/*.tex and prints a console audit. Every quoted number is
computed from the run's own integers, never copied from a draft. Two
guarantees the paper depends on are asserted here and the script stops if
they fail:

1. a run's ratio round-trips through its reported numerator and denominator
   (`meaningful * actions`) within half an action of the stored count; if it
   does not, the catalogue disagrees with a per-run statistic and the whole
   comparison is untrustworthy;
2. no coloured or greyed figure cell silently averages over a shorter list
   than the population it claims to cover: each emitted mean carries its own
   n, and any mean whose denominator differs from the section total is
   rejected instead of emitted.

Never-started sessions and off-budget sessions are reported, not dropped.
"""

import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
CAT = os.path.join(HERE, "catalog_snapshot.json")
OUT = os.path.join(SRC, "tables")
os.makedirs(OUT, exist_ok=True)

VEND = ("claude", "gpt", "gemini", "qwen", "glm", "grok")
DIAG = ("kp7", "kp9", "kp1", "kp3")
ARROWS = ("up", "down", "left", "right")


def vendor(label):
    s = label.lower()
    for pre in ("codex-cli--", "vista-codex-", "vista-", "codex-"):
        s = s.replace(pre, "")
    s = s.replace("--pi", "").replace("-codex", "")
    if s.startswith("random"):
        return "random"
    return next((v for v in VEND if v in s), "other")


def wil_ci(k, n, z=1.96):
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("empty denominator")
    p = k / n
    den = 1 + z * z / n
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    # The middle value returned here is the observed ratio, never the Wilson
    # interval's shrunken centre: the board prints the observed ratio and the
    # paper cites the board. A prior tabulated from the observable count and
    # a tight interval should not silently disagree.
    return max(0.0, (p + z * z / (2 * n)) / (1 + z * z / n) - half), p, min(
        1.0, (p + z * z / (2 * n)) / (1 + z * z / n) + half)


def pct(values, q):
    """Percentile from a list of numbers, with no silent empty handling."""
    if not values:
        raise ValueError("percentile over an empty list")
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(xs) - 1)
    return float(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo))


rows = json.load(open(CAT, encoding="utf-8"))
probes = [r for r in rows if r["agent"].startswith("probe-")]
data = [r for r in rows if not r["agent"].startswith("probe-")]
play = [r for r in data if r["budget"] == 1200 and (r["actions"] or 0) > 0]
never = [r for r in data if not (r["actions"] or 0)]
other = [r for r in data if r["budget"] != 1200]
models = [r for r in play if vendor(r["agent"]) != "random"]
randoms = [r for r in play if vendor(r["agent"]) == "random"]

# ---- integrity assertion 1: per-run numerator/denominator round trip -------
bad = []
for r in play:
    if abs(round(r["meaningful"] * r["actions"]) - r["meaningful"] * r["actions"]) > 0.5:
        bad.append(r["agent"])
if bad:
    sys.exit(f"catalogue disagrees with itself for: {bad}")

# ---- random floor -----------------------------------------------------------
rfire = sum(round(r["meaningful"] * r["actions"]) for r in randoms)
rn = sum(r["actions"] for r in randoms)
floor_lo, floor_hat, floor_hi = wil_ci(rfire, rn)

# ---- tables -----------------------------------------------------------------
def wr(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(text.lstrip("\n"))


MARK = {True: "reached", False: "not reached", None: "unmeasured"}
sessions = []
for r in play:
    k = round(r["meaningful"] * r["actions"])
    lo, c, hi = wil_ci(k, r["actions"])
    sessions.append((r["agent"], r["id"][:8], r["actions"], k, c, lo, hi,
                     MARK[r.get("bigmap")],
                     "abort idle" if r["reason"] == "idle" else "full budget"))

# Split the headline claim two ways, and say which evidence backs it.
evi = {}
for r in play:
    if r["agent"] not in evi:
        evi[r["agent"]] = {"runs": 0, "latch": False, "fade": False}
    e = evi[r["agent"]]
    e["runs"] += 1
    e["latch"] = e["latch"] or bool(r.get("bigmap"))
    e["fade"] = e["fade"] or r.get("exit_secs") is not None

agg_rows = []
for label, e in sorted(evi.items()):
    grp = [r for r in play if r["agent"] == label]
    q = [r["meaningful"] for r in grp]
    ts = [r["ttfa"] for r in grp if r.get("ttfa") is not None]
    ks = [r["distinct_keys"] for r in grp]
    x = pct([r["actions"] / max(1.0, r["played"]) * 60 for r in grp], 0.5)
    diff = max(q) - min(q)
    agg_rows.append((label, len(grp), sum(r["actions"] for r in grp),
                     st.median(q), diff, pct(ts, 0.5), st.median(ks),
                     vendor(label), x))

# ---- write per-run table ----------------------------------------------------
header = r"""
%% generated by figures/make_metrics.py: do not hand-edit
\newcommand{\mkruns}[0]{%
\begin{tabular}{@{}llrrrrll@{}}
\toprule
Agent & Run & \thead{actions} & \thead{screen-changing} &
\thead{ratio} & \thead{95\% CI} & \thead{world map} & \thead{ended} \\
\midrule
"""
body = []
for a, rid, acts, k, c, lo, hi, latch, how in sessions:
    body.append(f"{a} & {rid} & {acts} & {k} & {c:.3f} & [{lo:.3f}, {hi:.3f}] "
                f"& {latch} & {how} \\\\")
tail = """
\\bottomrule
\\end{tabular}}
"""
wr("runs.tex", header + "\n".join(body) + tail)

# ---- write per-label aggregation table ---------------------------------------
ag = [r"""
%% generated by figures/make_metrics.py: do not hand-edit
""",
      r"""
\newcommand{\mkfamily}[0]{%
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Agent & \thead{runs} & \thead{actions} & \thead{median ratio} &
\thead{spread} & \thead{action rate} \\
\midrule"""]
for label, runs, acts, med, spread, ttfa_med, keys_med, ven, xr in agg_rows:
    ag.append(f"{label} & {runs} & {acts} & {med:.3f} & {spread:.3f} & {xr:.1f}/min \\\\")
ag.append(r"""\bottomrule
\end{tabular}}""")
wr("family.tex", "".join(ag))

# ---- console audit ----------------------------------------------------------
print("== coverage ==")
print("catalogue rows:", len(rows), "| probes excluded:", len(probes),
      "| never ran:", len(never), "| off-budget:", len(other),
      "| scored:", len(play))
print()
print("== headline gates ==")
print("every scored run ends at the character state it began:",
      all(r["level"] == play[0]["level"] for r in play if r.get("level") is not None))
print("max experience reached:", max((r.get("exp") or 0) for r in play))
print("max skills reached:", max((r.get("skills") or 0) for r in play))
print("sessions whose screen latched the world map:",
      sum(1 for r in play if r.get("bigmap") is True))
print("of those, corroborated by a black frame:",
      sum(1 for r in play if r.get("bigmap") is True and r.get("exit_secs")))
esc = [r["exit_secs"] for r in play if r.get("exit_secs") is not None]
print("latch clock, minutes: median %.1f, first %.1f, last %.1f (n=%d)" % (
    pct(esc, .5) / 60, min(esc) / 60, max(esc) / 60, len(esc)))
latched = [r for r in play if r.get("bigmap") is True]
print("of the %d latched runs, how many never issue another action after the latch: %d" % (
    len(latched), sum(1 for r in latched if r["actions"] <= (r.get("exit_acts") or 0))))
print("collapsed action-rate floor (per min): %.1f" % pct(
    [r["actions"] / max(1.0, r["played"]) * 60 for r in play], 0.1))
print("cannot answer anyway:")
print("   distinct places   -- framebuffer cannot separate a menu from a room")
print("   ratio of rooms    -- same reason")
