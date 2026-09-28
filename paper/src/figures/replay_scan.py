"""Read the events the game keeps no persistent record of out of the published replays.

    python3 figures/replay_scan.py [VIDEO_DIR]

Five panels the game draws at a fixed screen position are matched against
every frame of every published replay video, by normalised cross-correlation
against the crops in server/measure/assets/templates (cut from frames of this
field and described in templates.json). A panel counts when it scores above the threshold over
HOLD seconds of play: two consecutive frames of a replay at 8 times speed and
20 frames a second, one frame at 24 times speed, where a frame spans 1.2
seconds of play. The game holds these panels for a second or more, so a
shorter match is a screen transition. Scores are
kept per video second as the best minimum over the frames of one hold; the maximum of a session with no hit is
reported beside it so the margin is on record. The five events:

    hermit    the hermit's portrait in the dialogue frame: the conversation began
    compass   the coordinate line the compass adds to the item screen: the compass is held
    battle    the acting character's card in a fight: a fight was entered
    defeat    the banner the game draws when the party loses: the fight ran to a verdict
    prompt    the yes-or-no prompt of a recruitable character; the game holds it
              until a key is pressed, so the companion joined when the first key
              pressed after it appeared is `y`

A sixth event, the message the game draws when an item enters the bag, is
centred on the screen and as wide as the name of the item, so its first two
glyphs, 得到 (obtained), are searched along their row over the offsets the
names produce. It confirms a change of the bag, which the model need not have
looked at, so a single frame counts; its template never scored above 0.35
without the message.

    obtained  an item entered the bag

Three more messages close a battle the party wins, each in the banner the game
draws on the row of the defeat banner and dismisses at the next key, so, like
the obtained message, a single frame counts; none of their templates scored
above 0.3 on a frame without the message:

    won       戰鬥勝利 (battle won), at a fixed position
    exp       獲得經驗 (gained experience), after the name of the character,
              so searched along the row
    level     升級了 (levelled up), after the name, searched along the row

A seventh reading is the scene the party is in. On entering a scene from the
world map the game draws the scene's name in a banner at the top of the
screen: a rounded cream border around a dark box with the name in gold, centred
and as wide as the name. Every frame is tested for that box; a rising edge is
an entry, and the interior of the box is matched against the banners in
server/measure/assets/templates/scenes/, one file per scene name, so the count of distinct scenes and
the visits to the home (王居) are read from the replay.

The scan also finds the first fully black game frame of each replay at the
full frame rate of the video: the game blacks the screen on a scene change,
and the first one in a session that starts inside the compound is the exit
onto the world map. The number of actions before it is the crossing count,
and it agrees with the count the service recorded from the same signal on
every session that carries both.

Videos are read from VIDEO_DIR/<id>.mp4, or fetched from the video_url of
each session on record when the directory has none. The output,
replay_events.json, is committed beside the snapshot; field.py reads it.
"""
import json
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "server"))
import field  # noqa: E402
from measure import events, session  # noqa: E402  the service reads its sessions with the same code


def unnamed(crop):
    """A banner no template matches is saved beside the others, to be named by hand."""
    n = len(os.listdir(events.SCENES)) + 1
    name = "scene-%02d" % n
    Image.fromarray(crop.astype(np.uint8)).save(os.path.join(events.SCENES, name + ".png"))
    return name


def scan(path, timeline, known):
    speed = timeline["speed"] if timeline else 8.0
    fps, frames = session.video_frames(path)
    sc = events.Scanner(np.ceil(events.HOLD * fps / speed - 1e-9), known=known, unnamed=unnamed)
    for i, (g, _) in enumerate(frames):
        sc.feed(g, i / fps)
    return sc.summary(speed, timeline["marks"] if timeline else None)


def main():
    vdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "videos")
    os.makedirs(vdir, exist_ok=True)
    rows = field.load_runs(dedup=False, keep_excluded=True)   # the scan covers the whole catalogue
    known = events.load_scene_templates()
    out = {}
    for r in sorted(rows, key=lambda r: (r["agent"], r["id"])):
        path = os.path.join(vdir, r["id"] + ".mp4")
        if not os.path.exists(path):
            url = r.get("video_url")
            if not url:
                sys.exit(f"{r['agent']} {r['id']}: no video on record")
            urllib.request.urlretrieve(url, path)
        tl_path = os.path.join(HERE, "timelines", r["id"] + ".json")
        tl = json.load(open(tl_path, encoding="utf-8")) if os.path.exists(tl_path) else None
        out[r["id"]] = e = {"agent": r["agent"], **scan(path, tl, known)}
        print(f"{r['agent']:22s} {r['id']} " + " ".join(
            f"{n}={e[n]['first_minute']}" for n in events.NAMES)
            + f" recruited={e['recruited_minute']} scenes={[x['name'] for x in e['scenes']['entries']]}",
            file=sys.stderr, flush=True)
    json.dump(out, open(os.path.join(HERE, "replay_events.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
