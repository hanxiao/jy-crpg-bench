"""The panorama of the opening compound that anchored_route.py places replay
frames on.

    python compound_panorama.py [<session id>] [<out.png>]

human/templates/compound-bg.png is the compound stitched from a human speedrun
with the hero removed. The speedrun walks from the spawn tile to the gate, so
the stitch stops short of the west and south fences, and a model that wanders
there has nothing to be placed on. The panorama is grown from that stitch with
the replay of a session that walked the whole yard (8806d294db69 of
claude-opus-5 by default): each frame, up to the first black frame, is placed
on the panorama so far at the offset of highest normalised cross-correlation
over the pixels the panorama already has, and the pixels it does not have are
filled from the frame, except for a block around the hero. A frame is
registered against the growing panorama rather than against the previous
frame, so the chain drift of model_route.py does not arise. The coordinates
of the human stitch are kept, with its origin recorded in compound.json, so
SPAWN in anchored_route.py still names the spawn tile.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "human"))
import field  # noqa: E402

HUMAN = os.path.join(HERE, "human", "templates", "compound-bg.png")
SID = sys.argv[1] if len(sys.argv) > 1 else "8806d294db69"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "..", "..", "server", "measure", "assets", "compound.png")
W0, H0 = 320, 200
R0, R1 = 8, 192
MARGIN = 400            # canvas margin around the human stitch, cropped at the end
MIN_NCC = 0.6
HERO = (40, 64)         # width, height of the block left unfilled around the hero


def main():
    import anchored_route as AR
    hum = np.asarray(Image.open(HUMAN).convert("RGB"), np.float32)
    H, W = hum.shape[0] + 2 * MARGIN, hum.shape[1] + 2 * MARGIN
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[MARGIN:MARGIN + hum.shape[0], MARGIN:MARGIN + hum.shape[1]] = hum
    valid = canvas.sum(axis=2) > 0
    # pixels filled from the replay keep a running sum so repeated visits average out
    acc = np.zeros((H, W, 3), np.float32)
    cnt = np.zeros((H, W), np.float32)

    row = next(r for r in field.load_runs(dedup=False, keep_excluded=True) if r["id"] == SID)
    ev = json.load(open(os.path.join(HERE, "replay_events.json"), encoding="utf-8"))[SID]
    video = os.path.join(HERE, "videos", SID + ".mp4")
    if not os.path.exists(video):
        import urllib.request
        os.makedirs(os.path.dirname(video), exist_ok=True)
        urllib.request.urlretrieve(row["video_url"], video)

    screen, last, placed, grown = AR.SPAWN, None, 0, 0
    for i, f in enumerate(AR.frames(video, ev["first_black_second"])):
        if last is not None and (np.abs(f.astype(np.int16) - last.astype(np.int16)).max(axis=2) > 30)[R0:R1].sum() < 30:
            continue
        last = f
        g = f.astype(np.float32).mean(axis=2)
        keep = ~AR.dialogue_mask(f)
        keep[:R0] = False
        keep[R1:] = False
        if keep.mean() < 0.6:
            continue
        pg = canvas.mean(axis=2)
        m = AR.masked_ncc_map(pg, valid, g, keep)
        y, x = np.unravel_index(np.argmax(m), m.shape)
        if m[y, x] < MIN_NCC:
            continue
        placed += 1
        region = pg[y:y + H0, x:x + W0]
        d = (np.abs(g - region) > 40) & keep & valid[y:y + H0, x:x + W0]
        if d.sum() >= 40 and d.mean() < 0.2:
            c = np.pad(d.astype(np.float32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
            bh, bw = 40, 24
            s_ = c[bh:, bw:] - c[:-bh, bw:] - c[bh:, :-bw] + c[:-bh, :-bw]
            yy, xx = np.mgrid[0:s_.shape[0], 0:s_.shape[1]]
            far = (np.abs(xx + bw / 2 - screen[0]) > 60) | (np.abs(yy + bh * 0.75 - screen[1]) > 60)
            s_ = np.where(far, 0, s_)
            by, bx = np.unravel_index(np.argmax(s_), s_.shape)
            if s_[by, bx] >= 60:
                screen = (bx + bw / 2, by + bh * 0.75)
        fill = keep.copy()
        hx0, hy0 = int(screen[0] - HERO[0] / 2), int(screen[1] - HERO[1] * 0.8)
        fill[max(0, hy0):hy0 + HERO[1], max(0, hx0):hx0 + HERO[0]] = False
        new = fill & ~valid[y:y + H0, x:x + W0]
        if new.any():
            grown += 1
            acc[y:y + H0, x:x + W0][new] += f[new]
            cnt[y:y + H0, x:x + W0][new] += 1
            filled = cnt[y:y + H0, x:x + W0] > 0
            sub = canvas[y:y + H0, x:x + W0]
            sub[filled & ~valid[y:y + H0, x:x + W0]] = (acc[y:y + H0, x:x + W0] / cnt[y:y + H0, x:x + W0, None])[filled & ~valid[y:y + H0, x:x + W0]]
            # a pixel counts as known once two frames agreed on it, or one frame at the edge of the frame
            valid[y:y + H0, x:x + W0] |= filled & (cnt[y:y + H0, x:x + W0] >= 2)
    # pixels seen once are kept too, now that nothing more will arrive
    once = (cnt > 0) & ~valid
    canvas[once] = (acc / np.maximum(cnt, 1)[:, :, None])[once]
    valid |= once
    print(SID, row["agent"], "frames placed", placed, "frames that grew the panorama", grown)

    ys, xs = np.where(valid)
    cy0, cy1, cx0, cx1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cx0, cy0 = min(cx0, MARGIN), min(cy0, MARGIN)
    out = canvas[cy0:cy1, cx0:cx1]
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(OUT)
    with open(OUT[:-4] + ".json", "w") as fh:
        json.dump({"human_origin": [int(MARGIN - cx0), int(MARGIN - cy0)], "session": SID,
                   "size": [int(out.shape[1]), int(out.shape[0])]}, fh, indent=1)
    print("wrote", OUT, out.shape[1], "x", out.shape[0], "human origin at", (int(MARGIN - cx0), int(MARGIN - cy0)))


if __name__ == "__main__":
    main()
