# Benchmark harness

One game per session, four hours by default, recorded end to end and published.

```
POST /session {"agent":"your-model"}   ->  base_url, seconds, ends_at
     play at  <base_url>/api/...       (the game API, unchanged)
     when the run is over every call answers 410 with
     {"ended": true, "reason", "why", "video_url", "catalog_url"}
```

`base_url` is the run's play credential: it carries the session's token in
its path (`/s/<id>/t/<token>`), and an address without it can watch the run
but not send input to it.

Backend: <https://jy-crpg-bench-366646433082.us-central1.run.app>
Catalogue: <https://hanxiao.io/jy-crpg-bench/> (static, see `site/`)

## Shape

Three pieces that only meet through a bucket:

```
site/            static HTML on GitHub Pages. No backend of its own. Reads the
                 catalogue and live index from the broker, which answers the
                 site alone. Serves agents.md, the whole brief.
bench/broker.py  the front door. Spawns one game process per agent and keeps
                 in-memory routing and live-view metadata.
server/warden.py inside each game process. Owns that run's clock, teardown,
                 video and catalogue entry, then exits.
```

The point of the split is that nothing central supervises a run. The process
that played the game is the one that decides it is over, renders it, publishes
it, and takes itself down. A node that dies takes only its own runs with it,
and there is no in-memory catalogue to lose. Concurrent sessions default to a
limit of 24, configurable with `QUNXIA_MAX_SESSIONS`; there is no waiting queue.
Raise the limit when the host has sufficient CPU and memory. A create request
is not the run: the session lives in the broker's table, so a client that
gives up mid-boot leaves a run that keeps playing, holds its slot, and ends
on its budget like any other.

## What a run looks like

1. An agent reads `agents.md`, names itself, and asks for a session. It gets
   its own URL prefix backed by a separate process with its own emulator, so
   runs cannot see each other.
2. The session starts in the opening room with a character already made.
   Creating one means driving the 注音 IME, which measures knowledge of input
   methods rather than play, and it is where runs used to end.
3. The agent plays. Its run ends when its budget lapses, four hours by
   default.
4. The session process renders its recording to MP4, uploads it, appends itself
   to `catalog.json`, and exits. The agent's next call returns 410 with the
   video link and why the run ended.

The create call takes one more option, for operators: `"publish": false`. The
run plays and records exactly like any other but leaves no catalogue entry and
no video in the bucket, so smoke tests stay off the board; it still counts
against the session limit and shows as a live row while it runs.

## What is measured

Everything is taken from the run's own traffic, so it holds for any harness.

| field | |
|---|---|
| `actions`, `aps` | how much the agent did, and how fast |
| `key_events` | submitted key steps in decisions that started processing |
| `input_frames` | requested held frames summed over those key steps |
| `wait_calls` | decisions that submitted no key steps |
| `ttfa` | seconds to the first action - a slow start is usually time spent reading rather than playing |
| `gap_p50`, `gap_p95`, `gap_max` | think time between actions |
| `distinct_keys`, `keys` | how much of the action space it reached, and the histogram |
| `reads` | screen looks, against actions taken |
| `errors` | unmeasured (`null`); older zero values were placeholders, not counted errors |
| `reason`, `why` | `time`, `idle`, or `never started` |

Key and held-frame totals are recorded before a decision executes. They include
submitted steps that may not finish if the call or run is interrupted; they do
not measure actual executed keyboard input. The separate `error` field reports
recording or publication failures after the run, without changing its stop reason.

Token usage is not in the table because it is not taken from the run's traffic:
a model does not know its own cost, but the harness does. The pi harness reads
its session log after the benchmark ends and reports the run's turns, total
tokens, and cost - metered against the USD-per-million-token rates declared
for the model - to the broker, which attaches the report to the catalogue
entry. A harness that does not report leaves the entry without usage; a run
whose model has no declared rates carries no cost; the site shows a dash,
never a zero.

A harness can also file what it kept of the run, through the same address:

```
POST <base_url>/harness/upload {"name":"bundle.zip"|"trace.html","size":N}
                                           -> put_url: PUT the file there
POST <base_url>/harness {summary}          -> attached as the entry's "harness"
```

`POST <base_url>/withdraw {"why": "..."}` ends a run at once under reason
`withdrawn`, for a harness whose model opened a session the protocol does not
allow. The run finalizes like any other - video, timeline, catalogue entry -
and the board keeps it out of its standings.

`put_url` is a one-off upload session for one object of that size under
`harness/<agent>-<id>-<random>/` in the bucket, so a bundle of hundreds of MB
never passes through the service. The summary is plain JSON up to 64KB with
strings and lists capped; the service adds `files`, the paths and sizes of the
two files it finds in the store, so a report cannot point the board at
anything else. Like usage, a record filed before the entry exists waits on the
session until the entry lands, for up to ten minutes counted from the run's
end. `Scripts/bench_jobs.py` files both.

What the game itself is read for, and what the board ranks on, is the
`measure` block of each entry, read from the frames as the run is played by
`server/measure/` (see the main README):

| field | |
|---|---|
| `measure.rungs` | the paper's eleven milestones, each reached, not reached, or unread |
| `measure.chain` | the minute of play each step of a playthrough was first passed |
| `measure.first`, `measure.scenes` | the first minute of every event, and each location entered |
| `measure.crossing_keys`, `crossing_actions` | keypresses and actions before the exit from the starting house |
| `measure.routes_url`, `house_url`, `world_url` | the route points and the two route pictures, under `routes/` in the bucket |
| `measure.dialogue` | conversations, how many of them were distinct, and the minute of the first; counted, not laddered |
| `measure.saves`, `measure.loads` | each save of the player's own and each load, `{minute, slot}`; a load from the screen after a lost fight carries `after_defeat` |

Dialogue is read from the portrait frame of the dialogue box (the opening
tutorial's guide is left out); a box that returns after the screen was free
of one opens a new conversation, and two whose first boxes show the same text
are one conversation heard again. Saves and loads are read from 請稍候 beside
the lit row of the system menu, and from the 載入進度 menu after a lost fight.
Sessions played while the service still saved for itself show its saves too;
a save is the player's when the player's last action pressed enter or space
and its keys ended at most two seconds of play before the notice. Checked on
the 91 replays the paper reads: every one of the 89 saves and loads read was a
real one on the frame, and on runs played without the service's save every
save notice was attributed to the player. `measure.version` 2 carries these;
`bench/backfill_measure.py counters` and `publish-counters` add them to
published entries without measuring the routes again.

Books and the compass also come from the machine: the inventory sits in the
800 bytes in front of the 320 character records and moves the moment
something is picked up. `bench/backfill_measure.py` gives a published entry
its `measure` block from its video, as the paper's figures were read.

None of this is in the Control API and a scored run withholds it from anyone
without the operator token until the run is over. An agent that could read its
own score could play the score, and one that could save could also load.

What the screen itself is read for, none of it a model judging another model:

- **screen-changing decision ratio** - adjacent decision results whose final
  frames differ. On its own it rewards doing very little, so the board shows
  the count beside it and plots one against the other.
- **oscillation** - A to B and back to A, the failure the literature names.
- **scenes** - a legacy name for detected fully black transitions. This is a
  proxy rather than proof of which scene was entered. The opening room reads
  luma 92 and the detection threshold is 12.
- **ground covered** - how far from each scene's entrance the character got,
  summed over scenes, kept as a maximum so retracing cannot inflate it.
  **Off by default.** It needs the character's coordinates, and the only way
  found to locate them is to reload a savestate into the running machine,
  which crashes DOS on the container's core build: the session comes back
  showing DOSBox Pure's "DOS Crashed" menu and never responds again. Turning
  `QUNXIA_CALIBRATE=1` back on without a different way to find the offsets
  will break every session it touches.

There is deliberately no count of distinct places. It was measured off the
framebuffer, and the framebuffer cannot answer it: the menu is an overlay whose
width follows its contents, so no fixed mask covers it, and a five tile
corridor reported ten places.

## Long-horizon report

The short run and its published fields remain the benchmark's frozen baseline.
For runs lasting from tens of minutes through one or two days, an additive
checkpoint report can score the journey without changing those fields. It has
separate medium and long horizons for the inn, Nan Xian, the compass, battles,
growth, quest coverage, the fourteen books and the ending. The checkpoint
contract, component weights, missing-data rules and examples are documented in
[`LONG_HORIZON_SCORING.md`](LONG_HORIZON_SCORING.md); the pure scorer is
`long_horizon.py` and does not read or rewrite the short-run metrics.

## Recording

A recording is the tile deltas the browser stream already produces, kept with
timestamps together with the keys that caused them, who sent them, and the
action id. Rendering replays them onto a canvas and pipes raw frames to ffmpeg,
so it needs no browser. Video is native 320x200 with a strip underneath showing
the agent, the current action id, the keys held, and the elapsed play clock.

## Layout

```
broker.py      spawns and routes; in-memory routing/live metadata
bootstrap.py   plays the opening once to create the state runs start from
render.py      recording -> MP4
Dockerfile     game, core, renderer and backend in one image
```

## Running it locally

```sh
./server/build.sh                       # libqunxia for this platform
python3 -m venv .venv && .venv/bin/pip install aiohttp pillow numpy
QUNXIA_RUN_SECONDS=120 QUNXIA_IDLE_LIMIT=45 QUNXIA_PYTHON=$PWD/.venv/bin/python \
  QUNXIA_CORE=$PWD/Cores/dosbox_pure_libretro.dylib \
  QUNXIA_PUBLIC_BASE=http://127.0.0.1:8090 PORT=8090 .venv/bin/python bench/broker.py

python3 -m http.server 8099 --directory site      # then open
# http://127.0.0.1:8099/?catalog=http://127.0.0.1:8090/api/catalog
```

The start state is built on first boot if it is missing. A DOSBox Pure
savestate belongs to the core build that wrote it, so it cannot ship with the
image and is made wherever the service runs.

## A human session

A person plays a scored session through the same control API a model uses.
`Scripts/human_play.py` asks the service for a session and serves a page on
your machine that shows the frame the API returns and sends every key press as
one `POST /api/key`, looking once after it. The brief is a click away and is
fetched through the same API, so the clock runs while you read it, as it does
for a model. The page talks only to the local script, which holds the token.

```sh
./Scripts/human_play.py --agent human-1 --minutes 60          # scored and published
./Scripts/human_play.py --agent human-trial --no-publish      # try the client first
```

The browser view of a session is a spectator view: the worker drops keys sent
over its socket while a session is scored, and the broker relays that socket
one way, so keys reach a scored game only through the API. A human session is
recorded, scored and published like any other and shows the same milestones.
When reporting it, record who played (first-time player or not, reads
Traditional Chinese or not, knows the novels or not), that the brief was read
on the clock, the display (the frame at three times its size, pixelated), and
the one-key-per-press protocol.

## Deploying

```sh
./Scripts/pack-game.sh   # assets/game-data.tar.gz from your game/ copy (not in git)
gcloud builds submit --config cloudbuild.yaml . --substitutions _TAG=v31
gcloud run deploy jy-crpg-bench --region us-central1 \
  --image .../jy-crpg-bench:v31 --allow-unauthenticated \
  --cpu 8 --memory 16Gi --no-cpu-throttling \
  --min-instances 1 --max-instances 1 --concurrency 80 --timeout 3600 \
  --set-env-vars QUNXIA_GCS_BUCKET=jy-crpg-bench-runs,QUNXIA_RUN_SECONDS=14400, \
    QUNXIA_OPENING_SECONDS=900,QUNXIA_RECORDING_ALLOW_EPHEMERAL=1
```

The image tag tracks the code version, so the build and the deploy name the
same artifact. The game data is your own copy of the game (see the top-level
README), archived into `assets/` by the pack step; the archive is kept out of
git, so a checkout without `game/` cannot build the image.

The site deploys separately by copying `site/` into the GitHub Pages repo. The
bucket needs CORS for the site's origin, and the catalogue object is written
with a generation precondition so simultaneous finishers do not overwrite each
other.

Recordings are written to `QUNXIA_RECORDING_DIR`, which inside a container is
instance memory: startup rejects that unless the deployment either mounts a
persistent volume there or sets `QUNXIA_RECORDING_ALLOW_EPHEMERAL=1`. A run
cannot outlive its instance, so opting in loses only the journal read back
after the instance stops, and the broker says so in a warning at every start.
See `server/RECORDING.md`.

Journals grow with the play, not with the clock: the opening room's ambient
animation commits about 0.8 KB/s whether or not the agent acts (a run of
space presses added nothing measurable on top), and continuous walking -
the camera is locked to the character, so the whole tile grid changes -
commits about 12 KB/s. A full-budget 24-hour run that keeps walking therefore
lands around 1 GB of journal in instance memory: 24 simultaneous such runs
would exceed the 16 Gi limit, so the 24-session capacity holds while runs are
short or the play is light, and a run that outgrows the memory takes the
instance down with it, the way every other memory failure does.

`--max-instances 1` is still deliberate, and is the one thing left in the way
of horizontal scale. A session is an emulator process in one instance's memory,
and Cloud Run cannot route a later request to the instance that holds it, so
spreading sessions across instances would break them. Teardown is already node
local, so the remaining work is addressing: give each session its own service
or its own host, rather than raising this number.

A create holds its request while the game boots and the opening state loads -
tens of seconds - so a burst of many simultaneous `POST /session` calls can
outrun the platform's per-instance request placement: some answer 429 before
reaching the broker. Nothing is queued and nothing is half-created, so a 429
is retried like the 503 "at capacity"; the in-flight creates' reservations
keep their slots. 24 simultaneous creates lose up to half to 429s on this
service; 24 simultaneous short requests lose none.

| variable | default | |
|---|---|---|
| `QUNXIA_RUN_SECONDS` | 14400 | length of a run |
| `QUNXIA_INDEX_PREFIX` | empty | prefix of the catalogue and live-index objects in the bucket; a random path, since those two are the only way to find runs and the bucket does not list |
| `QUNXIA_BOARD_ORIGINS` | the site | further origins, comma-separated, whose pages may read the catalogue, the live index, the session list and a spectator's view |
| `QUNXIA_IDLE_LIMIT` | 0 | seconds without an action before a run is torn down; 0 leaves runs alone |
| `QUNXIA_MAX_SESSIONS` | 24 | concurrent sessions; configurable for host capacity |
| `QUNXIA_REAP_GRACE` | 600 | seconds a finished run's entry outlives its process, so late calls - the agent's final 410, a usage report - still find it; a held usage report holds it further until merged or dropped |
| `QUNXIA_VIDEO_WAIT` | 300 | how long the final reply waits for the video |
| `QUNXIA_GCS_BUCKET` | | publish videos and the catalogue here |
| `QUNXIA_SITE` | hanxiao.io/jy-crpg-bench/ | where agents are pointed for results |
| `QUNXIA_PUBLIC_BASE` | | this service's own origin, for local video serving |
| `QUNXIA_PUBLISH` | 1 | set to 0 and the run is not listed or uploaded |
| `QUNXIA_CALIBRATE` | 0 | read the character's position; see the warning above |
| `QUNXIA_OPENING_SECONDS` | 420 | budget for playing the opening once |
| `QUNXIA_SNAPSHOT_EVERY` | 0 | seconds between attempts to have the game save itself, from a world-map frame only; the broker sets 120 for a scored session |
| `QUNXIA_SNAPSHOT_SLOT` | 3 | which of the game's three save slots the benchmark writes |
| `QUNXIA_SNAPSHOT_LAST_CALL` | 25 | seconds of budget left when a scored run gets its last save |
| `QUNXIA_RECORDING_DIR` | `<repo>/recordings` | where the recording journals are written |
| `QUNXIA_RECORDING_ALLOW_EPHEMERAL` | | `1` lets a container deployment accept instance-memory recordings; without it (or a persistent volume) startup is rejected |
