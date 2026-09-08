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

Build: `cd src && latexmk -pdf main.tex`

Before submission: comment out `\iclrfinalcopy` (double blind) and replace
the hanxiao.io URLs with an anonymised mirror.
