import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "server"))

from game_knowledge import adapt_guide, guide, mcp_guide
from prompt import system_prompt


class GameKnowledgeTests(unittest.TestCase):
    def test_mcp_and_http_help_share_the_same_source(self):
        for language in ("en", "zh"):
            canonical = system_prompt("http://session.invalid", language)
            self.assertEqual(guide("http://session.invalid", language), canonical)
            for benchmark in (False, True):
                prompt = mcp_guide("http://session.invalid", language, benchmark)
                self.assertTrue(prompt.endswith(canonical))
                self.assertIn("`GET /api/screen` -> `look`", prompt)

    def test_benchmark_adapter_states_the_isolation_contract(self):
        prompt = mcp_guide("http://session.invalid", "en", True)
        self.assertIn("Actions return metadata only", prompt)
        self.assertIn("benchmark session is isolated", prompt)
        self.assertIn("BENCHMARK ENDED", prompt)

    def test_adapter_accepts_a_session_resolved_guide(self):
        canonical = "session-specific guide at https://session.invalid/api"
        prompt = adapt_guide(canonical, benchmark=True)
        self.assertTrue(prompt.endswith(canonical))
        self.assertIn("Actions return metadata only", prompt)


if __name__ == "__main__":
    unittest.main()
