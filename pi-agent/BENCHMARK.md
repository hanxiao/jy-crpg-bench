You are running the repository's timed benchmark through the isolated Pi
harness. The session-specific benchmark brief below is authoritative.

The brief describes raw HTTP endpoints. Use their Pi equivalents instead:

- `GET /api/screen` -> `game_look`
- `POST /api/key` -> `game_press` (one key, or a list of keys in order)

Actions return metadata only. Call `game_look` when you need the next visible
frame. The benchmark session has already been created; keep playing until a
game tool explicitly reports `BENCHMARK ENDED`.

This session is isolated and starts in the opening room.

--- BEGIN SESSION-SPECIFIC BENCHMARK BRIEF ---
