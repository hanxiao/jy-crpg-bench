"""The gate that decides whether the game will save.

The game only offers 存檔 from the world map, and it says so by how tall its
menu is. These numbers were measured on the running game: the panel's left
border is a white column at x 21 starting at y 23, 122 pixels long for the
six-row world-map menu and 82 for the four-row one a scene offers.
"""
import importlib.util
import os
import pathlib
import sys
import unittest

SERVER_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))
SPEC = importlib.util.spec_from_file_location("qunxia_menu_server", SERVER_DIR / "server.py")
game_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(game_server)

W, H = 320, 200
MEASURED = {6: 122, 5: 102, 4: 82}      # rows -> border length in pixels


def frame(border=None, extra=()):
    """An RGB frame with the menu's left border, plus any stray white."""
    px = bytearray(W * H * 3)
    for y in range(H):
        for x in range(W):
            at = (y * W + x) * 3
            px[at:at + 3] = b"\x30\x60\x30"          # grass, not white
    def white(x, y):
        at = (y * W + x) * 3
        px[at:at + 3] = b"\xff\xff\xff"
    if border is not None:
        top, length = border
        for y in range(top, top + length):
            white(game_server.MENU_X, y)
    for x, y0, y1 in extra:
        for y in range(y0, y1):
            white(x, y)
    return bytes(px)


class FakeCore:
    def __init__(self, data):
        self.data = data

    def fb_snapshot(self, buf, cap, scale, w, h):
        w._obj.value, h._obj.value = W, H
        game_server.SNAP[0:len(self.data)] = self.data
        return len(self.data)


class MenuRowTests(unittest.TestCase):
    def rows(self, data):
        original = game_server.LIB
        game_server.LIB = FakeCore(data)
        try:
            return game_server.menu_rows()
        finally:
            game_server.LIB = original

    def test_the_measured_panels_read_back_as_themselves(self):
        for rows, length in MEASURED.items():
            self.assertEqual(self.rows(frame(border=(23, length))), rows)

    def test_no_menu_is_no_rows(self):
        self.assertEqual(self.rows(frame()), 0)

    def test_clouds_do_not_grow_the_panel(self):
        # This is the failure it was written for: the world map's drifting
        # clouds are white, and a bounding box over the panel's whole width
        # counted them, reading the six-row menu as seven and refusing to save
        # somewhere the game would have saved.
        clouds = ((21, 5, 15), (21, 150, 160), (40, 30, 45))
        self.assertEqual(self.rows(frame(border=(23, MEASURED[6]), extra=clouds)), 6)

    def test_a_white_column_somewhere_else_is_not_the_menu(self):
        self.assertEqual(self.rows(frame(extra=((21, 90, 190),))), 0)


if __name__ == "__main__":
    unittest.main()


class WithholdingTests(unittest.TestCase):
    """Who may read what a run has achieved.

    A model that can watch its own score can play the score, so a scored run
    keeps its numbers from everyone but the operator - while it is still being
    played. Once it is over the board publishes them anyway.
    """

    class Request:
        def __init__(self, token=None):
            self.query = {"token": token} if token else {}
            self.headers = {}

    def setUp(self):
        self.was_on = game_server.warden.ON
        self.was_done = game_server.warden.run["done"]
        self.was_token = os.environ.get("QUNXIA_RESET_TOKEN")
        os.environ["QUNXIA_RESET_TOKEN"] = "secret"

    def tearDown(self):
        game_server.warden.ON = self.was_on
        game_server.warden.run["done"] = self.was_done
        if self.was_token is None:
            os.environ.pop("QUNXIA_RESET_TOKEN", None)
        else:
            os.environ["QUNXIA_RESET_TOKEN"] = self.was_token

    def test_an_unscored_session_hides_nothing(self):
        game_server.warden.ON = False
        self.assertFalse(game_server.withheld(self.Request()))

    def test_recorded_coordinates_are_operator_only_even_unscored(self):
        game_server.warden.ON = False
        self.assertFalse(game_server.include_trajectory(self.Request()))
        self.assertTrue(game_server.include_trajectory(self.Request("secret")))

    def test_a_live_scored_run_hides_from_everyone_but_the_operator(self):
        game_server.warden.ON = True
        game_server.warden.run["done"] = None
        self.assertTrue(game_server.withheld(self.Request()))
        self.assertTrue(game_server.withheld(self.Request("wrong")))
        self.assertFalse(game_server.withheld(self.Request("secret")))

    def test_a_finished_run_hides_nothing(self):
        game_server.warden.ON = True
        game_server.warden.run["done"] = "time"
        self.assertFalse(game_server.withheld(self.Request()))

    def test_the_scored_set_covers_what_the_save_adds(self):
        for field in ("books", "items_total", "team_size", "team_level",
                      "team", "saved_at", "saved_why"):
            self.assertIn(field, game_server.SCORED_FIELDS)

    def test_the_compass_is_scored_withheld_and_published(self):
        # A rung a live run could read about itself is a rung it could play
        # to, so it is withheld like the rest, and it leaves with the run.
        for field in ("compass", "completion_secs", "first_saved_at",
                      "party_size", "world_map_at"):
            self.assertIn(field, game_server.SCORED_FIELDS)
            self.assertIn(field, game_server.warden.run)
            self.assertIn(field, game_server.warden.metrics())
            self.assertIn(field, game_server.session_summary())

    def test_the_brief_language_a_run_fetched_is_on_the_record(self):
        warden = game_server.warden
        was = dict(warden.run["help_langs"])
        try:
            warden.run["help_langs"] = {}
            for lang in ("zh", "zh-Hant", "en", None):
                warden.note_help(lang)
            self.assertEqual(warden.run["help_langs"], {"zh": 2, "en": 2})
            self.assertEqual(warden.metrics()["help_langs"], {"zh": 2, "en": 2})
        finally:
            warden.run["help_langs"] = was

    def test_the_archive_fills_in_what_the_live_bag_lags_on(self):
        hero = game_server.hero
        was = {k: hero[k] for k in ("compass", "books", "picked_item", "inventory_baseline", "completion_secs")}
        try:
            game_server.warden.ON = False
            hero.update(compass=False, books=0, picked_item=False, completion_secs=None,
                        inventory_baseline={0: 3, 2: 3})
            game_server.absorb_archive({"bag": {0: 3, 2: 3, 182: 1, 144: 1}, "books": 1})
            self.assertEqual((hero["compass"], hero["books"], hero["picked_item"]), (True, 1, True))
            # nothing the archive says can take a rung away
            game_server.absorb_archive({"bag": {0: 3}, "books": 0})
            self.assertEqual((hero["compass"], hero["books"], hero["picked_item"]), (True, 1, True))
        finally:
            hero.update(**was)

    def test_completion_latches_at_fourteen_books_and_stays(self):
        hero = game_server.hero
        was = dict(books=hero["books"], completion_secs=hero["completion_secs"])
        started = game_server.session["started"]
        try:
            game_server.warden.ON = False
            hero.update(books=13, completion_secs=None)
            self.assertIsNone(game_server.latch_completion(now=started + 50))
            hero["books"] = 14
            self.assertEqual(game_server.latch_completion(now=started + 61.26), 61.3)
            # a later read does not move the time, and a book put down does
            # not clear it: the game's ending was reached once
            hero["books"] = 13
            self.assertIsNone(game_server.latch_completion(now=started + 90))
            self.assertEqual(hero["completion_secs"], 61.3)
        finally:
            hero.update(**was)


class DisabledTests(unittest.TestCase):
    def test_zero_switches_the_macro_off(self):
        # The worker that authors the start state is driven through the
        # opening by a script. A save macro's escape in the middle of that
        # derails the replay, so the broker sets the interval to zero and the
        # task must return rather than loop.
        import asyncio
        was = game_server.SNAPSHOT_EVERY
        game_server.SNAPSHOT_EVERY = 0
        try:
            asyncio.run(asyncio.wait_for(game_server.snapshotter(), timeout=1))
        finally:
            game_server.SNAPSHOT_EVERY = was
