import copy
import unittest
from unittest.mock import patch

from server import warden


class ActionAccountingTests(unittest.TestCase):
    def setUp(self):
        self.original = copy.deepcopy(warden.run)
        warden.run.update(
            playable=1.0, first=None, last=None, gaps=[], keys={}, actions=0,
            key_events=0, input_frames=0, wait_calls=0, done=None,
        )

    def tearDown(self):
        warden.run.clear()
        warden.run.update(self.original)

    def test_wait_is_a_timed_decision_but_not_keyboard_activity(self):
        with patch.object(warden.time, "time", return_value=2.0):
            warden.note_action([], "wait")
        self.assertEqual(warden.run["actions"], 1)
        self.assertEqual(warden.run["wait_calls"], 1)
        self.assertEqual(warden.run["key_events"], 0)
        self.assertEqual(warden.run["first"], 2.0)
        self.assertEqual(warden.run["last"], 2.0)

    def test_batch_reports_submitted_keys_and_requested_frames(self):
        warden.note_action(["kp3", "kp3", "enter"], input_frames=30)
        self.assertEqual(warden.run["actions"], 1)
        self.assertEqual(warden.run["key_events"], 3)
        self.assertEqual(warden.run["input_frames"], 30)
        self.assertEqual(warden.run["keys"], {"kp3": 2, "enter": 1})

    def test_final_metrics_keep_the_end_reason(self):
        warden.run["done"] = "idle"
        self.assertEqual(warden.metrics()["reason"], "idle")

    def test_final_metrics_keep_exact_screen_change_count(self):
        warden.run.update(actions=4000, meaningful=1)
        metrics = warden.metrics()
        self.assertEqual(metrics["meaningful"], 0)
        self.assertEqual(metrics["meaningful_count"], 1)

    def test_errors_remain_unmeasured_in_live_and_final_metrics(self):
        self.assertIsNone(warden.metrics()["errors"])
        with patch.object(warden, "ON", True):
            self.assertIsNone(warden.timing()["errors"])


if __name__ == "__main__":
    unittest.main()
