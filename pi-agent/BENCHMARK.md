You are running the repository's timed benchmark through the isolated Pi
harness. The session-specific benchmark brief below is authoritative.

The brief describes raw HTTP endpoints. Use their Pi equivalents instead:

- `GET /api/screen` -> `game_look`
- `POST /api/key` -> `game_press`
- `POST /api/keys` -> `game_press_sequence`
- `POST /api/wait` -> `game_wait`

Actions return metadata only. Call `game_look` when you need the next visible
frame. The benchmark session has already been created; keep playing until a
game tool explicitly reports `BENCHMARK ENDED`.

This session is isolated and the character is already named in the opening
room. Generic wording in the brief about sharing a game, choosing an `X-Agent`
name, or another player changing the screen does not apply here.

--- BEGIN SESSION-SPECIFIC BENCHMARK BRIEF ---
