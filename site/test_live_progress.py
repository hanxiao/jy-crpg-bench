import importlib.util
import json
import pathlib
import shutil
import subprocess
import unittest


SITE_DIR = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("qunxia_site_build", SITE_DIR / "build.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class LiveProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = BUILD.build(BUILD.EN, "test")

    def test_live_entries_carry_new_progress_fields(self):
        for field in (
            "level", "exp", "skills", "inventory_distinct", "picked_item",
            "key_events", "input_frames", "wait_calls",
        ):
            self.assertIn(f"{field}: s.{field} ?? null", self.html)

    def test_live_progress_cells_are_refreshed(self):
        for field in ("ladder", "hero", "exit", "scenes", "inputs"):
            self.assertIn(f'f === "{field}"', self.html)
        self.assertIn('data-live="${r.id}:ladder"', self.html)


@unittest.skipUnless(shutil.which("node"), "Node.js is required for site behavior tests")
class ScoringBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = BUILD.build(BUILD.EN, "test")
        def section(start, end):
            return html[html.index(start):html.index(end)]
        cls.script = "\n".join((
            "const T = " + json.dumps(BUILD.EN) + ";",
            "const Q = new URLSearchParams(); let runs = [], live = []; const stat = new Map();",
            section("const secs =", "// Which lab"),
            section("const RUNGS =", "function clip("),
            section("function wilson(", "// addressable,"),
            section("function drawFrontier(", "// the label under"),
            section("function entries()", "function sorted()"),
            "const wireOpen = () => {}; const mark = () => ''; const vendorOf = () => '';",
        ))

    def evaluate(self, expression, records=(), snapshots=()):
        program = (self.script + "\nruns = " + json.dumps(records)
                   + "; live = " + json.dumps(snapshots)
                   + "; console.log(JSON.stringify(" + expression + "));")
        result = subprocess.run(["node"], input=program, text=True,
                                capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_wait_only_milestone_is_consistent_on_card_and_board(self):
        result = self.evaluate("[rungs(runs[0]), rungs(boardRows()[0])]", [
            {"agent": "waiter", "actions": 4, "key_events": 0, "meaningful": 0},
        ])
        self.assertFalse(result[0][0])
        self.assertEqual(result[0], result[1])

    def test_exact_count_survives_rounded_ratio_on_card_and_board(self):
        result = self.evaluate("[rungs(runs[0]), boardRows()[0]]", [
            {"agent": "sparse", "actions": 4000, "key_events": 4000,
             "meaningful": 0, "meaningful_count": 1},
        ])
        self.assertTrue(result[0][1])
        self.assertEqual(result[1]["mact"], 1)
        self.assertEqual(result[1]["meaningful"], 1 / 4000)

    def test_unmeasured_runs_do_not_enter_ratio_denominator(self):
        result = self.evaluate("boardRows()[0]", [
            {"agent": "mixed", "actions": 100},
            {"agent": "mixed", "actions": 10, "meaningful": 0.5},
        ])
        self.assertEqual(result["actions"], 110)
        self.assertEqual(result["meaningful"], 0.5)

    def test_no_measurements_have_no_ratio_or_interval(self):
        result = self.evaluate("boardRows()[0]", [
            {"agent": "old", "actions": 20},
        ])
        for field in ("meaningful", "lo", "hi", "mact"):
            self.assertIsNone(result[field])
        self.assertEqual(self.evaluate("BOARDS.overview.val(boardRows()[0])", [
            {"agent": "old", "actions": 20},
        ]), "<b>-</b>")

    def test_live_records_preserve_counts_and_inventory(self):
        result = self.evaluate("[entries()[0], rungs(entries()[0])]", snapshots=[
            {"id": "live", "agent": "sparse", "actions": 4000,
             "meaningful": 1, "key_events": 0, "input_frames": 0,
             "wait_calls": 4000, "level": 1, "exp": 0, "skills": 2,
             "inventory_distinct": 4, "picked_item": True},
        ])
        self.assertEqual(result[0]["meaningful_count"], 1)
        self.assertEqual(result[0]["inventory_distinct"], 4)
        self.assertEqual(result[1][:3], [False, True, True])

    def test_publication_error_does_not_replace_stop_reason(self):
        result = self.evaluate("why(runs[0])", [
            {"reason": "idle", "error": "render failed", "played": 20},
        ])
        self.assertIn("went idle", result)
        self.assertIn("publication error", result)

    def test_error_counts_remain_unmeasured_including_legacy_placeholders(self):
        for errors in (None, 0):
            with self.subTest(errors=errors):
                result = self.evaluate("boardRows()[0].errors", [
                    {"agent": "unmeasured", "actions": 2, "errors": errors},
                ])
                self.assertIsNone(result)

    def test_frontier_excludes_unmeasured_and_equal_ratio_lower_count(self):
        result = self.evaluate("""(() => {
            const el = {}; drawFrontier(el, boardRows()); return el.innerHTML;
        })()""", [
            {"agent": "old", "actions": 100},
            {"agent": "smaller", "actions": 10, "meaningful": 0.5},
            {"agent": "larger", "actions": 20, "meaningful": 0.5},
        ])
        self.assertNotIn("<title>old", result)
        self.assertIn('<g class="off"><title>smaller', result)
        self.assertIn('<g class="on"><title>larger', result)

    def test_overview_renders_missing_values_without_a_rank(self):
        result = self.evaluate("""(() => {
            const nodes = {btable: {}, bnote: {}};
            globalThis.$ = id => nodes[id]; globalThis.bview = 'overview';
            drawBoard(); return nodes.btable.innerHTML;
        })()""", [
            {"agent": "old", "actions": 100},
            {"agent": "measured", "actions": 10, "meaningful": 0.5},
        ])
        self.assertNotIn("NaN", result)
        self.assertIn('<div class="bpos"><b>-</b></div>', result)

    def test_equal_milestones_share_rank_with_alphabetical_display_order(self):
        result = self.evaluate(r"""(() => {
            const nodes = {btable: {}, bnote: {}};
            globalThis.$ = id => nodes[id]; globalThis.bview = 'ladder';
            drawBoard();
            return {
                ranks: Array.from(nodes.btable.innerHTML.matchAll(
                    /class="bpos"><b>([^<]+)<\/b>/g), m => m[1]),
                html: nodes.btable.innerHTML
            };
        })()""", [
            {"agent": "Beta", "actions": 20, "key_events": 20, "meaningful": 0.5},
            {"agent": "Alpha", "actions": 10, "key_events": 10, "meaningful": 0.5},
            {"agent": "Gamma", "actions": 10, "key_events": 10, "meaningful": 0},
        ])
        self.assertEqual(result["ranks"], ["1", "1", "3"])
        self.assertLess(result["html"].index("<b>Alpha</b>"),
                        result["html"].index("<b>Beta</b>"))

    def test_live_refresh_updates_rendered_progress_and_input_cells(self):
        result = self.evaluate("""(() => {
            const cells = ['ladder', 'hero', 'inputs', 'scenes'].map(field =>
                ({dataset: {live: 'live:' + field}}));
            globalThis.document = {querySelectorAll: () => cells};
            refreshLive(); return cells;
        })()""", snapshots=[
            {"id": "live", "actions": 1, "key_events": 2, "input_frames": 20,
             "meaningful": 1, "level": 2, "skills": 3,
             "inventory_distinct": 4, "picked_item": True, "scenes": 2,
             "bigmap": True, "exp": 5},
        ])
        self.assertIn("<b>6/6</b>", result[0]["outerHTML"])
        self.assertEqual([cell["textContent"] for cell in result[1:]],
                         ["2 · 3 · 4", "1 · 2 · 20", "2 · ✓"])


if __name__ == "__main__":
    unittest.main()
