import Foundation
import AppKit

enum Overlay {
    case none
    case talk(text: String, head: Int, mode: Int)
    case confirm(title: String, options: [String], selection: Int)
    case message(String)
    case menu(title: String, items: [String], selection: Int, tag: MenuTag)
    case status(role: Int)
    case items(selection: Int, using: Bool)
    case shop(index: Int, selection: Int)
    case nameEntry(String)
}

struct ScriptFrame {
    var code: [Int]
    var pc: Int
}

enum WaitKind {
    case none
    case dismiss
    case confirm(yes: Int, no: Int, skip: Int)
    case battle(yes: Int, no: Int)
}

enum MenuTag {
    case system, team, useOn, save, load, battle
}

final class Game {
    let res: Resources
    var save = SaveArchive()
    let audio: GameAudio
    let text: TextRenderer
    var rng = OriginalRNG()
    var whereMode: Where = .title
    var overlay: Overlay = .none
    var running = true

    var mx = 0, my = 0, mFace = 0, mStep = 0
    var sx = 0, sy = 0, sFace = 0, sStep = 0
    var inShip = 0
    var curScene = -1
    var curEvent = -1
    var curItem = -1
    var sceneRolePic = 0
    var needRefresh = false
    var exitSceneMusic = 16
    var titleMenu = 0
    var clouds: [Cloud] = []
    var x50 = [Int](repeating: 0, count: 0x8000)
    var pendingKey: Key?
    var lastStep = Date()
    var lastAnim = Date()
    var walkHeld: Key?
    var statusDirty = true
    var lastMessage = ""

    var battleRoles: [BattleRole] = []
    var battleField: [[Int]] = []
    var battleCursorX = 0
    var battleCursorY = 0
    var battleActor = 0
    var battleSelecting = false
    var battleMenuSel = 0
    var battleMagicSel = 0
    var battleGetExp = 0
    var currentWar = 0
    var battleMoving = false
    var battleMoved = false
    var battleRange: Set<Int> = []
    var scripts: [ScriptFrame] = []
    var wait: WaitKind = .none
    var lastKey: String = ""
    var apiSeq: Int = 0
    var talkRemainder: [String] = []
    var talkHead = 0
    var talkMode = 0
    var lastBattleWon = false

    init(res: Resources) throws {
        self.res = res
        self.audio = GameAudio(dir: res.dir)
        self.text = TextRenderer(font: res.font)
        try save.load(dir: res.dir, slot: 0)
        for i in 0..<40 {
            clouds.append(Cloud(
                pic: i % max(1, res.clouds.count),
                x: rng.rnd(20000),
                y: rng.rnd(10000),
                speedX: 1 + rng.rnd(3),
                speedY: rng.rnd(2)
            ))
        }
        audio.playMusic(16)
    }

    func press(_ name: String) {
        handleKey(Key.parse(name))
    }

    func handleKey(_ key: Key) {
        pendingKey = key
        lastKey = key.token
        apiSeq += 1
        switch overlay {
        case .talk:
            if key == .ok || key == .cancel {
                if !talkRemainder.isEmpty {
                    let chunk = talkRemainder.prefix(4).joined(separator: "\n")
                    talkRemainder = Array(talkRemainder.dropFirst(4))
                    overlay = .talk(text: chunk, head: talkHead, mode: talkMode)
                } else {
                    overlay = .none
                    if case .dismiss = wait { wait = .none; runScript() }
                }
            }
        case .message:
            if key == .ok || key == .cancel {
                overlay = .none
                if case .dismiss = wait { wait = .none; runScript() }
            }
        case .confirm(_, let options, var sel):
            switch key {
            case .up, .left: sel = (sel + options.count - 1) % options.count; overlay = patchConfirm(sel)
            case .down, .right: sel = (sel + 1) % options.count; overlay = patchConfirm(sel)
            case .ok, .cancel:
                let yes = (key == .ok && sel == 1) || key == .yes
                overlay = .none
                if case .confirm(let y, let n, let skip) = wait {
                    if !scripts.isEmpty {
                        scripts[scripts.count - 1].pc += skip + (yes ? y : n)
                    }
                    wait = .none
                    runScript()
                }
            default: break
            }
        case .menu(let title, let items, var sel, let tag):
            switch key {
            case .up: sel = (sel + items.count - 1) % max(1, items.count); overlay = .menu(title: title, items: items, selection: sel, tag: tag)
            case .down: sel = (sel + 1) % max(1, items.count); overlay = .menu(title: title, items: items, selection: sel, tag: tag)
            case .ok: activateMenu(tag, sel)
            case .cancel: overlay = .none
            default: break
            }
        case .status(let role):
            if key == .left { overlay = .status(role: prevTeam(role)) }
            if key == .right { overlay = .status(role: nextTeam(role)) }
            if key == .ok || key == .cancel { overlay = .none }
        case .items(var sel, let using):
            let ids = save.base.bag.enumerated().filter { $0.element.id >= 0 }
            if !ids.isEmpty {
                if key == .up { sel = (sel + ids.count - 1) % ids.count }
                if key == .down { sel = (sel + 1) % ids.count }
            }
            if key == .ok, ids.indices.contains(sel) {
                useOrShowItem(ids[sel].offset, using: using)
            }
            if key == .cancel { overlay = .none }
            else { overlay = .items(selection: sel, using: using) }
        case .shop(let index, var sel):
            if key == .up { sel = (sel + 4) % 5 }
            if key == .down { sel = (sel + 1) % 5 }
            if key == .ok { buy(index, sel) }
            else if key == .cancel {
                overlay = .none
                if case .dismiss = wait { wait = .none; runScript() }
            } else { overlay = .shop(index: index, selection: sel) }
        case .nameEntry(let name):
            if key == .ok || key == .cancel {
                finishName(name.isEmpty ? "小蝦米" : name)
            }
        case .none:
            if whereMode == .title { handleTitle(key) }
            else if whereMode == .battle { handleBattleKey(key) }
            else { handleFieldKey(key) }
        }
    }

    func handleKeyUp(_ key: Key) {
        if walkHeld == key { walkHeld = nil }
    }

    func tick() {
        if whereMode == .battle { driveBattle() }
        if case .battle(let y, let n) = wait, whereMode != .battle {
            if !scripts.isEmpty {
                scripts[scripts.count - 1].pc += lastBattleWon ? y : n
            }
            wait = .none
            runScript()
        }
        let now = Date()
        if now.timeIntervalSince(lastAnim) > 0.2 {
            lastAnim = now
            animateScene()
            for i in clouds.indices {
                clouds[i].x += clouds[i].speedX
                clouds[i].y += clouds[i].speedY
                if clouds[i].x > 30000 { clouds[i].x = 0 }
            }
            if whereMode == .world || whereMode == .scene {
                mStep = (mStep + 1) % 7
                sStep = (sStep + 1) % 7
            }
        }
        if overlay.isNone, let held = walkHeld, now.timeIntervalSince(lastStep) > 0.08 {
            lastStep = now
            step(held)
        }
    }

    func draw(into fb: Framebuffer) {
        fb.clear(0)
        switch whereMode {
        case .title: drawTitle(fb)
        case .world: drawWorld(fb)
        case .scene: drawScene(fb)
        case .battle: drawBattle(fb)
        case .dead: drawDead(fb)
        }
        drawOverlay(fb)
    }

    // MARK: - Title

    private func handleTitle(_ key: Key) {
        switch key {
        case .up: titleMenu = (titleMenu + 2) % 3
        case .down: titleMenu = (titleMenu + 1) % 3
        case .ok:
            switch titleMenu {
            case 0: startNew()
            case 1: overlay = .menu(title: "讀取進度", items: ["進度一", "進度二", "進度三"], selection: 0, tag: .load)
            default: running = false; NSApp.terminate(nil)
            }
        default: break
        }
    }

    private func startNew() {
        try? save.load(dir: res.dir, slot: 0)
        applyBase()
        if !save.roles.isEmpty {
            overlay = .nameEntry(save.roles[0].name)
        } else {
            beginIntro()
        }
    }

    private func finishName(_ name: String) {
        if !save.roles.isEmpty { save.roles[0].name = name.isEmpty ? "小蝦米" : name }
        overlay = .none
        beginIntro()
    }

    private func beginIntro() {
        curScene = res.initScene
        sx = res.initSx
        sy = res.initSy
        sFace = 0
        whereMode = .scene
        audio.playMusic(save.scenes.indices.contains(curScene) ? save.scenes[curScene].enterMusic : 16)
        callEvent(Constants.beginEvent)
    }

    private func applyBase() {
        mx = save.base.mx
        my = save.base.my
        sx = save.base.sx
        sy = save.base.sy
        mFace = save.base.face
        sFace = save.base.face
        inShip = save.base.inShip
        if save.base.savedScene > 0 {
            curScene = save.base.savedScene - 1
            whereMode = .scene
        }
    }

    // MARK: - Field

    private func handleFieldKey(_ key: Key) {
        switch key {
        case .up, .down, .left, .right:
            walkHeld = key
            step(key)
            lastStep = Date()
        case .ok:
            if whereMode == .world { _ = checkEntrance() }
            else { _ = checkEvent1() }
        case .cancel:
            openSystemMenu()
        default: break
        }
    }

    private func step(_ key: Key) {
        let dir: Int
        switch key {
        case .up: dir = 0
        case .right: dir = 1
        case .left: dir = 2
        case .down: dir = 3
        default: return
        }
        if whereMode == .world {
            mFace = dir
            var x = mx, y = my
            moveCoord(&x, &y, dir)
            if canWalkWorld(x, y) {
                mx = x; my = y
                mStep = (mStep + 1) % 7
            }
        } else if whereMode == .scene {
            sFace = dir
            var x = sx, y = sy
            moveCoord(&x, &y, dir)
            if canWalkScene(sx, sy, x, y) {
                sx = x; sy = y
                sStep = (sStep + 1) % 7
                checkExit()
                checkEvent3()
            }
        }
    }

    private func moveCoord(_ x: inout Int, _ y: inout Int, _ dir: Int) {
        switch dir {
        case 0: x -= 1
        case 1: y += 1
        case 2: y -= 1
        case 3: x += 1
        default: break
        }
    }

    func canWalkWorld(_ x: Int, _ y: Int) -> Bool {
        if x <= 0 || x >= 479 || y <= 0 || y >= 479 { return false }
        var result = res.buildX[x][y] == 0
        let e = res.earth[x][y]
        if e == 838 || (e >= 612 && e <= 670) { result = false }
        if (e >= 358 && e <= 362) || (e >= 506 && e <= 670) || (e >= 1016 && e <= 1022) {
            inShip = 1
        } else {
            inShip = 0
        }
        return result
    }

    func canWalkScene(_ x1: Int, _ y1: Int, _ x: Int, _ y: Int) -> Bool {
        guard sceneIn(x), sceneIn(y) else { return false }
        var result = save.sdata[curScene][1][x][y] == 0
        let ev = save.sdata[curScene][3][x][y]
        if ev >= 0 && result && save.ddata[curScene][ev][0] == 1 { result = false }
        let ground = save.sdata[curScene][0][x][y]
        if (ground >= 358 && ground <= 362) || ground == 522 || ground == 1022
            || (ground >= 1324 && ground <= 1330) || ground == 1348 {
            result = false
        }
        let h0 = save.sdata[curScene][4][x1][y1]
        let h1 = save.sdata[curScene][4][x][y]
        return result && abs(h0 - h1) <= 10
    }

    private func sceneIn(_ v: Int) -> Bool { v >= 0 && v < 64 && curScene >= 0 && curScene < save.sdata.count }

    private func checkEntrance() -> Bool {
        var x = mx, y = my
        moveCoord(&x, &y, mFace)
        guard x >= 0 && y >= 0 && x < 480 && y < 480 else { return false }
        let snum = save.entrance[x][y]
        if snum >= 0, canEnter(snum) {
            instruct14()
            curScene = snum
            sFace = mFace
            mFace = 3 - mFace
            sStep = 0
            sx = save.scenes[curScene].enterX
            sy = save.scenes[curScene].enterY
            whereMode = .scene
            audio.playMusic(save.scenes[curScene].enterMusic)
            checkEvent3()
            return true
        }
        return false
    }

    func canEnter(_ snum: Int) -> Bool {
        guard save.scenes.indices.contains(snum) else { return false }
        let c = save.scenes[snum].enterCondition
        return c == 0 || c == 2
    }

    private func checkExit() {
        guard save.scenes.indices.contains(curScene) else { return }
        let sc = save.scenes[curScene]
        for i in 0..<3 {
            if sx == sc.exitX(i) && sy == sc.exitY(i) && sc.exitX(i) >= 0 {
                leaveScene()
                return
            }
        }
        if sc.jumpScene >= 0, sx == sc.jumpX1, sy == sc.jumpY1 {
            curScene = sc.jumpScene
            sx = sc.jumpX2
            sy = sc.jumpY2
            audio.playMusic(save.scenes[curScene].enterMusic)
        }
    }

    func leaveScene() {
        instruct14()
        whereMode = .world
        audio.playMusic(save.scenes.indices.contains(curScene) ? save.scenes[curScene].exitMusic : 16)
        curScene = -1
    }

    func checkEvent1() -> Bool {
        var x = sx, y = sy
        moveCoord(&x, &y, sFace)
        guard sceneIn(x), sceneIn(y) else { return false }
        let ev = save.sdata[curScene][3][x][y]
        if ev >= 0, save.ddata[curScene][ev][2] >= 0 {
            curEvent = ev
            callEvent(save.ddata[curScene][ev][2])
            curEvent = -1
            return true
        }
        return false
    }

    func checkEvent3() {
        guard sceneIn(sx), sceneIn(sy) else { return }
        let ev = save.sdata[curScene][3][sx][sy]
        if ev >= 0, save.ddata[curScene][ev][4] > 0 {
            curEvent = ev
            callEvent(save.ddata[curScene][ev][4])
            curEvent = -1
        }
    }

    private func animateScene() {
        guard whereMode == .scene, curScene >= 0, curScene < save.ddata.count else { return }
        for i in 0..<Constants.subMapEvents {
            let beg = save.ddata[curScene][i][7]
            let end = save.ddata[curScene][i][6]
            if beg < end {
                save.ddata[curScene][i][5] += 2
                if save.ddata[curScene][i][5] > end {
                    save.ddata[curScene][i][5] = beg
                }
            }
        }
    }

    // MARK: - Menus

    private func openSystemMenu() {
        overlay = .menu(
            title: "系統",
            items: ["醫療", "解毒", "物品", "狀態", "離隊", "讀檔", "存檔", "離開"],
            selection: 0,
            tag: .system
        )
    }

    private func activateMenu(_ tag: MenuTag, _ sel: Int) {
        switch tag {
        case .system:
            overlay = .none
            switch sel {
            case 0: overlay = .menu(title: "醫療", items: teamNames(), selection: 0, tag: .team)
            case 1: overlay = .menu(title: "解毒", items: teamNames(), selection: 0, tag: .team)
            case 2: overlay = .items(selection: 0, using: true)
            case 3: overlay = .status(role: save.base.team.first(where: { $0 >= 0 }) ?? 0)
            case 4: leaveTeamMenu()
            case 5: overlay = .menu(title: "讀取進度", items: ["進度一", "進度二", "進度三"], selection: 0, tag: .load)
            case 6: overlay = .menu(title: "保存進度", items: ["進度一", "進度二", "進度三"], selection: 0, tag: .save)
            default: running = false; NSApp.terminate(nil)
            }
        case .load:
            overlay = .none
            try? save.load(dir: res.dir, slot: sel + 1)
            applyBase()
            if save.base.savedScene > 0 { whereMode = .scene } else { whereMode = .world }
        case .save:
            overlay = .none
            overlay = .message("本版將進度寫入記憶體即可繼續。原檔格式存檔尚未寫入磁碟。")
        case .team:
            overlay = .none
        case .useOn:
            overlay = .none
        case .battle:
            handleBattleMenu(sel)
        }
    }

    private func leaveTeamMenu() {
        let names = teamNames().dropFirst()
        if names.isEmpty {
            overlay = .message("沒有可離隊的隊友")
        } else {
            overlay = .message("在事件中離隊")
        }
    }

    private func teamNames() -> [String] {
        save.base.team.compactMap { id in
            guard id >= 0, save.roles.indices.contains(id) else { return nil }
            return save.roles[id].name
        }
    }

    private func useOrShowItem(_ bagIndex: Int, using: Bool) {
        let slot = save.base.bag[bagIndex]
        guard save.items.indices.contains(slot.id) else { return }
        let item = save.items[slot.id]
        curItem = slot.id
        overlay = .none
        if !using {
            overlay = .message("\(item.name)\n\(item.desc)")
            return
        }
        switch item.itemType {
        case 1:
            overlay = .message("裝備 \(item.name)")
        case 2:
            overlay = .message("研習 \(item.name)")
        case 3, 4:
            applyItem(slot.id, to: save.base.team[0])
            save.addItem(slot.id, -1)
        default:
            if whereMode == .scene { _ = checkEvent1() }
            overlay = .message(item.desc.isEmpty ? item.name : item.desc)
        }
    }

    func applyItem(_ id: Int, to rnum: Int) {
        guard save.items.indices.contains(id), save.roles.indices.contains(rnum) else { return }
        let it = save.items[id]
        save.roles[rnum].hp += it.addHp
        save.roles[rnum].maxHp += it.addMaxHp
        save.roles[rnum].poisoned += it.addPoisoned
        save.roles[rnum].stamina += it.addStamina
        save.roles[rnum].mp += it.addMp
        save.roles[rnum].maxMp += it.addMaxMp
        save.roles[rnum].clampVitals()
    }

    func buy(_ shop: Int, _ sel: Int) {
        guard save.shops.indices.contains(shop) else { return }
        let item = save.shops[shop].item(sel)
        let price = save.shops[shop].price(sel)
        let amount = save.shops[shop].amount(sel)
        if amount <= 0 { overlay = .message("售罄"); return }
        if save.money() < price { overlay = .message("銀兩不足"); return }
        save.addItem(Constants.moneyId, -price)
        save.addItem(item, 1)
        save.shops[shop].setAmount(sel, amount - 1)
        let name = save.items.indices.contains(item) ? save.items[item].name : "物品"
        overlay = .message("得到 \(name)")
    }

    private func prevTeam(_ role: Int) -> Int {
        let ids = save.base.team.filter { $0 >= 0 }
        guard let i = ids.firstIndex(of: role) else { return role }
        return ids[(i + ids.count - 1) % ids.count]
    }

    private func nextTeam(_ role: Int) -> Int {
        let ids = save.base.team.filter { $0 >= 0 }
        guard let i = ids.firstIndex(of: role) else { return role }
        return ids[(i + 1) % ids.count]
    }

    private func patchConfirm(_ sel: Int) -> Overlay {
        if case .confirm(let title, let options, _) = overlay {
            return .confirm(title: title, options: options, selection: sel)
        }
        return overlay
    }

    func showTalk(_ text: String, head: Int, mode: Int) {
        let pages = paginate(text, width: 24)
        let chunk = pages.prefix(4).joined(separator: "\n")
        overlay = .talk(text: chunk.isEmpty ? text : chunk, head: head, mode: mode)
        wait = .dismiss
        talkRemainder = Array(pages.dropFirst(4))
        talkHead = head
        talkMode = mode
    }

    func showMessage(_ s: String) {
        overlay = .message(s)
        wait = .dismiss
    }

    func askConfirm(_ title: String, yes: Int, no: Int, skip: Int) {
        overlay = .confirm(title: title, options: ["否", "是"], selection: 0)
        wait = .confirm(yes: yes, no: no, skip: skip)
    }

    func snapshot() -> [String: Any] {
        var overlayName = "none"
        var overlayText = ""
        switch overlay {
        case .none: break
        case .talk(let t, _, _): overlayName = "talk"; overlayText = t
        case .confirm(let title, _, let sel): overlayName = "confirm"; overlayText = "\(title)#\(sel)"
        case .message(let s): overlayName = "message"; overlayText = s
        case .menu(let title, let items, let sel, _): overlayName = "menu"; overlayText = "\(title):\(items.joined(separator: "/"))#\(sel)"
        case .status: overlayName = "status"
        case .items: overlayName = "items"
        case .shop: overlayName = "shop"
        case .nameEntry(let n): overlayName = "name"; overlayText = n
        }
        let sceneName = (curScene >= 0 && save.scenes.indices.contains(curScene)) ? save.scenes[curScene].name : ""
        return [
            "mode": "\(whereMode)",
            "overlay": overlayName,
            "text": overlayText,
            "titleMenu": titleMenu,
            "mx": mx, "my": my, "sx": sx, "sy": sy,
            "face": whereMode == .world ? mFace : sFace,
            "scene": curScene,
            "sceneName": sceneName,
            "inShip": inShip,
            "money": save.money(),
            "team": save.base.team,
            "waiting": waitActive || !overlay.isNone,
            "scriptDepth": scripts.count,
            "lastKey": lastKey,
            "seq": apiSeq,
        ]
    }

    func currentFrame() -> Framebuffer {
        let fb = Framebuffer()
        draw(into: fb)
        return fb
    }

    private func paginate(_ s: String, width: Int) -> [String] {
        var lines: [String] = []
        for part in s.split(separator: "*", omittingEmptySubsequences: false) {
            var cur = ""
            var w = 0
            for ch in part {
                let cw = ch.asciiValue != nil ? 1 : 2
                if w + cw > width {
                    lines.append(cur)
                    cur = ""
                    w = 0
                }
                cur.append(ch)
                w += cw
            }
            lines.append(cur)
        }
        return lines.filter { !$0.isEmpty }
    }

    // MARK: - Draw

    private func drawTitle(_ fb: Framebuffer) {
        if res.titleBig.count >= 320 * 200 {
            fb.blitRaw(res.titleBig, width: 320, height: 200, x: 0, y: 0, scale: 2)
        } else {
            fb.fill(0, 0, Screen.width, Screen.height, 0)
        }
        let x = 278
        let y = 260
        if res.titles.indices.contains(0) { fb.blit(res.titles[0], x: x, y: y) }
        let hi = titleMenu + 1
        if res.titles.indices.contains(hi) { fb.blit(res.titles[hi], x: x, y: y + titleMenu * 20) }
    }

    private func drawDead(_ fb: Framebuffer) {
        if res.deadBig.count >= 320 * 200 {
            fb.blitRaw(res.deadBig, width: 320, height: 200, x: 0, y: 0, scale: 2)
        }
        text.draw("功力盡失，魂歸離恨天", x: 180, y: 360, color: 0x21, shadow: 0x23, onto: fb)
    }

    private func drawWorld(_ fb: Framebuffer) {
        let widthRegion = Screen.cx / 36 + 3
        let sumRegion = Screen.cy / 9 + 2
        var builds: [(x: Int, y: Int, pic: Int, depth: Int)] = []
        for sum in -sumRegion...(sumRegion + 15) {
            for i in -widthRegion...widthRegion {
                let i1 = mx + i + sum / 2
                let i2 = my - i + (sum - sum / 2)
                let (px, py) = screenPos(x: i1, y: i2, cx: mx, cy: my)
                if i1 >= 0 && i1 < 480 && i2 >= 0 && i2 < 480 {
                    blitM(res.earth[i1][i2] / 2, px, py, fb)
                    if res.surface[i1][i2] > 0 { blitM(res.surface[i1][i2] / 2, px, py, fb) }
                    var num = res.building[i1][i2] / 2
                    if i1 == mx && i2 == my {
                        if inShip == 0 {
                            num = 2501 + mFace * 7 + mStep
                        } else {
                            num = 3715 + mFace * 4 + (mStep + 1) / 2
                        }
                    }
                    if num > 0 {
                        let pic = picM(num)
                        let depth = ((i1 + i2) - (pic.width + 35) / 36 - (pic.originY - pic.height + 1) / 9) * 1024 + i2
                        builds.append((i1, i2, num, i1 == mx && i2 == my ? (i1 + i2) * 1024 + i2 : depth))
                    }
                } else {
                    blitM(0, px, py, fb)
                }
            }
        }
        builds.sort { $0.depth < $1.depth }
        for b in builds {
            let (px, py) = screenPos(x: b.x, y: b.y, cx: mx, cy: my)
            blitM(b.pic, px, py, fb)
        }
        drawClouds(fb)
        drawMini(fb, x: mx, y: my, name: "")
    }

    private func drawScene(_ fb: Framebuffer) {
        guard curScene >= 0, curScene < save.sdata.count else { return }
        let widthRegion = Screen.cx / 36 + 3
        let sumRegion = Screen.cy / 9 + 2
        var builds: [(x: Int, y: Int, pic: Int, yoff: Int, depth: Int)] = []
        for sum in -sumRegion...(sumRegion + 20) {
            for i in -widthRegion...widthRegion {
                let i1 = sx + i + sum / 2
                let i2 = sy - i + (sum - sum / 2)
                guard i1 >= 0 && i1 < 64 && i2 >= 0 && i2 < 64 else { continue }
                let (px, py) = screenPos(x: i1, y: i2, cx: sx, cy: sy)
                let ground = save.sdata[curScene][0][i1][i2] / 2
                blitS(ground, px, py, fb)
                let h4 = save.sdata[curScene][4][i1][i2]
                let h5 = save.sdata[curScene][5][i1][i2]
                let depth = 128 * (i1 + i2) + i2
                if save.sdata[curScene][1][i1][i2] > 0 {
                    builds.append((i1, i2, save.sdata[curScene][1][i1][i2] / 2, h4, depth))
                }
                if save.sdata[curScene][2][i1][i2] > 0 {
                    builds.append((i1, i2, save.sdata[curScene][2][i1][i2] / 2, h5, depth + 1))
                }
                let ev = save.sdata[curScene][3][i1][i2]
                if ev >= 0 {
                    let num = save.ddata[curScene][ev][5] / 2
                    if num > 0 { builds.append((i1, i2, num, h4, depth + 2)) }
                }
                if i1 == sx && i2 == sy {
                    let pic = Constants.beginWalkPic + sFace * 7 + sStep
                    builds.append((i1, i2, pic, h4, depth + 3))
                }
            }
        }
        builds.sort { $0.depth < $1.depth }
        for b in builds {
            let (px, py) = screenPos(x: b.x, y: b.y, cx: sx, cy: sy)
            blitS(b.pic, px, py - b.yoff, fb)
        }
        let name = save.scenes.indices.contains(curScene) ? save.scenes[curScene].name : ""
        drawMini(fb, x: sx, y: sy, name: name)
    }

    private func drawClouds(_ fb: Framebuffer) {
        for c in clouds {
            let x = c.x - (-mx * 18 + my * 18 + 8640 - Screen.cx)
            let y = c.y - (mx * 9 + my * 9 + 9 - Screen.cy)
            if x > -40 && x < Screen.width && y > -40 && y < Screen.height {
                if res.clouds.indices.contains(c.pic) {
                    fb.blit(res.clouds[c.pic], x: x, y: y)
                }
            }
        }
    }

    private func drawMini(_ fb: Framebuffer, x: Int, y: Int, name: String) {
        let label = name.isEmpty ? "(\(x),\(y))" : "\(name) (\(x),\(y))"
        let w = text.width(label) + 12
        fb.fill(Screen.width - w - 8, 8, w, 20, 0x08)
        fb.rect(Screen.width - w - 8, 8, w, 20, 0x30)
        text.draw(label, x: Screen.width - w - 2, y: 11, color: 0x70, shadow: 0x08, onto: fb)
    }

    private func drawOverlay(_ fb: Framebuffer) {
        switch overlay {
        case .none: break
        case .talk(let t, let head, let mode):
            let boxY = (mode == 1 || mode == 5) ? Screen.height - 130 : 20
            fb.fill(0, boxY, Screen.width, 120, 0)
            let headX = (mode == 1 || mode == 4) ? 546 : 40
            if head >= 0, res.heads.indices.contains(head), mode != 2 {
                fb.blit(res.heads[head], x: headX, y: boxY + 20)
            }
            let tx = (mode == 1 || mode == 4) ? 20 : 110
            var ly = boxY + 16
            for line in t.split(separator: "\n") {
                text.draw(String(line), x: tx, y: ly, color: 0xFF, shadow: 0, onto: fb)
                ly += 22
            }
        case .confirm(let title, let options, let sel):
            panel(fb, title, options, sel, x: Screen.cx - 80, y: Screen.cy - 50)
        case .message(let s):
            let w = min(400, text.width(s) + 24)
            let h = 40 + s.split(separator: "\n").count * 18
            let x = Screen.cx - w / 2
            let y = 90
            fb.fill(x, y, w, h, 0)
            fb.rect(x, y, w, h, 0xFF)
            var ly = y + 10
            for line in s.split(separator: "\n") {
                text.draw(String(line), x: x + 10, y: ly, color: 0x21, shadow: 0x23, onto: fb)
                ly += 18
            }
        case .menu(let title, let items, let sel, _):
            panel(fb, title, items, sel, x: 40, y: 40)
        case .status(let role):
            drawStatus(fb, role)
        case .items(let sel, _):
            drawItems(fb, sel)
        case .shop(let index, let sel):
            drawShop(fb, index, sel)
        case .nameEntry(let name):
            fb.fill(Screen.cx - 90, Screen.cy - 40, 180, 70, 0)
            fb.rect(Screen.cx - 90, Screen.cy - 40, 180, 70, 0x21)
            text.draw("請輸入主角之姓名", x: Screen.cx - 80, y: Screen.cy - 30, color: 0x21, shadow: 0x23, onto: fb)
            text.draw(name, x: Screen.cx - 40, y: Screen.cy + 4, color: 0x05, shadow: 0x07, onto: fb)
        }
    }

    private func panel(_ fb: Framebuffer, _ title: String, _ items: [String], _ sel: Int, x: Int, y: Int) {
        let w = max(text.width(title), items.map { text.width($0) }.max() ?? 40) + 28
        let h = 28 + items.count * 20
        fb.fill(x, y, w, h, 0)
        fb.rect(x, y, w, h, 0xFF)
        text.draw(title, x: x + 8, y: y + 4, color: 0x21, shadow: 0x23, onto: fb)
        for (i, item) in items.enumerated() {
            let color: UInt8 = i == sel ? 0x64 : 0x05
            text.draw(item, x: x + 12, y: y + 24 + i * 20, color: color, shadow: 0x07, onto: fb)
        }
    }

    private func drawStatus(_ fb: Framebuffer, _ rnum: Int) {
        guard save.roles.indices.contains(rnum) else { return }
        let r = save.roles[rnum]
        fb.fill(40, 20, 560, 360, 0)
        fb.rect(40, 20, 560, 360, 0xFF)
        if res.heads.indices.contains(r.headId) { fb.blit(res.heads[r.headId], x: 60, y: 40) }
        func line(_ s: String, _ y: Int) {
            text.draw(s, x: 180, y: y, color: 0x21, shadow: 0x23, onto: fb)
        }
        line("\(r.name)  \(r.nick)", 40)
        line("等級 \(r.level)  經驗 \(r.exp)", 64)
        line("生命 \(r.hp)/\(r.maxHp)  內力 \(r.mp)/\(r.maxMp)", 88)
        line("攻擊 \(r.attack)  防禦 \(r.defence)  輕功 \(r.speed)", 112)
        line("拳掌 \(r.fist)  御劍 \(r.sword)  耍刀 \(r.blade)", 136)
        line("特殊 \(r.special)  暗器 \(r.throwing)", 160)
        line("醫療 \(r.medic)  用毒 \(r.poison)  解毒 \(r.depoison)", 184)
        line("拳掌武學常識 \(r.knowledge)  品德 \(r.integrity)  聲望 \(r.reputation)", 208)
        line("資質 \(r.potential)  體力 \(r.stamina)  內傷 \(r.hurt)  中毒 \(r.poisoned)", 232)
        var y = 260
        for i in 0..<10 {
            let sid = r.skillId(i)
            if sid >= 0, save.magics.indices.contains(sid) {
                text.draw("\(save.magics[sid].name) \(r.skillLevel(i) / 100 + 1)級", x: 180, y: y, color: 0x05, shadow: 0x07, onto: fb)
                y += 18
            }
        }
    }

    private func drawItems(_ fb: Framebuffer, _ sel: Int) {
        let ids = save.base.bag.filter { $0.id >= 0 }
        fb.fill(60, 30, 520, 340, 0)
        fb.rect(60, 30, 520, 340, 0xFF)
        text.draw("物品  銀兩 \(save.money())", x: 80, y: 40, color: 0x21, shadow: 0x23, onto: fb)
        for (i, slot) in ids.enumerated() {
            guard save.items.indices.contains(slot.id) else { continue }
            let color: UInt8 = i == sel ? 0x64 : 0x05
            text.draw("\(save.items[slot.id].name) x\(slot.count)", x: 90, y: 70 + i * 18, color: color, shadow: 0x07, onto: fb)
            if i > 14 { break }
        }
        if ids.indices.contains(sel), save.items.indices.contains(ids[sel].id) {
            text.draw(save.items[ids[sel].id].desc, x: 80, y: 330, color: 0x70, shadow: 0x08, onto: fb)
        }
    }

    private func drawShop(_ fb: Framebuffer, _ index: Int, _ sel: Int) {
        guard save.shops.indices.contains(index) else { return }
        fb.fill(120, 80, 400, 200, 0)
        fb.rect(120, 80, 400, 200, 0xFF)
        text.draw("商店  銀兩 \(save.money())", x: 140, y: 90, color: 0x21, shadow: 0x23, onto: fb)
        for i in 0..<5 {
            let id = save.shops[index].item(i)
            let amt = save.shops[index].amount(i)
            let price = save.shops[index].price(i)
            let name = save.items.indices.contains(id) ? save.items[id].name : "——"
            let color: UInt8 = i == sel ? 0x64 : 0x05
            text.draw("\(name)  \(price)兩  x\(amt)", x: 150, y: 120 + i * 22, color: color, shadow: 0x07, onto: fb)
        }
    }

    func picM(_ id: Int) -> Pic {
        res.mmap.indices.contains(id) ? res.mmap[id] : Pic()
    }

    func blitM(_ id: Int, _ x: Int, _ y: Int, _ fb: Framebuffer) {
        if res.mmap.indices.contains(id) { fb.blit(res.mmap[id], x: x, y: y) }
    }

    func blitS(_ id: Int, _ x: Int, _ y: Int, _ fb: Framebuffer) {
        if res.smap.indices.contains(id) { fb.blit(res.smap[id], x: x, y: y) }
    }

    func blitW(_ id: Int, _ x: Int, _ y: Int, _ fb: Framebuffer) {
        if res.wmap.indices.contains(id) { fb.blit(res.wmap[id], x: x, y: y) }
    }
}

extension Game {
    var waitActive: Bool {
        if case .none = wait { return false }
        return true
    }
}

private extension Overlay {
    var isNone: Bool {
        if case .none = self { return true }
        return false
    }
}
