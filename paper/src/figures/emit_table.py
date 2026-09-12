"""Aggregate per-session runs into a leaderboard table from catalog data."""
import json, os, statistics as st

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import field


def wil(k, n, z=1.96):
    """Return observed proportion and Wilson interval."""
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return max(0.0, c - h), p, min(1.0, c + h)


def median(values):
    return st.median(values) if values else float("nan")


def display_agent(label):
    names = {"claude":"Claude", "gemini":"Gemini", "qwen":"Qwen", "grok":"Grok", "glm":"GLM", "gpt":"GPT", "vista":"Vista", "codex":"Codex", "random":"Random"}
    return "-".join(names.get(part.lower(), next((names[v] + part[len(v):] for v in names if part.lower().startswith(v)), part)) for part in label.split("-"))


def main():
    rows = field.load_runs()
    scored = field.played(rows)
    if not any(field.is_random(r["agent"]) for r in scored):
        scored = scored + field.random_rows(rows)
    groups = {}
    for r in scored:
        groups.setdefault(r["agent"], []).append(r)

    body = []
    for r in scored:
        rungs = field.rungs_of(r)
        body.append((r["agent"], (r["played"] or 0) / 60.0, r["reason"],
                     sum(1 for v in rungs if v is True), rungs, field.is_random(r["agent"])))
    # models by rungs reached and then by played time; the random floor last
    body.sort(key=lambda b: (b[5], -b[3], -b[1], b[0].lower()))
    mark = {True: r"\checkmark", False: r"$\circ$", None: "--"}
    lines = [
        r"\begin{tabular}{@{}lrrr*{8}{c}@{}}",
        r"\toprule",
        r"Model & played & ended & rungs & " + " & ".join(field.SHORT) + r" \\",
        r"\midrule",
    ]
    floor_started = False
    for agent, played, reason, count, rungs, is_random in body:
        if is_random and not floor_started:
            lines.append(r"\midrule")
            floor_started = True
        name = display_agent(agent).replace("_", "\\_").replace("--", "-{-}")
        lines.append(r"\texttt{%s} & %.0f & %s & %d/%d & %s \\"
                     % (name, played, reason, count, len(rungs),
                        " & ".join(mark[v] for v in rungs)))
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
