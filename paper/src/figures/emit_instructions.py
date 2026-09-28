"""The instructions the models receive, Chinese and English side by side.

    python3 figures/emit_instructions.py > tables/instructions.tex

Reads site/60m/agents.md (the Chinese instructions every model in the paper
reads) and site/en/60m/agents.md (their English translation, set in the
left column), which
site/agents_build.py assembles from skills/. The two have the same sections in
the same order; each pair is set in the two columns of one paracol row, so a
section starts level on both sides. The four-hour instructions differ only in
the minutes value of the session call, and the address of the hosted service is
withheld as SERVICE_URL.

The first row is the prompt, the one message each model is sent to start a
session. It names the instructions and sets the rules of the session; the
address of the site that serves the instructions is withheld as SITE_URL.

Chinese runs are set with CJKutf8, whose fonts cover either Traditional (bsmi)
or Simplified (gbsn) characters. The on-screen terms the instructions keep in
Traditional Chinese, the ON_SCREEN list of agents_build.py, are set in bsmi;
every other run takes gbsn where GB2312 covers it and bsmi otherwise.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "site"))
from agents_build import ON_SCREEN, PROMPT  # noqa: E402

ZH = os.path.join(ROOT, "site", "60m", "agents.md")
EN = os.path.join(ROOT, "site", "en", "60m", "agents.md")
TERMS = sorted({t.strip("*「」") for t in ON_SCREEN if re.fullmatch(r"[一-鿿]+", t.strip("*「」"))},
               key=len, reverse=True)
CJK = re.compile(r"[　-〿一-鿿＀-￯—…·《》]+")
CODE_WIDTH = 46
SITE = "https://hanxiao.io/jy-crpg-bench"

# the prompt each model is sent, and its English translation, from the site
PROMPT_ZH = "# 提示词\n\n" + PROMPT["zh"].format(url=SITE + "/{PLAYTIME}/agents.md", model="{MODEL_NAME}") + "\n"
PROMPT_EN = "# Prompt\n\n" + PROMPT["en"].format(url=SITE + "/{PLAYTIME}/agents.md", model="{MODEL_NAME}") + "\n"


def tex_escape(t):
    out = []
    for ch in t:
        out.append({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
                    "\u2196": r"$\nwarrow$", "\u2197": r"$\nearrow$", "\u2199": r"$\swarrow$", "\u2198": r"$\searrow$",
                    "\u2192": r"$\rightarrow$"}.get(ch, ch))
    return "".join(out)


def font_of(ch):
    try:
        ch.encode("gb2312")
        return "gbsn"
    except UnicodeEncodeError:
        return "bsmi"


def cjk(run):
    """A run of CJK text in the fonts that cover it."""
    parts = []
    i = 0
    while i < len(run):
        term = next((t for t in TERMS if run.startswith(t, i)), None)
        if term:
            parts.append(("bsmi", term))
            i += len(term)
            continue
        f = font_of(run[i])
        if parts and parts[-1][0] == f and not any(parts[-1][1] == t for t in TERMS):
            parts[-1] = (f, parts[-1][1] + run[i])
        else:
            parts.append((f, run[i]))
        i += 1
    return "".join(r"\begin{CJK}{UTF8}{%s}%s\end{CJK}" % (f, tex_escape(t)) for f, t in parts)


def text(t):
    """Escape a line of prose: CJK runs in their fonts, `code`, **bold**."""
    out, pos = [], 0
    for m in re.finditer(r"`([^`]+)`|\*\*([^*]+)\*\*", t):
        out.append(plain(t[pos:m.start()]))
        if m.group(1) is not None:
            out.append(r"\texttt{%s}" % plain(m.group(1)))
        else:
            out.append(r"\textbf{%s}" % plain(m.group(2)))
        pos = m.end()
    out.append(plain(t[pos:]))
    return "".join(out)


def plain(t):
    out, pos = [], 0
    for m in CJK.finditer(t):
        out.append(tex_escape(t[pos:m.start()]))
        out.append(cjk(m.group(0)))
        pos = m.end()
    out.append(tex_escape(t[pos:]))
    return "".join(out)


def code(lines):
    """An indented block, folded at CODE_WIDTH characters, spaces kept."""
    rows = []
    for ln in lines:
        ln = ln[4:] if ln.startswith("    ") else ln.lstrip()
        while len(ln) > CODE_WIDTH:
            cut = ln.rfind(" ", 0, CODE_WIDTH)
            cut = CODE_WIDTH if cut <= 8 else cut
            rows.append(ln[:cut])
            ln = "    " + ln[cut:].lstrip()
        rows.append(ln)
    body = r"\\".join(text(r).replace(" ", r"\ ") if r else r"\ " for r in rows)
    return r"{\ttfamily\scriptsize\raggedright\noindent " + body + r"\par}"


def table(lines):
    cells = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines if not re.fullmatch(r"\|[-| :]+\|", ln.strip())]
    body = r"\\".join(" & ".join(text(c) for c in row) for row in cells)
    return r"{\scriptsize\begin{tabular}{@{}ll@{}}" + body + r"\end{tabular}\par}"


def join(lines):
    """Lines of one paragraph: Chinese lines meet without a space."""
    out = ""
    for ln in lines:
        if out and not (CJK.match(out[-1]) and CJK.match(ln[0])):
            out += " "
        out += ln
    return out


def blocks(md):
    """Markdown to LaTeX, one string per block."""
    out, para, lst = [], [], None
    lines = md.split("\n")
    i = 0

    def flush():
        nonlocal para, lst
        if para:
            out.append(text(join(para)) + r"\par")
            para = []
        if lst:
            kind, items = lst
            env = "itemize" if kind == "-" else "enumerate"
            out.append(r"\begin{%s}[leftmargin=*,topsep=1pt,itemsep=0pt,parsep=0pt]" % env
                       + "".join(r"\item " + text(join(it)) for it in items) + r"\end{%s}" % env)
            lst = None
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            flush()
            i += 1
            continue
        if ln.startswith("    ") and not lst:
            flush()
            blk = []
            while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                blk.append(lines[i])
                i += 1
            while blk and not blk[-1].strip():
                blk.pop()
            out.append(code(blk))
            continue
        if ln.startswith("#"):
            flush()
            level = len(ln) - len(ln.lstrip("#"))
            size = r"\small" if level == 1 else r"\footnotesize"
            out.append(r"{%s\bfseries %s\par}" % (size, text(ln.lstrip("#").strip())))
            i += 1
            continue
        if ln.strip() == "---":
            flush()
            i += 1
            continue
        if ln.lstrip().startswith("|"):
            flush()
            blk = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                blk.append(lines[i])
                i += 1
            out.append(table(blk))
            continue
        m = re.match(r"(\s*)(-|\d+\.)\s+(.*)", ln)
        if m and not m.group(1):
            if para:
                out.append(text(join(para)) + r"\par")
                para = []
            kind = "-" if m.group(2) == "-" else "1"
            if lst and lst[0] != kind:
                flush()
            lst = lst or (kind, [])
            lst[1].append([m.group(3)])
            i += 1
            continue
        if lst and ln.startswith(" "):
            lst[1][-1].append(ln.strip())
            i += 1
            continue
        if lst:
            flush()
        para.append(ln.strip())
        i += 1
    flush()
    return out


def sections(md):
    """Split at every heading; the text before the first heading is dropped."""
    parts = re.split(r"(?m)^(?=#)", md)
    return [p for p in parts if p.startswith("#")]


def main():
    # the address of the hosted service is withheld for review
    from agents_build import BACKEND
    zh = sections(PROMPT_ZH.replace(SITE, "SITE_URL")) + sections(open(ZH, encoding="utf-8").read().replace(BACKEND, "SERVICE_URL"))
    en = sections(PROMPT_EN.replace(SITE, "SITE_URL")) + sections(open(EN, encoding="utf-8").read().replace(BACKEND, "SERVICE_URL"))
    if len(zh) != len(en):
        sys.exit("the Chinese and English instructions have %d and %d sections" % (len(zh), len(en)))
    # agents.md opens with the project name as its title; the row is named after the file
    zh[1] = re.sub(r"^#[^\n]*", "# agents.md", zh[1], count=1)
    en[1] = re.sub(r"^#[^\n]*", "# agents.md", en[1], count=1)
    print("% generated by figures/emit_instructions.py from site/60m/agents.md and site/en/60m/agents.md")
    print(r"\begin{paracol}{2}")
    print(r"{\footnotesize\centering\textbf{English translation}\par}")
    print(r"\switchcolumn")
    print(r"{\footnotesize\centering\textbf{Chinese, as sent}\par}")
    for k, (z, e) in enumerate(zip(zh, en)):
        # as in the ICLR sample table: a rule under the header, and one under the prompt
        print(r"\switchcolumn*[\vspace{-4pt}\noindent\rule{\linewidth}{0.4pt}\vspace{-2pt}]" if k < 2 else r"\switchcolumn*")
        print(r"\footnotesize\setlength{\parskip}{2pt}")
        print("\n".join(blocks(e)))
        print(r"\switchcolumn")
        print(r"\footnotesize\setlength{\parskip}{2pt}")
        print("\n".join(blocks(z)))
    print(r"\end{paracol}")

if __name__ == "__main__":
    main()
