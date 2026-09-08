import Foundation

extension Game {
    func startBattle(_ id: Int, getExp: Bool) {
        guard res.wars.indices.contains(id) else {
            lastBattleWon = true
            return
        }
        currentWar = id
        battleGetExp = getExp ? 1 : 0
        let war = res.wars[id]
        battleRoles = []
        for i in 0..<Constants.teamCount {
            let rnum = save.base.team[i]
            if rnum >= 0 {
                battleRoles.append(BattleRole(rnum: rnum, team: 0, y: war.teamY(i), x: war.teamX(i), face: 0))
            }
        }
        for i in 0..<Constants.warEnemies {
            let rnum = war.enemy(i)
            if rnum >= 0 {
                battleRoles.append(BattleRole(rnum: rnum, team: 1, y: war.enemyY(i), x: war.enemyX(i), face: 2))
            }
        }
        let fieldId = war.fieldId
        if res.warFields.indices.contains(fieldId) {
            battleField = []
            let layer = res.warFields[fieldId][0]
            for x in 0..<64 {
                var col = [Int](repeating: 0, count: 64)
                for y in 0..<64 { col[y] = layer[x * 64 + y] }
                battleField.append(col)
            }
        }
        whereMode = .battle
        audio.playMusic(war.music)
        beginBattleRound()
    }

    func driveBattle() {
        guard whereMode == .battle else { return }
        if overlay.isNone && !battleSelecting {
            nextBattleActor()
        }
    }

    private func beginBattleRound() {
        sortBattle()
        for i in battleRoles.indices where battleRoles[i].dead == 0 {
            let spd = roleSpeed(battleRoles[i].rnum)
            battleRoles[i].step = max(0, spd / 15 - (save.roles.indices.contains(battleRoles[i].rnum) ? save.roles[battleRoles[i].rnum].hurt / 40 : 0))
            battleRoles[i].acted = 0
        }
        nextBattleActor()
    }

    private func nextBattleActor() {
        guard whereMode == .battle else { return }
        if let i = battleRoles.indices.first(where: { battleRoles[$0].dead == 0 && battleRoles[$0].acted == 0 }) {
            battleActor = i
            battleMoved = false
            if battleRoles[i].team == 0 {
                playerTurn(i)
            } else {
                aiTurn(i)
                battleRoles[i].acted = 1
                finishActor()
            }
            return
        }
        endRound()
        if settleBattle() {
            finishBattle()
        } else {
            beginBattleRound()
        }
    }

    private func finishActor() {
        if settleBattle() {
            finishBattle()
        }
    }

    private func finishBattle() {
        lastBattleWon = battleRoles.contains { $0.team == 0 && $0.dead == 0 }
        if lastBattleWon && battleGetExp != 0, res.wars.indices.contains(currentWar) {
            awardExp(res.wars[currentWar].exp)
        }
        audio.playMusic(16)
        overlay = .none
        whereMode = curScene >= 0 ? .scene : .world
    }

    private func sortBattle() {
        for i in 0..<battleRoles.count {
            for j in (i + 1)..<battleRoles.count {
                if roleSpeed(battleRoles[j].rnum) > roleSpeed(battleRoles[i].rnum) {
                    battleRoles.swapAt(i, j)
                }
            }
        }
    }

    private func roleSpeed(_ rnum: Int) -> Int {
        guard save.roles.indices.contains(rnum) else { return 0 }
        var s = save.roles[rnum].speed
        for e in 0..<2 {
            let id = save.roles[rnum].equip(e)
            if id >= 0, save.items.indices.contains(id) { s += save.items[id].addSpeed }
        }
        return s
    }

    private func playerTurn(_ i: Int) {
        battleCursorX = battleRoles[i].x
        battleCursorY = battleRoles[i].y
        overlay = .menu(
            title: "戰鬥",
            items: battleMenuItems(i),
            selection: 0,
            tag: .battle
        )
    }

    func battleMenuItems(_ i: Int) -> [String] {
        guard save.roles.indices.contains(battleRoles[i].rnum) else { return ["等待"] }
        let r = save.roles[battleRoles[i].rnum]
        var items = ["等待", "狀態"]
        if r.stamina > 5 && battleRoles[i].step > 0 { items.insert("移動", at: 0) }
        if r.stamina > 10 { items.insert("武功", at: items.contains("移動") ? 1 : 0) }
        items.append(contentsOf: ["用毒", "解毒", "醫療", "物品", "休息", "自動", "逃跑"])
        return items
    }

    func handleBattleKey(_ key: Key) {
        if case .menu(_, let items, var sel, .battle) = overlay {
            switch key {
            case .up: sel = (sel + items.count - 1) % items.count
            case .down: sel = (sel + 1) % items.count
            case .ok: handleBattleMenuByName(items[sel]); return
            case .cancel:
                battleRoles[battleActor].acted = 1
                overlay = .none
                return
            default: break
            }
            overlay = .menu(title: "戰鬥", items: items, selection: sel, tag: .battle)
            return
        }
        if battleSelecting {
            var x = battleCursorX, y = battleCursorY
            switch key {
            case .up: x -= 1
            case .down: x += 1
            case .left: y -= 1
            case .right: y += 1
            case .ok:
                if battleMoving {
                    tryMoveActor(toX: x, toY: y)
                } else {
                    tryAttack(atX: x, atY: y)
                }
                battleSelecting = false
            case .cancel:
                battleSelecting = false
            default: break
            }
            battleCursorX = min(63, max(0, x))
            battleCursorY = min(63, max(0, y))
        }
    }

    func handleBattleMenu(_ sel: Int) {
        if case .menu(_, let items, _, .battle) = overlay, items.indices.contains(sel) {
            handleBattleMenuByName(items[sel])
        }
    }

    private func handleBattleMenuByName(_ name: String) {
        let i = battleActor
        switch name {
        case "移動":
            overlay = .none
            battleMoving = true
            battleSelecting = true
            fillMoveRange(i)
        case "武功":
            overlay = .none
            battleMoving = false
            battleSelecting = true
            fillAttackRange(i)
        case "等待":
            battleRoles[i].acted = 1
            overlay = .none
        case "狀態":
            overlay = .status(role: battleRoles[i].rnum)
        case "休息":
            restActor(i)
            battleRoles[i].acted = 1
            overlay = .none
        case "物品":
            overlay = .items(selection: 0, using: true)
        case "用毒", "解毒", "醫療":
            overlay = .none
            battleSelecting = true
            battleMoving = false
        case "自動":
            aiTurn(i)
            overlay = .none
        case "逃跑":
            if rng.rnd(100) < 50 {
                showMessage("逃走成功")
                whereMode = .scene
                battleRoles[i].acted = 1
            } else {
                showMessage("逃走失敗")
                battleRoles[i].acted = 1
            }
            overlay = .none
        default:
            battleRoles[i].acted = 1
            overlay = .none
        }
    }

    private func fillMoveRange(_ i: Int) {
        battleRange.removeAll()
        let steps = battleRoles[i].step
        let ox = battleRoles[i].x
        let oy = battleRoles[i].y
        for x in 0..<64 {
            for y in 0..<64 {
                if abs(x - ox) + abs(y - oy) <= steps { battleRange.insert(x * 64 + y) }
            }
        }
    }

    private func fillAttackRange(_ i: Int) {
        battleRange.removeAll()
        guard save.roles.indices.contains(battleRoles[i].rnum) else { return }
        let r = save.roles[battleRoles[i].rnum]
        var range = 1
        for s in 0..<10 {
            let id = r.skillId(s)
            if id >= 0, save.magics.indices.contains(id) {
                let lv = min(9, r.skillLevel(s) / 100)
                range = max(range, save.magics[id].moveDistance(lv))
            }
        }
        let ox = battleRoles[i].x
        let oy = battleRoles[i].y
        for x in 0..<64 {
            for y in 0..<64 {
                if abs(x - ox) + abs(y - oy) <= range { battleRange.insert(x * 64 + y) }
            }
        }
    }

    private func tryMoveActor(toX x: Int, toY y: Int) {
        let i = battleActor
        if battleRange.contains(x * 64 + y), occupant(x, y) < 0 {
            battleRoles[i].x = x
            battleRoles[i].y = y
            battleMoved = true
            battleRoles[i].step = 0
        }
        overlay = .menu(title: "戰鬥", items: battleMenuItems(i), selection: 0, tag: .battle)
    }

    private func tryAttack(atX x: Int, atY y: Int) {
        let i = battleActor
        let target = occupant(x, y)
        guard target >= 0, battleRoles[target].team != battleRoles[i].team else {
            overlay = .menu(title: "戰鬥", items: battleMenuItems(i), selection: 0, tag: .battle)
            return
        }
        performAttack(from: i, to: target)
        battleRoles[i].acted = 1
        overlay = .none
    }

    private func occupant(_ x: Int, _ y: Int) -> Int {
        battleRoles.firstIndex { $0.dead == 0 && $0.x == x && $0.y == y } ?? -1
    }

    private func performAttack(from a: Int, to b: Int) {
        let r1 = battleRoles[a].rnum
        let r2 = battleRoles[b].rnum
        guard save.roles.indices.contains(r1), save.roles.indices.contains(r2) else { return }
        var magic = 0
        var level = 0
        for s in 0..<10 {
            let id = save.roles[r1].skillId(s)
            if id >= 0 {
                magic = id
                level = min(9, save.roles[r1].skillLevel(s) / 100)
                break
            }
        }
        let dmg = calHurt(a, b, magic, level)
        save.roles[r2].hp -= dmg
        save.roles[r2].hurt = min(99, save.roles[r2].hurt + dmg / 10)
        save.roles[r1].stamina = max(0, save.roles[r1].stamina - 3)
        save.roles[r1].exp += dmg / 5
        if save.roles[r2].hp <= 0 {
            save.roles[r2].hp = 0
            battleRoles[b].dead = 1
            save.roles[r1].exp += save.roles[r2].level * 10
        }
        battleRoles[b].showNumber = dmg
        if save.magics.indices.contains(magic) {
            audio.playAttack(save.magics[magic].soundNum)
        }
        showMessage("\(save.roles[r1].name) 對 \(save.roles[r2].name) 造成 \(dmg) 傷害")
    }

    private func calHurt(_ a: Int, _ b: Int, _ mnum: Int, _ level: Int) -> Int {
        let r1 = battleRoles[a].rnum
        let r2 = battleRoles[b].rnum
        var k1 = 0, k2 = 0
        for br in battleRoles where br.dead == 0 && save.roles.indices.contains(br.rnum) {
            if save.roles[br.rnum].knowledge > Constants.knowledgeBarrier {
                if br.team == battleRoles[a].team { k1 += save.roles[br.rnum].knowledge }
                if br.team == battleRoles[b].team { k2 += save.roles[br.rnum].knowledge }
            }
        }
        var mhurt = 0
        if level > 0, save.magics.indices.contains(mnum) {
            mhurt = save.magics[mnum].attack(level - 1)
        }
        var att = save.roles[r1].attack + k1 * 3 / 2 + mhurt / 3
        var def = save.roles[r2].defence * 2 + k2 * 3
        if save.magics.indices.contains(mnum) {
            switch save.magics[mnum].magicType {
            case 1: att += save.roles[r1].fist; def += save.roles[r2].fist
            case 2: att += save.roles[r1].sword; def += save.roles[r2].sword
            case 3: att += save.roles[r1].blade; def += save.roles[r2].blade
            case 4: att += save.roles[r1].special; def += save.roles[r2].special
            default: break
            }
        }
        att = att * (100 - save.roles[r1].hurt / 2) / 100
        def = def * (100 - save.roles[r2].hurt / 2) / 100
        if save.roles[r1].equip(0) >= 0, save.items.indices.contains(save.roles[r1].equip(0)) {
            att += save.items[save.roles[r1].equip(0)].addAttack
        }
        if save.roles[r1].equip(1) >= 0, save.items.indices.contains(save.roles[r1].equip(1)) {
            att += save.items[save.roles[r1].equip(1)].addAttack
        }
        if save.roles[r2].equip(0) >= 0, save.items.indices.contains(save.roles[r2].equip(0)) {
            def += save.items[save.roles[r2].equip(0)].addDefence
        }
        if save.roles[r2].equip(1) >= 0, save.items.indices.contains(save.roles[r2].equip(1)) {
            def += save.items[save.roles[r2].equip(1)].addDefence
        }
        var result = att - def + rng.rnd(20) - rng.rnd(20)
        var dis = abs(battleRoles[a].x - battleRoles[b].x) + abs(battleRoles[a].y - battleRoles[b].y)
        if dis > 10 { dis = 10 }
        result = max(result, att / 10 + rng.rnd(10) - rng.rnd(10))
        result = result * (100 - (dis - 1) * 3) / 100
        if result <= 0 || level <= 0 { result = rng.rnd(10) + 1 }
        return min(result, 9999)
    }

    private func restActor(_ i: Int) {
        let rnum = battleRoles[i].rnum
        guard save.roles.indices.contains(rnum) else { return }
        save.roles[rnum].stamina = min(100, save.roles[rnum].stamina + rng.rnd(3) + (battleMoved ? 2 : 3))
        if save.roles[rnum].stamina >= 30 {
            save.roles[rnum].hp = min(save.roles[rnum].maxHp, save.roles[rnum].hp + rng.rnd(max(1, save.roles[rnum].stamina / 10 - 2)) + 3)
            save.roles[rnum].mp = min(save.roles[rnum].maxMp, save.roles[rnum].mp + rng.rnd(max(1, save.roles[rnum].stamina / 10 - 2)) + 3)
        }
    }

    private func aiTurn(_ i: Int) {
        var best = -1
        var bestD = 99
        for j in battleRoles.indices where battleRoles[j].dead == 0 && battleRoles[j].team != battleRoles[i].team {
            let d = abs(battleRoles[i].x - battleRoles[j].x) + abs(battleRoles[i].y - battleRoles[j].y)
            if d < bestD { bestD = d; best = j }
        }
        guard best >= 0 else { battleRoles[i].acted = 1; return }
        let tx = battleRoles[best].x
        let ty = battleRoles[best].y
        if abs(battleRoles[i].x - tx) + abs(battleRoles[i].y - ty) > 1 {
            if battleRoles[i].x < tx { battleRoles[i].x += 1 }
            else if battleRoles[i].x > tx { battleRoles[i].x -= 1 }
            else if battleRoles[i].y < ty { battleRoles[i].y += 1 }
            else if battleRoles[i].y > ty { battleRoles[i].y -= 1 }
        }
        if abs(battleRoles[i].x - battleRoles[best].x) + abs(battleRoles[i].y - battleRoles[best].y) <= 2 {
            performAttack(from: i, to: best)
        }
        battleRoles[i].acted = 1
    }

    private func settleBattle() -> Bool {
        let friends = battleRoles.contains { $0.team == 0 && $0.dead == 0 }
        let foes = battleRoles.contains { $0.team == 1 && $0.dead == 0 }
        if !friends { instruct15(); return true }
        if !foes { return true }
        return false
    }

    private func endRound() {
        for br in battleRoles where br.dead == 0 && save.roles.indices.contains(br.rnum) {
            let r = br.rnum
            if save.roles[r].hurt > 0 || save.roles[r].poisoned > 0 {
                save.roles[r].hp -= save.roles[r].hurt / 20
                save.roles[r].hp -= save.roles[r].poisoned / 10
                if save.roles[r].hp < 1 { save.roles[r].hp = 1 }
            }
        }
    }

    private func awardExp(_ base: Int) {
        for id in save.base.team where id >= 0 && save.roles.indices.contains(id) {
            save.roles[id].exp += base
            while save.roles[id].level < Constants.levelMax {
                let need = res.expTable.indices.contains(save.roles[id].level)
                    ? res.expTable[save.roles[id].level] : 9999
                if save.roles[id].exp >= need {
                    save.roles[id].exp -= need
                    save.roles[id].level += 1
                    save.roles[id].maxHp += save.roles[id].hpAddOnLevelUp
                    save.roles[id].hp = save.roles[id].maxHp
                    save.roles[id].maxMp += 4
                    save.roles[id].mp = save.roles[id].maxMp
                } else { break }
            }
        }
        showMessage("戰鬥勝利")
    }

    func drawBattle(_ fb: Framebuffer) {
        let ax = battleRoles.indices.contains(battleActor) ? battleRoles[battleActor].x : 32
        let ay = battleRoles.indices.contains(battleActor) ? battleRoles[battleActor].y : 32
        let widthRegion = Screen.cx / 36 + 3
        let sumRegion = Screen.cy / 9 + 2
        for sum in -sumRegion...(sumRegion + 12) {
            for i in -widthRegion...widthRegion {
                let i1 = ax + i + sum / 2
                let i2 = ay - i + (sum - sum / 2)
                guard i1 >= 0 && i1 < 64 && i2 >= 0 && i2 < 64 else { continue }
                let (px, py) = screenPos(x: i1, y: i2, cx: ax, cy: ay)
                let tile = battleField.indices.contains(i1) && battleField[i1].indices.contains(i2) ? battleField[i1][i2] / 2 : 0
                blitW(tile, px, py, fb)
                if battleSelecting && battleRange.contains(i1 * 64 + i2) {
                    fb.fill(px - 8, py - 4, 16, 8, 0x2A)
                }
            }
        }
        let sorted = battleRoles.indices.sorted {
            battleRoles[$0].x + battleRoles[$0].y < battleRoles[$1].x + battleRoles[$1].y
        }
        for idx in sorted where battleRoles[idx].dead == 0 {
            let br = battleRoles[idx]
            let (px, py) = screenPos(x: br.x, y: br.y, cx: ax, cy: ay)
            let pics = res.fightPics(save.roles.indices.contains(br.rnum) ? save.roles[br.rnum].headId : 0)
            if pics.indices.contains(0) {
                fb.blit(pics[0], x: px, y: py)
            } else {
                blitW(0, px, py, fb)
                text.draw(save.roles.indices.contains(br.rnum) ? String(save.roles[br.rnum].name.prefix(1)) : "?",
                          x: px - 8, y: py - 16, color: br.team == 0 ? 0x4F : 0x21, shadow: 0, onto: fb)
            }
            if save.roles.indices.contains(br.rnum) {
                let r = save.roles[br.rnum]
                let w = 24
                let hpW = max(1, r.maxHp == 0 ? 0 : w * r.hp / max(1, r.maxHp))
                fb.fill(px - 12, py - 28, w, 3, 0x08)
                fb.fill(px - 12, py - 28, hpW, 3, br.team == 0 ? 0x4F : 0x21)
            }
        }
        if battleSelecting {
            let (px, py) = screenPos(x: battleCursorX, y: battleCursorY, cx: ax, cy: ay)
            fb.rect(px - 10, py - 20, 20, 24, 0xFF)
        }
        if battleRoles.indices.contains(battleActor), save.roles.indices.contains(battleRoles[battleActor].rnum) {
            let r = save.roles[battleRoles[battleActor].rnum]
            text.draw("\(r.name) HP \(r.hp)/\(r.maxHp) MP \(r.mp)/\(r.maxMp)", x: 8, y: Screen.height - 18, color: 0x70, shadow: 0x08, onto: fb)
        }
    }
}
