"""Load MCP guidance from the same reviewed skills served by /api/help."""

import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
ADAPTER = pathlib.Path(__file__).resolve().parent / "ADAPTER.md"


def guide(base, language="en"):
    name = "zh" if str(language).lower().startswith("zh") else "en"
    play = (SKILLS / f"play.{name}.md").read_text(encoding="utf-8")
    speedrun = (SKILLS / f"speedrun.{name}.md").read_text(encoding="utf-8")
    text = play.rstrip() + "\n\n" + speedrun
    return text.replace("{BASE}", base).replace("{{", "{").replace("}}", "}")


def adapt_guide(canonical, benchmark=False):
    """Add MCP tool/session semantics to an already resolved game guide."""
    adapter = ADAPTER.read_text(encoding="utf-8")
    if benchmark:
        action = "Actions return metadata only. Call `look` when you need the next visible frame."
        session = (
            "This benchmark session is isolated, already created, and starts with a named "
            "character in the opening room. Generic shared-session or `X-Agent` wording in "
            "the guide does not apply. Keep playing until a tool reports `BENCHMARK ENDED`."
        )
    else:
        action = (
            "Action tools return the resulting frame when the connected API provides one. "
            "Call `look` whenever you need a fresh visible frame."
        )
        session = "Follow the connected game's session rules in the canonical guide."
    adapter = adapter.replace("{ACTION_BEHAVIOR}", action)
    adapter = adapter.replace("{SESSION_BEHAVIOR}", session).rstrip()
    return adapter + "\n\n" + canonical


def mcp_guide(base, language="en", benchmark=False):
    return adapt_guide(guide(base, language), benchmark)
