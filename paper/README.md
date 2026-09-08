# Paper

ICLR 2027 submission draft for jy-crpg-bench.

- `src/` - LaTeX source (official ICLR 2027 style), `main.pdf` is the build
- `src/figures/make.py` - regenerates every figure from the published catalogue numbers
- every number is generated from committed inputs: `src/figures/catalog_snapshot.json`
  and `src/figures/start.state` (the savestate every session boots into).
  `figures/emit_numbers.py` writes `figures/numbers.tex`,
  `figures/emit_table.py` writes `tables/aggregate.tex`,
  `figures/make_metrics.py` writes `tables/family.tex` and `tables/runs.tex`,
  `figures/make.py` draws the four figures, and `check_consistency.py`
  fails if a claim drifts from the snapshot
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

The committed `main.pdf` is the CI build: the `paper-pdf` job rebuilds the
source in a pinned TeXLive container (scheme-full - the apt `cjk-latex`
package on a bare runner omits the C70 font-shape definitions the abstract's
\game title needs) and fails unless the committed PDF matches that build
byte for byte, modulo the two timestamps hyperref stamps in and pdftex's
per-build /ID file identifier. A local build
is for reviewing changes; to commit a rebuilt PDF, push the source and commit
the job's `paper-main` artifact.

Before submission: comment out `\iclrfinalcopy` (double blind) and replace
the hanxiao.io URLs with an anonymised mirror.
