# Paper

ICLR 2027 submission draft for jy-crpg-bench.

- `src/` - LaTeX source (official ICLR 2027 style), `main.pdf` is the build
- `src/figures/make.py` - regenerates the data figures from the published catalogue numbers
- `src/figures/env.tex`, `keymap.tex`, `architecture.tex` - TikZ sources of the
  environment, action-space and apparatus figures; compile each with `pdflatex` in
  `src/figures/` to refresh its PDF
- every number is generated from committed inputs: `src/figures/catalog_snapshot.json`
  and `src/figures/start.state` (the savestate every session boots into),
  plus `src/figures/timelines/<id>.json`, the published keypress timeline of
  every session the paper reads, which the replay-pattern macros are read from.
  `src/figures/recover_sessions.py` rebuilds `recovered_sessions.json`, one row
  per session the live catalogue no longer lists, from the preserved saves in
  `src/figures/slots/` and the timelines; `catalog_backup_20260911T174413Z.json`
  is the catalogue as it stood before it was cleared for the final sweep.
  `field.py` merges the three, leaves out the models in its `EXCLUDED` list
  (a version with two later versions of its line in the field) and credits a
  model with every rung any of its sessions reached; `slots.py` decodes every preserved save in
  `src/figures/slots/`, including the leader's level and experience, which the
  live memory read does not follow; `replay_scan.py` matches five fixed panels of the game
  (`src/figures/templates/`), the message drawn when an item enters the
  bag and the three that close a won battle (win, experience, level) against every frame of every published replay video, keeping the best
  score of each second, and writes `replay_events.json`, the record of the
  events the game keeps only on screen, the item reading for sessions whose bag no record
  carries, the scenes each session entered (read by name from the banner
  the game draws on entry, matched against `src/figures/templates/scenes/`,
  one file per scene name), and, from the first fully black frame, the
  actions each session took to reach the world map
  (run it with a directory of the videos, or let it fetch them).
  `figures/emit_numbers.py` writes `figures/numbers.tex`,
  `figures/make_metrics.py` writes `tables/family.tex` and `tables/runs.tex`,
  `figures/emit_books.py` writes `tables/books.tex` from the save decoder's
  book table, `figures/emit_effort.py` writes `tables/effort.tex` (sessions,
  actions, keys per action and the time between actions per model),
  `figures/emit_milestones.py` writes `tables/milestones.tex` (all eleven
  milestones in the hour model sessions, with no median when none reached one),
  `figures/make.py` draws the data figures, and
  `check_consistency.py` fails if a claim drifts from the snapshot.
  `preflight.py` also runs `figures/test_priority_metrics.py`: the checks cover
  Figure 7's total-session denominator, Figure 3's separate model and human
  effort axes, and the counts and timestamp evidence of all eleven Table 4 rows.
- `src/figures/human_sessions.json` - the published videos of human players
  behind the two reference rows of Figure 3: for each, the class (speedrun or
  playthrough), the crop that maps the capture onto the native frame, the start
  of play, the minute of every milestone with the evidence it was read from, and
  the video-estimated steps to the world map (tile steps plus screen changes,
  not logged keypresses). Figure 3 shows these on their own axis, separate from
  model keypresses. The tools are in `src/figures/human/`:
  `gate.py` admits a capture when the opening room of a benchmark replay matches
  it at 0.90 or above and records every rejection in `dropped.json`;
  `read_video.py` locates the game frame (`findcrop`, `edgecrop`, `refinecrop`,
  with `cropfit.py` for the whole-pixel fit), crops and scales the capture,
  matches the panels and the messages, and counts tile steps and screen changes,
  which `actions.py` prints per capture; `respawn.py` sets the start of play on
  the first frame in which the hero stands on his spawn tile with his back to the
  camera, frame zero of a benchmark replay, and `spawnscan.py` does the same for
  one capture. The evidence sheets are under `human/evidence/<video id>/`, the
  videos themselves are not tracked, and `field.human_rows()` turns the file into
  the two rows. `src/figures/human_route.py` draws the human route figure
  (`route-human.pdf`) from the speedrun BV1UxvTz3Ehe: its walks through the starting
  house and on the world map are read by the trackers of the model figures into
  `routes/human-*.json`, and `src/figures/human/route.py` stitches the house of the
  hermit (`route-house.png`) and its path. `src/figures/compound_panorama.py` grows the
  human stitch `human/templates/compound-bg.png` into one panorama
  of the whole compound (`src/figures/compound.png`) with the replay of a session
  that walked the whole yard, and `src/figures/anchored_route.py <session id>` places
  each frame of a benchmark replay, up to its first black frame, on that panorama by
  masked cross-correlation and writes the hero's path with the minute of each point
  to `src/figures/routes/compound-<id>.json`.
- `src/figures/worldmap.py` - renders the world map at native scale from the game's
  EARTH, SURFACE and BUILDING grids and MMAP.GRP into `worldmap.png` (not tracked,
  since it is game art; rerun it from the local game copy). `worldmap_route.py
  <session id>` places every world-map frame of a replay on it and writes the hero's
  tile and minute to `routes/world-<id>.json`; the hero stands at a fixed screen
  point, fixed by a compass reading of a replay. `routes.py` draws
  `routes-compound.pdf` and `routes-world.pdf` from the `routes/` files.
- `src/figures/emit_instructions.py` - sets the instructions every model reads
  (`site/60m/agents.md`, Chinese) beside their English translation
  (`site/en/60m/agents.md`) as `tables/instructions.tex`, the appendix of the
  instructions, with the service address withheld.
- `src/figures/long_submissions.json` - every attempt at the four-hour budget with its
  status and reason. `long_cohort.py` selects the sessions that count (ended by the
  service at the budget, last key in the final fifteen minutes) and refuses an attempt
  the manifest does not list;
  `field.long_attempts()` returns the archive and `field.load_long()` the sessions
  that count. `long-submissions.md` lists the decisions. Run
  `python3 -B figures/test_long_cohort.py` from `src/` after editing the manifest.
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

Build with a scheme-full TeX Live. The Traditional Chinese terms are set with
`CJKutf8` in the `bsmi` face, which needs the `cjk` and `arphic` packages
(both in TeX Live full and on arXiv); the apt `cjk-latex` package omits the
C70 font-shape definitions and the build dies in an undefined macro two lines
after a font-substitution warning. A good build embeds only subset Type 1
fonts (`pdffonts main.pdf` shows every `bsmiu*` row as embedded) and its log
has no `Missing character` line. Two builds
of the same source differ only in the two timestamps hyperref stamps in and
pdftex's per-build /ID file identifier; commit the PDF alongside the source
change that produced it.

Before submission: comment out `\iclrfinalcopy` (double blind) and replace
the hanxiao.io URLs with an anonymised mirror.
