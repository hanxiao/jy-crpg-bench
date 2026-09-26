"""The filters: every model session (hour and four-hour) along the chain of
steps a playthrough passes in order.

    python filters.py

Left, the share of all model sessions that passed each step; the bar labels
use that same total denominator. Right, among sessions that passed the step
before, the minutes to passing this one (filled) or to the last key (open).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import field  # noqa: E402

INK = "#1c1c1e"
plt.rcParams.update({"font.family": "serif", "font.size": 7.5})


def rows():
    return [r for r in field.played(field.load_runs(dedup=False)) if not field.is_random(r["agent"])] + field.load_long()


def figure_filters():
    session_rows = rows()
    ch = field.chain(session_rows)
    n = len(session_rows)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 1.55), gridspec_kw={"width_ratios": [1.2, 1.2], "wspace": 0.28})
    xs = list(range(len(ch)))
    share = [len(s["passed"]) / n for s in ch]
    a.bar(xs, share, width=0.62, color="#d6d9df", edgecolor=INK, linewidth=0.6)
    for x, s, v in zip(xs, ch, share):
        a.text(x, v + 0.03, "%d/%d" % (len(s["passed"]), n), ha="center", fontsize=6.5, color=INK)
    a.set_xticks(xs)
    a.set_xticklabels([s["step"] for s in ch], fontsize=6.2)
    a.set_ylim(0, 1.0)
    a.set_ylabel("share of %d sessions" % n, color=INK)
    b.set_yscale("log")
    for x, s in zip(xs, ch):
        pd = [max(d, 0.5) for _, d in s["passed"]]
        sd = [max(d, 0.5) for _, d in s["stuck"]]
        b.scatter([x - 0.12] * len(pd), pd, s=9, color=INK, zorder=3)
        b.scatter([x + 0.12] * len(sd), sd, s=9, facecolors="white", edgecolors=INK, linewidths=0.6, zorder=3)
    b.axhline(30, color="#8a8d93", lw=0.6, ls=(0, (2, 2)))
    # the session with the most milestones, traced through every step it reached
    best = max(session_rows, key=lambda r: (field.rungs_reached(r), r["id"]))
    tx, ty = [], []
    for x, s in zip(xs, ch):
        for off, pts in ((-0.12, s["passed"]), (0.12, s["stuck"])):
            for r, d in pts:
                if r["id"] == best["id"]:
                    tx.append(x + off)
                    ty.append(max(d, 0.5))
    b.plot(tx, ty, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=2)
    b.text(tx[-1] - 0.05, ty[-1] * 1.45, best["agent"], fontsize=6, color=INK, ha="right", va="bottom")
    b.set_xticks(list(xs))
    b.set_xticklabels([s["step"] for s in ch], fontsize=6.2)
    b.set_ylabel("minutes since the step before", color=INK)
    b.scatter([], [], s=9, color=INK, label="passed")
    b.scatter([], [], s=9, facecolors="none", edgecolors=INK, linewidths=0.6, label="not passed")
    b.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=6.5, frameon=False, handletextpad=0.2)
    for ax in (a, b):
        ax.tick_params(colors=INK, labelsize=6.5)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    return fig


def main():
    fig = figure_filters()
    fig.savefig(os.path.join(HERE, "filters.pdf"), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote filters.pdf")


if __name__ == "__main__":
    main()
