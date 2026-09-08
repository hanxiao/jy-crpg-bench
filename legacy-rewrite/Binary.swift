import Foundation

enum Screen {
    static let width = 640
    static let height = 400
    static let cx = width / 2
    static let cy = height / 2
}

enum Constants {
    static let teamCount = 6
    static let bagCount = 200
    static let charFrameCount = 5
    static let learnSkillCount = 10
    static let carryItemCount = 4
    static let knowledgeBarrier = 80
    static let skillLevelMax = 999
    static let levelMax = 30
    static let hpMax = 999
    static let mpMax = 999
    static let staminaMax = 100
    static let itemTexStart = 3501
    static let moneyId = 174
    static let compassId = 182
    static let shopItemCount = 5
    static let subMapSize = 64
    static let subMapLayers = 6
    static let subMapEvents = 200
    static let warEnemies = 20
    static let warLayers = 8
    static let warSize = 64
    static let worldSize = 480
    static let beginEvent = 691
    static let beginScene = 70
    static let beginSx = 20
    static let beginSy = 19
    static let beginWalkPic = 2501
    static let beginLeaveEvent = 950
    static let softstarTalk = 2547
    static let softstarTalkCount = 18
    static let maxHead = 189
}

struct Binary {
    let bytes: [UInt8]
    var offset = 0

    init(_ data: Data) { bytes = [UInt8](data) }
    init(_ bytes: [UInt8]) { self.bytes = bytes }

    var count: Int { bytes.count }
    var remaining: Int { bytes.count - offset }

    mutating func skip(_ n: Int) { offset += n }

    mutating func i8() -> Int {
        guard offset < bytes.count else { return 0 }
        let v = Int8(bitPattern: bytes[offset])
        offset += 1
        return Int(v)
    }

    mutating func u8() -> UInt8 {
        guard offset < bytes.count else { return 0 }
        let v = bytes[offset]
        offset += 1
        return v
    }

    mutating func i16() -> Int {
        guard offset + 1 < bytes.count else { return 0 }
        let lo = UInt16(bytes[offset])
        let hi = UInt16(bytes[offset + 1])
        offset += 2
        return Int(Int16(bitPattern: lo | (hi << 8)))
    }

    mutating func u16() -> Int {
        guard offset + 1 < bytes.count else { return 0 }
        let lo = UInt16(bytes[offset])
        let hi = UInt16(bytes[offset + 1])
        offset += 2
        return Int(lo | (hi << 8))
    }

    mutating func u32() -> UInt32 {
        guard offset + 3 < bytes.count else { return 0 }
        let v = UInt32(bytes[offset])
            | (UInt32(bytes[offset + 1]) << 8)
            | (UInt32(bytes[offset + 2]) << 16)
            | (UInt32(bytes[offset + 3]) << 24)
        offset += 4
        return v
    }

    mutating func chars(_ n: Int) -> [UInt8] {
        let end = min(offset + n, bytes.count)
        let slice = Array(bytes[offset..<end])
        offset = end
        return slice
    }

    func i16(at i: Int) -> Int {
        guard i + 1 < bytes.count else { return 0 }
        let lo = UInt16(bytes[i])
        let hi = UInt16(bytes[i + 1])
        return Int(Int16(bitPattern: lo | (hi << 8)))
    }
}

enum Grp {
    static func load(idx: URL, grp: URL) throws -> [[UInt8]] {
        let indexData = try Data(contentsOf: idx)
        let groupData = try Data(contentsOf: grp)
        return parse(index: [UInt8](indexData), group: [UInt8](groupData))
    }

    static func parse(index: [UInt8], group: [UInt8]) -> [[UInt8]] {
        let count = index.count / 4
        var items: [[UInt8]] = Array(repeating: [], count: count)
        var offset = 0
        var reachedEnd = false
        for i in 0..<count {
            let base = i * 4
            var end = Int(UInt32(index[base])
                | (UInt32(index[base + 1]) << 8)
                | (UInt32(index[base + 2]) << 16)
                | (UInt32(index[base + 3]) << 24))
            if end == 0 {
                reachedEnd = true
                end = group.count
            } else if reachedEnd {
                break
            }
            if end < offset || end > group.count { break }
            if end > offset {
                items[i] = Array(group[offset..<end])
            }
            offset = end
        }
        return items
    }

    static func mergeNumbered(dir: URL, idxPrefix: String, grpPrefix: String, count: Int) -> [[UInt8]] {
        var merged: [[UInt8]] = []
        for i in 0..<count {
            let idx = dir.appendingPathComponent(String(format: "%@%03d", idxPrefix, i))
            let grp = dir.appendingPathComponent(String(format: "%@%03d", grpPrefix, i))
            guard FileManager.default.fileExists(atPath: idx.path) else { continue }
            guard let items = try? load(idx: idx, grp: grp) else { continue }
            if items.count > merged.count {
                merged.append(contentsOf: Array(repeating: [], count: items.count - merged.count))
            }
            for j in 0..<items.count where merged[j].isEmpty && !items[j].isEmpty {
                merged[j] = items[j]
            }
        }
        return merged
    }
}

enum Big5 {
    static func decode(_ bytes: [UInt8]) -> String {
        let trimmed = bytes.prefix { $0 != 0 }
        if trimmed.isEmpty { return "" }
        let encoding = String.Encoding(
            rawValue: CFStringConvertEncodingToNSStringEncoding(
                CFStringEncoding(CFStringEncodings.big5.rawValue)
            )
        )
        return String(data: Data(trimmed), encoding: encoding) ?? ""
    }

    static func encode(_ string: String, width: Int) -> [UInt8] {
        let encoding = String.Encoding(
            rawValue: CFStringConvertEncodingToNSStringEncoding(
                CFStringEncoding(CFStringEncodings.big5.rawValue)
            )
        )
        var out = [UInt8](repeating: 0, count: width)
        if let data = string.data(using: encoding) {
            let n = min(data.count, width)
            data.copyBytes(to: &out, count: n)
        }
        return out
    }

    static func xorDecode(_ bytes: [UInt8]) -> String {
        decode(bytes.map { $0 == 0 ? 0 : $0 ^ 0xFF })
    }
}

enum Packed {
    static func i16(_ bytes: [UInt8], _ index: Int) -> Int {
        let i = index * 2
        guard i + 1 < bytes.count else { return 0 }
        let lo = UInt16(bytes[i])
        let hi = UInt16(bytes[i + 1])
        return Int(Int16(bitPattern: lo | (hi << 8)))
    }

    static func setI16(_ bytes: inout [UInt8], _ index: Int, _ value: Int) {
        let i = index * 2
        if i + 1 >= bytes.count { return }
        let v = UInt16(bitPattern: Int16(clamping: value))
        bytes[i] = UInt8(v & 0xFF)
        bytes[i + 1] = UInt8(v >> 8)
    }

    static func map2D(_ data: Data, width: Int, height: Int) -> [[Int]] {
        var map = Array(repeating: Array(repeating: 0, count: height), count: width)
        let bytes = [UInt8](data)
        var o = 0
        for x in 0..<width {
            for y in 0..<height {
                if o + 1 < bytes.count {
                    let lo = UInt16(bytes[o])
                    let hi = UInt16(bytes[o + 1])
                    map[x][y] = Int(Int16(bitPattern: lo | (hi << 8)))
                }
                o += 2
            }
        }
        return map
    }
}

struct OriginalRNG {
    var seed: UInt32

    init(seed: UInt32 = UInt32.random(in: 1...UInt32.max)) {
        self.seed = seed
    }

    mutating func rand() -> Int {
        seed = seed &* 0x41C64E6D &+ 0x3039
        return Int((seed >> 16) & 0x7FFF)
    }

    mutating func rnd(_ n: Int) -> Int {
        if n <= 1 || n > 30000 { return 0 }
        return rand() % n
    }
}
