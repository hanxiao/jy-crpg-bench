"""Display and LaTeX escaping helpers for generated paper tables.

The catalogue's agent field is the data source.  We normalize only labels that
are present in that source; unknown labels keep their suffixes verbatim so a
new product name is never guessed from a partial match.
"""

_DISPLAY_NAMES = {
    "claude": "Claude", "gemini": "Gemini", "qwen": "Qwen",
    "grok": "Grok", "glm": "GLM", "gpt": "GPT", "vista": "Vista",
    "codex": "Codex", "random": "Random",
}

# These are the Claude labels actually present in catalog_snapshot.json.  The
# spaces are part of the product names; no absent names (for example GPT-5.0
# SOIL or OSPA-45) are invented here.
_EXACT_DISPLAY_NAMES = {
    "claude-sonnet-4.6": "Claude Sonnet 4.6",
    "claude-sonnet-5": "Claude Sonnet 5",
    "claude-opus-5": "Claude Opus 5",
    "claude-fable-5": "Claude Fable 5",
    "claude-fable-5-1": "Claude Fable 5-1",
    "gemini-3.7-flash": "Gemini 3.7 Flash",
    "glm-5.3-flash": "GLM-5.3 Flash",
    "qwen3.8-flash": "Qwen 3.8 Flash",
    "Qwen3.8-Flash-Next": "Qwen 3.8 Flash Next",
    "Qwen3.8-27B-NVFP4": "Qwen 3.8 27B NVFP4",
    "gpt-5.2-codex": "GPT-5.2 Codex",
    # ``sol`` is preserved exactly from the catalogue; no SOIL/SOL
    # expansion is inferred for a name absent from the data source.
    "gpt-5.6-sol": "GPT-5.6-sol",
    "grok-4.6": "Grok 4.6",
    "random-baseline": "Random Baseline",
    "codex-cli--gpt-5.6-sol--pi": "Codex CLI / GPT-5.6-sol / Pi",
    "vista-codex-gpt-5.6-sol": "Vista / Codex / GPT-5.6-sol",
    "vista-claude-opus-5": "Vista / Claude Opus 5",
}

_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def display_agent(label):
    """Normalize a recorded agent label without hiding unknown suffixes."""
    if label in _EXACT_DISPLAY_NAMES:
        return _EXACT_DISPLAY_NAMES[label]
    return "-".join(
        _DISPLAY_NAMES.get(
            part.lower(),
            next((_DISPLAY_NAMES[p] + part[len(p):] for p in _DISPLAY_NAMES
                  if part.lower().startswith(p)), part),
        )
        for part in label.split("-")
    )


def latex_agent(label):
    """Return a display label safe in ordinary LaTeX table text."""
    text = display_agent(label)
    out = []
    i = 0
    while i < len(text):
        if text.startswith("--", i):
            out.append("-{-}")
            i += 2
        else:
            out.append(_LATEX_ESCAPES.get(text[i], text[i]))
            i += 1
    return "".join(out)
