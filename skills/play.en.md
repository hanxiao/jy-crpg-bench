# Skill: play 金庸群俠傳 (The Legend of Jin Yong Heroes)

The original 1996 DOS game by 河洛工作室, running under emulation at {BASE}.
You send keys, you get back a picture of the screen. It is an open-world RPG:
how you play it is up to you.

## The loop

Acting and looking are separate calls. A key press applies your input and waits
for the screen to settle, but returns no picture; `GET /api/screen` returns one.
Act, then look when you need to see. Sending a few keys and looking once is fine.

The game is entirely in Traditional Chinese, and the text is where everything
happens: objectives, choices, and prompts that expect a specific key.

## API

    GET  {BASE}/api/screen                        look, pressing nothing
    POST {BASE}/api/key   {{"key":"kp3"}}           one key; +"times", +"hold"
    POST {BASE}/api/keys  {{"keys":["kp9","enter"]}} several, in order
    POST {BASE}/api/wait  {{"ms":1000}}             let the game run
    GET  {BASE}/api/help                          this skill

Only `/api/screen` returns a picture: JSON with `image`, a base64 PNG data URI
(`?format=png` or `?format=webp` for raw bytes). Action calls return `changed`
and `frame` only.

    curl -s -X POST {BASE}/api/key -H 'content-type: application/json' \
         -d '{{"key":"enter"}}'

Keys: kp1 kp3 kp7 kp9, up down left right, enter space esc y n, a-z, 0-9,
f1-f12, tab, backspace.

**Name yourself.** Others may be playing the same session. Send a name you
choose in an `X-Agent` header on every call, so the activity panel and the
history show who did what.

    curl -s -X POST {BASE}/api/key -H 'X-Agent: your-name' \
         -H 'content-type: application/json' -d '{{"key":"kp3"}}'

The game is shared. If the screen changes without you acting, that is someone
else, not a fault.

## Movement: use the numpad names

The world is isometric, so the four movement axes are **diagonals on screen**.
The numpad names match what you actually see, and are identical to the arrows:

    kp7  ↖ up-left      kp9  ↗ up-right        (kp7 == left, kp9 == up)
    kp1  ↙ down-left    kp3  ↘ down-right      (kp1 == down, kp3 == right)

Prefer `kp7/kp9/kp1/kp3`. Thinking in arrows is the main reason agents get lost
here. The aliases `upleft`, `upright`, `downleft`, `downright` also work.

No single key moves straight across the screen. To do that, alternate two:

    screen-right : kp3, kp9, kp3, kp9, ...      screen-left : kp7, kp1, ...
    screen-down  : kp3, kp1, kp3, kp1, ...      screen-up   : kp7, kp9, ...

**Hold to walk.** A held key walks continuously until it is released or you hit
something, so one call with `"hold": 120` covers far more ground than eight
separate presses, and costs one settle instead of eight. Use `hold` for travel
and short taps for precise positioning.

## Interacting

- enter and space are identical: confirm, advance dialogue, and interact.
  There is no separate interact key on the map, you walk into a person or object.
- **Any key advances dialogue**, not just enter.
- esc opens the menu. In a building: 醫療 / 解毒 / 物品 / 狀態. On the world map
  you also get 隊 (party) and 系統 (save, load, quit). Saving is only possible
  on the world map.
- y and n answer prompts written （Ｙ／Ｎ）.

## First priority: get the compass

Most buildings cannot be entered at the start. That is deliberate, not a
controls problem, and a locked entrance looks exactly like an open one. Head
south from the opening area to 南賢居 and talk to 南賢 to get the 羅盤 (compass).

With the compass, `esc → 物品 → 羅盤` shows **your current coordinates as
numbers**. That is the game's own ground truth for position, far better than
comparing screenshots of trees. Get it early and check coordinates every few
steps; it is the single best cure for going in circles.

Community coordinates for reference (from the original game, this build may
differ, trust your own compass): 主角居 (357,235), 河洛客棧 (359,229),
南賢居 (388,325), 天寧寺 (330,237), 鐵掌山 (302,343), 五毒教 (247,424).

## Reading a 320x200 screen

- **The camera is locked to you.** Your sprite barely moves; the scenery moves.
  Judge whether you actually moved by watching the background shift, never by
  looking at where your character appears.
- One step shifts the background by roughly an eighth of the screen. If a batch
  of 4-6 presses leaves the composition mostly unchanged, you were blocked.
- Your character sometimes vanishes behind a tree or building drawn on top of
  it. That is layering, not teleporting.
- Tell the boxes apart: a **menu** is narrow with stacked two-character words; a
  **dialogue box** is wide with full sentences; the **item screen** is a row of
  icon cells; a **status card** has a portrait and numbers.
- Do not compute pixel coordinates. Describe positions relatively.
- Animals, mist and distant colour specks are scenery. Spend your actions on
  human figures, doors, signs and chests.

## Traps that will cost you the most time

- **`changed: true` does not mean you moved.** Being blocked still plays a turn
  or idle animation, which reports `changed: true`. Trust `changed: false` as
  "blocked", but verify any `changed: true` against the background.
- **You will go in circles.** Nothing on screen says where you are. Keep your
  own record of places you have seen and compare against the last several, not
  just the last one; loops often run through a few screens before repeating.
  How you do that is up to you, but decide early, before you are lost.
- **If alternating two keys stalls**, you are bouncing between two tiles because
  the second key is blocked. Do not retry the same pair, push a single direction
  repeatedly instead.
- **A fully black screen is a scene transition**, not a crash. Call `/api/wait`
  about 1500ms and look again rather than pressing keys into the fade.
- **The menu sometimes opens by itself** when every direction is blocked. Press
  esc, wait, look, repeat until it closes, then go the opposite way, because the
  direction that triggered it is a wall.
- **A building's entrance is one specific tile**, not the whole wall. Walk the
  full perimeter and test each gap inward before concluding you cannot get in.
- **Looping ambient chatter is not a quest.** If the same opening line comes
  round a second time, it is scenery dialogue. Stop and walk away.

## The world

You are 小蝦米, a modern student who buys a VR copy of this very game and wakes
inside the world of Jin Yong's wuxia novels. Getting home means finding the
fourteen Jin Yong novels scattered across the land. Characters from those novels
can be recruited, their martial arts learned, and fights are turn-based between
teams, with turn order set by 輕功 (agility).

Only the protagonist dying ends the game; defeated companions are merely badly
hurt and return. Poke at anything that looks placed rather than decorative.
Everything past that is yours to discover.
