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
    "金庸群俠傳", "河洛工作室", "軟體娃娃", "小蝦米",
    "崑崙仙境", "無量山洞", "河洛客棧", "天寧寺", "鐵掌山", "五毒教",
    "衡山派", "閻基居", "北丑居", "南賢居", "主角居", "南賢",
    "羅盤", "醫療", "解毒", "物品", "狀態",
    "輕功", "體力", "體質", "資質", "道德", "名望", "注音",
    # 隊 and 系統 are menu labels in some places and ordinary words in others.
    # Protecting the bare characters left prose reading "團隊回合制" and
    # "選單系統", so only the label contexts are held back.
    "隊 與 系統", "狀態、隊、系統", "「隊」和「系統」", "**隊**", "**系統**",
]

PRE_ZH = """# jy-crpg-bench

你即将游玩《金庸群俠傳》，1996 年河洛工作室的原版 DOS 游戏，未经修改，跑在
模拟器上。你送出按键，需要时再另外取得画面截图。这是一个繁体中文的开放世界，
怎么玩由你决定。

这份文件就是全部说明。读一遍，然后开始。

## 一、先取名，再开局

取个名字，随便什么都行。写你自己的模型名（`claude-opus-5`、`gpt-5.2`、
`qwen3-max`）最有用，榜单会用它列出你这一局，但不要为这个多想一秒。

    curl -s -X POST {backend}/session \\
         -H 'content-type: application/json' \\
         -d '{{"agent":"YOUR-MODEL-NAME","minutes":{minutes}}}'

`minutes` 是这一局的总游玩时长，这份说明对应的是 {minutes} 分钟。回应里有 `base_url`。下面所有呼叫都送到那个网址，以下称 `$BASE`。它只属于你：
你自己的模拟机、你自己的存档，没有别人的输入。

开局时你已经在游戏里，站在开场房间中。角色已经建好，也已经有名字了：那个名字
是什么无所谓，不要试图去改它，也不用碰注音输入法。

## 二、一局的规则

- 你的**总游玩时长**在开局时就定好了。开局回应里的 `seconds` 就是你有多少秒，
  从连线可以开始动作的那一刻算起。别自己假设是多久。
- **每十分钟至少动作一次**，否则这一局会提早结束，并记为闲置。一个步骤想十分钟
  是失败，不是思考。看画面不算动作，按键才算。
- 全程录像。结束后录像会转成 MP4 公开发布，你的名字、动作速率、结束原因会进入
  <https://hanxiao.io/jy-crpg-bench/> 的公开榜单。
- 你会从下一次呼叫得知这局结束了：回应变成 `410`，带着 `"ended": true`、结束原因
  和 `video_url`。看到就停手。没有办法加时，开第二局也不是延长，那是从开场房间
  重新开始的另一局。

没有胜利条件。被衡量的是你拿这段时间做了什么。

## 三、开局往哪走

你现在在一个室内小场景里。这个世界分两层：很多这样的小场景，由一张大地图串起来。
大地图才是主干，小场景挂在上面。

1. 先把这个房间搜一遍。屋里有箱子，走上去撞它就是搜。
2. 找到门口出去，你就到大地图了。
3. 到大地图后往南走，完成南賢居事件并从柜子取得羅盤（下面第「零」节有细节）。
   在完成这一步之前，许多建筑进不去，所以不要一栋一栋去试门。

**保持前进。** 时间比你想的短，而跑不出东西的局几乎都死在同三件事上：原地不动、
反复读同一段循环对话、绕着同一栋进不去的建筑打转。一个场景榨不出新东西就走人，
一条路走不通就换一条。宁可粗略地走过五个场景，也不要把整局时间花在一个房间里。

---

"""

PRE_EN = """# jy-crpg-bench

You are about to play 金庸群俠傳 (The Legend of Jin Yong Heroes), the original
1996 DOS game by 河洛工作室, running unmodified under emulation. You send keys
and request pictures of the screen when you need them. It is an open world in
Traditional Chinese: what you do with it is yours to decide.

This file is the whole brief. Read it once, then start.

## 1. Name yourself, and start

Pick a name. Any name works. Your own model name (`claude-opus-5`, `gpt-5.2`,
`qwen3-max`) is the most useful one because the catalogue lists your run under
it, but do not spend a second deciding.

    curl -s -X POST {backend}/session \\
         -H 'content-type: application/json' \\
         -d '{{"agent":"YOUR-MODEL-NAME","minutes":{minutes}}}'

`minutes` is the total playtime for this run; this copy of the brief is the
{minutes} minute one. The reply carries `base_url`. Every call below goes to that URL, called `$BASE`
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
    # the markdown carries doubled braces so the JSON examples survive editing
    text = text.replace("{BASE}", "$BASE").replace("{{", "{").replace("}}", "}")
    # the shared instance tells agents to identify with a header; a bench run is
    # already named and alone on its machine, so that section is noise here
    cuts = [r"\n\*\*Name yourself\.\*\*.*?(?=\n## )",
            r"\n\*\*請幫自己取個名字。\*\*.*?(?=\n## )"]
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
