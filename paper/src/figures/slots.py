"""Every preserved save in slots/, decoded once with the service's own decoder.

A session's slot is the last save the game wrote in it, preserved by the
service when the session ended; `seed` is the slot every session starts with,
so a slot equal to the seed means no save landed. Beyond what from_archive
reports, the scene table is read for the entry conditions, which the
conversation of the hermit clears for the scenes the opening keeps closed.
"""
import glob
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = os.path.join(HERE, "slots")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "server"))
import save_state  # noqa: E402

COND_AT = 18     # entry condition of a scene, int16 in its 52-byte record; 0 is open


def _sections(stem):
    grp = open(stem + ".grp", "rb").read()
    idx = open(stem + ".idx", "rb").read()
    return save_state.split_archive(grp, idx)


def _open_scenes(submaps):
    return sum(1 for k in range(save_state.SUBMAP_SLOTS)
               if struct.unpack_from("<h", submaps, k * save_state.SUBMAP_SZ + COND_AT)[0] == 0)


def _decode(stem):
    sec = _sections(stem)
    s = save_state.from_archive(open(stem + ".grp", "rb").read(), open(stem + ".idx", "rb").read())
    p = s["position"]
    lead = s["team"][0] if s["team"] else {}
    return {
        "signature": (lead.get("name"), p["x"], p["y"], p["sub_x"], p["sub_y"]),
        "bag": (sum(s["bag"].values()), len(s["bag"])),
        "open_scenes": _open_scenes(sec[save_state.SEC_SUBMAPS]),
        "team_size": s["team_size"], "books": s["books"],
        "compass": bool(s["bag"].get(save_state.COMPASS_ID)),
        "level": lead.get("level"), "exp": lead.get("exp"), "hp": lead.get("hp"),
        "skills": lead.get("skills"), "x": p["x"], "y": p["y"],
    }


def scenes():
    """(named scenes, open at the start, open once the hermit has spoken):
    the scene table of the seed, and of every save that shows the hermit's
    conversation held, which all agree."""
    seed = _sections(os.path.join(SLOTS, "seed"))[save_state.SEC_SUBMAPS]
    named = len(save_state.decode_submaps(seed))
    start = _open_scenes(seed)
    after = {d["open_scenes"] for d in load().values() if d["world_opened"]}
    if len(after) != 1:
        raise SystemExit(f"saves after the hermit disagree on open scenes: {sorted(after)}")
    return named, start, after.pop()


def load():
    """``{session id: reading}`` for every slot on disk, with `saved` telling
    whether the game wrote it (the slot differs from the seed) and
    `world_opened` whether more scenes are open than the seed leaves open."""
    seed = _decode(os.path.join(SLOTS, "seed"))
    out = {}
    for grp in sorted(glob.glob(os.path.join(SLOTS, "*.grp"))):
        stem = grp[:-4]
        rid = os.path.basename(stem)
        if rid == "seed":
            continue
        d = _decode(stem)
        d["saved"] = d["signature"] != seed["signature"]
        d["picked_item"] = d["bag"] != seed["bag"]
        d["world_opened"] = d["open_scenes"] > seed["open_scenes"]
        d["seed_open_scenes"] = seed["open_scenes"]
        out[rid] = d
    return out


if __name__ == "__main__":
    for rid, d in load().items():
        print(rid, {k: v for k, v in d.items() if k not in ("signature",)})
