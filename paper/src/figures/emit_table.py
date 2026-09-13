"""Aggregate per-session runs into a leaderboard table from catalog data."""
import json, os, statistics as st
from labels import latex_agent

CAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalog_snapshot.json")


def wil(k, n, z=1.96):
    """Return observed proportion and Wilson interval."""
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return max(0.0, c - h), p, min(1.0, c + h)


def median(values):
    return st.median(values) if values else float("nan")


def main():
    rows = json.load(open(CAT, encoding="utf-8"))
    scored = [
        r for r in rows
        if r["budget"] == 1200 and (r["actions"] or 0) > 0
        and not r["agent"].startswith("probe-")
    ]
    groups = {}
    for r in scored:
        groups.setdefault(r["agent"], []).append(r)

    body = []
    # Ordered by the metric the table is read for, best first, with the random
    # baseline last: it is a floor rather than an entry.
    def rank(agent):
        g = groups[agent]
        num = sum(round(r["meaningful"] * r["actions"]) for r in g)
        den = sum(r["actions"] for r in g)
        return (agent.startswith("random"), -num / den)

    for agent in sorted(groups, key=rank):
        g = groups[agent]
        # aggregate count of screen-changing actions and actions
        num = sum(round(r["meaningful"] * r["actions"]) for r in g)
        den = sum(r["actions"] for r in g)
        lo, p, hi = wil(num, den)
        aps = median([r["actions"] / max(1.0, r["played"]) * 60 for r in g])
        ttfas = [r["ttfa"] for r in g if r.get("ttfa") is not None]
        ttfa = median(ttfas) if ttfas else float("nan")
        maps = sum(1 for r in g if r.get("bigmap") is True)
        maps_c = sum(1 for r in g if r.get("bigmap") is True and r.get("exit_secs") is not None)
        osc = median([r["oscillation"] for r in g])
        reads = sum(r["reads"] for r in g)
        n = len(g)
        g50 = median([r["gap_p50"] for r in g])
        g95 = median([r["gap_p95"] for r in g])
        body.append(
            (agent, n, den, num, p, lo, hi, aps, ttfa, g50, g95, osc,
             reads, maps, maps_c)
        )

    lines = [
        r"\begin{tabular}{@{}lrrrrrrr@{}}",
        r"\toprule",
        r"Agent & runs & actions & ratio [95\% CI] &"
        r" act/min & reads/act & think (s) & map \\",
        r"\midrule",
    ]
    best = max(r[4] for r in body if not r[0].startswith("random"))
    for agent, n, den, num, p, lo, hi, aps, ttfa, g50, g95, osc, reads, maps, maps_c in body:
        if agent.startswith("random"):
            lines.append(r"\midrule")
        ratio = ("\\textbf{%.3f}" if p == best else "%.3f") % p
        lines.append(
            "%s & %d & %d & %s [%.3f, %.3f] & %.1f & %.2f & %.1f & %d/%d \\\\"
            % (latex_agent(agent),
               n, den, ratio, lo, hi, aps, reads / den, g50, maps_c, maps)
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


if __name__ == "__main__":
    tex = main()
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tables",
                       "aggregate.tex")
    # define a command so main.tex can input it
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("%% generated from figures/catalog_snapshot.json by figures/emit_table.py\n")
        fh.write("\\newcommand{\\mktable}[0]{%\n")
        fh.write(tex + "\n")
        fh.write("}\n")
    print(tex)
