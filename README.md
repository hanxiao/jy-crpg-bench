# jy-crpg-bench

![jy-crpg-bench](docs/banner.png)

A long-horizon benchmark for agents, built on the unmodified 1996 DOS CRPG
金庸群俠傳. The agent gets raw 320x200 frames, a key list and one page of
objectives, and has to find fourteen books in an open world.

| | |
|---|---|
| Environment | 金庸群俠傳 (河洛工作室, 1996), DOS, unmodified binary under DOSBox Pure |
| Observation | raw VGA frames, 320x200, Traditional Chinese text |
| Action | 4 diagonal movement keys and 5 interaction keys; the API accepts the full DOS keyboard (~90 named keys) |
| Horizon | open world, no fixed episode length |
| Objective | recover fourteen books and return to the present |
| Interfaces | HTTP API, MCP server, built-in Pi harness, browser |
| Runners | native macOS (Metal), headless Linux or macOS (browser stream) |
| Leaderboard | <https://hanxiao.io/jy-crpg-bench/> |

![Native macOS runner](docs/native.png)

The macOS runner: Metal presents the framebuffer, CoreAudio plays the Sound
Blaster output, and the right pane logs every control API call with the key
pressed and the screen it returned.

![Browser runner](docs/web.png)

The headless runner streamed to a browser. The activity panel shows every
action from every agent and human on the session, with a replay and MP4 export.

## Why this game

- No level to clear. Progress means recruiting characters, learning martial
  arts and locating fourteen books across a large map. An episode is hours.
- Every objective and branch is Traditional Chinese prose at about sixteen
  pixels a line. Perception and reading cannot be separated.
- The four movement axes are diagonals on screen and the camera is centred on
  the player. Agents that reason in screen coordinates walk in circles.
- No accessibility tree, no state dump, no reward shaping, no walkthrough. The
  briefing in `skills/` teaches the controls and the mechanics that cannot be
  discovered by pressing keys, and stops there.

The emulator runs continuously. The environment does not pause while a model
thinks.

## Setup

You supply the game. The 1996 release is copyright its publisher and is not in
this repository. Put the original files in `./game`, or build the archive that
`run.sh` unpacks:

```sh
git clone https://github.com/hanxiao/jy-crpg-bench.git
cd jy-crpg-bench
mkdir -p game && cp -R /path/to/jinyong/* game/     # PLAY.BAT, Z.COM, DOS4GW.EXE, data
./Scripts/pack-game.sh                              # optional: assets/game-data.tar.gz
```

### Native macOS runner

```sh
./Scripts/run.sh                    # swift build -c release, then the app
./Scripts/run.sh --port 8765        # control API port (default 8765)
```

The DOSBox Pure core is prebuilt in `Cores/`. Window keys: arrows and numpad
move, enter and space confirm, esc opens the menu, y and n answer prompts, and
the 注音 name entry works. ⌘1 to ⌘5 set the scale, ⌘I hides the log pane, ⌘S
and ⌘L quick save and load, ⌘M mutes, ⌃⌘F is fullscreen. The window snaps to
whole multiples of 320x200.

### Headless runner (Linux or macOS)

```sh
./server/build.sh                                   # -> server/libqunxia.so
python3 -m venv .venv && .venv/bin/pip install aiohttp pillow
QUNXIA_CORE=$PWD/Cores/dosbox_pure_libretro.dylib PORT=8080 .venv/bin/python server/server.py
```

On Linux, download `dosbox_pure_libretro.so` from the libretro buildbot into
`cores/` (the default `QUNXIA_CORE`). Open `http://127.0.0.1:8080/` for the
browser client. The control API is under `/api/`. Set `QUNXIA_RESET_TOKEN` to
enable `POST /api/reset?token=...`, which restores the opening save state in
`saves/start.state`.

Both runners load the same core through the same C host (`Sources/CoreHost`)
and expose the same key vocabulary and control API.

## Three ways to let a model play

### 1. HTTP API and the served briefing

Any agent loop that can call HTTP can play. `GET /api/help?lang=en|zh` returns
the whole briefing with this host's URLs substituted in: `skills/play.*.md`
(controls, API, the isometric axes) followed by `skills/speedrun.*.md` (menus,
combat, attributes, the compass, the expensive traps). `?part=core` returns the
first half only. Paste it into a system prompt and the model has everything it
needs.

```
GET  /api/screen[?format=png]         look; JSON with a base64 PNG, or raw bytes
GET  /api/help?lang=en|zh[&part=core] the briefing
GET  /api/keys  /api/slots  /api/history?limit=100
POST /api/key    {"key":"kp3"}        one key; "times" repeats, "hold" frames
POST /api/keys   {"keys":["kp9","enter"]}   several in order, "gap" frames between
POST /api/wait   {"ms":1000}
POST /api/save   {"slot":1} | {"name":"before-boss"}
POST /api/load   {"slot":1}
```

Actions wait for the screen to react and then hold still, and return
`changed`, `frame` and `settled_frames`. They return no picture by default; add
`?image=1` to capture the settled frame before the action lock is released, so
the observation cannot belong to another controller's action. `?stable`,
`?react` and `?maxsettle` tune the wait in frames. The native runner uses the
same paths without the `/api` prefix and includes the image unless `?image=0`.

Requests outside these bounds get a 400 with the reason:

| parameter | range |
|---|---|
| `hold` | 1 to 1200 frames, default 10 |
| `times`, `keys` | 1 to 100 |
| `gap` | 0 to 600 frames, default 6 |
| `ms` | 0 to 60000 |
| `stable` | 1 to 600 frames, default 9 |
| one action | at most 2800 frames in total |

One action runs at a time. A caller that cannot get the lock within
`QUNXIA_LOCK_TIMEOUT` (30 s) gets a 503 with `"error": "busy"`. Name your agent
with an `X-Agent` header or `?agent=` so the activity log stays legible.

The world is isometric. The numpad names match what you see and are
byte-identical to the arrows:

| key | aliases | screen direction |
|---|---|---|
| `kp7` | `left`, `upleft`, `nw` | up-left |
| `kp9` | `up`, `upright`, `ne` | up-right |
| `kp1` | `down`, `downleft`, `sw` | down-left |
| `kp3` | `right`, `downright`, `se` | down-right |

Holding a key walks continuously: one call with `"hold": 120` covers more
ground than eight taps, at one settle instead of eight. Any key advances
dialogue. `Scripts/play.py` is a command-line client for the same API.

### 2. MCP server

`mcp-server/server.py` wraps the API for any MCP client (Codex, Claude Code,
Cursor, and others). It works with both major versions of the Python SDK.

```sh
QUNXIA_API=http://127.0.0.1:8765 uv run --with 'mcp>=1,<3' mcp-server/server.py
# headless runner: QUNXIA_API=http://127.0.0.1:8080/api
```

The server sends the briefing as MCP `instructions` at connection time and
exposes it again through the `guide` tool. Tools: `look`, `press`,
`press_sequence`, `move`, `wait`, `guide`, `save_state`, `load_state`,
`list_states`, `reset_game`. Action tools return a status line and the
resulting frame as an image. Rejected inputs surface as tool errors.

Register it once:

```sh
# Codex CLI or app
QUNXIA_API=http://127.0.0.1:8765 ./Scripts/setup-codex.sh

# Claude Code
claude mcp add qunxia -e QUNXIA_API=http://127.0.0.1:8765 \
  -- uv run --with 'mcp>=1,<3' "$PWD/mcp-server/server.py"
```

| variable | default | |
|---|---|---|
| `QUNXIA_API` | `http://127.0.0.1:8765` | game API base |
| `QUNXIA_MCP_PROFILE` | `standalone` | `benchmark` exposes only `look`, `press`, `press_sequence`, `wait`; actions return metadata and `look` returns the native frame |
| `QUNXIA_BENCH_LANG` | `en` | briefing language, `en` or `zh` |
| `QUNXIA_AGENT` | `mcp` | name in the activity log |
| `QUNXIA_SCALE` | `2` | action-frame scale, 1 to 6; native runner only (the headless runner returns native-resolution frames) |

For a timed benchmark session, create the session first, then point
`QUNXIA_API` at the returned `base_url` plus `/api`. The server reads that
session's `/api/help` at startup. The client must place the MCP `instructions`
in the model's context: benchmark mode has no `guide` tool.

### 3. Built-in Pi harness

`pi-agent/` is a complete harness on [pi](https://pi.dev), pinned to 0.84.4 in
`package-lock.json` (Node 22.19 or newer). Supply an OpenAI-compatible or Gemini
endpoint and a vision model.

```sh
npm ci

export QUNXIA_LLM_BASE_URL=http://localhost:11434/v1
export QUNXIA_LLM_API_KEY=sk-...
export QUNXIA_LLM_MODEL=local-openai/qwen3-vl:32b
./Scripts/play-agent.sh                       # interactive
./Scripts/play-agent.sh -p "play the opening" # non-interactive
```

Without `QUNXIA_API` the launcher starts the native game if needed and waits
for the title screen. Every run gets its own directory under
`.runs/pi/<run-id>/` with its own Pi configuration, sessions, empty workspace
and a manifest recording the model, tools and whether the checkout was dirty.
The API key stays in the environment. Pi's built-in shell and file tools,
user extensions, skills and context files are not exposed.

Tool exposure is declared in `pi-agent/profiles.json`:

| profile | prompt | tools | actions |
|---|---|---|---|
| `strict` (default) | `pi-agent/SYSTEM.md` | eight `game_*` tools including save and load | return the frame |
| `benchmark` | the session's `/api/help` | `game_look`, `game_press`, `game_press_sequence`, `game_wait` | metadata only; call `game_look` |

```sh
# timed benchmark session: BASE_URL is the base_url returned by POST /session
BASE_URL=https://benchmark.example/s/replace-with-the-created-session-id
QUNXIA_PI_PROFILE=benchmark QUNXIA_API="${BASE_URL%/}/api" \
QUNXIA_THINKING=high QUNXIA_LLM_REASONING=1 QUNXIA_LLM_SUPPORTS_REASONING_EFFORT=1 \
QUNXIA_RUN_ID=benchmark-01 ./Scripts/play-agent.sh -p "play until BENCHMARK ENDED"

# continue a run; model, API, profile and tools must match its manifest
QUNXIA_RUN_ID=benchmark-01 QUNXIA_RESUME=1 ./Scripts/play-agent.sh -p "continue"
```

| variable | |
|---|---|
| `QUNXIA_LLM_MODEL` | required, `provider/model` |
| `QUNXIA_LLM_API` | `openai-completions` (default), `openai-responses`, `google-generative-ai` |
| `QUNXIA_THINKING` | required for benchmark runs; must be a level the model supports |
| `QUNXIA_LLM_REASONING`, `QUNXIA_LLM_SUPPORTS_REASONING_EFFORT` | set to `1` for reasoning on Chat endpoints |
| `QUNXIA_LLM_INPUT`, `QUNXIA_LLM_CONTEXT`, `QUNXIA_LLM_MAX_TOKENS` | override model capabilities |
| `QUNXIA_MODEL_CONFIG` | absolute path to a JSON model definition (`id`, `api`, `reasoning`, `input`, `contextWindow`, `maxTokens`, `thinkingLevelMap`) |
| `QUNXIA_BENCH_LANG` | briefing language for benchmark runs, default `zh` |
| `QUNXIA_RUN_ID`, `QUNXIA_RESUME`, `QUNXIA_RUNS_DIR` | run identity and location |

Unsupported thinking levels are rejected before play rather than clamped. The
resolved level and its mapping are recorded in `run.json`. The harness calls
the HTTP API directly through the `qunxia` extension; it does not go through
MCP.

## Leaderboard

<https://hanxiao.io/jy-crpg-bench/> is the public catalogue of recorded runs,
Chinese at `/` and English at `/en/`. It is a static page that reads
`catalog.json` from the benchmark's bucket, so it has no backend of its own.

![The public benchmark board](docs/board.png)

The board: the totals, the brief, and one card per recorded run.

Each card is one run: model name, the MP4 replay with the keys composited in,
how the run ended, and a six-rung progress ladder: acted, screen responded,
picked something up, reached the world map, gained experience, reached level
2. Each rung comes from the request log, the frames or the emulator's memory,
never from a model's own report. The board ranks models on
the screen-changing decision ratio and shows speed, effort and reliability
beside it, with a trade-off view of screen changes against decisions and a
random-key baseline for scale. Runs in progress appear as live cards that
anyone can watch read-only. Every score comes from running the unmodified
game; no model judges another and no run is vendor-reported.

To put a model on the board:

1. Take the brief for the playtime you want: <https://hanxiao.io/jy-crpg-bench/agents.md>
   (Chinese, 20 minutes) or <https://hanxiao.io/jy-crpg-bench/en/agents.md>,
   with `60m/`, `240m/`, `480m/` and `1440m/` variants under each language.
   The brief is the whole instruction set: how to create a session, the rules
   of a run, the controls and the field manual.
2. Give it to the agent as its system prompt. The agent names itself after the
   model and thinking level, creates a session, plays at the returned
   `base_url`, and stops when a call answers 410. A run lasts its playtime
   budget or ends after 10 minutes without an action.
3. Or use the harnesses above in benchmark mode: `QUNXIA_PI_PROFILE=benchmark`
   for Pi, `QUNXIA_MCP_PROFILE=benchmark` for MCP, each pointed at the
   session's `base_url` plus `/api`. Both fetch that session's brief.
4. The card appears while the run is live and gains its video and metrics when
   the session process finishes rendering and publishing.

## Benchmark service

`bench/` is the service behind the leaderboard. One process per session, one
game per model, recorded end to end.

```
POST /session {"agent":"your-model","minutes":20}   ->  base_url, seconds, ends_at
     play at <base_url>/api/...                     (the same API)
     after the run every call answers 410 with
     {"ended": true, "reason", "why", "video_url", "catalog_url"}
```

A run ends at its playtime budget (default 20 minutes) or after 10 minutes
without an action. The session process renders its recording to MP4, uploads
it, appends itself to the catalogue and exits. A scored session has no
emulator snapshots: `/api/save`, `/api/load` and `/api/slots` answer 404, the
served briefing omits them, and an action called with `?image=1` counts as a
screen read.

Everything measured comes from the run's own traffic, so it holds for any
harness: actions and rate, key events and held frames, time to first action,
think-time gaps, distinct keys, screen reads, screen-changing decisions,
oscillation, black-screen transitions, the character record (level, HP,
skills) and shared-inventory growth read from the emulator's memory.
`bench/README.md` covers deployment and the variables.

## Control loop

A key press applies input, waits for the picture to change, then waits for it
to hold still. Waiting only for stillness returns the frame from before the
game reacted, and dialogue draws with a typewriter effect, so the settle
threshold is generous.

```mermaid
sequenceDiagram
    participant A as Agent
    participant S as Control API
    participant E as Emulation thread
    A->>S: POST /api/key {"key":"kp3"}
    S->>E: key down, hold, key up
    E-->>S: frame hashes, 70 fps
    Note over S,E: wait for the picture to change,<br/>then to hold still
    S-->>A: {"changed": true, "image": "..."} when requested
```

Key down, release and inter-tap phases are fenced by the core frame clock, so
host scheduling cannot collapse repeated taps. Short taps default to 10
emulated frames, long enough for a slow DOS redraw and short of the game's
held-key repeat delay.

## Architecture

```mermaid
flowchart LR
    subgraph native["Native macOS"]
        direction TB
        MA[AppKit window] --> MM[MetalView]
        MM -->|texture.replace| MC
        MAPI[ControlAPI<br/>Network.framework] --> MEMU[Emulator thread<br/>+ action queue]
        MEMU --> MC[CoreHost.c<br/>libretro host]
        MC --> MAU[AudioOut<br/>CoreAudio]
        MC --> DP1[dosbox_pure.dylib]
    end
```

```mermaid
flowchart LR
    subgraph web["Headless"]
        direction TB
        BR[Browser canvas] <-->|WebSocket| WS[aiohttp server]
        WS --> TD[tiles.c<br/>16x10 tile differ]
        WS --> WE[emulation thread<br/>ctypes]
        WE --> WC[CoreHost.c<br/>libretro host]
        TD --> WC
        WC --> DP2[dosbox_pure.so]
    end
```

The browser receives no video stream. `tiles.c` compares each frame with the
last one sent and emits only the changed 16x10 tiles, deflated, over the socket
that also carries input. A dialogue update is about 60 tiles and 5 KB; an idle
screen sends nothing.

Every session is recorded as those tile deltas plus the keys that caused them,
appended to a JSONL journal on disk. The activity panel replays at 4x and
exports an MP4 in the browser; the benchmark renders the same journal with
ffmpeg.

## Emulated CPU speed

The x86 code is JIT compiled by the DOSBox Pure recompiler. CPU cost is the
cycle budget. Measured on an M3 Ultra, 10 seconds at the title screen:

| `dosbox_pure_cycles` | CPU (one core = 100%) | emulated fps | boot to title |
|---|---:|---:|---:|
| `max` | 99.5% | 70.22 | 15.8s |
| `auto` | 81.3% | 70.19 | 19.5s |
| fixed 77000 | 31.3% | 70.17 | 15.9s |
| fixed 26800 | 15.6% | 70.04 | |

The macOS runner defaults to 77000 and the server to 26800 (`QUNXIA_CYCLES`),
which holds 70 fps on a shared-core VM. Override with
`QUNXIA_SET="dosbox_pure_cycles=max"` or `--set dosbox_pure_cycles=200000`.

## Tests

```sh
./server/build.sh
python -m unittest discover -s server -p 'test_*.py'      # needs aiohttp, pillow
python -m unittest discover -s mcp-server -p 'test_*.py'  # run with mcp<2 and mcp>=2
python -m unittest discover -s bench -p 'test_*.py'       # needs numpy
python -m unittest discover -s site -p 'test_*.py'        # needs zhconv
python -m unittest Scripts/test_agent_launchers.py
node --test Scripts/test-pi-run.mjs Scripts/test-pi-launch.mjs   # after npm ci
swift build
```

`site/build.py` and `site/agents_build.py` regenerate the leaderboard pages
and the published briefs; the committed output must not drift.

## Layout

```
Sources/CoreHost/    libretro host: dlopen, env callbacks, video, audio, input
Sources/QunXia/      macOS app: Emulator, MetalView, AudioOut, ControlAPI, HistoryView
server/              headless runner: tile differ, aiohttp server, browser client,
                     recording journal, watchdog, benchmark warden
bench/               benchmark broker, MP4 renderer, Dockerfile
site/                leaderboard and published briefs
skills/              play.*.md and speedrun.*.md, served at /api/help
pi-agent/            built-in harness: prompts, profiles, game_* extension
mcp-server/          MCP server
Scripts/             run.sh, play-agent.sh, play.py, setup-codex.sh, packaging
paper/               paper source and reference audit
Cores/               dosbox_pure_libretro.dylib
saves/               emulator snapshots, untracked
```

## Licensing

Code written here (`Sources/`, `server/`, `bench/`, `site/`, `mcp-server/`,
`pi-agent/`, `Scripts/`, `skills/`) is MIT, in `LICENSE`.

DOSBox Pure (`Cores/dosbox_pure_libretro.dylib`) is GPLv2, built from
`schellingb/dosbox-pure` at `7f6e8fb`, loaded at runtime through the libretro
C API and redistributed unmodified.

The game data is the 1996 commercial release, copyright 智冠科技 and
河洛工作室. It is not redistributable and is not tracked here; supply your own
copy.
