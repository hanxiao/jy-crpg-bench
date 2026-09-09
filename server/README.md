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
- `/api/key`, `/api/keys`, `/api/wait` apply input and wait for
  the screen to react and then settle. They return metadata by default; add
  `?image=1` to capture the settled PNG before another controller can act.
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
- `/api/recording` the session as tile deltas plus key presses, for playback.
  Recording restarts with the game, keeps every frame while anyone is acting,
  and once idle keeps only the last 30 seconds so an untouched game still shows
  its own animation without growing forever. A whole picture is forced every 30
  seconds so a pruned recording always has somewhere to start replaying from.
  The page plays it back at 4x from a button in the activity header, and can
  export it as a video from another. Export composites the frames with the keys
  that were held and encodes in the browser with MediaRecorder, so the server
  spends nothing on it. MediaRecorder captures in real time, so an export takes
  the length of the recording divided by four.
- `/api/history?limit=100` the bounded action log. Every REST call and every key pressed in a
  browser is recorded and pushed to all connected pages over the same
  WebSocket, so the activity panel shows an agent and a human acting on the
  shared session side by side. Only the calls that explicitly ask to see the
  screen, `/api/screen`, carries a 150px WebP thumbnail
  (about 2 KB). Attaching one to every keypress buried the log. Only the
  newest 40 entries keep their image.

The live canvas uses the small `zlib` tile encoder. Pillow is used only for
on-demand PNG/WebP observations and activity thumbnails.

## Several agents on one session

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
fields: `ok`, `action`, `changed`, `settled_frames`, `width`, `height`, `frame`
and `screen` (the frame hash). `GET /keys` returns one vocabulary -
`server/test_api.py::KeyVocabularyTest` parses `Keys.swift` and fails if a name
resolves to a different scancode in either direction. `GET /help?lang=&part=`
serves the same `skills/` briefing from both, with each host's own URLs
substituted in.

There is one way to do each thing. A wait is `ms`; there is no frame-counted
spelling of it. A settle is `?react`, `?stable` and `?maxsettle`; there is no
fourth knob that replaces them. A saved state has a `name`; `slot` was that
same name spelled a second way. A repeat of one key is `/key` with `times`;
`/keys` is for a sequence of different keys. A reply says what the action was,
not what the request said, so the request fields are not echoed back.

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
