"""Measure every published session from its video, as the paper did, and put
the result on its catalogue entry.

    python bench/backfill_measure.py measure <catalog.json> <out dir> <worldmap cache> [--jobs N]
    python bench/backfill_measure.py publish <out dir> <bucket> <catalog object> <catalog.json> <worldmap cache>

`measure` reads each entry's video and keypress timeline from the bucket,
runs server/measure over every frame with the exact placement the paper's
figures use, and writes <out>/<id>.json (the measure block and the route
points) and the two route pictures. `publish` uploads the pictures and points
under routes/ and merges the blocks into the catalogue object with a
generation precondition, so a session that finishes meanwhile is not lost.
"""
import json
import multiprocessing as mp
import os
import pathlib
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "server"))

from measure import draw  # noqa: E402
from measure.ladder import STEPS, chain_minutes, rungs_of  # noqa: E402
from measure.routes import WorldMap  # noqa: E402
from measure.session import VERSION, crossing_keys, measure_video, world_marks  # noqa: E402

BUCKET_URL = "https://storage.googleapis.com/jy-crpg-bench-runs/"
EVENTS = ("hermit", "compass", "battle", "defeat", "prompt", "obtained", "won", "exp", "level")


def block(row, ev, house, world, speed, marks=None):
    """The measure block of a catalogue entry, the shape a live session writes."""
    r = dict(row, replay=ev)
    rungs = rungs_of(r)
    chain = chain_minutes(r, speed)
    return {"version": VERSION, "rungs": rungs, "reached": sum(1 for v in rungs if v is True),
            "chain": [chain[s] for s in STEPS],
            "first": {n: (ev.get(n) or {}).get("first_minute") for n in EVENTS},
            "scenes": [[e["minute"], e["name"]] for e in ev["scenes"]["entries"]],
            "crossing_actions": ev["crossing_actions"], "recruited_minute": ev["recruited_minute"],
            "crossing_keys": crossing_keys(marks, ev["first_black_second"]),
            "house_points": len(house), "world_points": len(world), "source": "replay"}


def fetch(url, path):
    if not path.exists():
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(path)
    return path


def one(args):
    row, out, cache, videos = args
    sid = row["id"]
    dest = out / f"{sid}.json"
    if dest.exists():
        return sid, "done before"
    try:
        video = fetch(row["video_url"], videos / f"{sid}.mp4")
        tl = None
        if row.get("timeline_url"):
            tlp = fetch(BUCKET_URL + row["timeline_url"], videos / f"{sid}.timeline.json")
            tl = json.loads(tlp.read_text())
        world = WorldMap(cache)
        m, res = measure_video(str(video), tl, world=world, memory=row)
        speed = tl["speed"] if tl else 8.0
        ev = res["events"]
        b = block(row, ev, res["house"], res["world"], speed, tl["marks"] if tl else None)
        budget = (row.get("budget") or 3600) / 60
        if len(res["house"]) >= 2:
            (out / f"{sid}-house.png").write_bytes(draw.house(res["house"], budget))
        if len(m.world.points) >= 2:
            png = draw.world(m.world.points, world, budget, marks=world_marks(m.world.points, ev))
            (out / f"{sid}-world.png").write_bytes(png)
        routes = {"columns_house": ["x", "y", "minute"], "house": res["house"],
                  "columns_world": ["px", "py", "x", "y", "minute"], "world": res["world"]}
        dest.write_text(json.dumps({"block": b, "routes": routes, "events": ev}, ensure_ascii=False))
        return sid, f"{b['reached']} milestones"
    except Exception as exc:
        return sid, f"failed: {type(exc).__name__}: {exc}"


def measure(catalog, out, cache, jobs):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    videos = out / "videos"
    videos.mkdir(exist_ok=True)
    rows = [r for r in json.loads(pathlib.Path(catalog).read_text()) if r.get("video_url")]
    with mp.Pool(jobs) as pool:
        for sid, what in pool.imap_unordered(one, [(r, out, cache, videos) for r in rows]):
            print(sid, what, flush=True)


def gs(*args, capture=False):
    return subprocess.run(["gcloud", "storage", *args], check=True, text=True,
                          capture_output=capture).stdout


def publish(out, bucket, catalog_object, catalog, cache):
    """Upload the pictures and points, then merge the blocks into the
    catalogue. Each block is rebuilt from the stored readings, the entry as it
    stands in `catalog` and its timeline, so a change to the rules reaches
    every session without measuring the videos again."""
    out = pathlib.Path(out)
    world_map = WorldMap(cache)
    rows = {r["id"]: r for r in json.loads(pathlib.Path(catalog).read_text())}
    done = {}
    stage = out / "publish"
    stage.mkdir(exist_ok=True)
    for f in sorted(out.glob("*.json")):
        sid = f.stem
        if sid not in rows:
            continue
        d = json.loads(f.read_text())
        tlp = out / "videos" / f"{sid}.timeline.json"
        tl = json.loads(tlp.read_text()) if tlp.exists() else None
        b = block(rows[sid], d["events"], d["routes"]["house"], d["routes"]["world"],
                  tl["speed"] if tl else 8.0, tl["marks"] if tl else None)
        (stage / f"{sid}.json").write_text(json.dumps(d["routes"]))
        b["routes_url"] = f"routes/{sid}.json"
        budget = (rows[sid].get("budget") or 3600) / 60
        house, world = d["routes"]["house"], d["routes"]["world"]
        pics = {"house": draw.house(house, budget) if len(house) >= 2 else None,
                "world": draw.world(world, world_map, budget, marks=world_marks(world, d["events"]))
                if len(world) >= 2 else None}
        for kind, png in pics.items():
            if png:
                (stage / f"{sid}-{kind}.png").write_bytes(png)
                b[kind + "_url"] = f"routes/{sid}-{kind}.png"
        done[sid] = b
    gs("cp", "--cache-control=public, max-age=3600", *[str(p) for p in sorted(stage.iterdir())],
       f"gs://{bucket}/routes/")
    for attempt in range(8):
        meta = json.loads(gs("objects", "describe", f"gs://{bucket}/{catalog_object}", "--format=json", capture=True))
        gen = meta["generation"]
        local = out / "catalog.json"
        gs("cp", f"gs://{bucket}/{catalog_object}#{gen}", str(local))
        runs = json.loads(local.read_text())
        n = 0
        for r in runs:
            if r.get("id") in done:
                r["measure"] = done[r["id"]]
                n += 1
        local.write_text(json.dumps(runs))
        try:
            gs("cp", "--if-generation-match", str(gen), "--cache-control=public, max-age=15",
               "--content-type=application/json", str(local), f"gs://{bucket}/{catalog_object}")
            print(f"merged {n} of {len(done)} measured sessions into {len(runs)} entries")
            return
        except subprocess.CalledProcessError:
            print("the catalogue changed meanwhile; merging again", flush=True)
    raise SystemExit("the catalogue is too contended to merge into")


if __name__ == "__main__":
    if sys.argv[1] == "measure":
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else os.cpu_count()
        measure(sys.argv[2], sys.argv[3], sys.argv[4], jobs)
    elif sys.argv[1] == "publish":
        publish(*sys.argv[2:7])
    else:
        sys.exit(__doc__)
