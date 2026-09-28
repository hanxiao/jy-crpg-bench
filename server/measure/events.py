"""The events the game keeps only on screen, read from frames.

Every frame is matched against the panels in assets/templates by normalised
cross-correlation. Five panels are held by the game for a second or more and
count when they score above the threshold over HOLD seconds of play:

    hermit    the hermit's portrait in the dialogue frame
    compass   the coordinate line the compass adds to the item screen
    battle    the acting character's card in a battle
    defeat    the banner the game draws when the party loses
    prompt    the yes-or-no prompt of a character who asks to join

Four messages are dismissed at the next key, so a single frame counts:

    obtained  得到, an item entered the inventory (searched along its row)
    won       戰鬥勝利, a battle won
    exp       獲得經驗, experience gained (searched along its row)
    level     升級了, a new level (searched along its row)

The name banner the game draws on entering a location is found by its border
and matched against the banners in assets/templates/scenes. The first fully
black frame of a session that starts in the starting house is its exit onto
the world map.

A Scanner is fed frames with a clock in the replay's own seconds; `speed` is
the play seconds per clock second (8 for a replay at eight times speed). The
same code reads a published video and a live session, which feeds its frames
with clock = play seconds / speed.
"""
import json
import os
import pathlib

import numpy as np
from PIL import Image

ASSETS = pathlib.Path(__file__).resolve().parent / "assets"
TEMPLATES = ASSETS / "templates"
SCENES = TEMPLATES / "scenes"
META = json.loads((TEMPLATES / "templates.json").read_text(encoding="utf-8"))
THRESH = META["threshold"]
HELD = ("hermit", "compass", "battle", "defeat", "prompt")
SINGLE = ("obtained", "won", "exp", "level")
SLIDE = ("obtained", "exp", "level")
NAMES = HELD + SINGLE
HOLD = 0.8        # seconds of play a held panel must stay above the threshold
CANDIDATE = 0.6   # scores above this are kept, so the threshold can be revisited without a rescan
HOME = "王居"      # the banner of the starting house
BANNER_TOP, BANNER_H, BANNER_W = (7, 17), (20, 27), (24, 150)
WHITE = 235
SETTLE = 6        # frames a banner is watched before its name is read
BLACK_LUMA, BLACK_SHARE = 0.10 * 255, 0.98


def _load(name):
    return np.asarray(Image.open(TEMPLATES / (name + ".png")).convert("L"), dtype=np.float32)


TPL = {n: _load(n) for n in NAMES}


def ncc(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def to_gray(rgb):
    """Luma of an RGB frame, as the game frame of a video decodes to gray."""
    return np.asarray(Image.fromarray(np.ascontiguousarray(rgb[:200])).convert("L"), dtype=np.float32)


def is_black(gray):
    """A fully black game frame: the game blacks the screen on every change of
    location."""
    g = gray[:200]
    return bool((g <= BLACK_LUMA).mean() >= BLACK_SHARE)


def _runs(row):
    """(start, length) of the longest run of True in a boolean row."""
    if not row.any():
        return 0, 0
    d = np.diff(np.concatenate(([0], row.view(np.int8), [0])))
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    k = int(np.argmax(ends - starts))
    return int(starts[k]), int(ends[k] - starts[k])


def scene_banner(f):
    """The interior of the location-name banner in a gray frame, or None.

    The banner's border is a cream rounded rectangle whose top edge sits in a
    fixed band of rows and whose width follows the name; the box is centred on
    the screen. Its top and bottom edges must both be present and agree in
    extent, which no dialogue box, prompt or menu of the game satisfies."""
    band = f[BANNER_TOP[0]:BANNER_TOP[1], 40:280] > WHITE
    for i in range(band.shape[0]):
        x0, w = _runs(band[i])
        if not BANNER_W[0] <= w <= BANNER_W[1]:
            continue
        x0 += 40
        cx = x0 + w / 2
        if not 140 <= cx <= 180:
            continue
        top = BANNER_TOP[0] + i
        for h in range(BANNER_H[0], BANNER_H[1]):
            y = top + h
            if y >= f.shape[0]:
                break
            # the bottom edge runs between rounded corners, so it is a few
            # pixels shorter than the top edge and starts a little to the right
            bx0, bw = _runs(f[y, 40:280] > WHITE)
            if -3 <= bx0 + 40 - x0 <= 5 and 0.8 * w <= bw <= w / 0.8:
                return f[top + 3:y - 2, x0 + 3:x0 + w - 3], (x0, top, x0 + w, y)
    return None


def load_scene_templates(directory=SCENES):
    out = []
    for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
        if name.endswith(".png"):
            # 'X.png' and its variants 'X.2.png' all name the location X
            out.append([name[:-4].split(".")[0],
                        np.asarray(Image.open(os.path.join(directory, name)).convert("L"), dtype=np.float32)])
    return out


def same_banner(a, b):
    """Whether two banner interiors show the same name: the same width within
    two pixels and a normalised cross-correlation above 0.85 at the best of
    the small offsets a one-pixel difference in the detected box produces."""
    if abs(a.shape[1] - b.shape[1]) > 2 or abs(a.shape[0] - b.shape[0]) > 2:
        return False
    h, w = min(a.shape[0], b.shape[0]) - 2, min(a.shape[1], b.shape[1]) - 2
    best = 0.0
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            for p, q in ((a[dy:dy + h, dx:dx + w], b[:h, :w]), (a[:h, :w], b[dy:dy + h, dx:dx + w])):
                if p.shape == q.shape == (h, w):
                    best = max(best, ncc(p, q))
    return best > 0.85


def banner_name(crop, known, unnamed=None):
    """The location the banner names. A banner no template matches is added to
    `known` as 'location-N', or passed to `unnamed`, which returns a name."""
    for name, tpl in known:
        if same_banner(crop, tpl):
            return name
    if unnamed is not None:
        name = unnamed(crop)
    else:
        name = "location-%d" % (1 + sum(1 for n, _ in known if n.startswith("location-")))
    known.append([name, crop.copy()])
    return name


class FrameScorer:
    """The score of every panel on one gray frame."""

    def __init__(self):
        self.slid = {}
        for n in SLIDE:
            t = TPL[n] - TPL[n].mean()
            self.slid[n] = (META[n]["box"][1], META[n]["slide"], t, np.sqrt((t * t).sum()))

    def score(self, f):
        out = {}
        for n in HELD:
            bx0, by0, bx1, by1 = META[n]["box"]
            out[n] = ncc(f[by0:by1, bx0:bx1], TPL[n])
        for n, (y0, (lo, hi), t, tn) in self.slid.items():
            h, w = t.shape
            win = np.lib.stride_tricks.sliding_window_view(f[y0:y0 + h], (h, w))[0, lo:hi + 1]
            wm = win - win.mean(axis=(1, 2), keepdims=True)
            den = np.sqrt((wm * wm).sum(axis=(1, 2))) * tn
            sc = (wm * t).sum(axis=(1, 2)) / np.where(den > 0, den, np.inf)
            out[n] = float(sc.max())
        bx0, by0, bx1, by1 = META["won"]["box"]
        out["won"] = ncc(f[by0:by1, bx0:bx1], TPL["won"])
        return out


class Scanner:
    """Per clock second, the best score of every panel, and the banners
    entered. `need` is the number of consecutive frames that span HOLD seconds
    of play; a held panel scores the minimum over them."""

    def __init__(self, need, known=None, unnamed=None):
        self.need = max(1, int(need))
        self.scorer = FrameScorer()
        self.known = load_scene_templates() if known is None else known
        self.unnamed = unnamed
        self.best = {n: [] for n in NAMES}
        self.recent = {n: [] for n in HELD}
        self.entries = []            # (clock second, location name) at each banner's rising edge
        self.pending = None
        self.showing = False
        self.first_black = None      # clock of the first fully black frame
        self.clock = 0.0

    def feed(self, f, clock, black=None):
        """One gray frame of the game (200 or more rows of 320) at `clock`."""
        self.clock = clock
        s = int(clock)
        for n in self.best:
            if s >= len(self.best[n]):
                self.best[n].extend([0.0] * (s + 1 - len(self.best[n])))
        sc = self.scorer.score(f)
        for n in HELD:
            self.recent[n] = (self.recent[n] + [sc[n]])[-self.need:]
            if len(self.recent[n]) == self.need:
                self.best[n][s] = max(self.best[n][s], min(self.recent[n]))
        for n in SINGLE:
            self.best[n][s] = max(self.best[n][s], sc[n])
        b = scene_banner(f)
        if b is not None and not self.showing:
            self.pending = [s, b[0], SETTLE]
        elif b is not None and self.pending is not None:
            self.pending[1] = b[0]
            self.pending[2] -= 1
            if self.pending[2] == 0:
                self.entries.append((self.pending[0], banner_name(self.pending[1], self.known, self.unnamed)))
                self.pending = None
        elif b is None and self.pending is not None:
            self.entries.append((self.pending[0], banner_name(self.pending[1], self.known, self.unnamed)))
            self.pending = None
        self.showing = b is not None
        if black is None:
            black = is_black(f)
        if black and self.first_black is None:
            self.first_black = clock

    def close(self):
        if self.pending is not None:
            self.entries.append((self.pending[0], banner_name(self.pending[1], self.known, self.unnamed)))
            self.pending = None

    def hits(self, name):
        return [s for s, v in enumerate(self.best[name]) if v > THRESH]

    def summary(self, speed, marks=None, first_black=None):
        """The readings in minutes of play. `marks` is the keypress timeline
        ({"t": clock, "keys": [[key, hold], ...]} per action); `first_black`
        overrides the clock of the first black frame."""
        pending = self.pending
        self.close()
        out = {"video_seconds": len(self.best["obtained"])}
        away = [name for _, name in self.entries if name != HOME]
        out["scenes"] = {
            "entries": [{"minute": round(t * speed / 60, 1), "name": name} for t, name in self.entries],
            "distinct": len(set(away)),
            "first_minute": round(min((t for t, n in self.entries if n != HOME), default=0) * speed / 60, 1)
            if away else None}
        for n in NAMES:
            out[n] = panel(self.best[n], speed)
        black = self.first_black if first_black is None else first_black
        out["first_black_second"] = black
        out["crossing_actions"] = (sum(1 for m in marks if m["t"] <= black)
                                   if black is not None and marks is not None else None)
        out["recruited_minute"] = recruited(self.hits("prompt"), marks, speed)
        self.pending = pending
        if pending is not None:
            self.entries.pop()
        return out


def panel(sec, speed):
    idx = [s for s, v in enumerate(sec) if v > THRESH]
    return {"seconds": len(idx), "max": round(max(sec), 3) if sec else None,
            "first_minute": round(idx[0] * speed / 60, 1) if idx else None,
            "minutes": [round(s * speed / 60, 1) for s in idx],
            "candidates": [[s, round(v, 3)] for s, v in enumerate(sec) if v > CANDIDATE]}


def recruited(prompt_seconds, marks, speed):
    """Minute of the yes that answered the join prompt, or None. The game holds
    the prompt until a key is pressed, so the answer is the first key pressed
    after the prompt appeared; any other key dismisses it."""
    if not prompt_seconds or not marks:
        return None
    marks = sorted(marks, key=lambda m: m["t"])
    for i in prompt_seconds:
        after = [m for m in marks if m["t"] >= i]
        if after and after[0]["keys"] and after[0]["keys"][0][0] == "y":
            return round(after[0]["t"] * speed / 60, 1)
    return None
