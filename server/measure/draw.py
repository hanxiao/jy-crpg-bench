"""Route pictures: a path coloured by minute of play over the starting house or
a crop of the world map, in the colours of the paper's route figures."""
import io
import math

import numpy as np
from PIL import Image, ImageDraw

from .routes import ASSETS

STOPS = ((0xe9, 0x8f, 0xe6), (0xb5, 0x4f, 0xc9), (0x6f, 0x1f, 0x93), (0x2a, 0x05, 0x44))
FADE = 0.35            # the picture is pulled towards white so the path reads first
INK = (28, 28, 30)


def colour(t):
    """The colour of a fraction t in [0, 1] of the budget."""
    t = min(1.0, max(0.0, t)) * (len(STOPS) - 1)
    i = min(int(t), len(STOPS) - 2)
    f = t - i
    a, b = STOPS[i], STOPS[i + 1]
    return tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def faded(rgb):
    a = np.asarray(rgb, np.float32)
    return Image.fromarray((a * (1 - FADE) + 255 * FADE).clip(0, 255).astype(np.uint8))


MIN_RUN = 4            # points a connected stretch needs to be drawn


def _path(draw, xy, minutes, budget, width, gap):
    """Segments coloured by minute over a white halo, an arrowhead every sixth
    of the path. A segment longer than `gap` is a jump (a location, a loaded
    save) and is left out, and a stretch of fewer than MIN_RUN connected
    points is a frame placed on a look-alike and is not drawn."""
    runs, cur = [], [0]
    for i in range(1, len(xy)):
        p, q = xy[i - 1], xy[i]
        if math.hypot(q[0] - p[0], q[1] - p[1]) <= gap:
            cur.append(i)
        else:
            runs.append(cur)
            cur = [i]
    runs.append(cur)
    segs = [(xy[i], xy[j], (minutes[i] + minutes[j]) / 2)
            for r in runs if len(r) >= MIN_RUN for i, j in zip(r, r[1:])]
    for p, q, _ in segs:
        draw.line([p, q], fill=(255, 255, 255), width=width + 3)
    for p, q, m in segs:
        draw.line([p, q], fill=colour(m / budget), width=width)
    step = max(1, len(segs) // 6)
    for p, q, m in segs[step // 2::step]:
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        if p == q:
            continue
        s = width * 3 + 2
        tip = q
        left = (q[0] - s * math.cos(ang - 0.45), q[1] - s * math.sin(ang - 0.45))
        right = (q[0] - s * math.cos(ang + 0.45), q[1] - s * math.sin(ang + 0.45))
        draw.polygon([tip, left, right], fill=colour(m / budget))


def _ends(draw, start, end, r):
    x, y = start
    draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=INK, width=2)
    x, y = end
    draw.rectangle([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=INK, width=2)


def _png(img):
    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def house(points, budget_minutes):
    """The walk through the starting house: rows of (x, y, minute) on
    compound.png, from the spawn tile (circle) to the last point (square)."""
    img = faded(Image.open(ASSETS / "compound.png").convert("RGB")).convert("RGB")
    d = ImageDraw.Draw(img)
    if len(points) >= 2:
        xy = [(p[0], p[1]) for p in points]
        _path(d, xy, [p[2] for p in points], budget_minutes, 3, 90)
        _ends(d, xy[0], xy[-1], 6)
    return _png(img)


def world(points, world_map, budget_minutes, marks=(), max_width=900, pad=160):
    """The walk on the world map: rows of (px, py, x, y, minute, ncc) in
    full-resolution map pixels, drawn on a crop of the half-scale map around
    the path. `marks` are (px, py, label) drawn as numbered circles."""
    if len(points) < 2:
        return None
    xs = [p[0] for p in points] + [m[0] for m in marks]
    ys = [p[1] for p in points] + [m[1] for m in marks]
    x0, y0 = max(0, min(xs) - pad) // 2, max(0, min(ys) - pad) // 2
    x1 = min(world_map.half.shape[1], (max(xs) + pad) // 2)
    y1 = min(world_map.half.shape[0], (max(ys) + pad) // 2)
    crop = faded(np.asarray(world_map.half[y0:y1, x0:x1])).convert("RGB")
    scale = min(1.0, max_width / max(1, crop.width))
    if scale < 1.0:
        crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(crop)

    def at(px, py):
        return ((px / 2 - x0) * scale, (py / 2 - y0) * scale)

    xy = [at(p[0], p[1]) for p in points]
    _path(d, xy, [p[4] for p in points], budget_minutes, 2, 60)
    _ends(d, xy[0], xy[-1], 5)
    for px, py, label in marks:
        x, y = at(px, py)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 255, 255), outline=INK, width=2)
        d.text((x, y), str(label), fill=INK, anchor="mm")
    return _png(crop)
