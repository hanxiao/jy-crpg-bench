"""Read the events the game keeps no persistent record of out of the published replays.

    python3 figures/replay_scan.py [VIDEO_DIR]

Five panels the game draws at a fixed screen position are matched against
every published replay video at one frame a second, by normalised
cross-correlation against the crops in templates/ (cut from frames of this
field and described in templates.json). A match above the threshold is a
hit; the maximum score of a session with no hit is reported beside it so the
margin is on record. The five events:

    hermit    the hermit's portrait in the dialogue frame: the conversation began
    compass   the coordinate line the compass adds to the item screen: the compass is held
    battle    the acting character's card in a fight: a fight was entered
    defeat    the banner the game draws when the party loses: the fight ran to a verdict
    prompt    the yes-or-no prompt of a recruitable character; with a `y` key
              in the timeline within a minute of it, the companion was asked to join

Videos are read from VIDEO_DIR/<id>.mp4, or fetched from the video_url of
each session on record when the directory has none. The output,
replay_events.json, is committed beside the snapshot; field.py reads it.
"""
import json
import os
import subprocess
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import field  # noqa: E402

META = json.load(open(os.path.join(HERE, "templates", "templates.json"), encoding="utf-8"))
W, H = META["frame"]
THRESH = META["threshold"]
NAMES = ("hermit", "compass", "battle", "defeat", "prompt")
TPL = {n: np.asarray(Image.open(os.path.join(HERE, "templates", n + ".png")), dtype=np.float32) for n in NAMES}


def ncc(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def frames(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-vf",
                          f"fps={META['frames_per_second']},scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (W * H)
    return np.frombuffer(raw[:n * W * H], dtype=np.uint8).reshape(n, H, W).astype(np.float32)


def scan(path, timeline):
    fr = frames(path)
    speed = timeline["speed"] if timeline else 8.0
    out = {"video_seconds": len(fr)}
    hits = {}
    for n in NAMES:
        x0, y0, x1, y1 = META[n]["box"]
        sc = np.array([ncc(f[y0:y1, x0:x1], TPL[n]) for f in fr]) if len(fr) else np.zeros(0)
        idx = np.flatnonzero(sc > THRESH)
        hits[n] = idx
        out[n] = {"seconds": int(len(idx)), "max": round(float(sc.max()), 3) if len(sc) else None,
                  "first_minute": round(float(idx[0]) * speed / 60, 1) if len(idx) else None,
                  "minutes": [round(float(i) * speed / 60, 1) for i in idx]}
    # recruitment: the prompt on screen, then a `y` within a minute of video
    out["recruited_minute"] = None
    if len(hits["prompt"]) and timeline:
        ys = [m["t"] for m in timeline["marks"] if any(k == "y" for k, _ in m["keys"])]
        for i in hits["prompt"]:
            after = [t for t in ys if i <= t <= i + 60]
            if after:
                out["recruited_minute"] = round(after[0] * speed / 60, 1)
                break
    return out


def main():
    vdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "videos")
    os.makedirs(vdir, exist_ok=True)
    rows = field.load_runs(dedup=False)
    events = {}
    for r in sorted(rows, key=lambda r: (r["agent"], r["id"])):
        path = os.path.join(vdir, r["id"] + ".mp4")
        if not os.path.exists(path):
            url = r.get("video_url")
            if not url:
                sys.exit(f"{r['agent']} {r['id']}: no video on record")
            urllib.request.urlretrieve(url, path)
        tl_path = os.path.join(HERE, "timelines", r["id"] + ".json")
        tl = json.load(open(tl_path, encoding="utf-8")) if os.path.exists(tl_path) else None
        events[r["id"]] = {"agent": r["agent"], **scan(path, tl)}
        e = events[r["id"]]
        print(f"{r['agent']:22s} {r['id']} " + " ".join(
            f"{n}={e[n]['first_minute']}" for n in NAMES) + f" recruited={e['recruited_minute']}",
            file=sys.stderr, flush=True)
    json.dump(events, open(os.path.join(HERE, "replay_events.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
