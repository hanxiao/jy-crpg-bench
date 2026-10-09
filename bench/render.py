#!/usr/bin/env python3
"""Turn a session recording into an MP4.

The recording is the same tile deltas the browser stream uses, so rendering is
replaying them onto a canvas and piping raw frames to ffmpeg. Doing it here
rather than in a browser means a run can be finalised with nobody watching.
"""
import base64
import json
import os
import struct
import subprocess
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BAR = 32                 # strip under the game for the actor, action and keys
FPS = 20                 # output frame rate
# Native resolution. A benchmark run starts from a savestate already in the
# game, so the picture is 320x200 throughout; the 640x400 publisher intro only
# appears when booting from cold. Anything larger is scaled down to fit rather
# than the whole video being inflated to suit it.
GAME_W, GAME_H = 320, 200
GLYPH = {"up": "↗", "kp9": "↗", "upright": "↗", "ne": "↗",
         "down": "↙", "kp1": "↙", "downleft": "↙", "sw": "↙",
         "left": "↖", "kp7": "↖", "upleft": "↖", "nw": "↖",
         "right": "↘", "kp3": "↘", "downright": "↘", "se": "↘",
         "enter": "⏎", "space": "␣", "esc": "esc", "backspace": "⌫"}


def _font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/System/Library/Fonts/Menlo.ttc",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def apply_delta(canvas, raw):
    """Paint one tile delta. Returns the canvas, reallocating on a mode change."""
    d = zlib.decompress(raw)
    _flags, w, h, tw, th, cols, _rows, count = struct.unpack_from("<BHHBBHHH", d, 0)
    if canvas is None or canvas.shape[1] != w or canvas.shape[0] != h:
        canvas = np.zeros((h, w, 3), np.uint8)
    idx_off, data_off = 13, 13 + count * 2
    tile_len = tw * th * 3
    for i in range(count):
        t = struct.unpack_from("<H", d, idx_off + i * 2)[0]
        x, y = (t % cols) * tw, (t // cols) * th
        src = np.frombuffer(d, np.uint8, tile_len, data_off + i * tile_len)
        src = src.reshape(th, tw, 3)
        ch, cw = min(th, h - y), min(tw, w - x)
        if ch > 0 and cw > 0:
            canvas[y:y + ch, x:x + cw] = src[:ch, :cw]
    return canvas


# A run can now be as long as a day. At a fixed 4x that would be a six hour
# video nobody watches and a render nobody waits for, so playback speeds up for
# long runs to keep the result bounded. Short runs are untouched.
MAX_VIDEO_SECONDS = float(os.environ.get("QUNXIA_MAX_VIDEO_SECONDS", "600"))


def action_fields(event, ordinal):
    """Normalize viewer labels without changing numbered benchmark actions."""
    action = event['act']
    if isinstance(action, str):
        label = event.get('label')
        if not isinstance(label, str) or not label:
            label = f"{action} {event.get('on') or ''}".rstrip()
        # Interactive GET/KEY markers have no benchmark action number. This
        # ordinal identifies their position in the offline viewer only.
        return ordinal, label
    return action, event.get('label', '')


# Published replays run at this speed unless the run is long enough to hit
# MAX_VIDEO_SECONDS, when they run faster.
DEFAULT_SPEED = 8.0



def last_frame(video, out):
    """The video's last frame as a JPEG. `video` may be a URL: ffmpeg seeks
    near the end, so only that part is fetched. A frame caught in a screen
    transition is black; then the frame a few seconds earlier stands in, and
    a run that really ended in the dark keeps its last frame."""
    for back in (1, 4, 12):
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-sseof", f"-{back}",
             "-i", str(video), *(["-update", "1"] if back == 1 else ["-frames:v", "1"]),
             "-q:v", "4", str(out) + ".try.jpg"],
            check=True, timeout=60)
        with Image.open(str(out) + ".try.jpg") as im:
            g = np.asarray(im.convert("L"))   # the game, without the strip under it
            dark = g[:g.shape[0] * 200 // 232].mean() < 10
        if back == 1 or not dark:
            os.replace(str(out) + ".try.jpg", out)
        if not dark:
            break
    Path(str(out) + ".try.jpg").unlink(missing_ok=True)


def render(recording, out_path, agent="", speed=DEFAULT_SPEED, width=960, timeline_extra=None):
    events = recording.get("events") or []
    first_frame = next((e for e in events if "d" in e), None)
    if first_frame is None:
        raise ValueError("recording has no frames")

    # Start when the agent starts playing, not when the machine came up. The
    # gap between the two is the harness booting and the model reading its
    # brief, which is dead air on screen. Every delta before that point is
    # still applied to the canvas below, so the first rendered frame shows the
    # game as the agent found it rather than the black an earlier version had.
    acted = next((e["t"] for e in events
                  if e.get("act") is not None or e.get("key")), None)
    t_start = acted if acted is not None else first_frame["t"]
    t_end = recording.get("duration")
    if t_end is None:
        t_end = events[-1]["t"]
    span = t_end - t_start
    speed = max(speed, span / MAX_VIDEO_SECONDS)
    duration = max(0.2, span / speed)

    # A timeline of what happened and when, in video seconds. A few KB beside
    # a 1MB MP4, which is what makes the replay scrubbable without shipping the
    # 100MB+ recording to a browser.
    timeline = Path(out_path).with_suffix('.timeline.json')
    # Stream completed action marks; long recordings need no growing list.
    meta = dict(speed=round(speed, 3), seconds=round(duration, 2),
                size=[GAME_W, GAME_H + BAR], bar=BAR, **(timeline_extra or {}))
    with timeline.open('w') as stream:
        stream.write(json.dumps(meta)[:-1] + ',"marks":[')
        mark, held, first, ordinal = None, {}, True, 0
        for e in events:
            vt = round((e['t'] - t_start) / speed, 3)
            if vt < 0:
                continue
            if e.get('act') is not None:
                ordinal += 1
                if mark is not None:
                    stream.write(('' if first else ',') + json.dumps(mark))
                    first = False
                number, label = action_fields(e, ordinal)
                mark = {'n': number, 't': vt, 'do': label, 'keys': []}
            elif e.get('key'):
                if e.get('down'):
                    held[e['key']] = e['t']
                else:
                    down = held.pop(e['key'], None)
                    if mark is not None:
                        mark['keys'].append([e['key'], round(e['t'] - down if down is not None else 0, 3)])
        if mark is not None:
            stream.write(('' if first else ',') + json.dumps(mark))
        stream.write(']}')

    canvas = None
    for e in events:
        if "d" in e:
            canvas = apply_delta(canvas, base64.b64decode(e["d"]))
            break

    out_w, out_h = GAME_W, GAME_H + BAR
    name_font, key_font = _font(10), _font(11)
    bar_cache, bar_key = None, None

    def bar_image(actor, act, clock, keys):
        img = Image.new("RGB", (out_w, BAR), (16, 16, 20))
        dr = ImageDraw.Draw(img)
        y = BAR // 2
        x = 6
        if actor:
            dr.text((x, y), actor, font=name_font, fill=(150, 190, 230), anchor="lm")
            x += int(dr.textlength(actor, font=name_font)) + 8
        stamp = f"#{act}" if act is not None else ""
        if stamp:
            dr.text((x, y), stamp, font=name_font, fill=(200, 170, 110), anchor="lm")
            x += int(dr.textlength(stamp, font=name_font)) + 8
        for k in keys[:4]:
            label = GLYPH.get(k, k)
            kw = int(dr.textlength(label, font=key_font)) + 8
            dr.rectangle([x, 6, x + kw, BAR - 6], fill=(30, 30, 38),
                         outline=(70, 90, 110))
            dr.text((x + kw // 2, y), label, font=key_font,
                    fill=(142, 205, 247), anchor="mm")
            x += kw + 4
        mm, ss = divmod(int(clock), 60)
        dr.text((out_w - 6, y), f"{mm}:{ss:02d}", font=name_font,
                fill=(120, 120, 132), anchor="rm")
        return np.asarray(img)

    def blit(dst, src):
        """Fit a frame of any mode into the native-sized game area."""
        h_, w_ = src.shape[0], src.shape[1]
        if w_ > GAME_W or h_ > GAME_H:                 # cold-boot 640x400
            step = max(1, -(-w_ // GAME_W), -(-h_ // GAME_H))
            src = src[::step, ::step]
            h_, w_ = src.shape[0], src.shape[1]
        oy, ox = (GAME_H - h_) // 2, (GAME_W - w_) // 2
        dst[:GAME_H] = 0
        dst[oy:oy + h_, ox:ox + w_] = src

    ff = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{out_w}x{out_h}",
         "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)],
        stdin=subprocess.PIPE)

    down, actor, act, ordinal = [], agent, None, 0
    cursor = iter(events)
    pending = next(cursor, None)
    total_frames = max(1, int(duration * FPS))
    frame = np.zeros((out_h, out_w, 3), np.uint8)
    try:
        for n in range(total_frames):
            now = t_start + (n / FPS) * speed
            while pending is not None and pending["t"] <= now:
                e = pending
                pending = next(cursor, None)
                if "d" in e:
                    canvas = apply_delta(canvas, base64.b64decode(e["d"]))
                elif e.get("act") is not None:
                    ordinal += 1
                    act, _ = action_fields(e, ordinal)
                    if e.get("who"):
                        actor = e["who"]
                elif e.get("key"):
                    if e.get("who"):
                        actor = e["who"]
                    if e.get("down"):
                        if e["key"] not in down:
                            down.append(e["key"])
                    elif e["key"] in down:
                        down.remove(e["key"])
            elapsed = int(now - t_start)
            key = (actor, act, elapsed, tuple(down))
            if key != bar_key:
                bar_cache, bar_key = bar_image(actor, act, elapsed, down), key
            blit(frame, canvas)
            frame[GAME_H:] = bar_cache
            ff.stdin.write(frame.tobytes())
    finally:
        ff.stdin.close()
        ff.wait()

    # A still to show before the video loads. Without one, a card is a blank
    # box: the thumbnails are preload="none" so nothing is fetched until they
    # scroll into view, and on iOS often not even then. Measured in WebKit at
    # an iPhone size, two of eight cards ever painted a frame. It is the last
    # frame, where the run ended: the first second of every run is the same
    # opening room, so a wall of them showed one world many times.
    poster = Path(str(out_path)).with_suffix(".jpg")
    try:
        last_frame(out_path, poster)
    except Exception as exc:
        print(f"poster failed: {exc}", flush=True)
        poster = None

    return {"path": str(out_path), "seconds": round(duration, 1),
            "frames": total_frames, "size": f"{out_w}x{out_h}",
            "speed": round(speed, 3), "timeline": str(timeline),
            "poster": str(poster) if poster and poster.exists() else None}


if __name__ == "__main__":
    import sys
    rec = json.load(open(sys.argv[1]))
    print(render(rec, sys.argv[2], agent=sys.argv[3] if len(sys.argv) > 3 else ""))
