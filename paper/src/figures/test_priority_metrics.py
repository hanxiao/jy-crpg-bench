"""Regression checks for Figures 3 and 7 and Table 4.

Run from any directory: python3 -B figures/test_priority_metrics.py.
No figures or tables are written by these tests.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import field
import emit_milestones
import filters
import make
import matplotlib.pyplot as plt


class FilterTests(unittest.TestCase):
    def test_rendered_bar_heights_and_labels_have_the_same_denominator(self):
        rows = filters.rows()
        chain = field.chain(rows)
        self.assertEqual(len(rows), 52)
        self.assertEqual([len(s["passed"]) for s in chain], [41, 18, 10, 4, 1, 0])
        fig = filters.figure_filters()
        try:
            axis = fig.axes[0]
            self.assertEqual(axis.get_ylabel(), "share of 52 sessions")
            self.assertEqual(len(axis.patches), len(chain))
            self.assertEqual(len(axis.texts), len(chain))
            for bar, label, step in zip(axis.patches, axis.texts, chain):
                numerator, denominator = map(int, label.get_text().split("/"))
                self.assertEqual(denominator, len(rows))
                self.assertEqual(numerator, len(step["passed"]))
                self.assertAlmostEqual(bar.get_height(), numerator / denominator)
        finally:
            plt.close(fig)


class HumanEffortTests(unittest.TestCase):
    def test_video_estimates_do_not_occupy_model_key_fields(self):
        humans = field.human_rows()
        self.assertEqual(len(humans), 2)
        for row, (cls, label) in zip(humans, field.HUMAN_CLASSES):
            expected = sorted(v["steps_to_map"] for v in field.human_videos()
                              if v["class"] == cls)
            self.assertEqual(row["agent"], label)
            self.assertEqual(row["cross_steps"], expected)
            self.assertNotIn("cross_keys", row)
            self.assertNotIn("map_actions", row)

    def test_crossing_panels_have_separate_axes_and_exact_record_counts(self):
        fig = make.figure_ladder(save=False)
        try:
            axes = {a.get_label(): a for a in fig.axes}
            models = axes["model-crossings"]
            humans = axes["human-crossings"]
            self.assertFalse(models.get_shared_x_axes().joined(models, humans))
            self.assertEqual(models.get_xscale(), "log")
            self.assertEqual(humans.get_xscale(), "linear")
            self.assertIn("model keypresses", models.get_xlabel())
            self.assertIn("video-estimated steps", humans.get_xlabel())
            self.assertEqual([t.get_text() for t in humans.get_yticklabels()],
                             ["speedrun", "playthrough"])
            self.assertFalse(any(t.get_text().startswith("human")
                                 for t in models.get_yticklabels()))
            rows = emit_milestones.hour_rows()
            expected_models = field.model_rows(rows)
            expected_models = sorted((m for m in expected_models if m["cross_keys"]),
                                     key=field.crossing_order)
            for axis, group, key in ((models, expected_models, "cross_keys"),
                                     (humans, field.human_rows(), "cross_steps")):
                self.assertEqual(len(axis.collections), 2 * len(group))
                for i, row in enumerate(group):
                    actual = axis.collections[2 * i].get_offsets()[:, 0].tolist()
                    self.assertEqual(actual, row[key])
            top = axes["milestones"]
            self.assertEqual([t.get_text() for t in top.get_yticklabels()][:2],
                             ["human speedrun", "human playthrough"])
        finally:
            plt.close(fig)

    def test_text_names_the_human_measure_without_calling_it_keypresses(self):
        text = (HERE.parent / "main.tex").read_text()
        self.assertIn(r"\LhumanSpeedStepsMax{} video-estimated steps", text)
        self.assertNotIn(r"\LhumanSpeedStepsMax{} keypresses", text)
        self.assertIn("The videos contain no keyboard log", text)


class MilestoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = emit_milestones.hour_rows()
        cls.summary = emit_milestones.summarize(cls.rows)

    def test_cohort_is_only_played_hour_model_sessions(self):
        self.assertEqual(len(self.rows), 42)
        self.assertTrue(all(r["budget"] == field.DEFAULT_BUDGET and r["actions"] > 0
                            and not field.is_random(r["agent"]) for r in self.rows))
        self.assertTrue({r["id"] for r in self.rows}.isdisjoint(
            r["id"] for r in field.load_long()))

    def test_all_eleven_rows_agree_with_ladder_counts(self):
        self.assertEqual(tuple(k for _, _, k in emit_milestones.ROWS), field.SHORT)
        self.assertEqual(len(self.summary), len(field.DEFINITION))
        self.assertEqual([n for _, n, _, _ in self.summary],
                         [32, 22, 13, 9, 5, 2, 3, 2, 1, 1, 0])
        for i, (_, n, _, _) in enumerate(self.summary):
            self.assertEqual(n, sum(field.rungs_of(r)[i] is True for r in self.rows))

    def test_new_experience_and_level_rows_use_replay_time_and_actions(self):
        winners = [r for r in self.rows if field.rungs_of(r)[8] is True]
        self.assertEqual(len(winners), 1)
        row = winners[0]
        timeline = json.loads((HERE / "timelines" / (row["id"] + ".json")).read_text())
        for index, event in ((8, "exp"), (9, "level")):
            minute = row["replay"][event]["minutes"][0]
            second = minute * 60 / timeline["speed"]
            actions = sum(m["t"] <= second for m in timeline["marks"])
            _, count, median_actions, median_minute = self.summary[index]
            self.assertEqual(count, 1)
            self.assertEqual(median_actions, actions)
            self.assertAlmostEqual(median_minute, minute)
            self.assertEqual(actions, 372)
            self.assertAlmostEqual(minute, 27.6)

    def test_zero_books_have_no_fabricated_median(self):
        self.assertEqual(self.summary[-1], ("held a book", 0, None, None))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            emit_milestones.main()
        self.assertIn(r"held a book & 0 & -- & -- \\", output.getvalue())
        table = HERE.parent / "tables" / "milestones.tex"
        self.assertEqual(output.getvalue(), table.read_text())

    def test_missing_timestamp_is_not_silently_reported_as_zero(self):
        row = copy.deepcopy(next(r for r in self.rows if field.rungs_of(r)[8] is True))
        row["replay"]["exp"]["minutes"] = []
        with self.assertRaisesRegex(ValueError, "without a replay timestamp"):
            emit_milestones.summarize([row])

    def test_book_requires_a_timestamp_if_a_future_record_credits_one(self):
        row = copy.deepcopy(self.rows[0])
        row["books"] = 1
        with self.assertRaisesRegex(ValueError, "held a book.*without a replay timestamp"):
            emit_milestones.summarize([row])

    def test_unknown_milestone_is_not_silently_reported_as_unreached(self):
        verdicts = [False] * len(field.DEFINITION)
        verdicts[0] = None
        with mock.patch.object(field, "rungs_of", return_value=verdicts):
            with self.assertRaisesRegex(ValueError, "no reading"):
                emit_milestones.summarize([self.rows[0]])

    def test_empty_event_and_exact_action_boundary(self):
        self.assertIsNone(emit_milestones.first_second({"speed": 8}, "exp"))
        marks = [{"t": 1}, {"t": 2}, {"t": 3}]
        self.assertEqual(emit_milestones.actions_by(marks, 2), 2)
        self.assertEqual(emit_milestones.actions_by(marks, 0), 0)


if __name__ == "__main__":
    unittest.main()
