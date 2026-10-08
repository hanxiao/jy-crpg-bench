# 技能：游玩《金庸群俠傳》

1996 年河洛工作室的原版 DOS 游戏，以模拟器执行于 {BASE}。你送出按键，并取得画面。

## API

    GET  {BASE}/api/screen                        只看画面，不按任何键
    POST {BASE}/api/key   {{"key":"kp3"}}           按一个键；可加 "hold"（帧数）
    POST {BASE}/api/key   {{"key":["kp9","enter"]}} 依序按多个键
    GET  {BASE}/api/slots                         列出模拟器快照
    POST {BASE}/api/save  {{"name":"checkpoint"}}   储存快照
    POST {BASE}/api/load  {{"name":"checkpoint"}}   还原快照
    GET  {BASE}/api/help                          本技能说明

`/api/screen` 回传 JSON，`image` 是 base64 的 PNG data URI；加 `?format=png` 直接取得
PNG 位元组。`/api/key` 是唯一的动作：`key` 是一个键名或依序按下的键名列表，重复按键
就是同一个键的列表，选单路径也是一个列表。它会等画面稳定（包括场景切换）才回传
`ok`、`action` 与 `frame`（接下来那张画面的编号），不说明画面发生了什么：一切效果
从画面判断。没有等待呼叫：游戏只在按键时前进，动作本身已等到结果。

每个呼叫只读取上面列出的栏位，其他栏位会以 400 指明并拒绝。

    curl -s -X POST {BASE}/api/key -H 'content-type: application/json' \
         -d '{{"key":"enter"}}'

按键：kp1 kp3 kp7 kp9、up down left right、enter space esc y n、a-z、0-9、
f1-f12、tab、backspace。

动作和看画面是两次呼叫。送按键会等画面稳定后回传状态；`GET /api/screen` 回传画面。
在动作 URL 加 `?image=1`，可在同一回应取得动作后的画面。

游戏全是繁体中文。目标、选项和等待特定按键的提问都在文字里。

## 移动

世界是等角视角，四个移动轴在画面上都是斜的。九宫数字键的名称对应画面上的方向，
与方向键等效：

    kp7  ↖ 左上      kp9  ↗ 右上        （kp7 == left，kp9 == up）
    kp1  ↙ 左下      kp3  ↘ 右下        （kp1 == down，kp3 == right）

## 互动

- enter 与 space 确定、推进对话、调查。与人物或容器互动时，站在相邻格并朝向目标，
  再按 enter 或 space。踩到特定格子触发的剧情是另一种机制。
- 一般对话可用任意键推进；选项与“（Ｙ／Ｎ）”用 y 与 n 作答。
- esc 开启选单。建筑内：醫療／解毒／物品／狀態。大地图上另有離隊与系統（存档、
  读档、离开）。游戏只在大地图上存档。

小说中的人物可以入队，武功可以习得。战斗是团队回合制，行动顺序依輕功。角色倒下、
战斗失败与游戏结束是三件不同的事；败北后能否继续取决于该场遭遇。
