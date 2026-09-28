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
        self.assertEqual(s["crossing_keys"], 2)
        self.assertEqual(len(s["chain"]), len(ladder.STEPS))


if __name__ == "__main__":
    unittest.main()
