# jy-crpg-bench

You are about to play 金庸群俠傳 (The Legend of Jin Yong Heroes), the original
1996 DOS game by 河洛工作室, running unmodified under emulation. You send keys
and request pictures of the screen when you need them. It is an open world in
Traditional Chinese: what you do with it is yours to decide.

This file is the whole brief. Read it once, then start.

## 1. Name yourself, and start

Use a name identifying the model and thinking level for this run; the catalogue
uses that name to identify the result.

    curl -s -X POST https://jy-crpg-bench-366646433082.us-central1.run.app/session \
         -H 'content-type: application/json' \
         -d '{"agent":"YOUR-MODEL-NAME","minutes":20}'

`minutes` is the total playtime for this run; this copy of the brief is the
20 minute one. The reply carries `base_url`. Every call below goes to that URL, called `$BASE`
from here on. It is yours alone: the URL carries this run's token, and only
its bearer can send input to your emulated machine; an address without it
only watches. Your own machine, your own save, nobody else's inputs.

You start already inside the game, standing in the opening room. The character
is made and already has a name. Whatever that name is does not matter, do not
try to change it, and do not touch the 注音 input method.

## 2. The rules of a run

- Your **total playtime** is fixed when the run is created. The `seconds` field
  in the session reply is how long you have, counted from the moment the
  session is playable. Do not assume a number.
- **The default idle limit is ten minutes.** A long gap without a game action
  can end the run early. Looking at the screen alone does not count as a game action.
- Frames and actions used for replay are recorded, and a video is generated
  after the run. The public service lists results at
  <https://hanxiao.io/jy-crpg-bench/> by default; publication depends on the
  session's publishing settings.
- You find out the run is over from your next call: it comes back `410` with
  `"ended": true`, a reason, and `video_url`. When you see it, stop. There is
  no way to buy more time, and a second session is not a longer run, it is a
  second run from the opening room.

The game goal remains to collect fourteen books and return to the present.
This session records progress within a fixed budget and ends when that budget
expires even if the game is unfinished. Idleness and other conditions can end it earlier.

## 3. Where to go first

You are in a small indoor scene. The world has two tiers: many small scenes
like this one, strung together by a single large outdoor map. The outdoor map
is the trunk; the scenes hang off it.

1. Search the room. To investigate an ordinary person or container, stand
   adjacent, face the target, and press confirm.
2. Find the doorway and leave. That puts you on the world map.
3. Follow the small path south to 南賢居, talk to 南賢, then investigate the
   cabinet to obtain the compass. Many locations open after this encounter;
   if an entrance still resists you, check its position and the game text.

Use the screen and dialogue to advance your current objective. Adjust the plan
when there is no new information, but do not skip discovered clues merely to
visit more scenes, or repeat the same action without new evidence.

---

# Skill: play 金庸群俠傳 (The Legend of Jin Yong Heroes)

The original 1996 DOS game by 河洛工作室, running under emulation at $BASE.
You send keys and request pictures of the screen when you need them. It is an
open-world RPG: how you play it is up to you.

## The loop

By default, acting and looking are separate calls. A key press waits for the
screen to settle and returns metadata; `GET /api/screen` returns the picture.
Add `?image=1` to an action URL when you need the resulting picture atomically,
before another player can act. Sending a few keys and looking once is also fine.

The game is entirely in Traditional Chinese, and the text is where everything
happens: objectives, choices, and prompts that expect a specific key.

## API

    GET  $BASE/api/screen                        look, pressing nothing
    POST $BASE/api/key   {"key":"kp3"}           one key; +"times", +"hold"
    POST $BASE/api/keys  {"keys":["kp9","enter"]} several, in order
    POST $BASE/api/wait  {"ms":1000}             let the game run
    GET  $BASE/api/help                          this skill

`/api/screen` returns JSON with `image`, a base64 PNG data URI (`?format=png` or
`?format=webp` for raw bytes). Action calls return `changed` and `frame`, and
also return the same `image` when called with `?image=1`.

    curl -s -X POST $BASE/api/key -H 'content-type: application/json' \
         -d '{"key":"enter"}'

Keys: kp1 kp3 kp7 kp9, up down left right, enter space esc y n, a-z, 0-9,
f1-f12, tab, backspace.


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

# Field manual: controls and game knowledge

This manual covers controls, menus, combat, attributes, and suggestions for
checking keyboard actions against screenshots. Apply those suggestions to the
current screen and game text; a single observation is not a universal mechanic.

## First: get the compass

Many locations open after the initial encounter with 南賢. Complete that
encounter, then use visible entrances and story clues to continue exploring.

1. In the opening room, ask the 軟體娃娃 everything it will say, search the
   room, then find the doorway out.
2. On the world map, **follow the small path south to 南賢居**, roughly
   `[388,325]`. Talk to 南賢, then investigate the cabinet beside him to get
   the 羅盤 (compass).
3. The first conversation opens many locations. Prioritize it if unfinished.
   If an entrance still resists you, check its position, your facing direction,
   and game text rather than assuming a prerequisite is missing.
4. In the original game, giving money to the waiter at 河洛客棧 provides clues
   to 南賢居, including the small path and a circular landmark near the house.
   The clue starts from the inn; obtaining it is not required to enter 南賢居.
5. After obtaining the compass, highlight it in `esc → 物品` to read the person
   and boat coordinates. Use the actual readings to check your position,
   especially when you suspect a loop or are unsure of the route.

## Controls and menus

- Move with `kp1 kp3 kp7 kp9` or the arrows; they are the same four axes.
  **Holding a key keeps sending the same direction**, without following paths,
  turning, or avoiding obstacles. Use short actions while the route is unclear
  and longer holds on confirmed clear stretches.
- For an ordinary person or container, stand adjacent, face the target, and
  press space or enter to investigate. Stepping on a tile can trigger a
  separate story event. In combat, choose commands and targets through its menu.
- `esc` opens the menu anywhere. Arrows move the highlight, space or enter
  confirms, `esc` backs out.
- `y` and `n` answer （Ｙ／Ｎ）. Any key can advance ordinary dialogue; read
  choices and answer them with the appropriate keys.

The world-map menu includes 醫療 heal, 解毒 cure poison, 物品 items, 狀態 status,
離隊 dismiss a companion, and 系統 system. Inside a scene, the first four are
available. In-game saving, loading, and the dismissal menu require the world
map; recruitment usually happens through dialogue and story conditions.

- **醫療**: choose a healer and patient. Healing needs at least 50 體力 and
  sufficient medical ability for the patient's injury.
- **解毒**: choose a person to remove poison and a patient. Its effect depends
  on the ability and poison severity; do not copy the healing stamina condition
  to this command. Check selectable characters, available commands, and results.
- **物品**: for a story item used on a scene person or object, stand adjacent
  and face the target first. Medicines, equipment, and manuals select their
  user through the item menu. The five kinds are story items; pills that restore
  or raise attributes; hidden weapons, usable only in
  combat; weapons and armour, equippable depending on the character; and
  manuals, which a party member can study to gain attributes or learn a skill.
- **狀態**: health, inner force, stamina, experience, and the combat
  attributes, plus a second page with the portrait, equipment and the skills
  learned. A character can learn at most ten martial arts, each to level ten,
  but has only one currently assigned training manual.
- **系統**: three save slots, load, and quit. Save regularly.

## Combat

Combat is turn-based. The order usually follows combat agility; waiting can
move the current character later in that order. Stamina, inner force, ability,
and remaining movement affect available commands. Read the current menu and status.

- **Move**: choose a position in the available range. After moving, check which
  commands remain instead of assuming their menu positions are fixed.
- **Attack**: choose a martial art, then its target, direction, or area as
  appropriate. Not every art uses the same targeting method.
- **Poison / cure / heal**: use the relevant ability, resources, and a suitable
  target. Injury also affects healing. Do not confuse a command's minimum
  requirement with its per-use cost, or apply healing requirements to other commands.
- **Items**: choose the use and target for that item, then check quantity and status.
- **Wait**: delay the current character's action; this differs from ending it.
- **Status**: inspect attributes, equipment, and martial arts before choosing an action.
- **Rest**: end that character's current action and recover some stamina. Other
  conditions affect whether health or inner force also recovers.
- **Auto**: the game controls friendly combat actions, not necessarily only the
  current actor. Watch the whole party and verify any attempt to cancel it.

A character falling is not necessarily permanent death, and a lost battle is not
always game over. Encounters have different defeat branches. Do not assume every
defeat is survivable either; use the story and battle result, and watch party health,
injury, and poison.

## Attributes

Visible: health, inner force, stamina, experience, attack, defence, 輕功
agility, healing, poison, curing, and the weapon skills. Base attack, defence,
and 輕功 cap at 100; equipment bonuses are separate. The listed ability and
weapon attributes also cap at 100, and some skills or items require minimum values.

Other attributes not fully listed on the ordinary status screen:

- **體質** affects health gained per level and is assigned an initial value at creation.
- **資質** decides how fast you learn skills. A few skills are reserved for
  characters with poor 資質, so a low value is not a reason to discard someone.
- **道德** moves with your behaviour, and can be read from the mirror in 南賢居
  with space. Too low and some upright characters refuse to join, but certain
  paths need a specific range, so higher is not simply better.
- **名望** changes through some story events and battle results and affects
  later events. Gaining experience does not necessarily also increase reputation.

## Checking actions against the screen

**`changed` does not say whether you moved.** It only reports whether a visible
screen change was observed. Compare landmarks or compass readings, and distinguish
walking from menus or story sequences instead of inferring a cause from the flag.

**During ordinary walking, the camera follows the character.** Judge movement
from landmarks or the compass, not just the sprite position. A short tap may cause
only a small shift; do not assume a fixed fraction of the screen per step or use a
fixed similarity threshold to decide that movement was blocked.

**Check the route.** Record landmarks you have actually seen and, after obtaining
the compass, actual coordinates. Compare a new observation with several recent
ones. Similar screens are not necessarily the same position; animation can change
parts of a scene. If you suspect a loop, verify the current screen and direction
before adjusting the route. Shorten actions and look again when the cause is unclear.

**Choose action length from the visible route.** Use short actions at junctions,
entrances, and unfamiliar terrain. Longer holds can help on confirmed clear stretches.
Decide when to look again from the situation, not a fixed number of keys or a fixed
screen-similarity rule. Do not blindly increase hold time to break a suspected blockage.

**Alternating keys without progress does not establish a two-tile loop.** Check
for menus or dialogue, try short movements, and use the observed results to find a
passable direction. Record entrances and route segments confirmed in this run, and
verify the starting position before reusing them elsewhere.

**Read the current interface.** Menus show stacked choices, dialogue contains
sentences and possible choices, inventory shows icons and descriptions, and status
cards show portraits and attributes. Relative landmark descriptions can help; if
comparing pixels, distinguish screen coordinates from map coordinates and allow for
animation or occlusion. A sprite hidden by foreground art does not prove teleportation
or a fault.

**A fully black screen does not reveal its cause.** Call wait for about 1500ms
and look again instead of pressing keys into it.

**Entrances are at specific locations, not across the whole wall.** Use visible
paths, doors, and other clues, and try short movements from different positions when
needed. A failed attempt alone does not prove a missing prerequisite. Furniture can
block routes indoors; when near an NPC, check the facing direction and investigate
with enter or space, routing around obstacles according to the screen.

**Repeated dialogue does not establish that an NPC has no function.** If the
whole exchange has no new information, record that and consider another objective.
Items or later story conditions may still enable another interaction with that NPC.

**Appearance alone does not establish what is decorative.** Use game text and
actual interactions rather than dismissing animals, mist, or other shapes solely
because of their appearance.

## Coordinates from community guides

These are reference coordinates from original-game guides. An entrance and an
adjacent outside tile may differ by one coordinate. Use actual compass readings
and the visible entrance, not the table alone, to confirm arrival or entry.

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
