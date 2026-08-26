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
python3 -m venv .venv && .venv/bin/pip install aiohttp
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
  the screen to react and then settle, but return no picture. Acting and
  looking are separate calls. Short taps default to ten emulated frames, and
  their down, release and inter-tap phases are fenced by the core frame clock,
  so host scheduling cannot silently collapse repeated movement taps.
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
- `/api/history` the action log. Every REST call and every key pressed in a
  browser is recorded and pushed to all connected pages over the same
  WebSocket, so the activity panel shows an agent and a human acting on the
  shared session side by side. Only the calls that explicitly ask to see the
  screen, `/api/screen`, carries a 150px WebP thumbnail
  (about 2 KB). Attaching one to every keypress buried the log. Only the
  newest 40 entries keep their image.

PNGs are written by a ~10 line encoder over `zlib` rather than pulling in an
image library.

## Several agents on one session

Actions are serialised so the game stays coherent, and the queue is FIFO, so
agents take strictly fair turns. Measured against the deployed e2-micro, each
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
