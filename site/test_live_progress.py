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


def reading(rungs, chain=(None,) * 6, **over):
    """A measure block as the service writes it."""
    b = {"version": 1, "rungs": list(rungs), "reached": sum(1 for v in rungs if v is True),
         "chain": list(chain), "first": {}, "scenes": [], "crossing_actions": None,
         "crossing_keys": None, "recruited_minute": None}
    b.update(over)
    return b


class LiveProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = BUILD.build(BUILD.EN, "test")

    def test_live_entries_carry_the_reading(self):
        self.assertIn("measure: s.measure || null, routes_at: s.routes_at || 0", self.html)

    def test_live_cells_are_refreshed(self):
        for field in ("ladder", "crossing", "places", "inputs", "acts"):
            self.assertIn(f'f === "{field}"', self.html)
        self.assertIn('data-live="${r.id}:ladder"', self.html)

    def test_the_human_references_are_the_paper_ones(self):
        rows = BUILD.human_rows()
        self.assertEqual([r["cls"] for r in rows], ["speedrun", "playthrough"])
        self.assertTrue(all(len(r["counts"]) == 11 for r in rows))


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
            "const STORE = 'https://store';",
            "globalThis.document = {documentElement: {lang: 'en'}};",
            section("const secs =", "// Which lab"),
            section("// The usage report", "function clip("),
            section("function entries()", "function refreshLive()"),
            section("const SORTKEY =", "function render()"),
            "let sort = 'started', desc = true;",
            "const nodes = {btable: {}, bnote: {}}; globalThis.$ = id => nodes[id];",
            "const wireOpen = () => {}; const mark = () => '';",
        ))

    def evaluate(self, expression, records=(), snapshots=()):
        program = (self.script + "\nruns = " + json.dumps(records)
                   + "; live = " + json.dumps(snapshots)
                   + "; console.log(JSON.stringify(" + expression + "));")
        result = subprocess.run(["node"], input=program, text=True,
                                capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_the_milestones_are_the_reading(self):
        r = {"id": "a", "agent": "m", "measure": reading([True, True] + [False] * 9)}
        self.assertEqual(self.evaluate("[msReached(runs[0]), msOf(runs[0]).length]", [r]), [2, 11])

    def test_a_run_without_a_reading_shows_no_count(self):
        out = self.evaluate("[msOf(runs[0]), msLadder(runs[0])]", [{"id": "old", "agent": "m"}])
        self.assertEqual(out[0], [None] * 11)
        self.assertIn('<b class="n">-</b>', out[1])

    def test_the_crossing_reads_keys_actions_and_minute(self):
        r = {"id": "a", "agent": "m", "measure": reading([True] + [False] * 10, chain=[2.5, None, None, None, None, None],
                                                        crossing_keys=120, crossing_actions=40)}
        self.assertEqual(self.evaluate("crossing(runs[0])", [r]), "120 keys · 40 actions · 2.5m")
        stay = {"id": "b", "agent": "m", "measure": reading([False] * 11)}
        self.assertEqual(self.evaluate("crossing(runs[0])", [stay]), "—")

    def test_models_pool_their_sessions_under_the_paper_names(self):
        rows = self.evaluate("modelRows().map(m => [m.agent, m.sessions, m.counts[0]])", [
            {"id": "a", "agent": "claude-opus-5.5-high", "budget": 3600, "actions": 50, "measure": reading([True] + [False] * 10)},
            {"id": "b", "agent": "claude-opus-5.5", "budget": 3600, "actions": 50, "measure": reading([False] * 11)},
            {"id": "c", "agent": "claude-opus-5.5", "budget": 14400, "actions": 50, "measure": reading([True] * 11)},
            {"id": "d", "agent": "claude-opus-5.5", "budget": 3600, "actions": 3, "measure": reading([False] * 11)},
        ])
        self.assertEqual(rows, [["claude-opus-5.5", 2, [1, 2, 2]]])

    def test_the_chain_counts_passes_and_the_minutes_since_the_step_before(self):
        out = self.evaluate("chainOf(runs).map(c => [c.atRisk, c.passed.map(p => p[2]), c.stuck.map(s => s[1])])", [
            {"id": "a", "agent": "m", "played": 3600,
             "measure": reading([True] * 4 + [False] * 7, chain=[2, 10, 12, None, None, None])},
            {"id": "b", "agent": "m", "played": 1800,
             "measure": reading([False] * 11)},
        ])
        self.assertEqual(out[0], [2, [2], [30]])
        self.assertEqual(out[1], [1, [8], []])
        self.assertEqual(out[3], [1, [], [48]])

    def test_the_boards_draw_without_gaps(self):
        recs = [{"id": "a", "agent": "m", "budget": 3600, "played": 3600, "actions": 10, "key_events": 20,
                 "gap_p50": 3.0, "reads": 5,
                 "measure": reading([True] * 3 + [False] * 8, chain=[2, 10, None, None, None, None], crossing_keys=50)}]
        for view in ("milestones", "crossing", "filters", "effort"):
            html = self.evaluate(f"(bview = '{view}', drawBoard(), nodes.btable.innerHTML)", recs)
            self.assertNotIn("NaN", html, view)
            self.assertNotIn("undefined", html, view)
        self.assertIn("human speedrun", self.evaluate("(bview = 'milestones', drawBoard(), nodes.btable.innerHTML)", recs))

    def test_live_records_carry_the_reading_and_the_routes(self):
        out = self.evaluate("[entries()[0].measure.reached, routeSrc(entries()[0], 'world')]", snapshots=[
            {"id": "live", "agent": "m", "actions": 3, "routes_at": 7, "measure": reading([True] + [False] * 10)}])
        self.assertEqual(out, [1, "https://store/live/live-world.png?v=7"])

    def test_the_events_are_listed_in_minutes_of_play(self):
        r = {"id": "a", "agent": "m", "measure": reading(
            [True] * 4 + [False] * 7, chain=[2, 8.7, 9.6, None, None, None],
            first={"hermit": 9.6}, scenes=[[0.0, "王居"], [8.7, "南賢居"]])}
        self.assertEqual(self.evaluate("eventRows(runs[0]).map(e => e[1])", [r]),
                         ["left the starting house", "entered house of the hermit", "spoke with the hermit"])

    def test_short_sessions_are_hidden_unless_asked_for(self):
        recs = [{"id": "long", "agent": "m", "actions": 40, "key_events": 60},
                {"id": "few", "agent": "m", "actions": 4, "key_events": 30},
                {"id": "none", "agent": "m", "actions": 0}]
        self.assertEqual(self.evaluate("sorted().map(r => r.id)", recs), ["long"])
        self.assertEqual(self.evaluate("(showShort = true, sorted().map(r => r.id).sort())", recs),
                         ["few", "long", "none"])
        self.assertEqual(self.evaluate("entries().map(r => r.id)",
                                       snapshots=[{"id": "live", "agent": "m", "actions": 0}]), ["live"])

    def test_publication_error_does_not_replace_stop_reason(self):
        result = self.evaluate("why(runs[0])", [
            {"reason": "idle", "error": "render failed", "played": 20},
        ])
        self.assertIn("stopped idle", result)
        self.assertIn("publishing failed", result)

    def test_usage_report_drives_cell_sort_and_details(self):
        result = self.evaluate(
            "[fusage(runs[0]), fusage(runs[1]), fusage(runs[2]), usageFull(runs[0]),"
            " entries().map(e => e.usage_total),"
            " (sort = 'usage_total', desc = true, sorted().map(e => e.agent))]",
            records=[
                {"id": "a", "agent": "metered", "actions": 20,
                 "usage": {"turns": 42, "totalTokens": 1234567, "cost": 1.2345}},
                {"id": "b", "agent": "unmetered", "actions": 20},
                {"id": "c", "agent": "pennies", "actions": 20,
                 "usage": {"turns": 7, "totalTokens": 940, "cost": 0.0042}},
            ])
        self.assertEqual(result[0], "1.2M · $1.23")
        self.assertEqual(result[1], "-")
        # A positive cost below a cent must not render as $0.00.
        self.assertEqual(result[2], "940 · $0.0042")
        self.assertEqual(result[3], "1,234,567 tokens · 42 turns · $1.2345")
        self.assertEqual(result[4], [1234567, None, 940])
        self.assertEqual(result[5], ["metered", "pennies", "unmetered"])


class UsageReportLocaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.zh = BUILD.build(BUILD.ZH, "test")
        cls.en = BUILD.build(BUILD.EN, "test")

    def test_usage_column_and_helpers_are_built(self):
        for html in (self.zh, self.en):
            self.assertIn('{k: "usage_total",   f: r => fusage(r)}', html)
            self.assertIn("function fusage(r)", html)
            self.assertIn("function usageFull(r)", html)
            self.assertIn(
                "runs.map(r => ({...r, usage_total: r.usage?.totalTokens ?? null}))",
                html)

    def test_usage_is_shown_in_the_run_details(self):
        for html in (self.zh, self.en):
            self.assertIn("<span>${T.b_usage}</span><b>${usageFull(r)}</b>", html)
            self.assertIn('"b_usage_unit": "tokens"', html)


if __name__ == "__main__":
    unittest.main()
