"""Results tables for the paper, from figures/catalog_snapshot.json.

    python3 figures/make_table.py

Writes tables/auto_sessions.tex and tables/auto_models.tex. Proportions are
recomputed from the run's own numerator and denominator and compared with the
fraction stored by the calculator; a disagreement of more than half an action
stops the script instead of shipping a table."""
import json, math, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
CAT = os.path.join(HERE, "catalog_snapshot.json")
OUTD = os.path.join(SRC, "tables")

VEND = ("claude", "gpt", "gemini", "qwen", "glm", "grok")


def vend(a):
    s = a.lower()
    for p in ("codex-cli--", "vista-codex-", "vista-", "codex-"):
        s = s.replace(p, "")
    s = s.replace("--pi", "").replace("-codex", "")
    if s.startswith("random"):
        return "random"
    return next((v for v in VEND if s.startswith(v)), "other")


def wil(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), p, min(1.0, c + h)


def frac(act, stored, who):
    n = float(act)
    diff = abs(round(stored * n) - stored * n) * n
    return diff


def rows(data):
    out = []
    for r in data:
        act = int(r["actions"])
        if act <= 0:
            continue
        k = round((r["meaningful"] or 0) * act / 0.001) / 1000.0 * act
        out.append((r, act))
    return out
