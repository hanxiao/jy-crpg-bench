#!/usr/bin/env python3
"""Assemble agents.md, one per language, from the skills in ../skills.

The brief an agent reads is the same text the server hands out at /api/help,
plus a preamble about how a benchmark run starts and ends. Generating it here
rather than keeping a second copy means the skill cannot drift from the one the
game itself serves.

Chinese output is Simplified, but the words that appear on the game's own
screen stay Traditional: an agent matches what it reads against 1996 Taiwanese
text, and 罗盘 would never match 羅盤.
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SKILLS = HERE.parent / "skills"
BACKEND = "https://jy-crpg-bench-366646433082.us-central1.run.app"

# Everything in this list is text the agent will see rendered by the game, or a
# proper name the game uses. Masked before conversion so it survives.
ON_SCREEN = [
    "金庸群俠傳", "河洛工作室", "軟體世界娃娃", "軟體娃娃", "小蝦米",
    "崑崙仙境", "無量山洞", "河洛客棧", "天寧寺", "鐵掌山", "五毒教",
    "衡山派", "閻基居", "北丑居", "南賢居", "主角居", "南賢",
    "羅盤", "醫療", "解毒", "物品", "狀態", "離隊",
    "輕功", "體力", "體質", "資質", "道德", "名望", "注音",
    # 隊 and 系統 are menu labels in some places and ordinary words in others.
    # Protecting the bare characters left prose reading "團隊回合制" and
    # "選單系統", so only the label contexts are held back.
    "隊 與 系統", "狀態、隊、系統", "「隊」和「系統」", "**隊**", "**系統**",
    "離隊與系統", "離隊、系統", "「系統」",
]

PRE_ZH = """# jy-crpg-bench

你即将游玩《金庸群俠傳》，1996 年河洛工作室的原版 DOS 游戏，未经修改，跑在
模拟器上。你送出按键，需要时再另外取得画面截图。这是一个繁体中文的开放世界，
怎么玩由你决定。

这份文件就是全部说明。读一遍，然后开始。

## 一、先取名，再开局

填写能标识本次模型及档位的名字，榜单会用它标识这一局。

    curl -s -X POST {backend}/session \\
         -H 'content-type: application/json' \\
         -d '{{"agent":"YOUR-MODEL-NAME","minutes":{minutes}}}'

`minutes` 是这一局的总游玩时长，这份说明对应的是 {minutes} 分钟。回应里有 `base_url`。下面所有呼叫都送到那个网址，以下称 `$BASE`。它只属于你：
网址里带着这一局的令牌，拿着它才能往你的模拟机里送按键；没有它的网址只能旁观。
你自己的模拟机、你自己的存档，没有别人的输入。

开局时你已经在游戏里，站在开场房间中。角色已经建好，也已经有名字了：那个名字
是什么无所谓，不要试图去改它，也不用碰注音输入法。

## 二、一局的规则

- 你的**总游玩时长**在开局时就定好了。开局回应里的 `seconds` 就是你有多少秒，
  从连线可以开始动作的那一刻算起。别自己假设是多久。
- **默认闲置上限为十分钟**；长时间没有游戏动作会提前结束。单纯查看画面不算游戏动作。
- 会记录用于回放的画面和操作，结束后生成录像。公共服务默认把结果列入
  <https://hanxiao.io/jy-crpg-bench/>；是否公开取决于本次会话的发布设置。
- 你会从下一次呼叫得知这局结束了：回应变成 `410`，带着 `"ended": true`、结束原因
  和 `video_url`。看到就停手。没有办法加时，开第二局也不是延长，那是从开场房间
  重新开始的另一局。

游戏目标仍是收集十四本书并返回现实；本次会话记录限时进展，即使尚未通关也会在预算
结束时停止。闲置等情况也可能使会话提前结束。

## 三、开局往哪走

你现在在一个室内小场景里。这个世界分两层：很多这样的小场景，由一张大地图串起来。
大地图才是主干，小场景挂在上面。

1. 先把这个房间搜一遍。调查普通人物或容器时，站在相邻格朝向目标，再按确认键。
2. 找到门口出去，你就到大地图了。
3. 进入大地图后，沿小路往南，前往南賢居；先对话，再调查柜子取得羅盤。
   许多地点在这段开局事件后开放；仍走不进去时，结合入口位置和游戏文字判断。

根据画面和对话推进当前目标。没有新信息时可以调整计划，但不要只为增加场景数量而
跳过已经发现的线索，也不要在没有新证据时反复尝试同一操作。

---

"""

PRE_EN = """# jy-crpg-bench

You are about to play 金庸群俠傳 (The Legend of Jin Yong Heroes), the original
1996 DOS game by 河洛工作室, running unmodified under emulation. You send keys
and request pictures of the screen when you need them. It is an open world in
Traditional Chinese: what you do with it is yours to decide.

This file is the whole brief. Read it once, then start.

## 1. Name yourself, and start

Use a name identifying the model and thinking level for this run; the catalogue
uses that name to identify the result.

    curl -s -X POST {backend}/session \\
         -H 'content-type: application/json' \\
         -d '{{"agent":"YOUR-MODEL-NAME","minutes":{minutes}}}'

`minutes` is the total playtime for this run; this copy of the brief is the
{minutes} minute one. The reply carries `base_url`. Every call below goes to that URL, called `$BASE`
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

"""


def to_simplified(text: str) -> str:
    """Simplify the prose, leave the game's own words alone."""
    from zhconv import convert
    terms = sorted(set(ON_SCREEN), key=len, reverse=True)
    holes = {}
    for n, t in enumerate(terms):
        if t in text:
            key = f"\x00{n}\x00"
            holes[key] = t
            text = text.replace(t, key)
    text = convert(text, "zh-hans")
    for key, t in holes.items():
        text = text.replace(key, t)
    return text


def skill(lang: str) -> str:
    text = (SKILLS / f"play.{lang}.md").read_text(encoding="utf-8").rstrip()
    text += "\n\n" + (SKILLS / f"speedrun.{lang}.md").read_text(encoding="utf-8")
    # The markdown carries doubled braces in its JSON examples; un-double them
    # before the {BASE} substitution, so a doubled {{BASE}} would land at
    # $BASE instead of the corrupted {$BASE}.
    text = text.replace("{{", "{").replace("}}", "}").replace("{BASE}", "$BASE")
    # the shared instance tells agents to identify with a header; a bench run is
    # already named and alone on its machine, so that section is noise here
    cuts = [r"\n\*\*Name yourself\.\*\*.*?(?=\n## )",
            r"\n\*\*請幫自己取個名字。\*\*.*?(?=\n## )"]
    # a scored session answers 404 to emulator snapshots; do not list them
    text = re.sub(r"^[ \t]*(?:GET|POST)[ \t]+\$BASE/api/(?:slots|save|load)\b.*\n", "",
                  text, flags=re.M)
    for c in cuts:
        text, n = re.subn(c, "\n", text, flags=re.S)
        if n:
            break
    else:
        raise RuntimeError("the shared-session section moved; check the skill")
    return text.strip() + "\n"


def build(lang: str, minutes: int = 20) -> str:
    pre = (PRE_EN if lang == "en" else PRE_ZH).format(backend=BACKEND,
                                                      minutes=minutes)
    body = skill(lang)
    if lang == "zh":
        body = to_simplified(body)
    return pre + body


# The page carries the chosen playtime in the URL it hands out rather than in
# the text of the line, so what a reader copies is just an address. One file
# per option, all generated from the same source, so they cannot drift.
OPTIONS = [20, 60, 240, 480, 1440]


def main():
    made = []
    for lang, root in (("zh", HERE), ("en", HERE / "en")):
        for m in OPTIONS:
            d = root if m == OPTIONS[0] else root / f"{m}m"
            d.mkdir(parents=True, exist_ok=True)
            out = d / "agents.md"
            out.write_text(build(lang, m), encoding="utf-8")
            made.append(out)
    print(f"  {len(made)} briefs, {len(OPTIONS)} playtimes x 2 languages")
    for p in made[:1] + made[-1:]:
        print(f"    {p.relative_to(HERE.parent)}  {len(p.read_text())} chars")


if __name__ == "__main__":
    main()
