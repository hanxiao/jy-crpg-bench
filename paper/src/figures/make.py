"""Figures for the paper.

Every number comes from `catalog_snapshot.json`, a copy of the published
catalogue (gs://jy-crpg-bench-runs/catalog.json) fetched before each build.
Refresh the snapshot and rerun to regenerate the figures:

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
from matplotlib.patches import Patch

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
    sys.path.insert(0, HERE)
    import field
    rows = field.load_runs()
    out = []
    for r in rows:
        name = r["agent"]
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
import field as _field
PLAY = sorted([r for r in RUNS if r["budget"] == _field.DEFAULT_BUDGET and (r["actions"] or 0) > 0],
              key=lambda r: (ORDER.index(r["family"]) if r["family"] in ORDER else 9,
                             -(r["actions"] or 0)))
DEFINITION, OPENING, rungs_of = _field.DEFINITION, _field.OPENING, _field.rungs_of


def bar_box(ax, x, lo, hi, pad=1.5):
    """Display-unit box for the vertical error bar between `lo` and `hi`.

    A label that clears every marker can still sit on a neighbouring interval,
    which reads as text drawn over data.
    """
    from matplotlib.transforms import Bbox
    cx, ylo = ax.transData.transform((x, lo))
    _cx, yhi = ax.transData.transform((x, hi))
    return Bbox.from_bounds(cx - pad, ylo - pad, 2 * pad, (yhi - ylo) + 2 * pad)


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


def _own_box(box, anchor, tol=16.0):
    """True when `box` is the marker or interval the label at `anchor` names.

    Proximity rather than containment, because a point contributes both a
    marker box and a taller, narrower interval box, and a label that names two
    runs at almost the same coordinates names both of them.
    """
    cx, cy = (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2
    return abs(cx - anchor[0]) <= tol and (box.y0 - tol) <= anchor[1] <= (box.y1 + tol)


def check_overlaps(fig, ax, texts, points=(), name="", anchors=()):
    """Fail if any two texts overlap, or a text overlaps a data marker.

    A label is allowed to touch the marker it names, which is what `anchors`
    records; every other marker it must clear.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    boxes = [(t.get_text(), _ext(t, rend)) for t in texts]
    own = {label: ax.transData.transform(xy) for label, xy in anchors}
    bad = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][1].overlaps(boxes[j][1]):
                bad.append(f"{boxes[i][0]!r} vs {boxes[j][0]!r}")
    for label, bb in boxes:
        for p in points:
            if label in own and _own_box(p, own[label]):
                continue
            if bb.overlaps(p):
                bad.append(f"{label!r} overlaps a marker")
    if bad:
        shown = bad[:12]
        more = f"\n  ... and {len(bad) - 12} more" if len(bad) > 12 else ""
        sys.exit(f"{name}: {len(bad)} overlap(s):\n  " + "\n  ".join(shown) + more)


# ------------------------------------------------------- Fig: milestone ladder
def figure_ladder():
    # one row per model with every session it played behind it; models by
    # rungs reached, the random floor last
    rows = _field.played(_field.load_runs(dedup=False))
    models = _field.model_rows([r for r in rows if not _field.is_random(r["agent"])])
    floor = _field.model_rows([r for r in rows if _field.is_random(r["agent"])])
    models.sort(key=lambda m: (-m["reached"], m["agent"].lower()))
    entries = models + floor
    labels = [m["agent"] for m in entries]
    fig, ax = plt.subplots(figsize=(7.6, 0.34 * len(entries) + 1.1))
    cells = []
    unmeasured = False
    # the fewest actions any session of the model took to reach the world map,
    # as a bar behind the row on a linear scale, with the count at the right
    span = len(DEFINITION)
    acts = [m["map_actions"] for m in entries if m.get("map_actions") is not None]
    amax = max(acts) if acts else 1
    counts = []
    xcount = span + 0.4
    for row, m in enumerate(entries):
        a = m.get("map_actions")
        if a is not None:
            ax.barh(row, span * a / amax, left=-0.5, height=0.66, color="#DCE9F6",
                    edgecolor="none", zorder=1.2)
            counts.append(ax.text(xcount, row, str(a), ha="center", va="center",
                                  fontsize=7.6, color=INK))
    for row, m in enumerate(entries):
        for col, v in enumerate(m["rungs"]):
            if v is None:
                unmeasured = True
                sval = 52.0
                ax.scatter(col, row, s=sval, facecolor="#e4e4e6",
                           edgecolors="#d0d0d3", linewidths=0.9, zorder=3)
            elif v:
                sval = 52.0
                ax.scatter(col, row, s=sval, marker="o", facecolors=INK,
                           edgecolors=INK, linewidths=1.1, zorder=3)
            else:
                sval = 52.0
                ax.scatter(col, row, s=sval, marker="o", facecolors="white",
                           edgecolors="#8c8c90", linewidths=1.1, zorder=3)
            cells.append((col, row, sval ** 0.5))
    # milestone names along the top, the count column headed beside them
    from matplotlib.transforms import blended_transform_factory
    heads = [ax.annotate("actions to\nworld map", xy=(xcount, 1.0),
                         xycoords=blended_transform_factory(ax.transData, ax.transAxes),
                         xytext=(0, 4), textcoords="offset points", ha="center",
                         va="bottom", fontsize=6.6, color="#67676b")]
    ax.set_yticks(range(len(entries)), labels, fontsize=8.5, fontfamily="monospace")
    ax.set_xticks(range(len(DEFINITION)), DEFINITION, fontsize=6.6)
    ax.xaxis.tick_top()
    ax.set_xlim(-0.55, span + 0.85)
    ax.set_ylim(len(entries) - 0.42, -0.62)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.tick_params(length=0)
    handles = [
        Line2D([], [], marker="o", ls="", color=INK, ms=7, label="reached in a session"),
        Line2D([], [], marker="o", ls="", markerfacecolor="white",
               markeredgecolor="#8c8c90", ms=7, label="not reached"),
        Patch(facecolor="#DCE9F6", edgecolor="none", label="fewest actions to the world map"),
    ]
    # the third state is drawn only when some model carries no reading, so the
    # legend never names a marker the figure does not show
    if unmeasured:
        handles.append(Line2D([], [], marker="o", ls="", markerfacecolor="#e4e4e6",
                              markeredgecolor="#d0d0d3", ms=7, label="unmeasured"))
    leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.45, 0.0),
                    fontsize=8, frameon=False, ncol=len(handles), handletextpad=0.2,
                    columnspacing=1.1)
    fig.tight_layout(pad=0.3)
    boxes = [box_at(ax, c, r, size) for c, r, size in cells]
    check_overlaps(fig, ax, list(ax.get_xticklabels()) + list(ax.get_yticklabels())
                   + heads + counts + list(leg.get_texts()), boxes, name="ladder")
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
    offs = [(x, y) for r in range(1, 17) for x in (5 * r, -5 * r)
            for y in (0, 4 * r, -4 * r, 8 * r, -8 * r)]
    for label, (x, y) in anchors:
        # A label names its own point, so the marker and interval it belongs to
        # are not obstacles for it; every other one is.
        own = ax.transData.transform((x, y))
        near = [b for b in boxes if not _own_box(b, own)]
        for dx, dy in offs:
            txt = ax.annotate(label, (x, y), xytext=(dx, dy),
                              textcoords="offset points",
                              ha="left" if dx >= 0 else "right", va="center",
                              fontsize=fontsize, color="#3f3f43", zorder=5,
                              annotation_clip=False)
            bb = _ext(txt, rend, pad=1.0)
            clash = any(bb.overlaps(b) for b in near) or any(
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
LABELLED = {}   # points are labelled from the data below, never by session id


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
                continue
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
    # Obstacle boxes are display units, so they are only valid once the axes
    # have been laid out; building them before the draw pins them to a stale
    # transform and the placer then reads collisions that are not there.
    fig.canvas.draw()
    marker_boxes = [box_at(ax, k, p, FAMILY[r["family"]][2])
                    for r, k, p, _lo, _hi in pts]
    marker_boxes += [bar_box(ax, k, lo, hi) for _r, k, _p, lo, hi in pts]
    labels = place_labels(fig, ax, anchors, obstacles=marker_boxes, name="pareto")
    ax.set_xlabel("meaningful actions in the run")
    ax.set_ylabel("meaningful-step ratio")
    ax.set_xlim(0, 345)
    ax.set_ylim(0, 1.0)
    ax.tick_params(labelsize=7.5)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=0.3)
    check_overlaps(fig, ax, list(leg.get_texts()) + labels, marker_boxes,
                   name="pareto", anchors=anchors)
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
            # the label sits inside the grey stretch before the crossing, so
            # neighbouring rows with similar crossings cannot collide
            texts.append(ax.annotate(f"act {r['exit_acts']}", (exit_at, row),
                                     xytext=(-3, 0), textcoords="offset points",
                                     ha="right", va="center", fontsize=6.1, color="#33506e"))
        elif r.get("bigmap") is True:
            ax.barh(row, span, left=0, height=0.55, color="none", zorder=3,
                   hatch="///", edgecolor=ACCENT, linewidth=0.0)
        if r.get("reason") == "idle":
            texts.append(ax.annotate("idle stop", (span, row), xytext=(4, 0),
                                     textcoords="offset points", fontsize=6.1,
                                     va="center", color="#8b8b8f"))
    ax.axvline(_field.DEFAULT_BUDGET, lw=0.9, color="#8f8f93", zorder=4)
    ax.annotate("budget", (_field.DEFAULT_BUDGET, -0.78), xytext=(-3, 0), textcoords="offset points",
                ha="right", fontsize=6.4, color="#6d6d70")
    ax.set_yticks(range(len(PLAY)), [r["short"] for r in PLAY], fontsize=6.6)
    ax.set_xlabel("seconds of play")
    ax.set_xlim(0, _field.DEFAULT_BUDGET * 1.075)
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
    cross = [r for r in PLAY if r.get("exit_secs") is not None]
    print(f"{len(RUNS)} sessions, {len(PLAY)} at the {_field.DEFAULT_BUDGET // 60}-minute budget")
    print(f"world map by fingerprint: {sum(1 for r in PLAY if r.get('bigmap') is True)}"
          f" | corroborated by a black frame: {len(cross)}"
          f" | unmeasured: {sum(1 for r in PLAY if r.get('bigmap') is None)}")
    print(f"first crossing median: {sorted(r['exit_secs'] for r in cross)[len(cross)//2]}s")
    print("wrote ladder.pdf")
