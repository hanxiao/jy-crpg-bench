import pathlib
import subprocess
import sys
import unittest

from labels import display_agent, latex_agent


class LabelTests(unittest.TestCase):
    def test_known_prefixes_and_unknown_suffix_are_preserved(self):
        self.assertEqual(display_agent("gpt-5.6-sol"), "GPT-5.6-sol")
        self.assertEqual(display_agent("new-agent-v2"), "new-agent-v2")

    def test_latex_special_characters_are_escaped(self):
        self.assertEqual(
            latex_agent(r"new_agent&v2--x%{y}^~$#"),
            r"new\_agent\&v2-{-}x\%\{y\}\textasciicircum{}\textasciitilde{}\$\#",
        )


class GeneratedTableTests(unittest.TestCase):
    def test_family_generation_is_displayed_and_line_separated(self):
        here = pathlib.Path(__file__).resolve().parent
        subprocess.run([sys.executable, "make_metrics.py"], cwd=here, check=True,
                       stdout=subprocess.DEVNULL)
        text = (here.parent / "tables" / "family.tex").read_text(encoding="utf-8")
        self.assertIn("\\midrule\nClaude-", text)
        self.assertNotIn(r"\midruleclaude-", text)


if __name__ == "__main__":
    unittest.main()
