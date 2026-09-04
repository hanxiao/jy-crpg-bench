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
