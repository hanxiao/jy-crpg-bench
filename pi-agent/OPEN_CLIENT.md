You are playing a timed benchmark in a private client container. The
session-specific brief below is the game manual and objective.

You may use read, write, edit and bash to keep notes, write programs, crop
frames, run OCR or build a computer-vision pipeline. Python 3, NumPy, Pillow
and OpenCV are installed. All of this work counts against the same running
wall-clock budget as playing the game.

Only your own visible game frames and brief are game-state evidence. There
is no game source, ROM, save reader, other player's files or shared host /tmp
in this container. External network access is disabled. Do not try to read
another session, a replay, a catalogue, hidden state or server files.

Use game_look to see a frame and game_press to press one key or a list of
keys. Actions return metadata only; look again to check what happened.
Frames returned by game_look are also saved under $QUNXIA_SCREEN_DIR so your
programs can inspect them. Your persistent scratch directory is /client/workspace.

Shell programs can call $QUNXIA_API/screen, /help, /keys (GET), and /key
(POST). This local gateway is bound to your session, accepts no other game
routes and cannot connect to other services. In-game saves through the
keyboard are allowed; emulator save/load/reset tools are not available.

The game has already started in the opening room.
You do not create a session. Stop when a tool reports BENCHMARK ENDED.

--- BEGIN SESSION-SPECIFIC BENCHMARK BRIEF ---
