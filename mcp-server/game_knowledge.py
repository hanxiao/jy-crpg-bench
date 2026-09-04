"""Everything an agent needs to know to play 金庸群俠傳 (1996, DOS).

Kept separate from the transport so the wording can be tuned without touching
the tool plumbing. Facts marked (verified) were measured against this build.
"""

INSTRUCTIONS = """
You are playing 金庸群俠傳 (The Legend of Jin Yong Heroes), the original 1996
DOS game by 河洛工作室, running under emulation. You drive it with a keyboard
only. There is no mouse.

HOW TO PLAY WITH THESE TOOLS
Every action tool returns a PNG of the screen after the action has been applied
and the picture has stopped changing. Look at that image before choosing the
next action. One tool call is one action and one observation. Do not batch long
blind sequences: read each screen.

The game is entirely in Traditional Chinese. Read the dialogue. It carries the
objectives, and several screens are yes/no or menu choices where pressing the
wrong key changes the run.

CONTROLS
- arrow up/down/left/right: walk on the map, and move the highlight in menus.
  One press turns the character to face that way and steps one tile if the tile
  is not blocked. Walking into a person or object is what triggers it.
- enter (or space): confirm a menu choice, advance dialogue, and interact with
  whatever you are facing. In the world these two keys are equivalent.
- esc: open the main menu (醫療 heal / 解毒 cure poison / 物品 items / 狀態
  status). Press esc again to close it.
- y / n: answer 是/否 prompts, which the game writes as （Ｙ／Ｎ）.
- k: light a torch inside caves. l: clear fog inside caves.

THE ONE THING THAT WILL CONFUSE YOU
While a scripted event or cutscene is playing, the game ignores movement and
menu keys completely. Any key you send only advances the dialogue. So if arrows
do not move the character and esc does not open the menu, you are still inside a
cutscene: keep pressing enter and reading until it ends. Do not conclude the
controls are broken. A reliable check for "am I free to move": press esc, and
see whether the 醫療/解毒/物品/狀態 menu appears. (verified)

ENTERING A CHINESE NAME
Character naming uses the game's own 注音 (bopomofo) IME in the 大千 layout.
Type the zhuyin letters, then press the digit next to the character you want.
Layout:
  1ㄅ 2ㄉ 3ˇ 4ˋ 5ㄓ 6ˊ 7˙ 8ㄚ 9ㄞ 0ㄢ -ㄦ
  qㄆ wㄊ eㄍ rㄐ tㄔ yㄗ uㄧ iㄛ oㄟ pㄣ
  aㄇ sㄋ dㄎ fㄑ gㄕ hㄘ jㄨ kㄜ lㄠ ;ㄤ
  zㄈ xㄌ cㄏ vㄒ bㄖ nㄙ mㄩ ,ㄝ .ㄡ /ㄥ
Tones: 1st = space, 2nd = 6, 3rd = 3, 4th = 4, neutral = 7.
Example: 王 is ㄨㄤˊ, so type "j;6" then press "1" to pick 王. (verified)

THE STORY AND YOUR GOAL
You play 小蝦米, a modern student who buys a VR copy of this very game and wakes
up inside the world of Jin Yong's novels. To get home you must find the fourteen
Jin Yong novels scattered across the world. Along the way you recruit famous
characters into your party, learn their martial arts, and fight turn-based team
battles.

Opening sequence: you wake on the floor of a room. Talk to the 軟體娃娃 (the
floating VR helmet). It tells you to leave and ask at the inn across the way
(河洛客棧). There you find the waiter 韋小寶; tip him some silver and he points
you to 南賢. Pick up the few items lying in the starting room before you leave.

PACING
Booting the emulator to the title screen takes about 14 seconds. From the title,
重新開始 starts a new game, 載入進度 loads, 離開遊戲 quits. Use save_state before
anything risky: these are emulator snapshots and restore exactly, which the
game's own save system cannot do mid-scene.
"""

GUIDE = INSTRUCTIONS + """

KEY NAMES ACCEPTED BY press / press_sequence
  up down left right
  enter (aliases: ok, confirm)   space
  esc (aliases: cancel, back)
  y n   a-z   0-9   f1-f12
  tab backspace delete home end pageup pagedown
  shift ctrl alt, and combos such as "alt+x"

TUNING THE WAIT
Each action waits for the screen to react and then to hold still. If a tool
returns a half-drawn dialogue line, raise `stable`. If an action legitimately
does nothing, the result says changed=false after the react budget expires.
"""
