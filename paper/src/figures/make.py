"""Figures for the paper.

Every number comes from `catalog_snapshot.json`, a copy of the published
catalogue (gs://jy-crpg-bench-runs/catalog.json) taken on 7 September 2026.
Refresh the snapshot and rerun to regenerate all four figures:

    python3 figures/make.py

Labels are placed with a collision check: after drawing, every text object's
rendered bounding box is compared against every other text and every marker,
and the run fails loudly if anything still overlaps. Sixty-second service
probes and sessions that never sent a key are reported in prose, not plotted.
"""

import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 200,
})

INK = "#1c1c1e"
GRAY = "#9c9c9f"
ACCENT = "#2f6fb0"
GRID = "#e9eaec"

FAMILY = {              # one accent colour, used where machine state confirms an arrival
    "Claude": (INK, "o", 5.0),
    "GPT": (ACCENT, "s", 4.6),
    "Gemini": ("#3f3f42", "^", 5.2),
    "Qwen": ("#6a6a6e", "v", 5.2),
    "GLM": ("#505054", "D", 4.4),
    "Grok": ("#38383c", "P", 4.8),
    "Random": (GRAY, "X", 5.6),
}
ORDER = ["Claude", "GPT", "Gemini", "Qwen", "GLM", "Grok", "Random"]


def load():
    with open(os.path.join(HERE, "catalog_snapshot.json")) as fh:
        rows = json.load(fh)
    out = []
    for r in rows:
        name = r["agent"]
        if name.startswith("probe-"):
            continue
        low = name.lower()
        for pre in ("codex-cli--", "vista-codex-", "vista-", "codex-"):
            low = low.replace(pre, "")
        low = low.replace("--pi", "")
        r["family"] = ("Random" if low.startswith("random")
                      else next((f for f in ORDER if low.startswith(f.lower())), "Other"))
        r["short"] = low
        out.append(r)
    return out


def wilson(k, n, z=1.96):
    if n <= 0:
        return 0.0, 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, ctr - half), p, min(1.0, ctr + half)


RUNS = load()
PLAY = sorted([r for r in RUNS if r["budget"] == 1200 and (r["actions"] or 0) > 0],
              key=lambda r: (ORDER.index(r["family"]) if r["family"] in ORDER else 9,
                             -(r["actions"] or 0)))
DEFINITION = ("acted", "screen\nresponded", "picked\nsomething up",
              "reached\nworld map", "gained\nexperience", "reached\nlevel 2")


def rungs_of(row):
    """(reached, known) for each rung, exactly as the published ladder computes it."""
    known = [
        True,
        row.get("meaningful") is not None,
        row.get("picked_item") is not None,
        row.get("bigmap") is not None,
        row.get("exp") is not None,
        row.get("level") is not None,
    ]
    got = [
        (row.get("key_events") if row.get("key_events") is not None
         else row["actions"]) > 0,
        (row.get("meaningful") or 0) > 0,
        bool(row.get("picked_item")),
        bool(row.get("bigmap")),
        (row.get("exp") or 0) > 0,
        (row.get("level") or 0) > 1,
    ]
    return [(g if k else None) for g, k in zip(got, known)]


def box_at(ax, x, y, size_pt, pad=1.5):
    """Display-unit box for a marker of `size_pt` points centred on data (x, y).

    PathCollection.get_window_extent returns the bbox of the whole collection,
    which for a one-point scatter is not what a reader sees. Markers are sized
    in points, so the visible box is exact this way.
    """
    cx, cy = ax.transData.transform((x, y))
    half = size_pt / 2.0 + pad
    from matplotlib.transforms import Bbox
    return Bbox.from_bounds(cx - half, cy - half, 2 * half, 2 * half)


def _ext(obj, rend, pad=1.5):
    """Bounding box in display units, grown by `pad` points on every side."""
    bb = obj.get_window_extent(renderer=rend)
    if bb.width <= 0 or bb.height <= 0:
        return bb
    return bb.expanded(1 + 2 * pad / bb.width, 1 + 2 * pad / bb.height)


def check_overlaps(fig, ax, texts, points=(), name=""):
    """Fail if any two texts overlap, or a text overlaps a data marker."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    boxes = [(t.get_text(), _ext(t, rend)) for t in texts]
    bad = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][1].overlaps(boxes[j][1]):
                bad.append(f"{boxes[i][0]!r} vs {boxes[j][0]!r}")
    for label, bb in boxes:
        for p in points:
            if bb.overlaps(p):
                bad.append(f"{label!r} overlaps a marker")
    if bad:
        shown = bad[:12]
        more = f"\n  ... and {len(bad) - 12} more" if len(bad) > 12 else ""
        sys.exit(f"{name}: {len(bad)} overlap(s):\n  " + "\n  ".join(shown) + more)


# ------------------------------------------------------- Fig: milestone ladder
def figure_ladder():
    fams = [f for f in ORDER if any(r["family"] == f for r in PLAY)]
    fig, ax = plt.subplots(figsize=(5.3, 0.30 * len(fams) + 1.0))
    notes, boxes = [], []
    for row, fam in enumerate(fams):
        frows = [r for r in PLAY if r["family"] == fam]
        for col in range(len(DEFINITION)):
            states = [rungs_of(r)[col] for r in frows]
            hit = sum(1 for s in states if s is True)
            known = sum(1 for s in states if s is not None)
            if known == 0:
                sval = 42.0
                ax.scatter(col, row, s=sval, facecolor="#e4e4e6",
                          edgecolors="#d0d0d3", linewidths=0.9, zorder=3)
            elif hit:
                sval = 62.0
                ax.scatter(col, row, s=sval, marker="o",
                          color=ACCENT if col >= 3 else INK, zorder=3)
            else:
                sval = 46.0
                ax.scatter(col, row, s=sval, marker="o", facecolors="white",
                          edgecolors="#8c8c90", linewidths=1.1, zorder=3)
            cell_pt = sval ** 0.5
            boxes.append(box_at(ax, col, row, cell_pt))
            if known > 1:
                notes.append(ax.annotate(f"{hit}/{known}", (col, row),
                                         xytext=(7, 0), textcoords="offset points",
                                         ha="left", va="center", fontsize=5.9,
                                         color="#67676b"))
    ax.axvspan(2.5, 3.5, color="#eef3f9", zorder=1)
    ax.axvspan(3.5, len(DEFINITION) - 0.5, color="#f5f5f6", zorder=1)
    ax.set_yticks(range(len(fams)), fams, fontsize=8)
    ax.set_xticks(range(len(DEFINITION)), DEFINITION, fontsize=7)
    ax.set_xlim(-0.55, len(DEFINITION) - 0.35)
    ax.set_ylim(len(fams) - 0.42, -0.9)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(length=0)
    handles = [
        Line2D([], [], marker="o", ls="", color=INK, ms=7, label="reached"),
        Line2D([], [], marker="o", ls="", markerfacecolor="white",
               markeredgecolor="#8c8c90", ms=7, label="not reached"),
        Line2D([], [], marker="o", ls="", markerfacecolor="#e4e4e6",
               markeredgecolor="#d0d0d3", ms=7, label="unmeasured"),
    ]
    leg = ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.42, 1.0),
                   fontsize=7, frameon=False, ncol=3, handletextpad=0.2,
                   columnspacing=1.1)
    fig.tight_layout(pad=0.3)
    check_overlaps(fig, ax, list(ax.get_xticklabels()) + list(ax.get_yticklabels())
                   + notes + list(leg.get_texts()), boxes, name="ladder")
    fig.savefig(os.path.join(HERE, "ladder.pdf"), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


# ------------------------------------------------ Fig: quality versus throughput
def place_labels(fig, ax, anchors, obstacles=(), fontsize=6.8, name="labels"):
    """Attach each label to its point at the first collision-free offset.

    Offsets are searched outward from the point, in points. A leader line is
    drawn when the text has to sit far from its own point. Unplaceable text is
    an error, not a silent drop.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    boxes = [b for b in obstacles if b.width > 0 and b.height > 0]
    placed = []
    offs = [(x, y) for r in range(1, 11) for x in (5 * r, -5 * r)
            for y in (0, 4 * r, -4 * r, 8 * r, -8 * r)]
    for label, (x, y) in anchors:
        for dx, dy in offs:
            txt = ax.annotate(label, (x, y), xytext=(dx, dy),
                              textcoords="offset points",
                              ha="left" if dx >= 0 else "right", va="center",
                              fontsize=fontsize, color="#3f3f43", zorder=5,
                              annotation_clip=False)
            bb = _ext(txt, rend, pad=1.0)
            clash = any(bb.overlaps(b) for b in boxes) or any(
                bb.overlaps(_ext(o, rend)) for o in placed)
            if clash:
                txt.remove()
                continue
            if abs(dx) + abs(dy) > 22:
                ax.annotate("", xy=(x, y), xytext=(dx * 0.55, dy * 0.55),
                           textcoords="offset points", zorder=4,
                           arrowprops=dict(arrowstyle="-", lw=0.4, color="#a9adb3",
                                           shrinkA=0, shrinkB=2))
            placed.append(txt)
            break
        else:
            sys.exit(f"{name}: no free position for {label!r}")
    return placed


# Runs worth naming in Figure 4, chosen for what they show rather than their rank:
# the best quality with a machine-confirmed crossing, the largest number of
# meaningful actions, the quietest deliberate run, and the run whose screen
# almost never changes.
LABELLED = {
    "gpt-5.6-sol (pi)": ["d1468967"],
    "claude-fable-5-1": ["468e2872"],
    "Qwen3.8-27B": ["fda3f4f3"],
    "gemini-3.7-flash": ["f22647a1"],
    "claude-sonnet-5": ["5c1dbe3b"],
    "random": ["72cd8319", "09a2c7a9"],
}


def figure_pareto():
    pts = []
    for r in PLAY:
        n = r["actions"]
        k = round((r["meaningful"] or 0) * n)
        lo, p, hi = wilson(k, n)
        pts.append((r, k, p, lo, hi))
    front = sorted([q for q in pts if not any(o[1] > q[1] and o[2] > q[2] for o in pts)],
                   key=lambda q: q[1])
    fig, ax = plt.subplots(figsize=(5.1, 3.42))
    ax.plot([q[1] for q in front], [q[2] for q in front], ls=(0, (4, 3)),
            lw=0.9, color="#b6bac0", zorder=1)
    drawn = []
    for r, k, p, lo, hi in pts:
        col, mk, ms = FAMILY[r["family"]]
        ax.errorbar(k, p, yerr=[[p - lo], [hi - p]], fmt=mk, ms=ms, color=col,
                    ecolor="#c6c8cc", elinewidth=0.8, capsize=1.8, zorder=3)
        drawn.append(ax.plot(k, p)[0])
    anchors = []
    for lab, ids in LABELLED.items():
        coords = []
        for rid in ids:
            r = next((q for q in PLAY if q["id"].startswith(rid)), None)
            if r is None:
                sys.exit(f"figure_pareto: session {rid} is not in the snapshot")
            coords.append((round((r["meaningful"] or 0) * r["actions"]),
                           r["meaningful"]))
        anchors.append((lab, max(coords, key=lambda c: c[0])))
    handles = [Line2D([], [], ls="", marker=mk, color=col, ms=5.4, label=fam)
               for fam, (col, mk, _ms) in FAMILY.items()
               if fam != "Random"]
    handles.append(Line2D([], [], ls="", marker="X", color=GRAY, ms=5.4,
                          label="Random"))
    leg = ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.005),
                   fontsize=6.8, frameon=False, handletextpad=0.15, ncol=4,
                   columnspacing=0.9, labelspacing=0.3)
    marker_boxes = [box_at(ax, k, p, FAMILY[r["family"]][2])
                    for r, k, p, _lo, _hi in pts]
    labels = place_labels(fig, ax, anchors, obstacles=marker_boxes, name="pareto")
    ax.set_xlabel("meaningful actions in the run")
    ax.set_ylabel("meaningful-step ratio")
    ax.set_xlim(0, 345)
    ax.set_ylim(0, 1.0)
    ax.tick_params(labelsize=7.5)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=0.3)
    check_overlaps(fig, ax, list(leg.get_texts()) + labels, marker_boxes, name="pareto")
    fig.savefig(os.path.join(HERE, "pareto.pdf"), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


# -------------------------------------------- Fig: where the twenty minutes went
def figure_horizon():
    fig, ax = plt.subplots(figsize=(5.4, 0.185 * len(PLAY) + 1.05))
    texts = []
    for row, r in enumerate(PLAY):
        span = max(r["played"] or 0, 6)
        exit_at = r.get("exit_secs")
        ax.barh(row, span, left=0, height=0.55, color="#e2e5e9", zorder=2)
        if exit_at is not None:
            ax.barh(row, max(span - exit_at, 2), left=exit_at, height=0.55,
                   color=ACCENT, zorder=3)
            texts.append(ax.annotate(f"act {r['exit_acts']}", (exit_at, row),
                                     xytext=(0, 7.5), textcoords="offset points",
                                     ha="left", fontsize=6.1, color="#33506e"))
        elif r.get("bigmap") is True:
            ax.barh(row, span, left=0, height=0.55, color="none", zorder=3,
                   hatch="///", edgecolor=ACCENT, linewidth=0.0)
        if span < 1180:
            texts.append(ax.annotate("idle stop", (span, row), xytext=(4, 0),
                                     textcoords="offset points", fontsize=6.1,
                                     va="center", color="#8b8b8f"))
    ax.axvline(1200, lw=0.9, color="#8f8f93", zorder=4)
    ax.annotate("budget", (1200, -0.78), xytext=(-3, 0), textcoords="offset points",
                ha="right", fontsize=6.4, color="#6d6d70")
    ax.set_yticks(range(len(PLAY)), [r["short"] for r in PLAY], fontsize=6.6)
    ax.set_xlabel("seconds of play")
    ax.set_xlim(0, 1290)
    ax.set_ylim(len(PLAY) - 0.45, -0.95)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=7.5)
    handles = [
        Line2D([], [], ls="", marker="s", color="#e2e5e9", ms=7,
               label="actor in the opening scene"),
        Line2D([], [], ls="", marker="s", color=ACCENT, ms=7,
               label="actor on the world map"),
        Line2D([], [], ls="", marker="s", mfc="white", markeredgecolor=ACCENT,
               ms=7, label="world map, no fade seen"),
    ]
    leg = ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.46, 1.0),
                   fontsize=6.5, frameon=False, ncol=3, handletextpad=0.2,
                   columnspacing=0.8)
    fig.tight_layout(pad=0.3)
    check_overlaps(fig, ax, texts + list(ax.get_yticklabels()) + list(leg.get_texts()),
                   name="horizon")
    fig.savefig(os.path.join(HERE, "horizon.pdf"), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


# ------------------------------------------ Fig (appendix): behavioural panels
def figure_behaviour():
    fig, axes = plt.subplots(1, 3, figsize=(6.0, 0.16 * len(PLAY) + 0.9), sharey=True)
    y = list(range(len(PLAY)))
    panels = [
        ("screen reads per action", lambda r: r["reads"] / r["actions"]),
        ("think time p50 (s)", lambda r: r["gap_p50"] or 0),
        ("actions per minute", lambda r: r["actions"] / (r["played"] / 60)),
    ]
    for ax, (title, fn) in zip(axes, panels):
        ax.barh(y, [fn(r) for r in PLAY],
               color=[GRAY if r["family"] == "Random" else INK for r in PLAY],
               height=0.6)
        ax.set_title(title, fontsize=7.5)
        ax.invert_yaxis()
        ax.tick_params(axis="x", labelsize=7)
        ax.grid(axis="x", color=GRID, lw=0.5)
        ax.set_axisbelow(True)
    axes[0].set_yticks(y, [r["short"] for r in PLAY], fontsize=6.6)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(HERE, "behaviour.pdf"), bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


if __name__ == "__main__":
    figure_ladder()
    figure_pareto()
    figure_horizon()
    figure_behaviour()
    cross = [r for r in PLAY if r.get("exit_secs") is not None]
    print(f"{len(RUNS)} sessions, {len(PLAY)} at the 20-minute budget")
    print(f"world map by fingerprint: {sum(1 for r in PLAY if r.get('bigmap') is True)}"
          f" | corroborated by a black frame: {len(cross)}"
          f" | unmeasured: {sum(1 for r in PLAY if r.get('bigmap') is None)}")
    print(f"first crossing median: {sorted(r['exit_secs'] for r in cross)[len(cross)//2]}s")
    print("wrote ladder.pdf pareto.pdf horizon.pdf behaviour.pdf")
