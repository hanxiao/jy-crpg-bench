# 技能：遊玩《金庸群俠傳》

1996 年河洛工作室的原版 DOS 遊戲，以模擬器執行於 {BASE}。你送出按鍵，並取得畫面。

## API

    GET  {BASE}/api/screen                        只看畫面，不按任何鍵
    POST {BASE}/api/key   {{"key":"kp3"}}           按一個鍵；可加 "hold"（幀數）
    POST {BASE}/api/key   {{"key":["kp9","enter"]}} 依序按多個鍵
    GET  {BASE}/api/slots                         列出模擬器快照
    POST {BASE}/api/save  {{"name":"checkpoint"}}   儲存快照
    POST {BASE}/api/load  {{"name":"checkpoint"}}   還原快照
    GET  {BASE}/api/help                          本技能說明

`/api/screen` 回傳 JSON，`image` 是 base64 的 PNG data URI；加 `?format=png` 直接取得
PNG 位元組。`/api/key` 是唯一的動作：`key` 是一個鍵名或依序按下的鍵名列表，重複按鍵
就是同一個鍵的列表，選單路徑也是一個列表。它會等畫面穩定（包括場景切換）才回傳
`ok`、`action` 與 `frame`（接下來那張畫面的編號），不說明畫面發生了什麼：一切效果
從畫面判斷。沒有等待呼叫：遊戲只在按鍵時前進，動作本身已等到結果。

每個呼叫只讀取上面列出的欄位，其他欄位會以 400 指明並拒絕。

    curl -s -X POST {BASE}/api/key -H 'content-type: application/json' \
         -d '{{"key":"enter"}}'

按鍵：kp1 kp3 kp7 kp9、up down left right、enter space esc y n、a-z、0-9、
f1-f12、tab、backspace。

動作和看畫面是兩次呼叫。送按鍵會等畫面穩定後回傳狀態；`GET /api/screen` 回傳畫面。
在動作 URL 加 `?image=1`，可在同一回應取得動作後的畫面。

遊戲全是繁體中文。目標、選項和等待特定按鍵的提問都在文字裡。

## 移動

世界是等角視角，四個移動軸在畫面上都是斜的。九宮數字鍵的名稱對應畫面上的方向，
與方向鍵等效：

    kp7  ↖ 左上      kp9  ↗ 右上        （kp7 == left，kp9 == up）
    kp1  ↙ 左下      kp3  ↘ 右下        （kp1 == down，kp3 == right）

## 互動

- enter 與 space 確定、推進對話、調查。與人物或容器互動時，站在相鄰格並朝向目標，
  再按 enter 或 space。踩到特定格子觸發的劇情是另一種機制。
- 一般對話可用任意鍵推進；選項與「（Ｙ／Ｎ）」用 y 與 n 作答。
- esc 開啟選單。建築內：醫療／解毒／物品／狀態。大地圖上另有離隊與系統（存檔、
  讀檔、離開）。遊戲只在大地圖上存檔。

小說中的人物可以入隊，武功可以習得。戰鬥是團隊回合制，行動順序依輕功。角色倒下、
戰鬥失敗與遊戲結束是三件不同的事；敗北後能否繼續取決於該場遭遇。
