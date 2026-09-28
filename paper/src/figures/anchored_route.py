"""A model's walk through the opening compound, placed frame by frame on a
fixed panorama of the compound, with its path drawn on it.

    python anchored_route.py <session id>

model_route.py chains the shift between consecutive frames, which drifts on
the open grass of the yard when a replay is recorded at a high speed and the
view jumps several tiles between frames. Here every frame of the replay, up to
its first black frame, is placed directly on a fixed panorama of the compound
at the offset of highest normalised cross-correlation, so every session lands
on the same picture and the panels of the figure can be compared.

The panorama is server/measure/assets/compound.png, built by compound_panorama.py
from human/templates/compound-bg.png, the compound stitched from a human
speedrun with the hero removed, and from the wider stitch of a model session
that walked the whole yard; the two are registered by cross-correlation and
the human stitch is kept where both cover a pixel.

The correlation is computed on the frame with a mask: the rows of the status
strip and any dialogue box (a white text run over a black panel) are left out,
and a frame that correlates below MIN_NCC or whose masked area exceeds a third
of the frame (a menu, a fight screen) is skipped. The fence and the walls
repeat, so a match is only accepted within MAX_JUMP px of the last placed
frame, and a frame that repeats the one before it, while the model thinks, is
not placed again. The hero is located as in the hybrid mode of
human/route.py: the scene scrolls to keep him on his tile, so while the view
moves between placed frames he stands on the spawn tile of the frame, and
while the view is clamped at a border of the scene he is the densest 24x40
block of pixels that differ from the panorama, from which he was removed,
kept within 60 px of his last screen position. His place on the compound is
the offset of the frame plus his screen position. The path is smoothed by a
running mean of three and written to routes/compound-<session>.json, one row
per placed frame with its minute of play; routes.py draws the figure from it.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "human"))
import field  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "server"))
from measure.routes import HouseTracker, dialogue_mask, masked_ncc_map  # noqa: E402,F401

W0, H0 = 320, 200
R0, R1 = 8, 192


def frames(path, t1):
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-t", str(t1),
           "-vf", f"crop={W0}:{H0}:0:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(W0 * H0 * 3)
        if len(buf) < W0 * H0 * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(H0, W0, 3)
    p.stdout.close()
    p.wait()


def fps_of(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    a, b = o.split("/") if "/" in o else (o, "1")
    return float(a) / float(b)


def track(video, t_end, speed, t_start=0.0):
    """The hero's path through the starting house in a video from t_start to
    t_end seconds, one (x, y, minute of play) per placed frame on the
    panorama; speed is the replay speed, 1 for a recording in real time."""
    fps = fps_of(video)
    t = HouseTracker()
    for i, f in enumerate(frames(video, t_end)):
        if i / fps >= t_start:
            t.feed(f, i / fps * speed / 60.0)
    print(video, "frames placed", len(t.points))
    return [tuple(p) for p in t.path()]


def main():
    sid = sys.argv[1]
    row = next(r for r in field.load_runs(dedup=False, keep_excluded=True) if r["id"] == sid)
    ev = json.load(open(os.path.join(HERE, "replay_events.json"), encoding="utf-8"))[sid]
    video = os.path.join(HERE, "videos", sid + ".mp4")
    if not os.path.exists(video):
        import urllib.request
        os.makedirs(os.path.dirname(video), exist_ok=True)
        urllib.request.urlretrieve(row["video_url"], video)
    speed = json.load(open(os.path.join(HERE, "timelines", sid + ".json"), encoding="utf-8"))["speed"]
    path = track(video, ev["first_black_second"], speed)
    os.makedirs(os.path.join(HERE, "routes"), exist_ok=True)
    out = os.path.join(HERE, "routes", f"compound-{sid}.json")
    json.dump({"session": sid, "agent": row["agent"], "columns": ["px", "py", "minute"],
               "rows": [[round(float(a), 1), round(float(b), 1), round(float(c), 3)] for a, b, c in path]}, open(out, "w"))
    print("wrote", out)


if __name__ == "__main__":
    main()
