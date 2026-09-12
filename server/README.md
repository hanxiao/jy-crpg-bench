# Headless server

Runs the game with no display and streams the VGA framebuffer to a browser.

- `tiles.c` diffs the framebuffer against the last frame sent and emits only the
  16x10 tiles that changed. `CoreHost.c` is reused unmodified: it is portable C.
- `server.py` loads both through ctypes, paces the emulation on its own thread,
  deflates each delta and fans it out over one WebSocket that also carries input.
- `index.html` reassembles the tiles onto a canvas with `DecompressionStream`.

## Deploy

```sh
./build.sh                      # -> libqunxia.so (Linux)
python3 -m venv .venv && .venv/bin/pip install aiohttp pillow
.venv/bin/python server.py      # PORT=8080
```

Needs `../cores/dosbox_pure_libretro.so` (libretro buildbot) and `../game/`.

## Endpoints

- `/` browser client, WebSocket tile stream at `/ws`
- `/api/help?lang=en|zh` the whole briefing, in English or Traditional Chinese,
  with this host's URLs baked in: how to drive the game, then the field manual
  covering menus, combat, attributes, the compass and the traps that cost the
  most time. `?part=core` returns only the first half for a tight context
  budget. The page shows it in a copy box so
  a user can paste it into their own LLM and play with no harness of ours. It
  teaches the controls, the two rules that are not discoverable by pressing
  keys, and enough of the opening to get moving. It is deliberately not a
  walkthrough.
- `/api/screen` look at the screen, at its native 320x200. JSON with a base64
  PNG, or `?format=png` for raw bytes. One endpoint, not two envelopes around
  the same thing, and no scaling knob: upscaling server-side only made a bigger
  PNG out of the same pixels.
- `/api/key` presses one key or a list of keys in order and waits for the
  screen to react and then settle, through a scene transition if one starts.
  It returns metadata by default; add `?image=1` to capture the settled PNG
  before another controller can act. There is no wait call: the game moves
  only on input, and an action already waits for its result.
  Short taps default to ten emulated frames, and
  their down, release and inter-tap phases are fenced by the core frame clock,
  so host scheduling cannot silently collapse repeated movement taps.
- `GET /api/keys`, `GET /api/slots`, `POST /api/save` and `POST /api/load` mirror the native
  control API. Save and load are paused between emulated frames so libretro is
  never serialized concurrently with `retro_run`.
- `POST /api/reset?token=...` hidden. Restores the start state, a character
  already created and standing in the opening room, and wipes the activity log.
  Creating a character means driving the 注音 IME, which tests input-method
  knowledge rather than play, so a run should not begin there. Falls back to a
  full reboot when no start state exists, and `POST /api/snapshot?token=...`
  writes the current position as that state. Unlisted in `/api/help`, and 404s
  without the token from `QUNXIA_RESET_TOKEN` rather than 403, so the path
  cannot be confirmed by probing. Pauses the emulation thread first, since
  `retro_reset` underneath a running `retro_run` is a race.
- `/api/recording` streams the original recording journal; `?format=jsonl`
  downloads its tile deltas, input events and action markers as JSONL. Readers
  pin a committed file prefix, so later appends or reset do not change an open
  snapshot. The source journal remains on disk.
  With the saved-history backend, the page plays current and archived recordings
  as saved actions, skipping idle gaps. Each action occupies 0.6 / speed seconds;
  pause/resume and both seek directions retain the selected picture. Original
  JSONL timestamps (`recorded_t`) are shown separately to the millisecond and do
  not wrap after 24 hours. There is no continuous-recording fallback; an
  unavailable action source can be retried.
- `/api/video` submits a background action-video job to the saved-history backend.
  It uses ffmpeg on the server, with progress, cancellation and a completed MP4
  download. Encoding does not wait through original recording timestamps and
  does not disable playback. Temporary status-query failures retain the job and
  retry it. An `X-Video-Request-Id` header or JSON `requestId` makes submission
  idempotent while its in-process job record is retained: retries return the
  same queued/active job, or replay cancelled/error terminal state with HTTP
  200. Reusing a token with a different recording or speed is HTTP 409. If a
  ready MP4 has been evicted while its job record remains, the token returns
  HTTP 410 so the caller can submit a new token instead of silently creating a
  second export. Request-token mappings are not persisted: the same-job-ID
  guarantee ends when the job record is reaped or the service restarts. The
  completed MP4 cache remains persistent. ffmpeg must be installed on the
  server. Cached results are bounded by a 2 GiB / 30-day policy, retaining the
  latest result and active downloads. The source recording and benchmark
  counters are unaffected by export.
- `/api/history?limit=100` the bounded action log. Every REST call and every key pressed in a
  browser is recorded and pushed to all connected pages over the same
  WebSocket, so the activity panel shows an agent and a human acting on the
  shared session side by side. Only the calls that explicitly ask to see the
  screen, `/api/screen`, carries a 150px WebP thumbnail
  (about 2 KB). Attaching one to every keypress buried the log. Only the
  newest 40 entries keep their image.

The live canvas uses the small `zlib` tile encoder. Pillow is used for on-demand PNG/WebP observations, activity thumbnails,
history reconstruction and background video captions.

## Several agents on one session

For long-lived interactive play, set `QUNXIA_RESUME_STATE` to a checkpoint on
persistent storage. The server waits for 1500 emulated frames and a nonempty
framebuffer before loading it, then verifies that frames continue advancing.
`QUNXIA_RESUME_WARMUP_FRAMES` can tune that initial warmup for another core.
`/status.checkpoint.state` is `warming`, `restoring`, `ready` or `failed`;
input is refused until ready. An unreadable checkpoint remains untouched and
blocks input instead of silently starting a new game.

`QUNXIA_AUTOSAVE_SECONDS` defaults to 30; zero disables periodic saves. A clean
shutdown also saves. Serialization and its before/after frame checks share the
action lock. Cancellation and failures discard only the staged new checkpoint,
so the previous one remains available. Abrupt process termination can lose
progress since the last successful checkpoint. Recordings continue through the
existing RecordingStore and are not scanned for replay during startup.
This guarantee requires the atomic CoreHost saver and a rebuilt native bridge:
an older saver that reports success despite a failed buffered close can pass a
partial staged file to the checkpoint layer.

This mode disables the game's automatic menu-save macro and optional position
calibration, whose reload of the opening state would undo resumed progress.
`QUNXIA_BENCH=1` ignores all resume/autosave settings and keeps the normal
benchmark startup, action limits and save/load restrictions.

REST actions and browser key holds share one single-player lease, so a browser
release cannot cancel an API press (or another browser's hold). The queue is
FIFO. Measured against the deployed e2-micro, each
agent pressing a key and reading the screen every third action, with a
spectator attached throughout:

| agents | actions/s | latency p50 | p90 | errors |
|---:|---:|---:|---:|---:|
| 1 | 2.07 | 289 ms | 656 ms | 0 |
| 4 | 3.19 | 1207 ms | 1318 ms | 0 |
| 8 | 2.70 | 2593 ms | 3769 ms | 0 |

Throughput is bounded by how long an action holds the lock, which is dominated
by waiting for the screen to settle. A request that cannot get the lock inside
`QUNXIA_LOCK_TIMEOUT` returns 503 with `"error": "busy"` instead of hanging.
Agents can name themselves with an `X-Agent` header or `?agent=` so a shared
session stays legible in the activity log.

Spectators cost close to nothing. One encode is fanned out to every client, so
the number of watchers changes bandwidth and not CPU.

## Why 26800 cycles

Measured on the target VM: at 77000 cycles the core runs 1.75x faster than the
70.09 fps it needs, which a shared-core instance cannot hold once burst credits
run out. At 26800 (486DX2-66, period-correct for a 1996 game) it runs 6.7x
faster than needed, about 15% of a core, and an e2-micro holds a full 70.1 fps
indefinitely. Override with `QUNXIA_CYCLES`.


## One API, two runners

The native runner (`Sources/QunXia`) and this one answer the same paths under
the same names, with and without the `/api` prefix, and return the same reply
fields: `ok`, `action`, `width`, `height` and `frame`, and no hash or changed
flag, since neither tells a step from an idle animation. `GET /keys` returns one vocabulary -
`server/test_api.py::KeyVocabularyTest` parses `Keys.swift` and fails if a name
resolves to a different scancode in either direction. `GET /help?lang=&part=`
serves the same `skills/` briefing from both, with each host's own URLs
substituted in.

There is one way to do each thing. A press is `/key` with a name or a list of
names, and a repeat is a list of the same name. A settle is `?react`,
`?stable` and `?maxsettle`; there is no fourth knob that replaces them. A
saved state has a `name`; `slot` was that same name spelled a second way. A
reply says what the action was, not what the request said, so the request
fields are not echoed back.

A body field a call does not read is a 400 naming it. Ignoring it silently is
the failure this API exists to avoid: the caller is told 200 and the game does
something else, and the agent has no way to find that out.

Three things still differ, and each is a property of the runner rather than of
the API. The native runner honours `?scale` and defaults to including the
image; this one returns native-resolution frames and omits the image unless
`?image=1`, because a benchmark session should not pay for pixels nobody read.
A scored session also hides `/slots`, `/save`, `/load` and `/reset`: a run with
an out-of-band rewind is not a run.


## Control API and meta API

The nine calls above are the control API: what an agent uses, and all the
briefing in `skills/` teaches. `/status`, `/api/history`, `/api/recording` and
`/ws` are the meta API - what the browser client and the leaderboard read.
They report on a run rather than playing one, and a scored session's own
numbers (`meaningful`, `scenes`, `frontier`, `remaining`) are in `/status`, so
nothing tells an agent they exist. Keep new endpoints on the side of that line
they belong to.

`hold` is in emulated frames and starts at `MIN_HOLD_FRAMES` (5). The game
reads its keyboard once per game-loop iteration, so a keydown and keyup inside
one of them are consumed together and the press never happens. Measured over 24
taps a point against a key whose effect is certain: 1 frame lands 0-29% of the
time, 2 frames 33-67%, 3 frames 79-88%, 4 frames 96-100%, 5 and up 100%. The
default of 10 leaves twice the margin, and every phase is counted in emulated
frames rather than wall clock so host scheduling cannot shorten a pulse.


## Frame waits and failure evidence

An input action keeps its original core-tick targets across hold, release, gap
and settle phases. Its deadline is fixed at entry: requested wall-clock waits
plus the larger of `QUNXIA_STALL_SECONDS + 0.5` (15.5 seconds by default) and
`5 * total_requested_frames / nominal_fps + 0.5`. The frame total includes
release fences and the maximum settle window. Progress never renews the
deadline, and a key or sequence is never replayed to recover from a slow wait.

A progressing core that exhausts this deadline reports `input_frame_timeout`.
A core with no progress for the watchdog interval reports `core_stalled`;
event-loop and finalization watchdog failures have separate sources. Pending
keys are released on exceptions/cancellation when native calls can return. A
native deadlock is terminated by the independent watchdog.

The first fault freezes the current key, stage, target/actual ticks, elapsed
times, up to 64 completed stages and up to 64 watchdog samples. The watchdog
writes `incident.json` and Python thread stacks to `QUNXIA_DIAGNOSTIC_DIR`, or
by default to a unique directory under `QUNXIA_HEALTH_DIR/incidents`. These
records distinguish timeout paths; they do not establish why DOSBox slowed.

Benchmark runs use a fixed monotonic deadline from the moment the opening
state is playable. All waiting (including optional calibration) consumes that
budget without credit. Deadline checks run before each key, while waiting and
before reporting success; the native key gate checks again after acquiring its
execution lock. A time-limit ending still validates core health before it can
be scored as valid. Input/environment failures remain invalid. The broker
stores diagnostics under `<result-dir>/<session-id>.diagnostics` and archives
the last heartbeat, fault and exit status before reclaiming worker scratch.

The multiuser lobby lists games by their latest `live.state` save time and offers
name search, creation-time/name sorting, and a new-game dialog. Reading the lobby
only inspects user metadata and save-file timestamps; it does not start game
workers or read recordings. The displayed time is explicitly a save time, since
a running game may autosave without player input.

## Recording files and reset archives

Interactive servers expose `GET /api/recordings` with a `files` list containing
the current recording and reset archives, including their IDs, filenames and
byte sizes. `GET /api/recordings/{id}` downloads the original JSONL as an
attachment. Single byte ranges, open-ended ranges, suffix ranges and `If-Range`
are supported so a large download can resume. Each response pins its file
descriptor and byte length before streaming; a concurrent reset or append does
not change the bytes in that response.

To replay an archive, start the existing paged reader with
`/api/recording?view=paged&recording={id}`. Continue with the returned token and
cursor as usual; subsequent requests keep the same snapshot. `current` remains
the default. Archive IDs must match `YYYYMMDD-HHMMSS-<12 lowercase hex>.jsonl`
inside the recording's `recordings/` directory. Symbolic links and other file
types are refused. Archives are opened read-only, and their replay duration is
recovered from a bounded file tail without opening another recording writer.

In benchmark mode, the file-list and download routes are absent and archive
selection is rejected. The existing current-recording endpoint and benchmark
accounting remain unchanged. These file selectors do not change the source of
the right-hand screenshot history.

### Disk-backed screenshot history and realtime activity

The page separates two views: **historical screenshots** page through the full
recording, eight images at a time, while **realtime activity** keeps a small
reconnect cache. The 300-entry/40-thumbnail cache does not limit historical
browsing. The history pane can jump to the oldest or latest page and move in
both directions. Only one page of image blobs is held by the browser.

`/api/replay` pins the recording's committed file prefix and builds a disposable
SQLite index in the background. An initial `202` reports indexing progress;
clients poll the returned token until ready, then read bounded `/steps` pages
and individual `/frame` PNGs. Later opens incrementally index appended data.
Tokens expire and release their file handles. Normal game startup does not
scan the recording. The endpoints are absent in benchmark mode.
The benchmark observer page uses the realtime log directly. Reset or a server
session change invalidates an open history page before loading the new snapshot.
Version 2 of the disposable index preserves unknown action results instead of
treating them as failures. The first history open after this upgrade rebuilds
that index once; the source JSONL and the previous version 1 index are retained.

Legacy agent GET/KEY records and older key-only recordings remain readable.
Numbered action markers from newer recordings are supported too. A historical
image is reconstructed from recorded frames, not claimed to be the exact API
response: GET uses the preceding frame, while old key steps wait up to one
second or until the next action. Failed actions show their failure and reason,
and use the frame before their marker. Corrupt frame windows report an error instead
of manufacturing an image. Source JSONL files are never rewritten by readers.

For long-lived play, enable `QUNXIA_PERSIST_HISTORY=1`. New interactive actions
and GET markers are then appended to the full recording, including screen
reads that later leave the realtime cache. Session counters still start fresh
on restart. An explicit game reset clears the cache and rotates the recording
through the existing recording lifecycle. Formal benchmark accounting is
unchanged.

The optional `QUNXIA_SAVES/activity.json` snapshot retains the latest 300 entries
and 40 small WebP thumbnails (64 KiB each) for fast reconnects. Atomic writes
preserve the prior file on failure; invalid snapshots are left intact and
snapshot persistence is disabled for that process. The independent full-disk
history reader remains available.

The optional `server/import_activity.py` command can seed that **realtime
cache** while the server is stopped. This import is optional and not needed to browse complete disk history.
It preserves the recording and labels reconstructed previews with their source
and frame time; existing original thumbnails take priority.

### Trajectory analysis

Every completed input action now has a post-action `trajectory` event in the
JSONL recording. It carries the action number, original recording time, scene,
frontier, and whether the settled picture changed. When position offsets have
been calibrated for that worker it also carries the game's `x` and `y`; a
missing coordinate is explicit and is never interpreted as zero distance. The
event also stores the source action timestamp, so analysis remains correct
when a worker restarts and its local action counter starts over.

The raw recording can be analyzed without starting the game:

```sh
python3 Scripts/analyze_trajectory.py /path/to/recording.jsonl --window 25
```

The JSON result includes per-action rows, early/later windows, action gaps,
long pauses, reversals, screen-change ratio, and position distance/frontier
regressions when coordinates are available. These are descriptive indicators, not a route-quality score. Distances
only join consecutive samples in the same recorded scene; missing samples
and scene changes break the path. Calibration remains off by default, so
this change does not by itself provide reliable live coordinates. The the `position-unmeasured` status
marks runs where only action-level smoothness can be assessed.
Trajectory events are recorder-only data: benchmark callers can continue to
read the ordinary action/frame journal, while the coordinate-bearing events
are filtered from their recording endpoint responses.
