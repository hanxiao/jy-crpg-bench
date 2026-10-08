"""The milestones of the paper, and the chain of steps a playthrough passes.

A row is one session: the fields the service records from memory (the
inventory, the compass, the books), the save fields where a save was written,
and under "replay" the readings of events.Scanner.summary.
"""
from .events import HOME

KEYS = ("map", "item", "location", "hermit", "compass", "party", "battle", "ended", "exp", "level", "book")
DEFINITION = ("reached\nworld map", "picked up\nan item", "entered\na location", "spoke with\nthe hermit",
              "held the\ncompass", "recruited a\nparty member",
              "entered\na battle", "ended\na battle",
              "gained\nexperience", "reached\nlevel 2", "one of the\nfourteen")
MAP = 0


def rungs_of(row):
    """(reached | not reached | None for no reading) per milestone, from
    whichever record carries the event. The inventory and character records
    are read from emulator memory, the party and the world position from a
    save the game wrote, and the events the game keeps only on screen from the
    replay. A milestone with no record behind it is None; a session that wrote
    no save and whose replay shows no black frame did not reach the world map.
    Two readings follow the game's own rules: a session whose inventory no
    record carries takes the item from the message the game draws when an item
    enters it, and a session whose replay shows no battle gained no
    experience, reached no level and holds no book, since victories pay
    experience and every book sits behind a battle."""
    slot = row.get("slot_saved")
    saved = "saved_at" in row or "world_map_at" in row or slot is not None
    ev = row.get("replay")

    def seen(name):
        return bool(ev and ev.get(name) and ev[name]["seconds"] > 0)

    recruited = bool(ev and ev.get("recruited_minute") is not None)
    gained = (row.get("save_exp") or 0) > 0 or seen("exp")
    no_fight = ev is not None and not seen("battle")
    scenes = (ev or {}).get("scenes")
    crossed = bool(ev and ev.get("first_black_second") is not None)
    known = [
        True if saved or ev is not None else row.get("bigmap") is not None,
        bool(ev and ev.get("obtained")),
        scenes is not None,
        ev is not None,
        ev is not None or saved or row.get("compass") is not None,
        ev is not None or saved or row.get("team_size") is not None,
        ev is not None,
        ev is not None or "save_exp" in row,
        ev is not None or "save_exp" in row,
        ev is not None or "save_level" in row,
        (True if saved else row.get("books") is not None) or no_fight,
    ]
    got = [
        crossed or ((row.get("saved_at") is not None
                     or row.get("world_map_at") is not None
                     or slot is True) if saved
                    else bool(row.get("bigmap")) and row.get("exit_secs") is not None),
        seen("obtained"),
        bool(scenes and any(x["name"] != HOME for x in scenes["entries"])),
        seen("hermit"),
        bool(row.get("compass")) or seen("compass"),
        (row.get("team_size") or 0) > 1 or recruited,
        seen("battle"),
        seen("defeat") or seen("won") or gained,
        gained,
        (row.get("save_level") or 0) > 1 or seen("level"),
        (row.get("books") or 0) > 0,
    ]
    return [(g if k else None) for g, k in zip(got, known)]


def rungs_reached(row):
    return sum(1 for v in rungs_of(row) if v is True)


# The service grades three more after the paper's eleven, which the paper
# does not read: a conversation, a save and a load, each reached once it
# happened at least once.
COUNTER_KEYS = ("talk", "save", "load")
SERVICE_KEYS = KEYS + COUNTER_KEYS


def counter_rungs(ev):
    """Talked, saved and loaded at least once, from a reading or a measure
    block, both of which carry `dialogue`, `saves` and `loads`. A reading
    older than these has none, and saves are unknown without the keypresses
    that tell the player's from the service's."""
    if not ev or "dialogue" not in ev:
        return [None, None, None]
    saves = ev.get("saves")
    return [(ev["dialogue"] or {}).get("count", 0) > 0,
            None if saves is None else len(saves) > 0,
            len(ev.get("loads") or []) > 0]


def service_rungs(row):
    """The fourteen the service grades: the paper's eleven, then the three."""
    return rungs_of(row) + counter_rungs(row.get("replay"))


# The steps every playthrough passes in order.
STEPS = ("leave_house", "enter_location", "reach_hermit", "enter_battle", "win_battle", "hold_book")


def chain_minutes(row, speed=None):
    """The minute of play each step of STEPS was first passed, or None.
    `speed` converts the replay clock of the first black frame to play time
    when the service recorded no crossing time of its own."""
    ev = row.get("replay") or {}
    on_map = rungs_of(row)[MAP] is True
    cross = None
    if on_map:
        if row.get("exit_secs") is not None:
            cross = row["exit_secs"] / 60
        elif ev.get("first_black_second") is not None and speed:
            cross = ev["first_black_second"] * speed / 60

    def first(name):
        return (ev.get(name) or {}).get("first_minute")

    return {"leave_house": cross,
            "enter_location": (ev.get("scenes") or {}).get("first_minute"),
            "reach_hermit": first("hermit"),
            "enter_battle": first("battle"),
            "win_battle": first("won"),
            "hold_book": row.get("book_minute")}
