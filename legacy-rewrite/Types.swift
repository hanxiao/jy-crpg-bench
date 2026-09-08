import Foundation

struct ItemSlot {
    var id: Int = -1
    var count: Int = 0
}

struct Role {
    var raw: [UInt8]
    static let wordCount = 91
    static let byteCount = wordCount * 2

    init() { raw = [UInt8](repeating: 0, count: Self.byteCount) }
    init(bytes: [UInt8]) {
        raw = bytes
        if raw.count < Self.byteCount {
            raw.append(contentsOf: [UInt8](repeating: 0, count: Self.byteCount - raw.count))
        }
    }

    subscript(word: Int) -> Int {
        get { Packed.i16(raw, word) }
        set { Packed.setI16(&raw, word, newValue) }
    }

    var id: Int { get { self[0] } set { self[0] = newValue } }
    var headId: Int { get { self[1] } set { self[1] = newValue } }
    var hpAddOnLevelUp: Int { get { self[2] } set { self[2] = newValue } }
    var name: String {
        get { Big5.decode(Array(raw[8..<18])) }
        set {
            let encoded = Big5.encode(newValue, width: 10)
            for i in 0..<10 { raw[8 + i] = encoded[i] }
        }
    }
    var nick: String { Big5.decode(Array(raw[18..<28])) }
    var sex: Int { get { self[14] } set { self[14] = newValue } }
    var level: Int { get { self[15] } set { self[15] = newValue } }
    var exp: Int { get { self[16] } set { self[16] = newValue } }
    var hp: Int { get { self[17] } set { self[17] = newValue } }
    var maxHp: Int { get { self[18] } set { self[18] = newValue } }
    var hurt: Int { get { self[19] } set { self[19] = newValue } }
    var poisoned: Int { get { self[20] } set { self[20] = newValue } }
    var stamina: Int { get { self[21] } set { self[21] = newValue } }
    var expForMakeItem: Int { get { self[22] } set { self[22] = newValue } }
    func equip(_ i: Int) -> Int { self[23 + i] }
    mutating func setEquip(_ i: Int, _ v: Int) { self[23 + i] = v }
    func frame(_ i: Int) -> Int { self[25 + i] }
    func frameDelay(_ i: Int) -> Int { self[30 + i] }
    var mpType: Int { get { self[40] } set { self[40] = newValue } }
    var mp: Int { get { self[41] } set { self[41] = newValue } }
    var maxMp: Int { get { self[42] } set { self[42] = newValue } }
    var attack: Int { get { self[43] } set { self[43] = newValue } }
    var speed: Int { get { self[44] } set { self[44] = newValue } }
    var defence: Int { get { self[45] } set { self[45] = newValue } }
    var medic: Int { get { self[46] } set { self[46] = newValue } }
    var poison: Int { get { self[47] } set { self[47] = newValue } }
    var depoison: Int { get { self[48] } set { self[48] = newValue } }
    var antipoison: Int { get { self[49] } set { self[49] = newValue } }
    var fist: Int { get { self[50] } set { self[50] = newValue } }
    var sword: Int { get { self[51] } set { self[51] = newValue } }
    var blade: Int { get { self[52] } set { self[52] = newValue } }
    var special: Int { get { self[53] } set { self[53] = newValue } }
    var throwing: Int { get { self[54] } set { self[54] = newValue } }
    var knowledge: Int { get { self[55] } set { self[55] = newValue } }
    var integrity: Int { get { self[56] } set { self[56] = newValue } }
    var poisonAmp: Int { get { self[57] } set { self[57] = newValue } }
    var doubleAttack: Int { get { self[58] } set { self[58] = newValue } }
    var reputation: Int { get { self[59] } set { self[59] = newValue } }
    var potential: Int { get { self[60] } set { self[60] = newValue } }
    var learningItem: Int { get { self[61] } set { self[61] = newValue } }
    var expForItem: Int { get { self[62] } set { self[62] = newValue } }
    func skillId(_ i: Int) -> Int { self[63 + i] }
    mutating func setSkillId(_ i: Int, _ v: Int) { self[63 + i] = v }
    func skillLevel(_ i: Int) -> Int { self[73 + i] }
    mutating func setSkillLevel(_ i: Int, _ v: Int) { self[73 + i] = newValueClamp(v) }
    func takingItem(_ i: Int) -> Int { self[83 + i] }
    mutating func setTakingItem(_ i: Int, _ v: Int) { self[83 + i] = v }
    func takingCount(_ i: Int) -> Int { self[87 + i] }
    mutating func setTakingCount(_ i: Int, _ v: Int) { self[87 + i] = v }

    private func newValueClamp(_ v: Int) -> Int { min(Constants.skillLevelMax, max(0, v)) }

    mutating func clampVitals() {
        hp = min(max(hp, 0), maxHp)
        mp = min(max(mp, 0), maxMp)
        maxHp = min(max(maxHp, 1), Constants.hpMax)
        maxMp = min(max(maxMp, 0), Constants.mpMax)
        stamina = min(max(stamina, 0), Constants.staminaMax)
        hurt = min(max(hurt, 0), 99)
        poisoned = min(max(poisoned, 0), 99)
    }
}

struct Item {
    var raw: [UInt8]
    static let wordCount = 95
    static let byteCount = wordCount * 2

    init() { raw = [UInt8](repeating: 0, count: Self.byteCount) }
    init(bytes: [UInt8]) {
        raw = bytes
        if raw.count < Self.byteCount {
            raw.append(contentsOf: [UInt8](repeating: 0, count: Self.byteCount - raw.count))
        }
    }

    subscript(word: Int) -> Int {
        get { Packed.i16(raw, word) }
        set { Packed.setI16(&raw, word, newValue) }
    }

    var id: Int { self[0] }
    var name: String { Big5.decode(Array(raw[2..<22])) }
    var name2: String { Big5.decode(Array(raw[22..<42])) }
    var desc: String { Big5.decode(Array(raw[42..<72])) }
    var skillId: Int { self[36] }
    var throwingEffectId: Int { self[37] }
    var user: Int { get { self[38] } set { self[38] = newValue } }
    var equipType: Int { self[39] }
    var showDesc: Int { self[40] }
    var itemType: Int { self[41] } // 0 special, 1 equip, 2 skill, 3 heal, 4 attack
    var addHp: Int { self[45] }
    var addMaxHp: Int { self[46] }
    var addPoisoned: Int { self[47] }
    var addStamina: Int { self[48] }
    var changeMpType: Int { self[49] }
    var addMp: Int { self[50] }
    var addMaxMp: Int { self[51] }
    var addAttack: Int { self[52] }
    var addSpeed: Int { self[53] }
    var addDefence: Int { self[54] }
    var addMedic: Int { self[55] }
    var addPoison: Int { self[56] }
    var addDepoison: Int { self[57] }
    var addAntipoison: Int { self[58] }
    var addFist: Int { self[59] }
    var addSword: Int { self[60] }
    var addBlade: Int { self[61] }
    var addSpecial: Int { self[62] }
    var addThrowing: Int { self[63] }
    var addKnowledge: Int { self[64] }
    var addIntegrity: Int { self[65] }
    var addDoubleAttack: Int { self[66] }
    var addPoisonAmp: Int { self[67] }
    var charOnly: Int { self[68] }
    var reqMpType: Int { self[69] }
    var reqMp: Int { self[70] }
    var reqAttack: Int { self[71] }
    var reqSpeed: Int { self[72] }
    var reqPoison: Int { self[73] }
    var reqMedic: Int { self[74] }
    var reqDepoison: Int { self[75] }
    var reqFist: Int { self[76] }
    var reqSword: Int { self[77] }
    var reqBlade: Int { self[78] }
    var reqSpecial: Int { self[79] }
    var reqThrowing: Int { self[80] }
    var reqPotential: Int { self[81] }
    var reqExp: Int { self[82] }
    var reqExpForMakeItem: Int { self[83] }
    var reqMaterial: Int { self[84] }
    func makeItem(_ i: Int) -> Int { self[85 + i] }
    func makeItemCount(_ i: Int) -> Int { self[90 + i] }
}

struct SceneInfo {
    var raw: [UInt8]
    static let wordCount = 26
    static let byteCount = wordCount * 2

    init() { raw = [UInt8](repeating: 0, count: Self.byteCount) }
    init(bytes: [UInt8]) {
        raw = bytes
        if raw.count < Self.byteCount {
            raw.append(contentsOf: [UInt8](repeating: 0, count: Self.byteCount - raw.count))
        }
    }

    subscript(word: Int) -> Int {
        get { Packed.i16(raw, word) }
        set { Packed.setI16(&raw, word, newValue) }
    }

    var id: Int { self[0] }
    var name: String { Big5.decode(Array(raw[2..<12])) }
    var exitMusic: Int { self[6] }
    var enterMusic: Int { self[7] }
    var jumpScene: Int { self[8] }
    var enterCondition: Int { get { self[9] } set { self[9] = newValue } }
    var mainEntranceY1: Int { self[10] }
    var mainEntranceX1: Int { self[11] }
    var mainEntranceY2: Int { self[12] }
    var mainEntranceX2: Int { self[13] }
    var enterY: Int { self[14] }
    var enterX: Int { self[15] }
    func exitY(_ i: Int) -> Int { self[16 + i] }
    func exitX(_ i: Int) -> Int { self[19 + i] }
    var jumpY1: Int { self[22] }
    var jumpX1: Int { self[23] }
    var jumpY2: Int { self[24] }
    var jumpX2: Int { self[25] }
}

struct Magic {
    var raw: [UInt8]
    static let wordCount = 68
    static let byteCount = wordCount * 2

    init() { raw = [UInt8](repeating: 0, count: Self.byteCount) }
    init(bytes: [UInt8]) {
        raw = bytes
        if raw.count < Self.byteCount {
            raw.append(contentsOf: [UInt8](repeating: 0, count: Self.byteCount - raw.count))
        }
    }

    subscript(word: Int) -> Int {
        get { Packed.i16(raw, word) }
        set { Packed.setI16(&raw, word, newValue) }
    }

    var id: Int { self[0] }
    var name: String { Big5.decode(Array(raw[2..<12])) }
    var soundNum: Int { self[11] }
    var magicType: Int { self[12] } // 1 fist 2 sword 3 blade 4 special
    var amiNum: Int { self[13] }
    var hurtType: Int { self[14] } // 0 hp 1 mp drain
    var attAreaType: Int { self[15] } // 0 single 1 line 2 cross 3 area
    var needMp: Int { self[16] }
    var poison: Int { self[17] }
    func attack(_ level: Int) -> Int { self[18 + level] }
    func moveDistance(_ level: Int) -> Int { self[28 + level] }
    func attDistance(_ level: Int) -> Int { self[38 + level] }
    func addMp(_ level: Int) -> Int { self[48 + level] }
    func hurtMp(_ level: Int) -> Int { self[58 + level] }
}

struct Shop {
    var raw: [UInt8]
    static let wordCount = 15
    static let byteCount = wordCount * 2

    init() { raw = [UInt8](repeating: 0, count: Self.byteCount) }
    init(bytes: [UInt8]) {
        raw = bytes
        if raw.count < Self.byteCount {
            raw.append(contentsOf: [UInt8](repeating: 0, count: Self.byteCount - raw.count))
        }
    }

    subscript(word: Int) -> Int {
        get { Packed.i16(raw, word) }
        set { Packed.setI16(&raw, word, newValue) }
    }

    func item(_ i: Int) -> Int { self[i] }
    func amount(_ i: Int) -> Int { self[5 + i] }
    mutating func setAmount(_ i: Int, _ v: Int) { self[5 + i] = v }
    func price(_ i: Int) -> Int { self[10 + i] }
}

struct WarInfo {
    var raw: [UInt8]
    static let wordCount = 0x5D
    static let byteCount = wordCount * 2

    init(bytes: [UInt8]) {
        raw = bytes
        if raw.count < Self.byteCount {
            raw.append(contentsOf: [UInt8](repeating: 0, count: Self.byteCount - raw.count))
        }
    }

    subscript(word: Int) -> Int {
        get { Packed.i16(raw, word) }
        set { Packed.setI16(&raw, word, newValue) }
    }

    var id: Int { self[0] }
    var name: String { Big5.decode(Array(raw[2..<12])) }
    var fieldId: Int { self[6] }
    var exp: Int { self[7] }
    var music: Int { self[8] }
    func teamMate(_ i: Int) -> Int { self[9 + i] }
    func autoTeamMate(_ i: Int) -> Int { self[15 + i] }
    func teamY(_ i: Int) -> Int { self[21 + i] }
    func teamX(_ i: Int) -> Int { self[27 + i] }
    func enemy(_ i: Int) -> Int { self[33 + i] }
    func enemyY(_ i: Int) -> Int { self[53 + i] }
    func enemyX(_ i: Int) -> Int { self[73 + i] }
}

struct BattleRole {
    var rnum = 0
    var team = 0
    var y = 0
    var x = 0
    var face = 0
    var dead = 0
    var step = 0
    var acted = 0
    var pic = 0
    var showNumber = 0
    var expGot = 0
    var auto = 0
}

struct Cloud {
    var pic = 0
    var x = 0
    var y = 0
    var speedX = 0
    var speedY = 0
}

struct BaseState {
    var inShip = 0
    var savedScene = 0
    var my = 0
    var mx = 0
    var sy = 0
    var sx = 0
    var face = 0
    var shipX = 0
    var shipY = 0
    var shipX1 = 0
    var shipY1 = 0
    var shipFace = 0
    var team: [Int] = Array(repeating: -1, count: Constants.teamCount)
    var bag: [ItemSlot] = Array(repeating: ItemSlot(), count: Constants.bagCount)
}

enum Where: Int, CustomStringConvertible {
    case world = 0
    case scene = 1
    case battle = 2
    case title = 3
    case dead = 4
    var description: String {
        switch self {
        case .world: return "world"
        case .scene: return "scene"
        case .battle: return "battle"
        case .title: return "title"
        case .dead: return "dead"
        }
    }
}

enum Key: Equatable {
    case up, down, left, right
    case ok, cancel
    case yes, no
    case escape
    case other(UInt16)

    var token: String {
        switch self {
        case .up: return "up"
        case .down: return "down"
        case .left: return "left"
        case .right: return "right"
        case .ok: return "ok"
        case .cancel: return "cancel"
        case .yes: return "yes"
        case .no: return "no"
        case .escape: return "escape"
        case .other(let c): return "key:\(c)"
        }
    }

    static func parse(_ name: String) -> Key {
        switch name.lowercased() {
        case "up", "w": return .up
        case "down", "s": return .down
        case "left", "a": return .left
        case "right", "d": return .right
        case "ok", "enter", "space", "return": return .ok
        case "cancel", "esc", "escape", "back": return .cancel
        case "yes", "y": return .yes
        case "no", "n": return .no
        default: return .other(0)
        }
    }
}
