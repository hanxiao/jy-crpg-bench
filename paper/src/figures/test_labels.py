import json
import pathlib
import re
import subprocess
import sys
import unittest


HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from labels import display_agent, latex_agent


class LabelTests(unittest.TestCase):
    def test_catalogue_names_use_data_grounded_product_spacing(self):
        expected = {
            "claude-sonnet-5": "Claude Sonnet 5",
            "claude-opus-5": "Claude Opus 5",
            "vista-claude-opus-5": "Vista / Claude Opus 5",
            "claude-fable-5-1": "Claude Fable 5-1",
            "gemini-3.7-flash": "Gemini 3.7 Flash",
            "glm-5.3-flash": "GLM-5.3 Flash",
            "qwen3.8-flash": "Qwen 3.8 Flash",
            "Qwen3.8-27B-NVFP4": "Qwen 3.8 27B NVFP4",
        }
        for raw, shown in expected.items():
            self.assertEqual(display_agent(raw), shown)

    def test_unknown_suffix_and_unlisted_names_are_not_invented(self):
        self.assertEqual(display_agent("gpt-5.6-sol"), "GPT-5.6-sol")
        self.assertEqual(display_agent("new-agent-v2"), "new-agent-v2")
        self.assertEqual(display_agent("GPT-5.0 SOIL"), "GPT-5.0 SOIL")
        self.assertEqual(display_agent("OSPA-45"), "OSPA-45")

    def test_latex_special_characters_are_escaped(self):
        self.assertEqual(
            latex_agent(r"new_agent&v2--x%{y}^~$#"),
            r"new\_agent\&v2-{-}x\%\{y\}\textasciicircum{}\textasciitilde{}\$\#",
        )


class GeneratedOutputTests(unittest.TestCase):
    def _run(self, script):
        return subprocess.run([sys.executable, script], cwd=HERE, check=True,
                              stdout=subprocess.PIPE, text=True)

    def test_all_generated_tables_and_numbers_use_canonical_labels(self):
        self._run("make_metrics.py")
        self._run("emit_table.py")
        numbers = self._run("emit_numbers.py").stdout
        raw = {row["agent"] for row in json.loads(
            (HERE / "catalog_snapshot.json").read_text(encoding="utf-8"))}
        self.assertIn("claude-sonnet-5", raw)
        self.assertFalse(any(re.fullmatch(r"sonnet-5", label, re.IGNORECASE)
                             for label in raw))
        self.assertFalse(any(re.search(r"gpt[- ]?5\.0|soil|ospa[- ]?45", label,
                                       re.IGNORECASE) for label in raw))
        self.assertIn("Claude Sonnet 5", numbers)
        self.assertIn("Gemini 3.7 Flash", numbers)
        self.assertNotIn("claude-sonnet-5", numbers)
        self.assertNotIn("gemini-3.7-flash", numbers)
        generated = []
        for name in ("aggregate.tex", "family.tex", "runs.tex"):
            text = (HERE / "../tables" / name).read_text(encoding="utf-8")
            generated.append(text)
            for shown in ("Claude Sonnet 5", "Claude Opus 5", "Vista / Claude Opus 5",
                          "Gemini 3.7 Flash", "GLM-5.3 Flash", "Qwen 3.8 Flash"):
                self.assertIn(shown, text)
            self.assertNotRegex(text, r"GPT[- ]?5\.0|OSPA[- ]?45|(?<![A-Za-z])SONNET-5(?![A-Za-z])")
        paper_text = (HERE / "../main.tex").read_text(encoding="utf-8")
        generated.append(paper_text)
        raw_ids = raw
        for raw_id in raw_ids:
            if raw_id.startswith("probe-"):
                continue
            for text in generated:
                self.assertNotIn(raw_id, text)
        self.assertNotRegex("\n".join(generated),
                            r"GPT[- ]?5\.0\s+SOIL|OSPA[- ]?45|(?<![A-Za-z])SONNET-5(?![A-Za-z])")
