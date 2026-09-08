# Skill: play 金庸群俠傳 (The Legend of Jin Yong Heroes)

The original 1996 DOS game by 河洛工作室, running under emulation at {BASE}.
You send keys and request pictures of the screen when you need them. It is an
open-world RPG: how you play it is up to you.

## The session address

Every call in this skill is relative to a session address. A benchmark
session has two of them:

- **public** — watch-only. Reads (`GET`) work; writes (`POST`) answer 403.
- **play** — the public address with the session's token in its path. The
  only address that accepts play requests. It is the `base_url` that
  `POST /session` returns, and the address your harness runs you on.

If a call answers 403, "this address watches; it does not play", you are
on the public address: use the play address instead. In a standalone game
there is one address, and it is the play address.

## The loop

By default, acting and looking are separate calls. A key press waits for the
screen to settle and returns metadata; `GET /api/screen` returns the picture.
Add `?image=1` to an action URL when you need the resulting picture atomically,
before another player can act. Sending a few keys and looking once is also fine.

The game is entirely in Traditional Chinese, and the text is where everything
happens: objectives, choices, and prompts that expect a specific key.

## API

    GET  {BASE}/api/screen                        look, pressing nothing
    POST {BASE}/api/key   {{"key":"kp3"}}           one key; +"times", +"hold"
    POST {BASE}/api/keys  {{"keys":["kp9","enter"]}} several, in order
    POST {BASE}/api/wait  {{"ms":1000}}             let the game run
    GET  {BASE}/api/slots                         list emulator snapshots
    POST {BASE}/api/save  {{"name":"checkpoint"}}   save a snapshot
    POST {BASE}/api/load  {{"name":"checkpoint"}}   restore a snapshot
    GET  {BASE}/api/help                          this skill

`/api/screen` returns JSON with `image`, a base64 PNG data URI (`?format=png` or
`?format=webp` for raw bytes). Action calls return `changed` and `frame`, and
also return the same `image` when called with `?image=1`.

    curl -s -X POST {BASE}/api/key -H 'content-type: application/json' \
         -d '{{"key":"enter"}}'

Keys: kp1 kp3 kp7 kp9, up down left right, enter space esc y n, a-z, 0-9,
f1-f12, tab, backspace.

**Name yourself.** Others may be playing the same session. Send a name you
choose in an `X-Agent` header on every call, so the activity panel and the
history show who did what.

    curl -s -X POST {BASE}/api/key -H 'X-Agent: your-name' \
         -H 'content-type: application/json' -d '{{"key":"kp3"}}'

Others may operate the same session. Animation or story events can also change
the screen without your input; a change alone does not identify another player
or a fault.

## Movement: use the numpad names

The world is isometric, so the four movement axes are **diagonals on screen**.
The numpad names match what you actually see, and are identical to the arrows:

    kp7  ↖ up-left      kp9  ↗ up-right        (kp7 == left, kp9 == up)
    kp1  ↙ down-left    kp3  ↘ down-right      (kp1 == down, kp3 == right)

Prefer `kp7/kp9/kp1/kp3` to match the visible diagonal movement.
The aliases `upleft`, `upright`, `downleft`, `downright` also work.

On a clear path, alternating two directions can move horizontally or vertically
across the screen:

    screen-right : kp3, kp9, kp3, kp9, ...      screen-left : kp7, kp1, ...
    screen-down  : kp3, kp1, kp3, kp1, ...      screen-up   : kp7, kp9, ...

**Holding a key keeps sending the same direction.** `hold` counts held frames,
not tiles travelled. It does not follow paths, turn, or avoid obstacles for you.
Landmarks may leave the current view as you move. Use short taps and look again
when the route or a junction is unclear; use longer holds on a confirmed clear
stretch, checking the actual distance from the screen or compass.

## Interacting

- enter and space confirm, advance ordinary dialogue, and investigate. For an
  ordinary person or container, stand in an adjacent tile, face the target,
  then press enter or space. Story events triggered by stepping on a tile are
  a separate mechanism.
- Any key can advance ordinary dialogue; answer choices and （Ｙ／Ｎ） prompts
  with the appropriate keys.
- esc opens the menu. In a building: 醫療 / 解毒 / 物品 / 狀態. On the world map
  you also get 離隊 (dismiss a companion) and 系統 (save, load, quit). The
  in-game save menu is available on the world map.
- y and n answer prompts written （Ｙ／Ｎ）.

## First priority: get the compass

Many locations remain unavailable until you complete the opening encounter at
南賢居. On the world map, **follow the small path south to 南賢居**. Once there,
talk to 南賢, then investigate the cabinet beside him to get the 羅盤 (compass).

After obtaining the compass, highlight it in `esc → 物品` to read **your current
coordinates**. Check actual readings together with visible landmarks, especially
when the route is unclear or you suspect a loop.

Community coordinates for reference (from the original game, this build may
differ, trust your own compass): 主角居 (357,235), 河洛客棧 (359,229),
南賢居 (388,325), 天寧寺 (330,237), 鐵掌山 (302,343), 五毒教 (247,424).

## Reading a 320x200 screen

- **During ordinary walking, the camera follows the character.** Compare the
  background or compass coordinates, not just the sprite position. Story
  sequences can also change the view.
- A short tap may cause only a small shift. Do not assume a fixed fraction of
  the screen per step. If progress is unclear, shorten the input and check the
  current screen, facing direction, and possible paths.
- Your character sometimes vanishes behind a tree or building drawn on top of
  it. That is layering, not teleporting.
- Tell the boxes apart: a **menu** is narrow with stacked two-character words; a
  **dialogue box** is wide with full sentences; the **item screen** is a row of
  icon cells; a **status card** has a portrait and numbers.
- Relative descriptions can help track landmarks. If comparing pixel shifts,
  distinguish screen positions from game map coordinates.
- Some scenery is decorative, but appearance alone does not establish whether
  animals, mist, or distant specks are interactive. Use game text and actual
  interaction results.

## Traps that will cost you the most time

- **`changed` does not say whether you moved.** It only reports whether a visible
  screen change was observed. Judge movement from the background and do not infer
  the cause of `changed: false`.
- **Similar terrain can lead you back to a place you have visited.** Record
  landmarks and compare new observations with several recent ones. Once you
  have the compass, use coordinates as well. The recording method is up to you.
- **No progress while alternating keys does not establish its cause.** Check
  whether you are on the map, in a menu, or in dialogue, then use short taps and
  observations to find a passable direction. Do not blindly increase hold time.
- **A fully black screen does not reveal its cause.** Call `/api/wait` for about
  1500ms and look again rather than pressing keys into it.
- **Entrances are at specific locations; the entire wall is not passable.**
  Use paths, doorways, and story clues. One failed attempt does not establish
  whether the entrance is wrong or a prerequisite is missing.
- **Repeated dialogue does not establish that an NPC has no function.** Item
  interactions or later story conditions may still apply. Distinguish no new
  information this time from no quest or function at all.

## The world

You are 小蝦米, a modern student who buys a VR copy of this very game and wakes
inside the world of Jin Yong's wuxia novels. Getting home means finding the
fourteen Jin Yong novels scattered across the land. Characters from those novels
can be recruited, their martial arts learned, and fights are turn-based between
teams. Turn order usually follows 輕功 (agility); commands such as waiting can
change the order within a round.

A character falling, losing a battle, and ending the game are different events.
Whether play continues after defeat depends on that encounter. Watch the whole
party and read the actual battle result. Investigate plausible people and
objects, and use the game's clues to decide what to explore.
