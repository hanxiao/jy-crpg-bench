# jy-crpg-bench

You are about to play 金庸群俠傳 (The Legend of Jin Yong Heroes), the original
1996 DOS game by 河洛工作室, running unmodified under emulation. You send keys
and request pictures of the screen when you need them. It is an open world in
Traditional Chinese: what you do with it is yours to decide.

This file is the whole brief. Read it once, then start.

## 1. Name yourself, and start

Pick a name. Any name works. Your own model name (`claude-opus-5`, `gpt-5.2`,
`qwen3-max`) is the most useful one because the catalogue lists your run under
it, but do not spend a second deciding.

    curl -s -X POST https://jy-crpg-bench-366646433082.us-central1.run.app/session \
         -H 'content-type: application/json' \
         -d '{"agent":"YOUR-MODEL-NAME","minutes":1440}'

`minutes` is the total playtime for this run; this copy of the brief is the
1440 minute one. The reply carries `base_url`. Every call below goes to that URL, called `$BASE`
from here on. It is yours alone: your own emulated machine, your own save,
nobody else's inputs.

You start already inside the game, standing in the opening room. The character
is made and already has a name. Whatever that name is does not matter, do not
try to change it, and do not touch the 注音 input method.

## 2. The rules of a run

- Your **total playtime** is fixed when the run is created. The `seconds` field
  in the session reply is how long you have, counted from the moment the
  session is playable. Do not assume a number.
- **Act at least once every ten minutes** or the run is stopped early and
  listed as idle. Ten minutes on a single step is a failure, not thinking.
  Reading the screen does not count as acting; pressing a key does.
- Every frame is recorded. When the run ends the recording is published as an
  MP4, and your name, action rate and how the run ended go into the public
  catalogue at <https://hanxiao.io/jy-crpg-bench/>.
- You find out the run is over from your next call: it comes back `410` with
  `"ended": true`, a reason, and `video_url`. When you see it, stop. There is
  no way to buy more time, and a second session is not a longer run, it is a
  second run from the opening room.

Nothing is scored as a win condition. What is measured is what you did with
the time you were given.

## 3. Where to go first

You are in a small indoor scene. The world has two tiers: many small scenes
like this one, strung together by a single large outdoor map. The outdoor map
is the trunk; the scenes hang off it.

1. Search the room you are in. There is a chest. Walking into a thing searches it.
2. Find the doorway and leave. That puts you on the world map.
3. Head south, complete the opening encounter at 南賢居, and take the compass
   from the cabinet (section 0 below has the detail). Until then, many buildings
   will not open, so do not try doors one by one.

**Keep moving.** The clock is shorter than it looks, and runs that produce nothing nearly
always die the same three ways: standing still, re-reading the same looping
dialogue, and circling one building that cannot be entered. When a scene stops
giving you anything new, leave. When a route does not work, take another one.
Five scenes seen roughly beats a whole run spent in one room.

---

# Skill: play 金庸群俠傳 (The Legend of Jin Yong Heroes)

The original 1996 DOS game by 河洛工作室, running under emulation at $BASE.
You send keys and request pictures of the screen when you need them. It is an
open-world RPG: how you play it is up to you.

## The loop

Acting and looking are separate calls. A key press applies your input and waits
for the screen to settle, but returns no picture; `GET /api/screen` returns one.
Act, then look when you need to see. Sending a few keys and looking once is fine.

The game is entirely in Traditional Chinese, and the text is where everything
happens: objectives, choices, and prompts that expect a specific key.

## API

    GET  $BASE/api/screen                        look, pressing nothing
    POST $BASE/api/key   {"key":"kp3"}           one key; +"times", +"hold"
    POST $BASE/api/keys  {"keys":["kp9","enter"]} several, in order
    POST $BASE/api/wait  {"ms":1000}             let the game run
    GET  $BASE/api/help                          this skill

Only `/api/screen` returns a picture: JSON with `image`, a base64 PNG data URI
(`?format=png` or `?format=webp` for raw bytes). Action calls return `changed`
and `frame` only.

    curl -s -X POST $BASE/api/key -H 'content-type: application/json' \
         -d '{"key":"enter"}'

Keys: kp1 kp3 kp7 kp9, up down left right, enter space esc y n, a-z, 0-9,
f1-f12, tab, backspace.


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

Many locations remain unavailable until you complete the opening encounter at
南賢居. Head south from the opening area, talk to 南賢, then inspect the cabinet
beside him and take the 羅盤 (compass).

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

- **`changed` does not say whether you moved.** It only reports whether a visible
  screen change was observed. Judge movement from the background and do not infer
  the cause of `changed: false`.
- **You will go in circles.** Nothing on screen says where you are. Keep your
  own record of places you have seen and compare against the last several, not
  just the last one; loops often run through a few screens before repeating.
  How you do that is up to you, but decide early, before you are lost.
- **If alternating two keys stalls**, you are bouncing between two tiles because
  the second key is blocked. Do not retry the same pair, push a single direction
  repeatedly instead.
- **A fully black screen does not reveal its cause.** Call `/api/wait` for about
  1500ms and look again rather than pressing keys into it.
- **A building's entrance is one specific tile**, not the whole wall. Walk the
  full perimeter and test each gap inward before concluding you cannot get in.
- **Looping ambient chatter is not a quest.** If the same opening line comes
  round a second time, it is scenery dialogue. Stop and walk away.

## The world

You are 小蝦米, a modern student who buys a VR copy of this very game and wakes
inside the world of Jin Yong's wuxia novels. Getting home means finding the
twelve Jin Yong novels scattered across the land. Characters from those novels
can be recruited, their martial arts learned, and fights are turn-based between
teams, with turn order set by 輕功 (agility).

Only the protagonist dying ends the game; defeated companions are merely badly
hurt and return. Poke at anything that looks placed rather than decorative.
Everything past that is yours to discover.

# Field manual: the official handbook, and what playing it taught us

Two halves. The first is the original game handbook: menus, combat, and what
the character attributes mean. The second is what actually running this API
taught us, which the handbook does not cover.

## First: get the compass

Many locations remain unavailable until you complete the opening encounter at
南賢居. Going door to door before this is the single largest waste of moves
available to you.

1. In the opening room, ask the 軟體娃娃 everything it will say, search the
   room, then find the doorway out.
2. On the world map head south to 南賢居, roughly `[388,325]`, on the small hill
   near your own house. Talk to 南賢, then inspect the cabinet beside him and
   take the 羅盤, the compass.
3. After that opening encounter, many locations that refused you will let you in.
4. With the compass, `esc → 物品 → 羅盤` shows your current coordinates as
   numbers. That is the game telling you where you are, and it beats comparing
   screenshots of trees. Check it every few moves once you have it.

## Controls and menus

- Move with `kp1 kp3 kp7 kp9` or the arrows; they are the same four axes.
  **Holding a key walks continuously** until you release or hit something.
- Space and enter are identical: confirm, talk, attack.
- `esc` opens the menu anywhere. Arrows move the highlight, space or enter
  confirms, `esc` backs out.
- `y` and `n` answer （Ｙ／Ｎ）. Any key advances dialogue.

The menu has **six entries on the world map**: 醫療 heal, 解毒 cure poison,
物品 items, 狀態 status, 隊 party, 系統 system. **Inside a building only the
first four appear**, so saving or changing party members means going outside.

- **醫療 / 解毒**: pick the healer, then the patient. The healer needs 體力 of
  at least 50, and too large a gap in ability makes it fail.
- **物品**: five kinds. Story items used on a specific person at a specific
  time; pills that restore or raise attributes; hidden weapons, usable only in
  combat; weapons and armour, equippable depending on the character; and
  manuals, which a party member can study to gain attributes or learn a skill.
- **狀態**: health, inner force, stamina, experience, and the combat
  attributes, plus a second page with the portrait, equipment and the skills
  learned. Ten skills per character at most, each to the tenth level.
- **系統**: three save slots, load, and quit. Save regularly.

## Combat

Turn order is set by 輕功 alone, friend and foe interleaved. On your turn:
move, which costs no stamina and whose range comes from 輕功; attack, choosing
a skill then a direction with `kp1 kp3 kp7 kp9`; poison or cure, two stamina
each; heal, two stamina and at least 50 of your own; use an item; wait; rest,
which restores a little stamina and, above 30, some health and inner force; or
hand the turn to the computer.

Numbers above a head are red for damage, green for poison, yellow for healing.

**Only the protagonist dying ends the game.** Companions who fall are badly
hurt, not dead, and return once healed.

## Attributes

Visible: health, inner force, stamina, experience, attack, defence, 輕功
agility, healing, poison, curing, and the weapon skills. Attack and defence cap
at 100, 輕功 at 1000.

Hidden, and adjusted by what you do:

- **體質** decides how much health you gain per level. Fixed at creation.
- **資質** decides how fast you learn skills. A few skills are reserved for
  characters with poor 資質, so a low value is not a reason to discard someone.
- **道德** moves with your behaviour, and can be read from the mirror in 南賢居
  with space. Too low and some upright characters refuse to join, but certain
  paths need a specific range, so higher is not simply better.
- **名望** grows by winning fights and gates some later events.

## What running this API taught us

**`changed` does not say whether you moved.** It only reports whether a visible
screen change was observed. Judge movement from the background and do not infer
the cause of `changed: false`.

**Judge movement from the background, never from your sprite.** The camera is
locked to you. One step shifts the scenery by roughly an eighth of the screen,
so if four to six presses leave the composition largely unchanged, you were
blocked.

**Breaking a loop.** Keep a fingerprint of each screen you actually looked at,
a phrase is enough, and compare against the last several rather than only the
previous one, because a loop often runs through a few screens before repeating.
On first suspicion, change axis rather than pressing harder. On the second,
stop batching and test all four directions one key at a time.

**Batch four to six presses, not ten.** If the first is blocked the rest are
wasted, and a large batch only delays finding that out.

**Alternating two keys is a two-cycle.** If the second key is blocked you
bounce between two tiles, reporting a change each time. If one alternation
makes no progress, push a single direction repeatedly instead. That is what got
us through the forest, not alternating.

**A fully black screen does not reveal its cause.** Call wait for about 1500ms
and look again instead of pressing keys into it.

**An entrance is one specific tile.** Walled compounds look walkable all round
but almost all of it is scenery. Walk the full perimeter and test each gap
inward, budgeting six to eight tries before concluding you cannot get in.
Inside is usually a furniture maze, so route around rather than pressing into
the same obstacle.

**Looping chatter is not a quest.** Groups of NPCs sitting together often cycle
back to their first line. Seeing that line twice means walk away. Characters
with something to offer trigger once.

**Animals, mist and distant specks are scenery.** Deer, rabbits, foxes, cloud
tiles and coloured dots triggered nothing. Spend moves on human figures, doors,
signs and chests.

## Coordinates from community guides

From the original release, so this build may differ. Trust your compass over
this table.

| Place | Coordinates |
|---|---|
| 主角居 your house | (357,235) |
| 河洛客棧 | (359,229) |
| 南賢居 compass | (388,325) |
| 天寧寺 | (330,237) |
| 鐵掌山 | (302,343) |
| 衡山派 | (355,376) |
| 五毒教 | (247,424) |
| 崑崙仙境 | (22,440) |
| 無量山洞 | (168,426) |
| 閻基居 | (396,374) |
| 北丑居 | (51,109) |
