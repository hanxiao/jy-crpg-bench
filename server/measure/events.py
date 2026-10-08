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

Three more things are read from boxes the game draws with a white border at
fixed places; the service grades each as a milestone once it happened:

    dialogue  the portrait frame of a speaker, at the top left, the top right
              or the bottom right; the opening tutorial's guide is left out.
              A box that returns after the screen was free of one opens a
              new conversation; conversations with the same text in their
              first box are the same one heard again.
    saves     請稍候 beside the 存檔 row of the system menu: the game is
              writing a slot. The service's own save, where it ran, used the
              same menu; a save is the player's when the action that confirmed
              it ended just before.
    loads     請稍候 beside the 讀檔 row, and the 載入進度 menu of the screen
              after a lost fight, left on one of its three slots.

A Scanner is fed frames with a clock in the replay's own seconds; `speed` is
the play seconds per clock second (8 for a replay at eight times speed). The
same code reads a published video and a live session, which feeds its frames
with clock = play seconds / speed. A capture of someone else's screen, scaled
back to the native frame (`capture=True`), blurs a border below WHITE and can
split it across two rows, so its boxes are found by the dark outline the game
draws around every border instead (`outlined`).
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

# Boxes with a white border at fixed places: (top row, bottom row, left
# column, right column) of the straight part of the border.
PORTRAITS = {"top-left": (13, 72, 28, 78), "top-right": (13, 72, 242, 292), "bottom-right": (126, 185, 242, 292)}
TEXTS = {"top-left": (20, 70, 101, 305), "top-right": (20, 70, 15, 219), "bottom-right": (133, 183, 15, 219)}
GUIDE_BOX = (16, 70, 29, 77)        # inside the top-left portrait frame
WAIT_BOX = (19, 47, 159, 216)       # 請稍候！
WAIT_GLYPHS = (24, 42, 160, 222)
SYSTEM_BOX = (19, 88, 76, 106)      # 讀檔 存檔 離開
SLOT_BOX = (19, 88, 124, 139)       # 一 二 三
OVER_BOX = (91, 178, 210, 301)      # 載入進度一 二 三, 離開睡覺去
OVER_CARD = (10, 40, 10, 160)       # the header of the card beside it
MENU_ROWS = (26, 46, 66)            # first row of each line of the system and slot menus
OVER_ROWS = (95, 113, 130, 148)
LOAD, SAVE = 0, 1                   # the rows of the system menu
TALK_GAP = 0.5      # seconds of play a dialogue box may vanish within one conversation
SAME_TEXT = 0.8     # correlation of the text of two first boxes that says they are one conversation
# Seconds of play from the end of the keys of the player's last action to a
# save notice it caused. The service's own save waited two seconds of idle
# after an action's end and then pressed ten keys before the notice showed.
AGENT_GAP = 2.0
CONFIRM = ("enter", "space", "return")
# A border of a resampled capture over the darker of the one or two pixels
# just outside it. Measured: the native borders of 263 dialogue frames stood
# 182 or more above that outline (outlined() and framed() agreed on all 8001
# frames read), the borders of a capture scaled 1.8 times 118 or more, and
# snow as bright as a border stands nowhere above it.
OUTLINE_RISE = 50.0
LIT_FLOOR, CAPTURE_LIT_FLOOR = 200.0, 150.0   # the lit line of a menu, native and captured
# Over the seven published human captures, every 請稍候 notice matched its
# glyphs at 0.48 (a save faded over snow) to 0.95, below the native
# threshold, and every other frame with a border at that place at 0.24 or
# less. A capture scaled 1.5 times drew them a pixel to the left, so a
# capture's glyphs are matched over a window of CAPTURE_SEARCH pixels, as
# the paper's capture tools match panels.
CAPTURE_MATCH = 0.4
CAPTURE_SEARCH = 2


def _load(name):
    return np.asarray(Image.open(TEMPLATES / (name + ".png")).convert("L"), dtype=np.float32)


TPL = {n: _load(n) for n in NAMES}
BOXES = {n: _load(n) for n in ("guide", "wait", "over")}


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


def framed(white, box):
    """Whether a white border runs along `box` of a frame's white mask. The
    corners are rounded, so the sides are looked for a few pixels outside the
    straight part of the top and bottom edges. A character drawn over the
    box may hide part of one edge."""
    y0, y1, a, b = box
    top = max(white[y, a + 4:b - 4].mean() for y in (y0 - 1, y0, y0 + 1))
    bottom = max(white[y, a + 4:b - 4].mean() for y in (y1 - 1, y1, y1 + 1))
    left = white[y0 + 5:y1 - 4, max(0, a - 6):a + 2].any(axis=1).mean()
    right = white[y0 + 5:y1 - 4, b - 2:b + 6].any(axis=1).mean()
    edges = sorted((top, bottom, left, right))
    return edges[0] > 0.5 and edges[1] > 0.85


def outlined(f, box, rise=OUTLINE_RISE):
    """framed() for a resampled capture: an edge pixel is one brighter by
    `rise` than the darker of the one or two pixels on either side of it.
    Outside the white line the game draws a dark outline, and inside lies
    the dark ground of the box; over snow the blur merges the outline into
    the snow, and only the inside still stands below the line. Tolerances
    are those of framed()."""
    y0, y1, a, b = box
    xs, ys = slice(a + 4, b - 4), slice(y0 + 5, y1 - 4)

    def stands(line, o1, o2, i1, i2):
        return (line - np.minimum(o1, o2) > rise) | (line - np.minimum(i1, i2) > rise)

    def row(y, out):
        return float(stands(f[y, xs], f[y + out, xs], f[y + 2 * out, xs], f[y - out, xs], f[y - 2 * out, xs]).mean())

    def side(x0, x1, out):
        hit = np.zeros(y1 - 4 - y0 - 5, bool)
        for x in range(max(2, x0), min(f.shape[1] - 2, x1)):
            hit |= stands(f[ys, x], f[ys, x + out], f[ys, x + 2 * out], f[ys, x - out], f[ys, x - 2 * out])
        return float(hit.mean())
    top = max(row(y, -1) for y in (y0 - 1, y0, y0 + 1))
    bottom = max(row(y, 1) for y in (y1 - 1, y1, y1 + 1))
    edges = sorted((top, bottom, side(a - 6, a + 2, -1), side(b - 2, b + 6, 1)))
    return edges[0] > 0.5 and edges[1] > 0.85


def _crop(f, box):
    y0, y1, a, b = box
    return f[y0:y1, a:b]


def _match(f, box, tpl, search=0):
    """The correlation of a template with its box, at best over a window of
    `search` pixels around it."""
    y0, y1, a, b = box
    return max(ncc(f[y0 + dy:y1 + dy, a + dx:b + dx], tpl)
               for dy in range(-search, search + 1) for dx in range(-search, search + 1)
               if y0 + dy >= 0 and a + dx >= 0 and y1 + dy <= f.shape[0] and b + dx <= f.shape[1])


def lit_row(f, rows, height, x0, x1, floor=LIT_FLOOR):
    """The line of a menu the game draws in white, the others being orange
    (luma about 165): its index, or None where no line stands out. The
    brightest glyph pixels of each line are compared, since a thin stroke such
    as 一 loses its peak to video compression."""
    peak = [float(np.percentile(f[y:y + height, x0:x1], 97)) for y in rows]
    order = np.argsort(peak)
    k = int(order[-1])
    return k if peak[k] >= floor and peak[k] - peak[int(order[-2])] >= 15 else None


def dialogue(f, boxed):
    """(place, the text area) of the dialogue box on a gray frame, or None;
    `boxed(box)` tells whether a border runs along a box. The opening
    tutorial's guide is not a dialogue of the run."""
    for place, box in PORTRAITS.items():
        if boxed(box):
            if place == "top-left" and ncc(_crop(f, GUIDE_BOX), BOXES["guide"]) > 0.6:
                return None
            return place, _crop(f, TEXTS[place])
    return None


def same_text(a, b):
    """Whether two text areas show the same text. Measured on the replays,
    the same box correlates at 0.99 or more and two different texts at 0.21
    or less; the darkened scene behind the text barely counts."""
    return a.shape == b.shape and ncc(a, b) > SAME_TEXT


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

    def __init__(self, need, known=None, unnamed=None, capture=False):
        self.need = max(1, int(need))
        self.capture = capture       # a resampled capture: borders by their outline
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
        self.talks = []              # [first clock, last clock, text of the first box] per box run
        self.talking = False
        self.notices = []            # (clock, system menu row, slot) at each 請稍候
        self.waiting = False
        self.slot = None             # the slot lit while the slot menu shows
        self.over = None             # [clock, lit row] while the menu after a lost fight shows
        self.over_loads = []         # (clock, slot) of each slot it was left on

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
        self.boxes(f[:200], clock)

    def boxes(self, f, clock):
        if self.capture:
            def boxed(box):
                return outlined(f, box)
            floor, match, search = CAPTURE_LIT_FLOOR, CAPTURE_MATCH, CAPTURE_SEARCH
        else:
            white = f > WHITE

            def boxed(box):
                return framed(white, box)
            floor, match, search = LIT_FLOOR, THRESH, 0
        d = dialogue(f, boxed)
        if d is not None and self.talking:
            self.talks[-1][1] = clock
        elif d is not None:
            self.talks.append([clock, clock, d[1].astype(np.uint8)])   # 10 KB a box
        self.talking = d is not None
        slot_menu = boxed(SLOT_BOX)
        if slot_menu:
            self.slot = lit_row(f, MENU_ROWS, 14, 124, 142, floor)
        wait = boxed(WAIT_BOX) and _match(f, WAIT_GLYPHS, BOXES["wait"], search) > match
        if wait and not self.waiting:
            row = lit_row(f, MENU_ROWS, 14, 75, 107, floor) if boxed(SYSTEM_BOX) else None
            self.notices.append((clock, row, self.slot))
        self.waiting = wait
        if not slot_menu and not wait:
            self.slot = None
        if boxed(OVER_BOX) and _match(f, OVER_CARD, BOXES["over"], search) > match:
            self.over = [clock, lit_row(f, OVER_ROWS, 17, 215, 300, floor)]
        elif self.over is not None:
            self.close_over()

    def close_over(self):
        if self.over is not None and self.over[1] is not None and self.over[1] < 3:
            self.over_loads.append((self.over[0], self.over[1]))
        self.over = None

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
        out["dialogue"] = conversations(self.talks, speed)
        out["saves"], out["loads"] = slots(self.notices, self.over_loads, marks, speed)
        self.pending = pending
        if pending is not None:
            self.entries.pop()
        return out


def conversations(talks, speed):
    """Conversations from the runs of dialogue boxes: runs apart by no more
    than TALK_GAP seconds of play are one conversation, and conversations
    whose first boxes carry the same text are one heard again."""
    starts = []
    for i, (t0, t1, text) in enumerate(talks):
        if i and (t0 - talks[i - 1][1]) * speed <= TALK_GAP:
            continue
        starts.append((t0, text))
    distinct = []
    for _, text in starts:
        if not any(same_text(text, d) for d in distinct):
            distinct.append(text)
    minutes = [round(t * speed / 60, 1) for t, _ in starts]
    return {"count": len(starts), "distinct": len(distinct),
            "first_minute": minutes[0] if minutes else None, "minutes": minutes}


def slots(notices, over_loads, marks, speed):
    """The player's saves and loads, each {"minute", "slot"} with slots
    numbered from one. A save notice is the player's when its last action
    pressed a confirming key and its keys ended at most AGENT_GAP seconds of
    play before; the service's own save pressed keys no action records.
    Without the keypress timeline the saves cannot be told apart: None."""
    def item(t, slot, **kw):
        return dict({"minute": round(t * speed / 60, 1), "slot": None if slot is None else slot + 1}, **kw)

    loads = [item(t, s) for t, row, s in notices if row == LOAD]
    loads += [item(t, s, after_defeat=True) for t, s in over_loads]
    loads.sort(key=lambda x: x["minute"])
    if marks is None:
        return None, loads
    marks = sorted(marks, key=lambda m: m["t"])
    saves = []
    for t, row, s in notices:
        if row != SAVE:
            continue
        before = [m for m in marks if m["t"] <= t]
        if not before:
            continue
        m = before[-1]
        end = m["t"] + sum(k[1] for k in m["keys"]) / speed
        if any(k[0] in CONFIRM for k in m["keys"]) and (t - end) * speed <= AGENT_GAP:
            saves.append(item(t, s))
    return saves, loads


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
