import unittest

import agents_build


class ChineseSkillTests(unittest.TestCase):
    """The Chinese skills are Simplified except for the game's own words."""

    def test_only_on_screen_words_are_traditional(self):
        paths = sorted(agents_build.SKILLS.glob("*.zh.md")) + [
            agents_build.SKILLS / "jyxzz-speedrun-tips" / "SKILL.md"]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            simple = agents_build.to_simplified(text).splitlines()
            for n, (line, want) in enumerate(zip(text.splitlines(), simple), 1):
                self.assertEqual(line, want, f"{path.name}:{n}")


if __name__ == "__main__":
    unittest.main()
