"""Where the hero walked: in the starting house and on the world map.

Every frame is placed on a fixed picture at the offset of highest normalised
cross-correlation, over the frame without the status strip and without any
dialogue box.

HouseTracker places frames up to the first black frame on assets/compound.png,
the starting house stitched from replays with the hero removed. The scene
scrolls to keep the hero on his tile, so while the view moves he stands on the
spawn tile of the frame; while the view is clamped at a border he is the
densest block of pixels that differ from the panorama.

WorldTracker places frames after the crossing on the world map rendered from
the game's data files (worldmap.py). The world map always scrolls to keep the
hero at one screen position, so his tile is the offset of the frame plus HERO.
A match is searched near the last placed frame and, when that fails (after a
location or a loaded save), over the whole map at a quarter of the resolution.
"""
import json
import pathlib

import numpy as np
from PIL import Image

ASSETS = pathlib.Path(__file__).resolve().parent / "assets"
W0, H0 = 320, 200
R0, R1 = 8, 192
DIALOGUE_WHITE, DIALOGUE_BLACK = 300, 800


def dialogue_mask(f):
    """True over a dialogue box: its white text and black panel, grown to cover the box."""
    white = f.min(axis=2) > 225
    black = f.max(axis=2) < 20
    if white.sum() <= DIALOGUE_WHITE or black.sum() <= DIALOGUE_BLACK:
        return np.zeros(f.shape[:2], bool)
    ys, xs = np.where(black)
    m = np.zeros(f.shape[:2], bool)
    y0, y1 = max(0, ys.min() - 4), min(H0, ys.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(W0, xs.max() + 5)
    m[y0:y1, x0:x1] = True
    return m


def masked_ncc_map(img, valid, t, keep):
    """Normalised cross-correlation of t at every position of img over the
    pixels where keep (in t) and valid (in img) both hold, through the FFT."""
    h, w = t.shape
    k = keep.astype(np.float32)
    kf = np.fft.rfft2(k[::-1, ::-1], s=img.shape)
    v = valid.astype(np.float32)
    iv = img * v

    def corr(a, b):
        return np.fft.irfft2(np.fft.rfft2(a) * b, s=img.shape)[h - 1:, w - 1:]

    n = corr(v, kf)
    tk = t * k
    s_t = corr(v, np.fft.rfft2(tk[::-1, ::-1], s=img.shape))
    s_tt = corr(v, np.fft.rfft2((tk * t)[::-1, ::-1], s=img.shape))
    s_i = corr(iv, kf)
    s_ii = corr(iv * img, kf)
    s_it = corr(iv, np.fft.rfft2(tk[::-1, ::-1], s=img.shape))
    n = np.maximum(n, 1.0)
    cov = s_it - s_i * s_t / n
    var_i = s_ii - s_i * s_i / n
    var_t = s_tt - s_t * s_t / n
    den = np.sqrt(np.maximum(var_i, 1.0) * np.maximum(var_t, 1.0))
    ncc = cov / den
    ncc[n < 0.6 * h * w] = -1.0                      # the frame must lie mostly on the picture
    return ncc


def ncc_map(img, t):
    """Normalised cross-correlation of t at every position of img, through the FFT."""
    h, w = t.shape
    t = t - t.mean()
    tn = np.sqrt((t * t).sum())
    F = np.fft.rfft2(img)
    num = np.fft.irfft2(F * np.fft.rfft2(t[::-1, ::-1], s=img.shape), s=img.shape)[h - 1:, w - 1:]
    O = np.fft.rfft2(np.ones_like(t)[::-1, ::-1], s=img.shape)
    s1 = np.fft.irfft2(F * O, s=img.shape)[h - 1:, w - 1:]
    s2 = np.fft.irfft2(np.fft.rfft2(img * img) * O, s=img.shape)[h - 1:, w - 1:]
    var = s2 - s1 * s1 / (h * w)
    return num / (np.sqrt(np.maximum(var, 1.0)) * tn)


def _half(a):
    h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
    return a[:h, :w].reshape(h // 2, 2, w // 2, 2).mean((1, 3))


def place(img, valid, g, keep, near=None, jump=None, fast=False):
    """(x, y, ncc) of the best placement of frame g (pixels where keep) on
    img (pixels where valid), within `jump` of `near` when given. The fast
    mode searches at half resolution, then refines within REFINE pixels at
    full resolution; a live session uses it, a published replay does not."""
    x0 = y0 = 0
    if near is not None and jump is not None:
        x0, y0 = max(0, near[0] - jump), max(0, near[1] - jump)
        img = img[y0:near[1] + H0 + jump, x0:near[0] + W0 + jump]
        valid = valid[y0:near[1] + H0 + jump, x0:near[0] + W0 + jump]
    if img.shape[0] < g.shape[0] or img.shape[1] < g.shape[1]:
        return None
    if not fast:
        m = masked_ncc_map(img, valid, g, keep)
        y, x = np.unravel_index(np.argmax(m), m.shape)
        return x0 + int(x), y0 + int(y), float(m[y, x])
    m = masked_ncc_map(_half(img), _half(valid.astype(np.float32)) > 0.5, _half(g), _half(keep.astype(np.float32)) > 0.5)
    y, x = np.unravel_index(np.argmax(m), m.shape)
    X, Y = int(x) * 2, int(y) * 2
    r = REFINE
    ax, ay = max(0, X - r), max(0, Y - r)
    sub = img[ay:Y + g.shape[0] + r, ax:X + g.shape[1] + r]
    subv = valid[ay:Y + g.shape[0] + r, ax:X + g.shape[1] + r]
    if sub.shape[0] < g.shape[0] or sub.shape[1] < g.shape[1]:
        return x0 + X, y0 + Y, float(m[y, x])
    m2 = masked_ncc_map(sub, subv, g, keep)
    y, x = np.unravel_index(np.argmax(m2), m2.shape)
    return x0 + ax + int(x), y0 + ay + int(y), float(m2[y, x])


REFINE = 4


def _repeat(f, last):
    """A frame that repeats the one before it, while the model thinks."""
    return last is not None and (np.abs(f.astype(np.int16) - last.astype(np.int16)).max(axis=2) > 30)[R0:R1].sum() < 30


class HouseTracker:
    """The hero's path through the starting house, on assets/compound.png."""

    SPAWN = (146, 78)
    MIN_NCC = 0.55
    MAX_JUMP = 120

    def __init__(self, fast=False):
        self.fast = fast
        pano = np.asarray(Image.open(ASSETS / "compound.png").convert("RGB"), np.float32)
        self.pg = pano.mean(axis=2)
        self.valid = pano.sum(axis=2) > 0
        self.size = (pano.shape[1], pano.shape[0])
        self.points = []           # (x, y, minute) on the panorama
        self.screen, self.last_off, self.last_f = self.SPAWN, None, None

    def feed(self, f, minute):
        """One RGB frame (at least 200 rows of 320) at a minute of play."""
        f = f[:H0]
        if _repeat(f, self.last_f):
            return None
        self.last_f = f
        g = f.astype(np.float32).mean(axis=2)
        keep = ~dialogue_mask(f)
        keep[:R0] = False
        keep[R1:] = False
        if keep.mean() < 0.6:
            return None
        if self.fast:
            hit = place(self.pg, self.valid, g, keep, self.last_off, self.MAX_JUMP if self.last_off else None, fast=True)
            if hit is None or hit[2] < self.MIN_NCC:
                return None
            x, y = hit[0], hit[1]
        else:
            m = masked_ncc_map(self.pg, self.valid, g, keep)
            if self.last_off is not None:
                # the view moves a few tiles between frames; a match far from
                # the last offset is a repeated pattern of fence or wall
                yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
                m = np.where((np.abs(xx - self.last_off[0]) > self.MAX_JUMP)
                             | (np.abs(yy - self.last_off[1]) > self.MAX_JUMP), -1.0, m)
            y, x = np.unravel_index(np.argmax(m), m.shape)
            if m[y, x] < self.MIN_NCC:
                return None
        moved = self.last_off is not None and (x, y) != self.last_off
        self.last_off = (x, y)
        if moved:
            self.screen = self.SPAWN
        else:
            region = self.pg[y:y + H0, x:x + W0]
            d = (np.abs(g - region) > 40) & keep & self.valid[y:y + H0, x:x + W0]
            if d.sum() >= 40 and d.mean() < 0.2:
                c = np.pad(d.astype(np.float32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
                bh, bw = 40, 24
                s_ = c[bh:, bw:] - c[:-bh, bw:] - c[bh:, :-bw] + c[:-bh, :-bw]
                yy, xx = np.mgrid[0:s_.shape[0], 0:s_.shape[1]]
                far = (np.abs(xx + bw / 2 - self.screen[0]) > 60) | (np.abs(yy + bh * 0.75 - self.screen[1]) > 60)
                s_ = np.where(far, 0, s_)
                by, bx = np.unravel_index(np.argmax(s_), s_.shape)
                if s_[by, bx] >= 60:
                    self.screen = (bx + bw / 2, by + bh * 0.75)
        p = (float(x + self.screen[0]), float(y + self.screen[1]), float(minute))
        self.points.append(p)
        return p

    def path(self):
        """The points smoothed by a running mean of three."""
        path = self.points
        if len(path) > 4:
            path = [path[0]] + [((a[0] + p[0] + b[0]) / 3, (a[1] + p[1] + b[1]) / 3, p[2])
                                for a, p, b in zip(path, path[1:], path[2:])] + [path[-1]]
        return [[round(a, 1), round(b, 1), round(c, 3)] for a, b, c in path]


class WorldMap:
    """The rendered world map: full-resolution gray for placing frames, a
    quarter-resolution copy for relocating, and a half-resolution colour copy
    for drawing, all memory-mapped from the cache worldmap.py writes, so every
    session process on a host shares one copy."""

    K = 4

    def __init__(self, cache):
        cache = pathlib.Path(cache)
        self.meta = json.loads((cache / "worldmap.json").read_text())
        self.gray = np.load(cache / "worldmap_gray.npy", mmap_mode="r")
        self.small = np.load(cache / "worldmap_small.npy", mmap_mode="r")
        self.half = np.load(cache / "worldmap_half.npy", mmap_mode="r")

    def coords(self, px, py):
        """Map pixel to the coordinates the compass shows."""
        u = (px - self.meta["origin"][0]) / self.meta["tile"][0]
        v = (py - self.meta["origin"][1]) / self.meta["tile"][1]
        return round((v + u) / 2), round((v - u) / 2)


class WorldTracker:
    HERO = (145, 117)
    MIN_NCC = 0.6
    GLOBAL_NCC = 0.8
    MAX_JUMP = 160
    RELOCATE_EVERY = 6

    def __init__(self, world, fast=False):
        self.world = world
        self.fast = fast
        self.misses = 0            # frames since the last whole-map try, in the fast mode
        self.points = []           # (px, py, x, y, minute, ncc)
        self.last, self.last_f = None, None
        self._small = None

    def feed(self, f, minute):
        f = f[:H0]
        if self.last_f is not None and (np.abs(f.astype(np.int16) - self.last_f.astype(np.int16)).max(axis=2) > 30).sum() < 30:
            return None
        self.last_f = f
        g = f.astype(np.float32).mean(axis=2)
        keep = ~dialogue_mask(f)
        if keep.mean() < 0.6:
            return None
        wm, K = self.world.gray, self.world.K
        hit = None
        if self.last is not None and self.fast:
            x0, y0 = max(0, self.last[0] - self.MAX_JUMP), max(0, self.last[1] - self.MAX_JUMP)
            win = np.asarray(wm[y0:self.last[1] + H0 + self.MAX_JUMP, x0:self.last[0] + W0 + self.MAX_JUMP], np.float32)
            h = place(win, np.ones(win.shape, bool), g, keep, fast=True)
            if h is not None and h[2] >= self.MIN_NCC:
                hit = (x0 + h[0], y0 + h[1], h[2])
        elif self.last is not None:
            x0, y0 = max(0, self.last[0] - self.MAX_JUMP), max(0, self.last[1] - self.MAX_JUMP)
            win = np.asarray(wm[y0:self.last[1] + H0 + self.MAX_JUMP, x0:self.last[0] + W0 + self.MAX_JUMP], np.float32)
            m = masked_ncc_map(win, np.ones(win.shape, bool), g, keep)
            y, x = np.unravel_index(np.argmax(m), m.shape)
            if m[y, x] >= self.MIN_NCC:
                hit = (x0 + x, y0 + y, float(m[y, x]))
        if hit is None and self.fast:
            # a whole-map try costs as much as a hundred local ones; inside a
            # location every frame misses, so the fast mode tries once every
            # RELOCATE_EVERY missed frames
            self.misses += 1
            if self.misses < self.RELOCATE_EVERY and self.last is not None:
                return None
            self.misses = 0
        if hit is None:
            if self._small is None:
                self._small = np.asarray(self.world.small, np.float32)
            gs = g[:H0 // K * K, :W0 // K * K].reshape(H0 // K, K, W0 // K, K).mean((1, 3))
            m = ncc_map(self._small, gs)
            y, x = np.unravel_index(np.argmax(m), m.shape)
            if m[y, x] < self.MIN_NCC:
                return None
            X, Y = x * K, y * K
            x0, y0 = max(0, X - 2 * K), max(0, Y - 2 * K)
            win = np.asarray(wm[y0:Y + H0 + 2 * K, x0:X + W0 + 2 * K], np.float32)
            m = masked_ncc_map(win, np.ones(win.shape, bool), g, keep)
            y, x = np.unravel_index(np.argmax(m), m.shape)
            if m[y, x] < self.GLOBAL_NCC:
                return None
            hit = (x0 + x, y0 + y, float(m[y, x]))
        self.last = hit[:2]
        px, py = hit[0] + self.HERO[0], hit[1] + self.HERO[1]
        cx, cy = self.world.coords(px, py)
        p = [int(px), int(py), cx, cy, round(float(minute), 3), round(hit[2], 3)]
        self.points.append(p)
        return p
