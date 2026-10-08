"""The measure the paper grades its sessions with, as the service runs it.

The whole scan was checked against every published replay the paper reads
(the events, the crossing, the recruitment and the location entries agree
exactly, and so does every committed route); these tests pin the pieces on
synthetic frames so a change to them shows here first.
"""
import pathlib
import sys
import time
import unittest

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from measure import events, ladder, routes, session  # noqa: E402
import live_measure  # noqa: E402


def frame_with(name):
    """A mid-gray game frame with the template of `name` drawn in its box."""
    f = np.full((200, 320), 90.0, np.float32)
    x0, y0, x1, y1 = events.META[name]["box"]
    f[y0:y1, x0:x1] = events.TPL[name]
    return f


class EventTests(unittest.TestCase):
    def test_a_held_panel_counts_only_when_held(self):
        sc = events.Scanner(need=3)
        blank = np.full((200, 320), 90.0, np.float32)
        sc.feed(frame_with("hermit"), 0.0)
        sc.feed(blank, 0.1)
        self.assertEqual(sc.hits("hermit"), [])
        for i in range(3):
            sc.feed(frame_with("hermit"), 1.0 + i * 0.1)
        self.assertEqual(sc.hits("hermit"), [1])

    def test_a_message_counts_on_one_frame(self):
        sc = events.Scanner(need=3)
        sc.feed(frame_with("won"), 2.0)
        self.assertEqual(sc.hits("won"), [2])

    def test_a_sliding_message_is_found_along_its_row(self):
        f = np.full((200, 320), 90.0, np.float32)
        t = events.TPL["obtained"]
        y0 = events.META["obtained"]["box"][1]
        x = events.META["obtained"]["slide"][0] + 11
        f[y0:y0 + t.shape[0], x:x + t.shape[1]] = t
        self.assertGreater(events.FrameScorer().score(f)["obtained"], events.THRESH)

    def test_the_first_black_frame_is_the_crossing(self):
        sc = events.Scanner(need=1)
        sc.feed(np.full((200, 320), 90.0, np.float32), 0.0)
        sc.feed(np.zeros((200, 320), np.float32), 3.5)
        sc.feed(np.zeros((200, 320), np.float32), 3.6)
        marks = [{"t": 1.0, "keys": [["kp9", 0.14]]}, {"t": 3.0, "keys": [["kp9", 0.14], ["kp3", 0.14]]},
                 {"t": 5.0, "keys": [["enter", 0.14]]}]
        s = sc.summary(8.0, marks)
        self.assertEqual(s["first_black_second"], 3.5)
        self.assertEqual(s["crossing_actions"], 2)
        self.assertEqual(session.crossing_keys(marks, 3.5), 3)

    def test_a_yes_after_the_prompt_is_a_recruitment(self):
        marks = [{"t": 9.5, "keys": [["y", 0.14]]}]
        self.assertEqual(events.recruited([9], marks, 8.0), round(9.5 * 8 / 60, 1))
        self.assertIsNone(events.recruited([9], [{"t": 9.5, "keys": [["n", 0.14]]}], 8.0))


def box(f, b, luma=255.0):
    """A white border along box b, with the rounded corners left out."""
    y0, y1, a, c = b
    f[y0, a:c] = f[y1, a:c] = luma
    f[y0 + 3:y1 - 2, a - 3] = f[y0 + 3:y1 - 2, c + 3] = luma


def lit(f, rows, height, x0, x1, k):
    """Menu lines in orange, line k in white."""
    for i, y in enumerate(rows):
        f[y + 4:y + height - 4:2, x0 + 2:x1 - 2:2] = 255.0 if i == k else 165.0


def put(f, b, img):
    y0, y1, a, c = b
    f[y0:y1, a:c] = img


class BoxTests(unittest.TestCase):
    """Dialogue, saves and loads, read from the boxes the game draws."""

    def blank(self):
        return np.full((200, 320), 60.0, np.float32)

    def talk(self, seed):
        f = self.blank()
        box(f, events.PORTRAITS["top-left"])
        put(f, events.TEXTS["top-left"], np.random.default_rng(seed).uniform(40, 255, (50, 204)))
        return f

    def test_a_returning_box_is_a_new_conversation_and_its_text_names_it(self):
        sc = events.Scanner(need=1)
        clock = [0.0]

        def feed(f, n=1):
            for _ in range(n):
                sc.feed(f, clock[0])
                clock[0] += 0.0125             # a tenth of a second of play at eight times
        feed(self.talk(1), 5)
        feed(self.blank(), 2)                  # a quarter of a second: the same conversation
        feed(self.talk(1), 3)
        feed(self.blank(), 10)
        feed(self.talk(1), 3)                  # heard again
        feed(self.blank(), 10)
        feed(self.talk(2), 3)                  # another
        d = sc.summary(8.0, [])["dialogue"]
        self.assertEqual((d["count"], d["distinct"]), (3, 2))

    def test_the_tutorial_guide_is_not_a_dialogue(self):
        f = self.talk(1)
        put(f, events.GUIDE_BOX, events.BOXES["guide"])
        sc = events.Scanner(need=1)
        sc.feed(f, 0.0)
        self.assertEqual(sc.summary(8.0, [])["dialogue"]["count"], 0)

    def notice(self, row, slot):
        f = self.blank()
        for b in (events.SYSTEM_BOX, events.SLOT_BOX, events.WAIT_BOX):
            box(f, b)
        lit(f, events.MENU_ROWS, 14, 75, 107, row)
        lit(f, events.MENU_ROWS, 14, 124, 142, slot)
        put(f, events.WAIT_GLYPHS, events.BOXES["wait"])
        return f

    def test_a_save_is_the_players_when_the_action_that_confirmed_it_just_ended(self):
        sc = events.Scanner(need=1)
        sc.feed(self.notice(events.SAVE, 0), 10.0)
        sc.feed(self.blank(), 10.1)
        sc.feed(self.notice(events.SAVE, 2), 20.0)     # the service's own save: no action before it
        sc.feed(self.blank(), 20.1)
        sc.feed(self.notice(events.LOAD, 1), 30.0)
        sc.feed(self.blank(), 30.1)
        marks = [{"t": 9.9, "keys": [["down", 0.14], ["enter", 0.14]]},
                 {"t": 19.0, "keys": [["kp9", 0.14]]}, {"t": 29.9, "keys": [["enter", 0.14]]}]
        s = sc.summary(8.0, marks)
        self.assertEqual(s["saves"], [{"minute": round(10 * 8 / 60, 1), "slot": 1}])
        self.assertEqual(s["loads"], [{"minute": 4.0, "slot": 2}])
        self.assertIsNone(sc.summary(8.0, None)["saves"])

    def test_the_slot_left_lit_after_a_lost_fight_is_loaded(self):
        f = self.blank()
        box(f, events.OVER_BOX)
        put(f, events.OVER_CARD, events.BOXES["over"])
        lit(f, events.OVER_ROWS, 17, 215, 300, 1)
        sc = events.Scanner(need=1)
        sc.feed(f, 50.0)
        sc.feed(np.zeros((200, 320), np.float32), 50.1)
        self.assertEqual(sc.summary(8.0, [])["loads"], [{"minute": 6.7, "slot": 2, "after_defeat": True}])


class LadderTests(unittest.TestCase):
    def reading(self, **over):
        sc = events.Scanner(need=1)
        sc.feed(np.full((200, 320), 90.0, np.float32), 0.0)
        ev = sc.summary(8.0, [])
        ev.update(over)
        return ev

    def test_a_black_frame_reaches_the_world_map_without_a_save(self):
        rungs = ladder.rungs_of({"replay": self.reading(first_black_second=4.0)})
        self.assertIs(rungs[ladder.MAP], True)

    def test_no_battle_means_no_experience_no_level_and_no_book(self):
        rungs = ladder.rungs_of({"replay": self.reading()})
        self.assertEqual(rungs[7:], [False, False, False, False])

    def test_the_service_grades_three_more_after_the_papers_eleven(self):
        ev = self.reading(dialogue={"count": 2}, saves=[], loads=[{"minute": 3.0, "slot": 1}])
        rungs = ladder.service_rungs({"replay": ev})
        self.assertEqual(len(rungs), len(ladder.SERVICE_KEYS))
        self.assertEqual(rungs[:len(ladder.KEYS)], ladder.rungs_of({"replay": ev}))
        self.assertEqual(rungs[len(ladder.KEYS):], [True, False, True])
        # saves unknown without keypresses, and a reading older than the counters has none
        self.assertIsNone(ladder.service_rungs({"replay": dict(ev, saves=None)})[-2])
        old = {k: v for k, v in ev.items() if k not in ("dialogue", "saves", "loads")}
        self.assertEqual(ladder.service_rungs({"replay": old})[len(ladder.KEYS):], [None] * 3)

    def test_the_chain_reads_play_minutes(self):
        ev = self.reading(first_black_second=15.0)
        chain = ladder.chain_minutes({"replay": ev}, speed=8.0)
        self.assertAlmostEqual(chain["leave_house"], 2.0)
        self.assertIsNone(chain["reach_hermit"])


class RouteTests(unittest.TestCase):
    def test_a_frame_cut_from_the_house_is_placed_where_it_was_cut(self):
        pano = np.asarray(Image.open(routes.ASSETS / "compound.png").convert("RGB"))
        x0, y0 = 300, 180
        f = np.ascontiguousarray(pano[y0:y0 + 200, x0:x0 + 320])
        for fast in (False, True):
            t = routes.HouseTracker(fast=fast)
            p = t.feed(f, 1.0)
            self.assertIsNotNone(p)
            self.assertEqual(t.last_off, (x0, y0))


class SearchCacheTests(unittest.TestCase):
    def test_a_cached_search_gives_the_same_numbers(self):
        # The cache keeps the transforms of the picture searched frame after
        # frame. The readings were checked against the paper's replays with
        # the uncached search, so a cached one must agree to the bit.
        rng = np.random.default_rng(3)
        img = (rng.random((240, 360)) * 255).astype(np.float32)
        valid = rng.random(img.shape) > 0.1
        masked, plain = {}, {}
        for _ in range(3):
            t = (rng.random((40, 64)) * 255).astype(np.float32)
            keep = rng.random(t.shape) > 0.2
            self.assertTrue(np.array_equal(
                routes.masked_ncc_map(img, valid, t, keep),
                routes.masked_ncc_map(img, valid, t, keep, cache=masked)))
            self.assertTrue(np.array_equal(routes.ncc_map(img, t),
                                           routes.ncc_map(img, t, cache=plain)))
        self.assertEqual(len(plain), 2)


class LiveTests(unittest.TestCase):
    def test_the_live_reading_follows_the_frames(self):
        frames = [np.full((200, 320, 3), 90, np.uint8)] * 3 + [np.zeros((200, 320, 3), np.uint8)] * 3
        state = {"i": 0, "t0": time.time()}

        def grab():
            f = frames[min(state["i"], len(frames) - 1)]
            state["i"] += 1
            return f

        live = live_measure.LiveMeasure(grab, lambda: time.time() - state["t0"], 60).start()
        live.mark(["kp9", "kp3"], [10, 10])
        deadline = time.time() + 5
        while state["i"] < len(frames) + 2 and time.time() < deadline:
            time.sleep(0.05)
        live.close()
        s = live.summary({"books": 0, "compass": None})
        self.assertIs(s["rungs"][ladder.MAP], True)
        self.assertEqual(len(s["rungs"]), len(ladder.SERVICE_KEYS))
        self.assertEqual(s["crossing_keys"], 2)
        self.assertEqual(len(s["chain"]), len(ladder.STEPS))


if __name__ == "__main__":
    unittest.main()
