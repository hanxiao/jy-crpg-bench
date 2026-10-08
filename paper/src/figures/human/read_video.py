"""Read a published video of a human player the way the paper reads its replays.

    python read_video.py calibrate <video> <second> [...]      # find the game frame: crop=w:h:x:y for prep
    python read_video.py findcrop <video> [t1] [stride]          # search the first t1 seconds for the opening room
    python read_video.py edgecrop <video> [n] [t1]                # the crop read off the black bars of the capture
    python read_video.py prep <video> <tag> <crop=w:h:x:y>      # crop and scale to the native frame: work/<tag>.320.mp4
    python read_video.py scan <tag>                             # the five panels, the obtained message, banners, black frames
    python read_video.py messages <tag>                         # the 升級了 and 獲得經驗點數 messages
    python read_video.py steps <tag> <t0> <t1>                  # tile steps and screen advances between two video seconds
    python read_video.py report <tag> [start=<s>]               # evidence sheets under work/<tag>-report/
    python read_video.py boxes <tag> start=<s> [record=<id>]    # conversations, saves and loads; record=<id> files them

The panels are the templates of ../templates/, matched in the same boxes as
for the model replays but over a window of two pixels, since a capture is
resampled; a crop found by `calibrate` maps the capture onto the native
320x200 frame. Work files go to figures/human/work/ (not tracked); the
readings are recorded by hand in ../human_sessions.json with the frame behind
each of them. `boxes` reads the conversations, saves and loads with the
service's own detectors in their capture mode, and `record=<id>` files them
under that video's "boxes" with an evidence sheet of every notice.
"""
import io
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.dirname(HERE)
WORK = os.path.join(HERE, "work")
sys.path.insert(0, os.path.join(FIG, "..", "..", "..", "server"))
from measure import events as R  # noqa: E402  the panels and banners the service reads

W, H = 320, 232
SEARCH = 2          # pixels of position search around each panel box
R.WHITE = 200       # the banner border of a re-encoded capture
OPENING_GAP = 60.0  # seconds without the guide that end the opening tutorial
MSG = {n: np.asarray(Image.open(os.path.join(HERE, "templates", n + ".png")).convert("L"), dtype=np.float32)
       for n in ("levelup", "expgain")}
ROOM_BOX = (24, 70, 296, 190)   # the part of the opening room matched by `calibrate`
ROOM = np.asarray(Image.open(os.path.join(HERE, "templates", "room.png")).convert("L"), dtype=np.float32)  # the first frame of a benchmark replay


def frames(path, t0=None, t1=None):
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error"]
    if t0 is not None:
        cmd += ["-ss", str(t0)]
    cmd += ["-i", path]
    if t1 is not None:
        cmd += ["-t", str(t1 - (t0 or 0))]
    cmd += ["-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        buf = proc.stdout.read(W * H)
        if len(buf) < W * H:
            break
        yield np.frombuffer(buf, np.uint8).reshape(H, W).astype(np.float32)
    proc.stdout.close()
    proc.wait()


def frame_at(path, t):
    sub = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", str(t), "-i", path, "-frames:v", "1",
                          "-f", "image2pipe", "-pix_fmt", "gray", "-vcodec", "png", "-"], capture_output=True).stdout
    return np.asarray(Image.open(io.BytesIO(sub)).convert("L"), dtype=np.float32)


def fps_of(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    a, b = out.split("/") if "/" in out else (out, "1")
    return float(a) / float(b)


def ncc_max(region, tpl):
    """the best normalised cross-correlation of tpl over every position in region."""
    h, w = tpl.shape
    if region.shape[0] < h or region.shape[1] < w:
        return 0.0
    win = np.lib.stride_tricks.sliding_window_view(region, (h, w))
    wm = win - win.mean(axis=(2, 3), keepdims=True)
    t = tpl - tpl.mean()
    tn = np.sqrt((t * t).sum())
    den = np.sqrt((wm * wm).sum(axis=(2, 3))) * tn
    return float(((wm * t).sum(axis=(2, 3)) / np.where(den > 0, den, np.inf)).max())


def ncc_map(img, t):
    """normalised cross-correlation of t at every position of img, through the FFT."""
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


def native_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    w, h = (int(v) for v in out.strip().split(",")[:2])
    return w, h


def native_frames(path, t1=None, fps=1.0):
    """the capture at its own size, sampled at `fps` frames a second."""
    w, h = native_size(path)
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error"]
    if t1 is not None:
        cmd += ["-t", str(t1)]
    cmd += ["-i", path, "-vf", f"fps={fps}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        buf = proc.stdout.read(w * h)
        if len(buf) < w * h:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w).astype(np.float32)
    proc.stdout.close()
    proc.wait()


def findcrop(video, t1=600.0, stride=2.0, stop=0.90):
    """the crop that maps the native frame onto the capture, searched over time as well
    as over scale and offset: the opening room of a benchmark replay is matched at every
    scale the capture could hold, so a capture that never shows the room says so."""
    bx0, by0, bx1, by1 = ROOM_BOX
    tpl = ROOM[by0:by1, bx0:bx1]
    Ws, Hs = native_size(video)
    cache = {}

    def scaled(sx, sy):
        if (sx, sy) not in cache:
            rt = np.asarray(Image.fromarray(tpl.astype(np.uint8)).resize(
                (int(round((bx1 - bx0) * sx)), int(round((by1 - by0) * sy))), Image.BILINEAR), dtype=np.float32)
            cache[(sx, sy)] = rt if rt.shape[0] < Hs and rt.shape[1] < Ws else None
        return cache[(sx, sy)]

    grid = [(sx, sy) for sx in np.arange(0.9, 2.61, 0.1) for sy in np.arange(0.8, 2.61, 0.1)
            if 0.55 * Ws <= 320 * sx <= 1.05 * Ws and 0.55 * Hs <= 200 * sy <= 1.05 * Hs
            and scaled(sx, sy) is not None]
    best = (-1.0, None, None)
    for i, src in enumerate(native_frames(video, t1=t1, fps=1.0 / stride)):
        t = i * stride
        for sx, sy in grid:
            m = ncc_map(src, scaled(sx, sy))
            y, x = np.unravel_index(np.argmax(m), m.shape)
            if 0.5 < float(m[y, x]) <= 0.999 and float(m[y, x]) > best[0]:
                best = (float(m[y, x]), (sx, sy, int(x), int(y)), t)
                if best[0] >= stop:
                    break
        if best[0] >= stop:
            break
    if best[1] is None:
        print(f"no opening room in the first {t1:.0f}s of {os.path.basename(video)}; best ncc {best[0]:.3f}")
        return
    v, (sx, sy, x, y), t = best
    for _ in range(2):
        for d in ((-0.05, 0), (0.05, 0), (0, -0.05), (0, 0.05)):
            sx_, sy_ = sx + d[0], sy + d[1]
            rt = scaled(sx_, sy_)
            if rt is None:
                continue
            m = ncc_map(src if t == 0 else frame_at(video, t), rt)
            yy, xx = np.unravel_index(np.argmax(m), m.shape)
            if float(m[yy, xx]) > v:
                v, sx, sy, x, y = float(m[yy, xx]), sx_, sy_, int(xx), int(yy)
    ox, oy = x - bx0 * sx, y - by0 * sy
    print(f"{t:.1f}s ncc {v:.3f} scale x{sx:.2f} y{sy:.2f} -> crop={int(round(320 * sx))}:{int(round(200 * sy))}"
          f":{int(round(ox))}:{int(round(oy))} in {Ws}x{Hs}")


def edgecrop(video, n=40, t1=None, thr=2.0):
    """the crop read off the black bars of the capture: over `n` frames the first and last
    column and row whose mean brightness leaves black. A capture with no bars returns the
    whole frame, and a stretched one says so by its ratio."""
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error"]
    if t1 is not None:
        cmd += ["-t", str(t1)]
    cmd += ["-i", video, "-vf", f"fps={n / (t1 or 600):.4f}", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    Ws, Hs = native_size(video)
    cols, rows = [], []
    seen = 0
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while seen < n:
        buf = proc.stdout.read(Ws * Hs)
        if len(buf) < Ws * Hs:
            break
        f = np.frombuffer(buf, np.uint8).reshape(Hs, Ws).astype(np.float32)
        cm, rm = f.mean(axis=0), f.mean(axis=1)
        cols.append((int(np.argmax(cm > thr)), int(Ws - 1 - np.argmax(cm[::-1] > thr))))
        rows.append((int(np.argmax(rm > thr)), int(Hs - 1 - np.argmax(rm[::-1] > thr))))
        seen += 1
    proc.stdout.close()
    proc.wait()
    if not seen:
        print("no frames read")
        return
    x0 = int(np.median([c[0] for c in cols])); x1 = int(np.median([c[1] for c in cols]))
    y0 = int(np.median([r[0] for r in rows])); y1 = int(np.median([r[1] for r in rows]))
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"{seen} frames: content x {x0}..{x1} y {y0}..{y1} -> crop={w}:{h}:{x0}:{y0}, "
          f"ratio {w / h:.3f} (the native frame is {320 / 200:.3f})")


def refinecrop(video, t, w0=None, h0=None, dh=8, dw=8, step=2, wide=2):
    """the integer crop of the capture that maps the native frame onto it best. A capture
    is often stretched, so width and height are searched apart around a nominal frame and
    the offset is searched too: `calibrate` names a frame that ffmpeg then clamps, which is
    not the frame it read."""
    Ws, Hs = native_size(video)
    w0 = int(w0) if w0 else Ws
    h0 = int(h0) if h0 else Hs
    step, wide, dh, dw = int(step), int(wide), int(dh), int(dw)
    tpl = ROOM[70:190, 24:296]
    bx0, by0, bx1, by1 = ROOM_BOX
    best = (-1.0, None)
    src = frame_at(video, t)
    for h in range(max(40, h0 - dh), min(Hs, h0 + dh) + 1, step):
        for w in range(max(40, w0 - dw), min(Ws, w0 + dw) + 1, step):
            for y in range(max(0, (Hs - h) // 2 - 12), min(Hs - h, (Hs - h) // 2 + 12) + 1, step):
                for x in range(max(0, (Ws - w) // 2 - 12), min(Ws - w, (Ws - w) // 2 + 12) + 1, wide):
                    sub = src[y:y + h, x:x + w]
                    f = np.asarray(Image.fromarray(sub.astype(np.uint8)).resize((320, 200), Image.BILINEAR), dtype=np.float32)
                    v = float(ncc_max(f[by0 - SEARCH:by1 + SEARCH, bx0 - SEARCH:bx1 + SEARCH], tpl))
                    if v > best[0]:
                        best = (v, f"{w}:{h}:{x}:{y}")
    print(f"{t:.1f}s best crop {best[1]} ncc {best[0]:.3f} in {Ws}x{Hs}")


def calibrate(video, seconds):
    """The crop that maps the native frame onto the capture, from the opening
    room of a benchmark replay matched at many scales in the given seconds."""
    room = ROOM
    bx0, by0, bx1, by1 = ROOM_BOX
    tpl = room[by0:by1, bx0:bx1]
    for t in seconds:
        src = frame_at(video, t)
        Hs, Ws = src.shape
        best = (-1.0, None)
        for sx in np.arange(0.8, 2.6, 0.05):
            for sy in np.arange(0.7, 2.6, 0.05):
                rt = np.asarray(Image.fromarray(tpl.astype(np.uint8)).resize(
                    (int(round((bx1 - bx0) * sx)), int(round((by1 - by0) * sy))), Image.BILINEAR), dtype=np.float32)
                if rt.shape[0] >= Hs or rt.shape[1] >= Ws:
                    continue
                m = ncc_map(src, rt)
                y, x = np.unravel_index(np.argmax(m), m.shape)
                if float(m[y, x]) > best[0]:
                    best = (float(m[y, x]), (sx, sy, int(x), int(y)))
        v, (sx, sy, x, y) = best
        ox, oy = x - bx0 * sx, y - by0 * sy
        print(f"{t:.0f}s ncc {v:.3f} scale x{sx:.2f} y{sy:.2f} -> crop={int(round(320 * sx))}:{int(round(200 * sy))}:{int(round(ox))}:{int(round(oy))} in {Ws}x{Hs}")


def prep(video, tag, crop):
    """crop=w:h:x:y in source pixels, x and y may be negative: the capture is padded first."""
    w, h, x, y = (int(v) for v in crop.split(":"))
    px, py = max(0, -x), max(0, -y)
    vf = (f"pad=iw+{px}:ih+{py}:{px}:{py}:black," if px or py else "") + f"crop={w}:{h}:{x + px}:{y + py}," + \
        "scale=320:200:flags=area,pad=320:232:0:0:black,format=gray"
    os.makedirs(WORK, exist_ok=True)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", video, "-vf", vf, "-an",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", os.path.join(WORK, f"{tag}.320.mp4")], check=True)


def banner_match(crop, known):
    best, name = 0.0, None
    for n, tpl in known:
        if abs(crop.shape[1] - tpl.shape[1]) > 3 or abs(crop.shape[0] - tpl.shape[0]) > 3:
            continue
        h, w = min(crop.shape[0], tpl.shape[0]) - 2, min(crop.shape[1], tpl.shape[1]) - 2
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                for p, q in ((crop[dy:dy + h, dx:dx + w], tpl[:h, :w]), (crop[:h, :w], tpl[dy:dy + h, dx:dx + w])):
                    if p.shape == q.shape == (h, w):
                        v = R.ncc(p, q)
                        if v > best:
                            best, name = v, n
    return name, best


def blacks_of(video, rows="200:0"):
    h, y = rows.split(":")
    err = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", video, "-vf",
                          f"crop=320:{h}:0:{y},blackdetect=d=0.03:pix_th=0.10", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [round(float(m.group(1)), 2) for m in re.finditer(r"black_start:([0-9.]+)", err)]


def scan(tag):
    video = os.path.join(WORK, f"{tag}.320.mp4")
    known = R.load_scene_templates()
    fps = fps_of(video)
    x0, y0, x1, y1 = R.META["obtained"]["box"]
    lo, hi = R.META["obtained"]["slide"]
    oh, ow = R.TPL["obtained"].shape
    best = {n: [] for n in R.NAMES + ("obtained",)}
    prev = {n: 0.0 for n in R.NAMES}
    entries, pending, showing = [], None, False
    for i, f in enumerate(frames(video)):
        s = int(i / fps)
        for n in best:
            if s >= len(best[n]):
                best[n].extend([0.0] * (s + 1 - len(best[n])))
        for n in R.NAMES:
            bx0, by0, bx1, by1 = R.META[n]["box"]
            score = ncc_max(f[max(0, by0 - SEARCH):by1 + SEARCH, max(0, bx0 - SEARCH):bx1 + SEARCH], R.TPL[n])
            best[n][s] = max(best[n][s], min(prev[n], score))
            prev[n] = score
        best["obtained"][s] = max(best["obtained"][s], ncc_max(f[y0 - SEARCH:y1 + SEARCH, lo:hi + ow + 1 + SEARCH], R.TPL["obtained"]))
        b = R.scene_banner(f)
        if b is not None and not showing:
            pending = [s, b[0], 6]
        elif b is not None and pending is not None:
            pending[1] = b[0]
            pending[2] -= 1
            if pending[2] == 0:
                name, v = banner_match(pending[1], known)
                entries.append((pending[0], name if name and v >= 0.7 else "unknown", round(v, 3)))
                pending = None
        elif b is None and pending is not None:
            name, v = banner_match(pending[1], known)
            entries.append((pending[0], name if name and v >= 0.7 else "unknown", round(v, 3)))
            pending = None
        showing = b is not None
    np.savez_compressed(os.path.join(WORK, f"{tag}.scores.npz"), **{n: np.array(v, dtype=np.float32) for n, v in best.items()})
    out = {"tag": tag, "fps": fps, "seconds": len(best["obtained"]), "black": blacks_of(video),
           "black_below_overlay": blacks_of(video, "150:40"),
           "banners": [{"second": s, "name": n, "score": v} for s, n, v in entries]}
    for n in best:
        arr = np.array(best[n])
        out[n] = {"max": round(float(arr.max()), 3), "above_0.8": [int(s) for s in np.flatnonzero(arr > 0.8)][:400]}
    json.dump(out, open(os.path.join(WORK, f"{tag}.scan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for n in R.NAMES + ("obtained",):
        print(n, "max", out[n]["max"], "n>0.8", len(out[n]["above_0.8"]), "first", out[n]["above_0.8"][:6])
    print("banners", [(e["second"], e["name"], e["score"]) for e in out["banners"]][:30])
    print("black", out["black"][:12])


def messages(tag):
    video = os.path.join(WORK, f"{tag}.320.mp4")
    fps = fps_of(video)
    best = {n: [] for n in MSG}
    last, scores = None, {n: 0.0 for n in MSG}
    for i, f in enumerate(frames(video)):
        s = int(i / fps)
        for n in best:
            if s >= len(best[n]):
                best[n].append(0.0)
        if i % 2:
            continue
        band = f[26:60, 40:280]
        if band.max() - band.min() < 20:
            continue
        if last is None or np.abs(band - last).mean() >= 0.5:
            last = band
            scores = {n: ncc_max(band, tpl) for n, tpl in MSG.items()}
        for n in scores:
            best[n][s] = max(best[n][s], scores[n])
    np.savez_compressed(os.path.join(WORK, f"{tag}.messages.npz"), **{n: np.array(v, dtype=np.float32) for n, v in best.items()})
    for n in best:
        a = np.array(best[n])
        print(n, "max", round(float(a.max()), 3), "seconds>0.75", [int(x) for x in np.flatnonzero(a > 0.75)][:40])


def steps(tag, t0, t1):
    """Tile steps and screen advances between two video seconds: the shift of the
    scene between consecutive frames, read on the (18, 9) lattice of the
    isometric tile, and screen changes without a shift."""
    video = os.path.join(WORK, f"{tag}.320.mp4")
    prev, total, skipped, advances = None, 0, 0, 0
    win = None
    for f in frames(video, t0=t0, t1=t1):
        g = f[8:192]
        if prev is not None:
            if win is None:
                win = np.outer(np.hanning(g.shape[0]), np.hanning(g.shape[1])).astype(np.float32)
            fa, fb = np.fft.rfft2((prev - prev.mean()) * win), np.fft.rfft2((g - g.mean()) * win)
            r = fa * np.conj(fb)
            r /= np.abs(r) + 1e-6
            c = np.fft.irfft2(r, s=g.shape)
            y, x = np.unravel_index(np.argmax(c), c.shape)
            peak = float(c[y, x])
            dy = int(y - g.shape[0]) if y > g.shape[0] // 2 else int(y)
            dx = int(x - g.shape[1]) if x > g.shape[1] // 2 else int(x)
            dx, dy = -dx, -dy
            if (dx, dy) == (0, 0):
                advances += int(float(np.abs(g - prev).mean()) > 6.0)
            elif peak < 0.25 or dx % 18 or dy % 9 or (abs(dx) // 18) % 2 != (abs(dy) // 9) % 2:
                skipped += 1
            else:
                total += max(abs(dx) // 18, abs(dy) // 9)
        prev = g
    print(f"tile steps {total}, screen advances {advances}, off-lattice shifts skipped {skipped}")


def report(tag, start=None):
    video = os.path.join(WORK, f"{tag}.320.mp4")
    sc = np.load(os.path.join(WORK, f"{tag}.scores.npz"))
    ev = json.load(open(os.path.join(WORK, f"{tag}.scan.json"), encoding="utf-8"))
    rd = os.path.join(WORK, f"{tag}-report")
    os.makedirs(rd, exist_ok=True)

    def grab(t):
        return next(frames(video, t0=t, t1=t + 0.5))[:200]

    def sheet(name, times, cols=6, label=None):
        ims = [(t, Image.fromarray(grab(t).astype(np.uint8))) for t in times]
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new("L", (320 * cols, 200 * max(rows, 1)), 0)
        d = ImageDraw.Draw(sh)
        for i, (t, im) in enumerate(ims):
            x, y = (i % cols) * 320, (i // cols) * 200
            sh.paste(im, (x, y))
            d.rectangle((x, y, x + 70, y + 12), fill=0)
            d.text((x + 3, y + 1), label(t) if label else f"{t:.1f}s", fill=255)
        sh.save(os.path.join(rd, name))

    if start is None:
        room = ROOM[100:200, 40:280]
        for i, f in enumerate(frames(video)):
            if i % 15 == 0 and R.ncc(f[100:200, 40:280], room) > 0.55:
                start = i / ev["fps"]
                break
        print("start of play by the opening room:", start)
    blacks = [b for b in ev["black"] if b > start]
    print("start", start, "first black after start", blacks[0] if blacks else None)
    ob = sc["obtained"]
    thr = next((float(lo + 0.05) for lo in np.arange(0.45, 0.85, 0.05)
                if ((ob >= lo) & (ob < lo + 0.05)).sum() == 0 and (ob >= lo + 0.05).sum() > 0), None)
    print("obtained threshold from the gap of the score distribution:", thr)
    runs = []
    if thr:
        for s in [int(x) for x in np.flatnonzero(ob >= thr)]:
            if runs and s - runs[-1][-1] <= 1:
                runs[-1].append(s)
            else:
                runs.append([s])
        x0, y0, x1, y1 = R.META["obtained"]["box"]
        lo_, hi_ = R.META["obtained"]["slide"]
        oh, ow = R.TPL["obtained"].shape
        tiles = []
        for r in runs:
            bestf = (0.0, None)
            for f in frames(video, t0=max(0, r[0] - 0.2), t1=r[-1] + 1.2):
                v = ncc_max(f[y0 - 2:y1 + 2, lo_:hi_ + ow + 3], R.TPL["obtained"])
                if v > bestf[0]:
                    bestf = (v, f)
            tiles.append((r[0], bestf[0], Image.fromarray(bestf[1].astype(np.uint8)).crop((50, 38, 270, 68)).resize((660, 90), Image.NEAREST)))
        if tiles:
            sh = Image.new("L", (780, 90 * len(tiles)), 0)
            d = ImageDraw.Draw(sh)
            for i, (s, v, im) in enumerate(tiles):
                sh.paste(im, (120, i * 90))
                m = (s - start) / 60
                d.text((4, i * 90 + 35), f"{int(m):02d}:{int((m % 1) * 60):02d} {v:.2f}", fill=255)
            sh.save(os.path.join(rd, "obtained.png"))
    print("obtained messages (video s):", [r[0] for r in runs][:80])

    def runs_of(name, thr_=0.8, gap=3):
        out = []
        for s in [int(x) for x in np.flatnonzero(sc[name] > thr_)]:
            if out and s - out[-1][-1] <= gap:
                out[-1].append(s)
            else:
                out.append([s])
        return [(r[0], r[-1]) for r in out]

    for n in R.NAMES:
        print(n, "max", round(float(sc[n].max()), 3), "runs>0.8", runs_of(n)[:12])
    sheet("black.png", [b + 1.6 for b in blacks[:12]], label=lambda t: f"{t - 1.6:.1f}s")
    fights = runs_of("battle")
    if fights:
        f0, f1 = fights[0]
        sheet("fight.png", [f0 - 2, f0, f0 + 2, f0 + 5] + [f1 + d for d in (0, 1, 2, 3, 4, 5, 7, 9)])
    prompts = runs_of("prompt")
    if prompts:
        sheet("prompt.png", [t for p0, p1 in prompts[:3] for t in (p0 - 2, p0 - 1, p0, p0 + 0.5, p1 + 1, p1 + 2)])
    firsts = [runs_of(n)[0][0] + 0.5 for n in ("hermit", "compass", "defeat") if runs_of(n)]
    if blacks:
        firsts += [blacks[0] - 0.3, blacks[0] + 1.6]
    if firsts:
        sheet("first.png", firsts)
    print("sheets in", rd)


def boxes(tag, start, record=None):
    """The conversations, saves and loads of a capture, read by the service's
    own detectors in their capture mode (events.outlined: a capture blurs the
    border the live reader thresholds). A benchmark session starts on the
    last lines of the opening tutorial's guide, so conversations count from
    the guide's last box of the opening on; minutes run from `start`, the
    clock start of the video's entry. Every capture is the player's own, so
    every save notice is a save."""
    video = os.path.join(WORK, f"{tag}.320.mp4")
    fps = fps_of(video)
    sc = R.Scanner(1, known={}, capture=True)
    guide = []
    for i, f in enumerate(frames(video)):
        g, t = f[:200], i / fps
        sc.boxes(g, t)
        if (R.outlined(g, R.PORTRAITS["top-left"])
                and R.ncc(R._crop(g, R.GUIDE_BOX), R.BOXES["guide"]) > 0.6):
            if not guide or t - guide[-1] <= OPENING_GAP:
                guide.append(t)
    sc.close_over()
    opening = guide[-1] if guide else start
    talks = [x for x in sc.talks if x[0] > opening]
    minute = (lambda s: round((s - start) / 60, 1))
    d = R.conversations(talks, 1.0)
    saves = [{"minute": minute(t), "slot": None if s is None else s + 1} for t, row, s in sc.notices if row == R.SAVE]
    loads = [{"minute": minute(t), "slot": None if s is None else s + 1} for t, row, s in sc.notices if row == R.LOAD]
    loads += [{"minute": minute(t), "slot": s + 1, "after_defeat": True} for t, s in sc.over_loads]
    loads.sort(key=lambda x: x["minute"])
    unread = [round(t, 1) for t, row, s in sc.notices if row is None]
    starts = []
    for k, (t0, t1, _) in enumerate(talks):
        if not k or (t0 - talks[k - 1][1]) > R.TALK_GAP:
            starts.append(t0)
    out = {"dialogue": {"count": d["count"], "distinct": d["distinct"],
                        "first_minute": minute(starts[0]) if starts else None},
           "saves": saves, "loads": loads,
           "conversation_minutes": [minute(s) for s in starts],
           "conversation_seconds": [round(s, 2) for s in starts],
           "opening_end_s": round(opening, 2), "notice_seconds": [round(t, 2) for t, _, _ in sc.notices],
           "unread_notices_s": unread}
    json.dump(out, open(os.path.join(WORK, f"{tag}.boxes.json"), "w"), indent=1)
    print(f"{tag}: opening ends {opening:.1f}s; {d['count']} conversations ({d['distinct']} distinct), "
          f"{len(saves)} saves, {len(loads)} loads, unread notices {unread}")
    print("saves", saves)
    print("loads", loads)
    if record:
        sheet = boxes_sheet(video, record, [t for t, _, _ in sc.notices] + [t for t, _ in sc.over_loads])
        path = os.path.join(FIG, "human_sessions.json")
        videos = json.load(open(path, encoding="utf-8"))
        v = next(v for v in videos if v["id"] == record)
        v["boxes"] = {k: out[k] for k in ("dialogue", "saves", "loads")}
        v["boxes"]["read"] = (f"read_video.py boxes: the dialogue frame, 請稍候 beside the lit row of the system "
                              f"menu and the 載入進度 menu, by their outline (events.outlined); conversations from "
                              f"{opening:.1f}s, the guide's last box of the opening; notices in {sheet}")
        json.dump(videos, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("recorded under", record)
    return out


def boxes_sheet(video, vid, seconds, cols=4):
    """The first frame of every save or load notice: a capture may show one for a fifth of a second."""
    rel = os.path.join("evidence", vid, "boxes.jpg")
    if not seconds:
        return "no notice"
    rows = (len(seconds) + cols - 1) // cols
    sheet = Image.new("L", (cols * 320, rows * 214), 0)
    d = ImageDraw.Draw(sheet)
    for k, s in enumerate(seconds):
        x, y = (k % cols) * 320, (k // cols) * 214
        sheet.paste(Image.fromarray(frame_at(video, s + 0.02)[:200].astype(np.uint8)), (x, y))
        d.text((x + 4, y + 201), f"{s:.1f}s", fill=255)
    os.makedirs(os.path.join(HERE, "evidence", vid), exist_ok=True)
    sheet.save(os.path.join(HERE, rel), quality=70)
    return "figures/human/" + rel


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "calibrate":
        calibrate(args[0], [float(a) for a in args[1:]])
    elif cmd == "findcrop":
        findcrop(args[0], *[float(a) for a in args[1:]])
    elif cmd == "refinecrop":
        refinecrop(args[0], *[float(a) for a in args[1:]])
    elif cmd == "edgecrop":
        edgecrop(args[0], *[float(a) for a in args[1:]])
    elif cmd == "prep":
        prep(args[0], args[1], args[2].split("=", 1)[-1])
    elif cmd == "scan":
        scan(args[0])
    elif cmd == "messages":
        messages(args[0])
    elif cmd == "steps":
        steps(args[0], float(args[1]), float(args[2]))
    elif cmd == "report":
        start = next((float(a.split("=", 1)[1]) for a in args[1:] if a.startswith("start=")), None)
        report(args[0], start)
    elif cmd == "boxes":
        kw = dict(a.split("=", 1) for a in args[1:])
        boxes(args[0], float(kw["start"]), kw.get("record"))
    else:
        sys.exit(__doc__)


def caption_rows(tag, t0, t1, factor=2.5):
    """the rows a burned-in title or subtitle occupies in this capture.

    A capture often carries a caption the game never drew - a channel title across the
    top, a line of commentary - and it changes every frame. The step counter reads a
    change of the whole screen without a shift as a screen change, so such a caption is
    counted as presses the player never made. The rows come from comparing each row's
    mean frame-to-frame change against the median of all rows: a caption band changes far
    more than the scene it lies on."""
    fs=[f[:200] for f in frames(os.path.join(WORK, f"{tag}.320.mp4"), t0=t0, t1=t1)]
    if len(fs)<8:
        return []
    A=np.stack(fs)
    row=np.abs(np.diff(A,axis=0)).mean(axis=0).mean(axis=1)
    med=float(np.median(row)) or 1e-6
    return [int(y) for y in np.flatnonzero(row > factor*med)]


def steps_gap(tag, t0, t1, lo=5.0, hi=20.0):
    """tile steps and screen changes, the threshold taken from this capture.

    A screen change - a line of dialogue, a menu, the fade onto the world map - repaints
    the whole frame, so its mean frame-to-frame difference is large. A soft capture's
    compression churn is small but not negligible, and a fixed threshold of six lets it
    through: this capture's own distribution sits at 0.07 at the median with a tail to 32,
    and six counts 56 presses the player never made. So the threshold is set in the gap of
    the no-shift differences of this capture, searched between five and twenty where the
    two populations separate, exactly as the panels are matched at each video's own gap."""
    v = os.path.join(WORK, f"{tag}.320.mp4")
    fps = fps_of(v)
    prev, win, zero, shifts = None, None, [], []
    for f in frames(v, t0=t0, t1=t1):
        g = f[8:192]
        if prev is not None:
            if win is None:
                win = np.outer(np.hanning(g.shape[0]), np.hanning(g.shape[1])).astype(np.float32)
            fa, fb = np.fft.rfft2((prev - prev.mean()) * win), np.fft.rfft2((g - g.mean()) * win)
            r = fa * np.conj(fb); r /= np.abs(r) + 1e-6
            c = np.fft.irfft2(r, s=g.shape)
            y, x = np.unravel_index(np.argmax(c), c.shape)
            dy = int(y - g.shape[0]) if y > g.shape[0] // 2 else int(y)
            dx = int(x - g.shape[1]) if x > g.shape[1] // 2 else int(x)
            dx, dy = -dx, -dy
            if (dx, dy) == (0, 0):
                zero.append(float(np.abs(g - prev).mean()))
            elif float(c[y, x]) < 0.25 or dx % 18 or dy % 9 or (abs(dx) // 18) % 2 != (abs(dy) // 9) % 2:
                shifts.append((-1, 0))
            else:
                shifts.append((max(abs(dx) // 18, abs(dy) // 9), 0))
        prev = g
    tiles = sum(a for a, _ in shifts if a > 0)
    z = np.sort(np.array(zero))
    band = z[(z >= lo) & (z <= hi)]
    thr = 8.0
    if len(band) > 3:
        d = np.diff(band)
        k = int(np.argmax(d))
        thr = round(float((band[k] + band[k + 1]) / 2), 2)
    advances = int((z > thr).sum())
    adv6 = int((z > 6.0).sum())
    print(f"{tag}: threshold {thr} (fixed 6.0 would count {int((z > 6.0).sum())}) | "
          f"tile steps {tiles}, screen advances {advances}, total {tiles + advances}, "
          f"no-shift frames {len(z)}, median {float(np.median(z)):.2f}" if len(z) else f"{tag}: no frames")
    return {"tile_steps": tiles, "screen_advances": advances, "advances_at_6": adv6,
            "total": tiles + advances, "threshold": thr,
            "median_diff": float(np.median(z)) if len(z) else None}


def steps_masked(tag, t0, t1, thr=6.0, factor=2.5):
    """as `steps`, but a screen change is judged on the rows the scene draws."""
    rows=set(caption_rows(tag,t0,t1,factor))
    keep=np.array([y for y in range(200) if y not in rows])
    video=os.path.join(WORK,f"{tag}.320.mp4"); fps=fps_of(video)
    prev=None; total=skipped=advances=0; win=None
    for i,f in enumerate(frames(video,t0=t0,t1=t1)):
        g=f[8:192]
        if prev is not None:
            if win is None:
                win=np.outer(np.hanning(g.shape[0]),np.hanning(g.shape[1])).astype(np.float32)
            fa,fb=np.fft.rfft2((prev-prev.mean())*win),np.fft.rfft2((g-g.mean())*win)
            r=fa*np.conj(fb); r/=np.abs(r)+1e-6
            c=np.fft.irfft2(r,s=g.shape); y,x=np.unravel_index(np.argmax(c),c.shape)
            dy=int(y-g.shape[0]) if y>g.shape[0]//2 else int(y)
            dx=int(x-g.shape[1]) if x>g.shape[1]//2 else int(x); dx,dy=-dx,-dy
            if (dx,dy)==(0,0):
                d=np.abs(g-prev)
                k=keep[(keep>=8)&(keep<192)]-8
                advances+=int(float(d[k].mean())>thr)
            elif float(c[y,x])<0.25 or dx%18 or dy%9 or (abs(dx)//18)%2!=(abs(dy)//9)%2:
                skipped+=1
            else:
                total+=max(abs(dx)//18,abs(dy)//9)
        prev=g
    print(f"tile steps {total}, screen advances {advances}, off-lattice shifts skipped {skipped}"
          f", caption rows masked {len(rows)}")
    return {"tile_steps":total,"screen_advances":advances,"total":total+advances,"caption_rows":sorted(rows)}
