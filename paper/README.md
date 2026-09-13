# Paper

ICLR 2027 submission draft for jy-crpg-bench.

- `src/` - LaTeX source (official ICLR 2027 style), `main.pdf` is the build
- `src/figures/make.py` - regenerates the data figures from the published catalogue numbers
- `src/figures/env.tex`, `keymap.tex`, `architecture.tex` - TikZ sources of the
  environment, action-space and apparatus figures; compile each with `pdflatex`
  in `src/figures/` to refresh its PDF
- every number is generated from committed inputs: `src/figures/catalog_snapshot.json`
  and `src/figures/start.state` (the savestate every session boots into).
  `figures/emit_numbers.py` writes `figures/numbers.tex`,
  `figures/emit_table.py` writes `tables/aggregate.tex`,
  `figures/make_metrics.py` writes `tables/family.tex` and `tables/runs.tex`,
  `figures/emit_books.py` writes `tables/books.tex` from the save decoder's
  book table, `figures/make.py` draws the data figures, and
  `check_consistency.py` fails if a claim drifts from the snapshot
- `refs/` - the fourteen reference papers read while shaping the structure, by arXiv id
- `iclr2027/` - the official style-file kit as downloaded

Build, from a clean tree (no `.aux`/`.bbl`):

```sh
cd src
pdflatex -interaction=nonstopmode main.tex   # writes main.aux
bibtex main                                  # refs.bib -> main.bbl
pdflatex -interaction=nonstopmode main.tex   # pulls in the references
pdflatex -interaction=nonstopmode main.tex   # resolves citations and the TOC
```

Do not use `latexmk -pdf main.tex` on a clean tree: with no `main.aux` yet,
latexmk's scheduler sometimes orders `bibtex` before the first `pdflatex`;
bibtex then reads the stub `main.aux` that latexmk planted and the build
dies - a coin flip on every run.

Build with a scheme-full TeXLive: the apt `cjk-latex` package omits the C70
font-shape definitions the abstract's \game title needs, and the build dies
in an undefined macro two lines after a font-substitution warning. Two builds
of the same source differ only in the two timestamps hyperref stamps in and
pdftex's per-build /ID file identifier; commit the PDF alongside the source
change that produced it.

The default `src/main.tex` build is the double-blind review copy. Verify it
without leaving build artefacts in the source tree:

```sh
cd src
python3 check_blind_build.py
```

For a named arXiv/preprint build, uncomment `\blindcopyfalse` and
`\iclrfinalcopy` near the top of `main.tex`; those switches restore the author
block and project links. Keep the blind defaults for a conference submission.
