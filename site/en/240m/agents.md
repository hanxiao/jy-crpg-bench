# jy-crpg-bench

You are about to play 金庸群俠傳 (Heroes of Jin Yong), the original
1996 DOS game by 河洛工作室, running unmodified under emulation. You send keys
and fetch the screen. The game is in Traditional Chinese.

## Start

    curl -s -X POST https://jy-crpg-bench-366646433082.us-central1.run.app/session \
         -H 'content-type: application/json' \
         -d '{"agent":"YOUR-MODEL-NAME","minutes":240}'

`agent` names the model and its thinking level. `minutes` is the playtime of
the run; this brief is the 240 minute one. The reply carries `base_url`,
called `$BASE` below. Every call goes there.

You start inside the game, in the starting house, with a character already made
and named. Do not change the name or touch the 注音 input method.

---

# Skill: play 金庸群俠傳 (Heroes of Jin Yong)

The original 1996 DOS game by 河洛工作室, running under emulation at $BASE.
You send keys and fetch the screen.

## The loop

Acting and looking are separate calls. A key press waits for the screen to
settle and returns metadata; `GET /api/screen` returns the picture. Add
`?image=1` to an action to get the picture in the same reply.

The game is entirely in Traditional Chinese. Objectives, choices and prompts
that expect a specific key are all in its text.

## API

    GET  $BASE/api/screen                        look, pressing nothing
    POST $BASE/api/key   {"key":"kp3"}           press one key; +"hold" frames
    POST $BASE/api/key   {"key":["kp9","enter"]} press several, in order
    GET  $BASE/api/help                          this skill

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

    curl -s -X POST $BASE/api/key -H 'content-type: application/json' \
         -d '{"key":"enter"}'

Keys: kp1 kp3 kp7 kp9, up down left right, enter space esc y n, a-z, 0-9,
f1-f12, tab, backspace.

## Movement

The world is isometric: the four movement axes are diagonals on screen. The
numpad names match the visible direction and are identical to the arrows:

    kp7  ↖ up-left      kp9  ↗ up-right        (kp7 == left, kp9 == up)
    kp1  ↙ down-left    kp3  ↘ down-right      (kp1 == down, kp3 == right)

Use `kp7/kp9/kp1/kp3`. On a clear path, alternating two directions moves
horizontally or vertically across the screen:

    screen-right : kp3, kp9, kp3, kp9, ...      screen-left : kp7, kp1, ...
    screen-down  : kp3, kp1, kp3, kp1, ...      screen-up   : kp7, kp9, ...

`hold` is the number of frames the key stays down, not tiles travelled; it
does not follow paths, turn or avoid obstacles. Use short taps where the route
is unclear and longer holds on a confirmed clear stretch. A `hold` below 5 is
refused: the game reads the keyboard once per loop, and a press released
within one loop is lost. The default is 10.

## Interacting

- enter and space confirm, advance dialogue and investigate. For a person or
  container, stand on an adjacent tile facing the target, then press enter or
  space. Story events triggered by stepping on a tile are separate.
- Any key advances ordinary dialogue. Answer choices and （Ｙ／Ｎ） prompts
  with y and n.
- esc opens the menu. In a building: 醫療 / 解毒 / 物品 / 狀態. On the world
  map also 離隊 (dismiss a party member) and 系統 (save, load, quit). The game
  saves only from the world map.

## The world

You play 小蝦米, who wakes inside the world of Jin Yong's novels. The way home
is to find the fourteen books scattered across the land. Characters from the
novels can be recruited and their martial arts learned. Battles are turn-based
between teams, in an order set by 輕功. A fallen character, a lost battle and
the end of the game are different events; whether play continues after a
defeat depends on the encounter.

# Field manual: controls and game knowledge

## First: get the compass

Many locations open only after the opening encounter at 南賢居, the house of the hermit.

1. In the starting house, talk to the 軟體娃娃 until nothing new is said, search
   the room, then find the doorway out.
2. On the world map, follow the small path south to 南賢居, near `[388,325]`.
   Talk to 南賢, the hermit, then investigate the cabinet beside him to get the 羅盤
   (compass).
3. Highlight the compass in `esc → 物品` to read the coordinates of the party
   and the boat. Use them to check your position whenever the route is unclear.

In the original game, paying the waiter at 河洛客棧, the Heluo Inn, buys directions to 南賢居.
They are not required to enter.

## Controls and menus

- Move with `kp1 kp3 kp7 kp9` or the arrows; they are the same four axes.
  Holding a key keeps sending the same direction without following paths,
  turning or avoiding obstacles.
- For a person or container, stand adjacent, face the target, and press space
  or enter. Stepping on a tile can trigger a separate story event. In a battle,
  choose commands and targets through its menu.
- `esc` opens the menu anywhere. Arrows move the highlight, space or enter
  confirms, `esc` backs out.
- `y` and `n` answer （Ｙ／Ｎ）. Any key advances ordinary dialogue.

The world-map menu holds 醫療 heal, 解毒 cure poison, 物品 items, 狀態 status,
離隊 dismiss a party member and 系統 system. Inside a location the first four are
available; saving, loading and dismissal need the world map. Recruitment
happens through dialogue.

- 醫療: choose a healer and a patient. Healing needs at least 50 體力 and
  enough medical ability for the injury.
- 解毒: choose a curer and a patient; the effect depends on the curing
  ability and the poison.
- 物品: a story item is used on a person or object while standing adjacent
  and facing it; medicines, equipment and manuals choose their user in the
  item menu. Five kinds: story items; pills that restore or raise attributes;
  hidden weapons, usable only in battle; weapons and armour, equippable by
  some characters; manuals, which a party member studies to gain attributes or
  a skill.
- 狀態: health, internal energy, stamina, experience and the battle attributes,
  with a second page of portrait, equipment and skills. A character learns at
  most ten martial arts, each to level ten, and studies one manual at a time.
- 系統: three save slots, load, and quit. Save often.

## Battles

Battles are turn-based. Order follows 輕功; waiting moves the current character
later in the round. Stamina, internal energy, ability and remaining movement decide
which commands are available; read the menu.

- 移動 move: choose a position in range. The commands that remain afterwards
  change.
- 攻擊 attack: choose a martial art, then its target, direction or area.
- 用毒 poison, 解毒 cure, 醫療 heal: need the ability, the resource and a
  suitable target.
- 物品 items: choose the use and the target, then check the quantity.
- 等待 wait: delay this character's action, which is not the same as ending
  it.
- 狀態 status: attributes, equipment and martial arts.
- 休息 rest: end the action and recover some stamina.
- 自動 auto: the game controls the whole party's battle actions.

A fallen character is not necessarily dead, and a lost battle is not always the
end of the game. Some defeats end the run; read the story and the result.

## Attributes

Visible: health, internal energy, stamina, experience, attack, defence, 輕功,
healing, poison, curing and the weapon skills. Base attack, defence and 輕功
cap at 100; equipment adds on top. Some skills and items need minimum values.

Hidden:

- 體質 sets the health gained per level.
- 資質 sets how fast skills are learned. A few skills are reserved for
  characters with poor 資質.
- 道德 moves with your actions and is read from the mirror in 南賢居 with
  space. Too low and upright characters refuse to join; some paths need a
  specific range.
- 名望 changes with story events and battles and affects later events.

## Coordinates from community guides

Reference coordinates from guides to the original game. An entrance and the
tile outside it may differ by one; confirm arrival with the compass and the
visible entrance.

| Place | Coordinates |
|---|---|
| 主角居 the starting house | (357,235) |
| 河洛客棧 | (359,229) |
| 南賢居 the house of the hermit | (388,325) |
| 天寧寺 | (330,237) |
| 鐵掌山 | (302,343) |
| 衡山派 | (355,376) |
| 五毒教 | (247,424) |
| 崑崙仙境 | (22,440) |
| 無量山洞 | (168,426) |
| 閻基居 | (396,374) |
| 北丑居 | (51,109) |
