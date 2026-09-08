import Foundation

extension Game {
    func callEvent(_ num: Int) {
        guard res.kdef.indices.contains(num) else { return }
        scripts.append(ScriptFrame(code: res.kdef[num], pc: 0))
        sStep = 0
        runScript()
    }

    func runScript() {
        while !waitActive && !scripts.isEmpty {
            if !stepScript() { scripts.removeLast() }
        }
    }

    @discardableResult
    private func stepScript() -> Bool {
        guard var frame = scripts.last else { return false }
        let e = frame.code
        var i = frame.pc
        if i >= e.count { return false }
        let op = e[i]
        if op < 0 { return false }
        var pause = false
        switch op {
            case 0: instruct0(); i += 1
            case 1:
                instruct1(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4; pause = true
            case 2:
                instruct2(arg(e, i, 1), arg(e, i, 2)); i += 3; pause = true
            case 3:
                var list = (0..<13).map { arg(e, i, 1 + $0) }
                instruct3(&list); i += 14
            case 4:
                i += instruct4(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 5:
                askConfirm("是否與之戰鬥？", yes: arg(e, i, 1), no: arg(e, i, 2), skip: 0)
                i += 3; pause = true
            case 6:
                _ = instruct6(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4))
                i += 5; pause = true
            case 7:
                i += 1
                scripts[scripts.count - 1].pc = i
                return false
            case 8:
                exitSceneMusic = arg(e, i, 1); i += 2
            case 9:
                askConfirm("是否要求加入？", yes: arg(e, i, 1), no: arg(e, i, 2), skip: 0)
                i += 3; pause = true
            case 10:
                instruct10(arg(e, i, 1)); i += 2
            case 11:
                askConfirm("是否休息一晚？", yes: arg(e, i, 1), no: arg(e, i, 2), skip: 0)
                i += 3; pause = true
            case 12:
                instruct12(); i += 1
            case 13:
                instruct13(); i += 1
            case 14:
                instruct14(); i += 1
            case 15:
                instruct15(); i += 1
                scripts[scripts.count - 1].pc = i
                return false
            case 16:
                i += instruct16(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 17:
                instruct17(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5)); i += 6
            case 18:
                i += instruct18(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 19:
                instruct19(arg(e, i, 1), arg(e, i, 2)); i += 3
            case 20:
                i += instruct20(arg(e, i, 1), arg(e, i, 2)); i += 3
            case 21:
                instruct21(arg(e, i, 1)); i += 2
            case 22:
                instruct22(); i += 1
            case 23:
                if save.roles.indices.contains(arg(e, i, 1)) {
                    save.roles[arg(e, i, 1)].poison = arg(e, i, 2)
                }
                i += 3
            case 24: i += 1
            case 25:
                instruct25(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4)); i += 5
            case 26:
                instruct26(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5)); i += 6
            case 27:
                instruct27(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 28:
                i += instructRange(save.roles.indices.contains(arg(e, i, 1)) ? save.roles[arg(e, i, 1)].integrity : 0,
                                   arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5)); i += 6
            case 29:
                i += instructRange(save.roles.indices.contains(arg(e, i, 1)) ? save.roles[arg(e, i, 1)].attack : 0,
                                   arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5)); i += 6
            case 30:
                instruct30(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4)); i += 5
            case 31:
                i += instruct31(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 32:
                instruct32(arg(e, i, 1), arg(e, i, 2)); i += 3
            case 33:
                instruct33(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 34:
                if save.roles.indices.contains(arg(e, i, 1)) {
                    save.roles[arg(e, i, 1)].potential += arg(e, i, 2)
                }
                i += 3
            case 35:
                instruct35(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4)); i += 5
            case 36:
                i += instruct36(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 37:
                if !save.roles.isEmpty { save.roles[0].integrity += arg(e, i, 1) }
                i += 2
            case 38:
                instruct38(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4)); i += 5
            case 39:
                if save.scenes.indices.contains(arg(e, i, 1)) {
                    save.scenes[arg(e, i, 1)].enterCondition = 0
                    save.rebuildEntrance()
                }
                i += 2
            case 40:
                sFace = arg(e, i, 1); mFace = sFace; i += 2
            case 41:
                instruct41(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 42:
                i += instruct42(arg(e, i, 1), arg(e, i, 2)); i += 3
            case 43:
                i += instruct18(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3)); i += 4
            case 44:
                instruct44(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5), arg(e, i, 6)); i += 7
            case 45:
                if save.roles.indices.contains(arg(e, i, 1)) { save.roles[arg(e, i, 1)].speed += arg(e, i, 2) }
                i += 3
            case 46:
                if save.roles.indices.contains(arg(e, i, 1)) { save.roles[arg(e, i, 1)].maxMp += arg(e, i, 2) }
                i += 3
            case 47:
                if save.roles.indices.contains(arg(e, i, 1)) { save.roles[arg(e, i, 1)].attack += arg(e, i, 2) }
                i += 3
            case 48:
                if save.roles.indices.contains(arg(e, i, 1)) { save.roles[arg(e, i, 1)].maxHp += arg(e, i, 2) }
                i += 3
            case 49:
                if save.roles.indices.contains(arg(e, i, 1)) { save.roles[arg(e, i, 1)].mpType = arg(e, i, 2) }
                i += 3
            case 50:
                let list = (0..<7).map { arg(e, i, 1 + $0) }
                let p = instruct50(list)
                i += 8
                if p < 622592 { i += p }
            case 51:
                instruct1(Constants.softstarTalk + rng.rnd(Constants.softstarTalkCount), 0x72, 0); i += 1; pause = true
            case 52:
                if !save.roles.isEmpty { showMessage("你的品德指數為：\(save.roles[0].integrity)") }
                i += 1; pause = true
            case 53:
                if !save.roles.isEmpty { showMessage("你的聲望指數為：\(save.roles[0].reputation)") }
                i += 1; pause = true
            case 54:
                for s in save.scenes.indices { save.scenes[s].enterCondition = 0 }
                save.rebuildEntrance(); i += 1
            case 55:
                i += instruct55(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4)); i += 5
            case 56:
                if !save.roles.isEmpty { save.roles[0].reputation += arg(e, i, 1) }
                i += 2
            case 57:
                instruct27(-1, 3832 * 2, 3844 * 2); i += 1
            case 58:
                i += 1
            case 59:
                for t in 1..<Constants.teamCount { save.base.team[t] = -1 }
                i += 1
            case 60:
                i += instruct60(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5)); i += 6
            case 61:
                i += instruct61(arg(e, i, 1), arg(e, i, 2)); i += 3
            case 62:
                instruct62(arg(e, i, 1), arg(e, i, 2), arg(e, i, 3), arg(e, i, 4), arg(e, i, 5), arg(e, i, 6)); i += 7
                scripts[scripts.count - 1].pc = i
                return false
            case 63:
                if save.roles.indices.contains(arg(e, i, 1)) { save.roles[arg(e, i, 1)].sex = arg(e, i, 2) }
                i += 3
            case 64:
                overlay = .shop(index: 0, selection: 0)
                wait = .dismiss
                i += 1; pause = true
            case 65: i += 1
            case 66:
                audio.playMusic(arg(e, i, 1)); i += 2
            case 67:
                audio.playEffect(arg(e, i, 1)); i += 2
            default:
                i += 1
            }
        scripts[scripts.count - 1].pc = i
        needRefresh = true
        if pause { return true }
        return i < e.count
    }

    private func arg(_ e: [Int], _ i: Int, _ d: Int) -> Int {
        let j = i + d
        return j < e.count ? e[j] : 0
    }

    func instruct0() {}

    func instruct1(_ talk: Int, _ head: Int, _ mode: Int) {
        let t = res.talks.indices.contains(talk) ? res.talks[talk] : ""
        showTalk(t, head: head, mode: mode)
    }

    func instruct2(_ inum: Int, _ amount: Int) {
        instruct32(inum, amount)
        let name = save.items.indices.contains(inum) ? save.items[inum].name : "物品"
        let word = amount >= 0 ? "得到物品" : "失去物品"
        showMessage("\(word)\n\(name) x\(abs(amount))")
    }

    func instruct3(_ list: inout [Int]) {
        if list[0] == -2 { list[0] = curScene }
        if list[1] == -2 { list[1] = curEvent }
        let s = list[0], ev = list[1]
        guard save.ddata.indices.contains(s), ev >= 0, ev < Constants.subMapEvents else { return }
        if list[11] == -2 { list[11] = save.ddata[s][ev][9] }
        if list[12] == -2 { list[12] = save.ddata[s][ev][10] }
        let oldx = save.ddata[s][ev][10]
        let oldy = save.ddata[s][ev][9]
        if sceneInBounds(s, oldx, oldy) {
            save.sdata[s][3][oldx][oldy] = -1
        }
        for i in 0...10 {
            if list[2 + i] != -2 {
                save.ddata[s][ev][i] = list[2 + i]
            }
        }
        let nx = save.ddata[s][ev][10]
        let ny = save.ddata[s][ev][9]
        if sceneInBounds(s, nx, ny) {
            save.sdata[s][3][nx][ny] = ev
        }
    }

    func instruct4(_ inum: Int, _ j1: Int, _ j2: Int) -> Int { inum == curItem ? j1 : j2 }
    func instruct6(_ battle: Int, _ j1: Int, _ j2: Int, _ getexp: Int) -> Int {
        lastBattleWon = false
        startBattle(battle, getExp: getexp != 0)
        wait = .battle(yes: j1, no: j2)
        return 0
    }

    func instruct10(_ rnum: Int) {
        save.join(rnum)
        if save.roles.indices.contains(rnum) {
            for i in 0..<4 {
                let id = save.roles[rnum].takingItem(i)
                let amt = save.roles[rnum].takingCount(i)
                if id >= 0 && amt > 0 { instruct2(id, amt) }
            }
        }
    }

    func instruct11(_ j1: Int, _ j2: Int) -> Int { j2 }

    func instruct12() {
        for id in save.base.team where id >= 0 && save.roles.indices.contains(id) {
            save.roles[id].hp = save.roles[id].maxHp
            save.roles[id].mp = save.roles[id].maxMp
            save.roles[id].stamina = Constants.staminaMax
            save.roles[id].hurt = 0
            save.roles[id].poisoned = 0
        }
    }

    func instruct13() {}
    func instruct14() {}

    func instruct15() {
        whereMode = .dead
        showMessage("功力盡失")
        whereMode = .title
        audio.playMusic(16)
    }

    func instruct16(_ rnum: Int, _ j1: Int, _ j2: Int) -> Int {
        save.base.team.contains(rnum) ? j1 : j2
    }

    func instruct17(_ s: Int, _ layer: Int, _ x: Int, _ y: Int, _ v: Int) {
        let scene = s == -2 ? curScene : s
        let xx = x == -2 ? sx : x
        let yy = y == -2 ? sy : y
        if save.sdata.indices.contains(scene), layer >= 0, layer < 6, sceneInBounds(scene, xx, yy) {
            save.sdata[scene][layer][xx][yy] = v
        }
    }

    func instruct18(_ inum: Int, _ j1: Int, _ j2: Int) -> Int { save.hasItem(inum) ? j1 : j2 }

    func instruct19(_ x: Int, _ y: Int) {
        sx = x; sy = y
    }

    func instruct20(_ j1: Int, _ j2: Int) -> Int { save.teamFull() ? j1 : j2 }

    func instruct21(_ rnum: Int) { save.leave(rnum) }

    func instruct22() {
        for id in save.base.team where id >= 0 && save.roles.indices.contains(id) {
            save.roles[id].mp = 0
        }
    }

    func instruct25(_ x1: Int, _ y1: Int, _ x2: Int, _ y2: Int) {
        sx = x2; sy = y2
    }

    func instruct26(_ snum: Int, _ en: Int, _ a1: Int, _ a2: Int, _ a3: Int) {
        let s = snum == -2 ? curScene : snum
        guard save.ddata.indices.contains(s), en >= 0, en < Constants.subMapEvents else { return }
        save.ddata[s][en][2] += a1
        save.ddata[s][en][3] += a2
        save.ddata[s][en][4] += a3
    }

    func instruct27(_ en: Int, _ beginPic: Int, _ endPic: Int) {
        let ev = en == -1 ? curEvent : en
        guard curScene >= 0, save.ddata.indices.contains(curScene), ev >= 0 else { return }
        var pic = beginPic
        while pic <= endPic {
            save.ddata[curScene][ev][5] = pic
            pic += 2
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.06))
        }
        save.ddata[curScene][ev][5] = endPic
    }

    func instructRange(_ value: Int, _ a: Int, _ b: Int, _ j1: Int, _ j2: Int) -> Int {
        (value >= a && value <= b) ? j1 : j2
    }

    func instruct30(_ x1: Int, _ y1: Int, _ x2: Int, _ y2: Int) {
        sx = x1; sy = y1
        let dx = x2 > x1 ? 1 : (x2 < x1 ? -1 : 0)
        let dy = y2 > y1 ? 1 : (y2 < y1 ? -1 : 0)
        while sx != x2 || sy != y2 {
            if sx != x2 { sx += dx }
            if sy != y2 { sy += dy }
            sStep = (sStep + 1) % 7
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.05))
        }
    }

    func instruct31(_ money: Int, _ j1: Int, _ j2: Int) -> Int { save.money() >= money ? j1 : j2 }

    func instruct32(_ inum: Int, _ amount: Int) { save.addItem(inum, amount) }

    func instruct33(_ rnum: Int, _ magic: Int, _ _: Int) {
        guard save.roles.indices.contains(rnum) else { return }
        for i in 0..<10 {
            if save.roles[rnum].skillId(i) < 0 {
                save.roles[rnum].setSkillId(i, magic)
                save.roles[rnum].setSkillLevel(i, 0)
                return
            }
            if save.roles[rnum].skillId(i) == magic { return }
        }
    }

    func instruct35(_ rnum: Int, _ slot: Int, _ magic: Int, _ exp: Int) {
        guard save.roles.indices.contains(rnum), slot >= 0, slot < 10 else { return }
        save.roles[rnum].setSkillId(slot, magic)
        save.roles[rnum].setSkillLevel(slot, exp)
    }

    func instruct36(_ sexual: Int, _ j1: Int, _ j2: Int) -> Int {
        (!save.roles.isEmpty && save.roles[0].sex == sexual) ? j1 : j2
    }

    func instruct38(_ snum: Int, _ layer: Int, _ oldpic: Int, _ newpic: Int) {
        let s = snum == -2 ? curScene : snum
        guard save.sdata.indices.contains(s), layer >= 0, layer < 6 else { return }
        for x in 0..<64 {
            for y in 0..<64 {
                if save.sdata[s][layer][x][y] == oldpic {
                    save.sdata[s][layer][x][y] = newpic
                }
            }
        }
    }

    func instruct41(_ rnum: Int, _ inum: Int, _ amount: Int) {
        guard save.roles.indices.contains(rnum) else { return }
        for i in 0..<4 {
            if save.roles[rnum].takingItem(i) == inum {
                save.roles[rnum].setTakingCount(i, max(0, save.roles[rnum].takingCount(i) + amount))
                return
            }
        }
        for i in 0..<4 where save.roles[rnum].takingItem(i) < 0 {
            save.roles[rnum].setTakingItem(i, inum)
            save.roles[rnum].setTakingCount(i, amount)
            return
        }
    }

    func instruct42(_ j1: Int, _ j2: Int) -> Int {
        for id in save.base.team where id >= 0 && save.roles.indices.contains(id) && save.roles[id].sex == 1 {
            return j1
        }
        return j2
    }

    func instruct44(_ e1: Int, _ b1: Int, _ end1: Int, _ e2: Int, _ b2: Int, _ end2: Int) {
        instruct27(e1, b1, end1)
        instruct27(e2, b2, end2)
    }

    func instruct50(_ list: [Int]) -> Int {
        if list[0] > 128 {
            var p = 0
            for i in 0..<5 { p += instruct18(list[i], 1, 0) }
            return p == 5 ? list[5] : list[6]
        }
        instruct50e(list[0], list[1], list[2], list[3], list[4], list[5], list[6])
        return 0
    }

    func instruct50e(_ code: Int, _ e1: Int, _ e2: Int, _ e3: Int, _ e4: Int, _ e5: Int, _ e6: Int) {
        switch code {
        case 0: if x50.indices.contains(e1) { x50[e1] = e2 }
        case 3:
            if x50.indices.contains(e3) && x50.indices.contains(e4) {
                switch e2 {
                case 0: x50[e3] = x50[e4] + e5
                case 1: x50[e3] = x50[e4] - e5
                case 2: x50[e3] = x50[e4] * e5
                case 3: if e5 != 0 { x50[e3] = x50[e4] / e5 }
                default: break
                }
            }
        case 5: x50 = [Int](repeating: 0, count: 0x8000)
        case 16:
            if e3 >= 0 {
                switch e2 {
                case 0: if save.roles.indices.contains(e3) { save.roles[e3][e4 / 2] = e5 }
                case 1: if save.items.indices.contains(e3) { save.items[e3][e4 / 2] = e5 }
                default: break
                }
            }
        default: break
        }
        _ = e6
    }

    func instruct55(_ en: Int, _ value: Int, _ j1: Int, _ j2: Int) -> Int {
        guard curScene >= 0, save.ddata.indices.contains(curScene), en >= 0 else { return j2 }
        return save.ddata[curScene][en][2] == value ? j1 : j2
    }

    func instruct60(_ s: Int, _ x: Int, _ y: Int, _ pic: Int, _ j1: Int) -> Int {
        let scene = s == -2 ? curScene : s
        if save.sdata.indices.contains(scene), sceneInBounds(scene, x, y), save.sdata[scene][0][x][y] == pic {
            return j1
        }
        return 0
    }

    func instruct61(_ j1: Int, _ _: Int) -> Int {
        var books = 0
        for slot in save.base.bag where slot.id >= 144 && slot.id <= 157 { books += 1 }
        return books >= 14 ? j1 : 0
    }

    func instruct62(_ x1: Int, _ y1: Int, _ _: Int, _ _: Int, _ _: Int, _ _: Int) {
        mx = x1; my = y1
        leaveScene()
    }

    private func sceneInBounds(_ s: Int, _ x: Int, _ y: Int) -> Bool {
        save.sdata.indices.contains(s) && x >= 0 && y >= 0 && x < 64 && y < 64
    }
}
