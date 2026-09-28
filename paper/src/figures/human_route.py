"""The human route figure: the speedrun BV1UxvTz3Ehe from the spawn tile to the
hermit, drawn as the model walks of Figures 4 and 5 are drawn.

    python human_route.py

The walk through the starting house and the walk on the world map are read by
the trackers of the model figures, anchored_route.track on compound.png and
worldmap_route.track on the rendered world map, from the clip of the speedrun
that starts 6.0 s into the video, scaled to the native frame. The house of the
hermit has no rendered panorama, so human/route.py stitches it from the same
clip. The paths are in routes/human-*.json, one row per placed frame with the
second of the clip; each is coloured on one scale of seconds with arrowheads
in the direction of the walk, and the figure is route-human.pdf.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import routes  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
plt.rcParams.update({"font.family": "serif", "font.size": 7})
INK = "#1c1c1e"


def rows(name):
    return np.array(json.load(open(os.path.join(HERE, "routes", name)))["rows"], np.float64)


def panel(fig, rect, img, extent, xy, t, norm, label):
    ax = fig.add_axes(rect)
    ax.imshow(img, extent=extent, interpolation="nearest")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_linewidth(0.4)
        sp.set_color(INK)
    routes.draw_path(ax, xy, t, lw=1.3, arrows=5, norm=norm)
    ax.text(0.5, -0.02, label, transform=ax.transAxes, ha="center", va="top", fontsize=7.5, color=INK)


def main():
    comp, world, house = rows("human-compound.json"), rows("human-world.json"), rows("human-house.json")
    norm = Normalize(0, float(np.ceil(max(comp[:, 2].max(), world[:, 4].max(), house[:, 2].max()))))
    # the world map around the walk
    pad = 60
    wx0, wx1 = int(world[:, 0].min() - pad), int(world[:, 0].max() + pad)
    wy0, wy1 = int(world[:, 1].min() - pad), int(world[:, 1].max() + pad)
    wimg = routes.faded(Image.open(os.path.join(HERE, "worldmap.png")).crop((wx0, wy0, wx1, wy1)))
    # the starting house, cropped as in Figure 4
    pano = Image.open(os.path.join(HERE, "..", "..", "..", "server", "measure", "assets", "compound.png"))
    cov = np.asarray(pano.convert("L")) > 0
    cimg = routes.faded(pano)
    cimg[~cov] = 255
    cx0, cx1 = max(0, int(comp[:, 0].min()) - 60), min(cimg.shape[1], int(comp[:, 0].max()) + 60)
    cy0, cy1 = max(0, int(comp[:, 1].min()) - 60), min(cimg.shape[0], int(comp[:, 1].max()) + 60)
    himg = np.asarray(Image.open(os.path.join(HERE, "route-house.png")).convert("RGB")).copy()
    himg[himg.max(axis=2) == 0] = 255
    himg = routes.faded(Image.fromarray(himg))

    # one row in the order of the walk, every panel the same height
    w_in, gap = 7.0, 0.1
    aspects = [(cx1 - cx0) / (cy1 - cy0), (wx1 - wx0) / (wy1 - wy0), himg.shape[1] / himg.shape[0]]
    h = (w_in - 2 * gap) / sum(aspects)
    H = h + 0.7
    fig = plt.figure(figsize=(w_in, H))
    y = (H - 0.04 - h) / H
    x = 0.0
    specs = [(cimg[cy0:cy1, cx0:cx1], (cx0, cx1, cy1, cy0), comp[:, :2], comp[:, 2], "(a) the starting house"),
             (wimg, (wx0, wx1, wy1, wy0), world[:, :2], world[:, 4], "(b) the world map"),
             (himg, (0, himg.shape[1], himg.shape[0], 0), house[:, :2], house[:, 2], "(c) the house of the hermit")]
    for a, (img, ext, xy, t, label) in zip(aspects, specs):
        panel(fig, [x / w_in, y, a * h / w_in, h / H], img, ext, xy, t, norm, label)
        x += a * h + gap
    cax = fig.add_axes([0.35, 0.3 / H, 0.3, 0.06 / H])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=routes.CMAP), cax=cax, orientation="horizontal")
    cb.outline.set_linewidth(0.4)
    cax.tick_params(labelsize=6, length=2, width=0.4)
    cb.set_label("second of the speedrun", fontsize=6.5, labelpad=1)
    fig.savefig(os.path.join(HERE, "route-human.pdf"), dpi=250)
    plt.close(fig)
    print("wrote route-human.pdf")


if __name__ == "__main__":
    main()
