# Skill: play 金庸群俠傳 (Heroes of Jin Yong)

The original 1996 DOS game by 河洛工作室, running under emulation at {BASE}.
You send keys and fetch the screen.

## API

    GET  {BASE}/api/screen                        look, pressing nothing
    POST {BASE}/api/key   {{"key":"kp3"}}           press one key; +"hold" frames
    POST {BASE}/api/key   {{"key":["kp9","enter"]}} press several, in order
    GET  {BASE}/api/slots                         list emulator snapshots
    POST {BASE}/api/save  {{"name":"checkpoint"}}   save a snapshot
    POST {BASE}/api/load  {{"name":"checkpoint"}}   restore a snapshot
    GET  {BASE}/api/help                          this skill

`/api/screen` returns JSON with `image`, a base64 PNG data URI; `?format=png`
returns the raw bytes. `/api/key` is the only action: `key` is one key name or
a list pressed in order, so a repeat is a list of the same key and a menu path
is a list. It returns once the screen has settled, a change of location included,
with `ok`, `action` and `frame`, the number of the picture that followed. It
says nothing about what the screen did: judge every effect from the picture.
There is no wait call: the game moves only on a key, and an action waits for
the result.

Each call reads only the fields shown. Any other field is refused with a 400
naming it.

    curl -s -X POST {BASE}/api/key -H 'content-type: application/json' \
         -d '{{"key":"enter"}}'

Keys: kp1 kp3 kp7 kp9, up down left right, enter space esc y n, a-z, 0-9,
f1-f12, tab, backspace.

Acting and looking are separate calls. A key press waits for the screen to
settle and returns metadata; `GET /api/screen` returns the picture. Add
`?image=1` to an action to get the picture in the same reply.

The game is entirely in Traditional Chinese. Objectives, choices and prompts
that expect a specific key are all in its text.

## Movement

The world is isometric: the four movement axes are diagonals on screen. The
numpad names match the visible direction and are identical to the arrows:

    kp7  ↖ up-left      kp9  ↗ up-right        (kp7 == left, kp9 == up)
    kp1  ↙ down-left    kp3  ↘ down-right      (kp1 == down, kp3 == right)

## Interacting

- enter and space confirm, advance dialogue and investigate. For a person or
  container, stand on an adjacent tile facing the target, then press enter or
  space. Story events triggered by stepping on a tile are separate.
- Any key advances ordinary dialogue. Answer choices and （Ｙ／Ｎ） prompts
  with y and n.
- esc opens the menu. In a building: 醫療 / 解毒 / 物品 / 狀態. On the world
  map also 離隊 (dismiss a party member) and 系統 (save, load, quit). The game
  saves only from the world map.

Characters from the novels can be recruited and their martial arts learned.
Battles are turn-based between teams, in an order set by 輕功. A fallen
character, a lost battle and the end of the game are different events; whether
play continues after a defeat depends on the encounter.
