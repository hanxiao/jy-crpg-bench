"""Display and LaTeX escaping helpers for generated paper tables."""

_DISPLAY_NAMES = {
    "claude": "Claude", "gemini": "Gemini", "qwen": "Qwen",
    "grok": "Grok", "glm": "GLM", "gpt": "GPT", "vista": "Vista",
    "codex": "Codex", "random": "Random",
}

_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def display_agent(label):
    """Normalize a recorded agent label without hiding unknown suffixes."""
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
