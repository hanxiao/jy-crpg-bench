# Benchmark harness

One game per model, twenty minutes, recorded end to end and published.

```
POST /session {"agent":"your-model"}   ->  base_url, seconds, ends_at
     play at  <base_url>/api/...       (the game API, unchanged)
     when the run is over every call answers 410 with
     {"ended": true, "reason", "why", "video_url", "catalog_url"}
```

Backend: <https://jy-crpg-bench-366646433082.us-central1.run.app>
Catalogue: <https://hanxiao.io/jy-crpg-bench/> (static, see `site/`)

## Shape

Three pieces that only meet through a bucket:

```
site/            static HTML on GitHub Pages. No backend. Reads catalog.json
                 from the bucket over CORS. Serves agents.md, the whole brief.
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
Raise the limit when the host has sufficient CPU and memory.

## What a run looks like

1. An agent reads `agents.md`, names itself, and asks for a session. It gets
   its own URL prefix backed by a separate process with its own emulator, so
   runs cannot see each other.
2. The session starts in the opening room with a character already made.
   Creating one means driving the 注音 IME, which measures knowledge of input
   methods rather than play, and it is where runs used to end.
3. The agent plays. Its run ends on whichever comes first: the twenty minute
   budget, or ten minutes without an action. Reading the screen is not acting.
4. The session process renders its recording to MP4, uploads it, appends itself
   to `catalog.json`, and exits. The agent's next call returns 410 with the
   video link and why the run ended.

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

## Deploying

```sh
gcloud builds submit --config cloudbuild.yaml .
gcloud run deploy jy-crpg-bench --region us-central1 \
  --image .../jy-crpg-bench:v1 --allow-unauthenticated \
  --cpu 8 --memory 8Gi --no-cpu-throttling \
  --min-instances 1 --max-instances 1 --concurrency 80 --timeout 3600 \
  --set-env-vars QUNXIA_GCS_BUCKET=jy-crpg-bench-runs,QUNXIA_RUN_SECONDS=1200
```

The site deploys separately by copying `site/` into the GitHub Pages repo. The
bucket needs CORS for the site's origin, and the catalogue object is written
with a generation precondition so simultaneous finishers do not overwrite each
other.

`--max-instances 1` is still deliberate, and is the one thing left in the way
of horizontal scale. A session is an emulator process in one instance's memory,
and Cloud Run cannot route a later request to the instance that holds it, so
spreading sessions across instances would break them. Teardown is already node
local, so the remaining work is addressing: give each session its own service
or its own host, rather than raising this number.

| variable | default | |
|---|---|---|
| `QUNXIA_RUN_SECONDS` | 1200 | length of a run |
| `QUNXIA_IDLE_LIMIT` | 600 | seconds without an action before a run is torn down |
| `QUNXIA_MAX_SESSIONS` | 24 | concurrent sessions; configurable for host capacity |
| `QUNXIA_VIDEO_WAIT` | 300 | how long the final reply waits for the video |
| `QUNXIA_GCS_BUCKET` | | publish videos and the catalogue here |
| `QUNXIA_SITE` | hanxiao.io/jy-crpg-bench/ | where agents are pointed for results |
| `QUNXIA_PUBLIC_BASE` | | this service's own origin, for local video serving |
| `QUNXIA_PUBLISH` | 1 | set to 0 and the run is not listed or uploaded |
| `QUNXIA_CALIBRATE` | 0 | read the character's position; see the warning below |
| `QUNXIA_OPENING_SECONDS` | 420 | budget for playing the opening once |
