import Foundation

struct Pic {
    var width: Int = 0
    var height: Int = 0
    var originX: Int = 0
    var originY: Int = 0
    var pixels: [UInt8] = []
    var empty: Bool { pixels.isEmpty || width <= 0 || height <= 0 }
}

enum RLE {
    static func decode(_ data: [UInt8]) -> Pic {
        guard data.count >= 8 else { return Pic() }
        var br = Binary(data)
        let w = br.i16()
        let h = br.i16()
        let ox = br.i16()
        let oy = br.i16()
        if w <= 0 || h <= 0 || w > 2048 || h > 2048 { return Pic() }
        var pixels = [UInt8](repeating: 0, count: w * h)
        for row in 0..<h {
            guard br.remaining > 0 else { break }
            let rowBytes = Int(br.u8())
            guard rowBytes >= 0, br.remaining >= rowBytes else { break }
            let rowEnd = br.offset + rowBytes
            var x = 0
            while br.offset < rowEnd && x < w {
                let skip = Int(br.u8())
                x += skip
                if br.offset >= rowEnd { break }
                let count = Int(br.u8())
                for _ in 0..<count {
                    if br.offset >= rowEnd { break }
                    let color = br.u8()
                    if x >= 0 && x < w {
                        pixels[row * w + x] = color
                    }
                    x += 1
                }
            }
            br.offset = rowEnd
        }
        return Pic(width: w, height: h, originX: ox, originY: oy, pixels: pixels)
    }
}

final class Palette {
    var colors: [UInt32] = Array(repeating: 0, count: 256)

    convenience init(file: URL) throws {
        self.init()
        let data = try Data(contentsOf: file)
        load(data)
    }

    func load(_ data: Data) {
        let bytes = [UInt8](data)
        for i in 0..<256 {
            let o = i * 3
            guard o + 2 < bytes.count else { break }
            // VGA DAC order is R,G,B stored as 6-bit (0..63).
            let r = Self.expand6(bytes[o])
            let g = Self.expand6(bytes[o + 1])
            let b = Self.expand6(bytes[o + 2])
            colors[i] = 0xFF00_0000 | (r << 16) | (g << 8) | b
        }
        colors[0] = 0
    }

    private static func expand6(_ v: UInt8) -> UInt32 {
        let x = UInt32(v) & 63
        return (x << 2) | (x >> 4)
    }

    func rgba(_ index: UInt8) -> (Float, Float, Float, Float) {
        let c = colors[Int(index)]
        let r = Float((c >> 16) & 0xFF) / 255
        let g = Float((c >> 8) & 0xFF) / 255
        let b = Float(c & 0xFF) / 255
        let a: Float = index == 0 ? 0 : 1
        return (r, g, b, a)
    }
}

final class FontAtlas {
    private var glyphs: [UInt8] = []
    private var ascii: [UInt8] = []

    init(dir: URL) {
        if let c16 = try? Data(contentsOf: dir.appendingPathComponent("FONT.C16")) {
            glyphs = [UInt8](c16)
        }
        if let x16 = try? Data(contentsOf: dir.appendingPathComponent("FONT.X16")) {
            ascii = [UInt8](x16)
        } else if let e16 = try? Data(contentsOf: dir.appendingPathComponent("FONT.E16")) {
            ascii = [UInt8](e16)
        }
    }

    func glyph(for ch: Character) -> (width: Int, rows: [UInt8])? {
        let s = String(ch)
        if let asciiValue = ch.asciiValue, asciiValue < 128 {
            return asciiGlyph(Int(asciiValue))
        }
        let encoding = String.Encoding(
            rawValue: CFStringConvertEncodingToNSStringEncoding(
                CFStringEncoding(CFStringEncodings.big5.rawValue)
            )
        )
        guard let data = s.data(using: encoding), data.count >= 2 else { return asciiGlyph(0x3F) }
        let b1 = Int(data[data.startIndex])
        let b2 = Int(data[data.startIndex.advanced(by: 1)])
        let hi = b1 - 0xA1
        let lo = b2 < 0x7F ? b2 - 0x40 : b2 - 0xA1 + 0x3F
        if hi < 0 || lo < 0 { return asciiGlyph(0x3F) }
        let index = hi * 157 + lo
        let offset = index * 32
        guard offset + 32 <= glyphs.count else { return asciiGlyph(0x3F) }
        return (16, Array(glyphs[offset..<(offset + 32)]))
    }

    private func asciiGlyph(_ code: Int) -> (width: Int, rows: [UInt8])? {
        if ascii.count >= 4096 {
            let offset = code * 16
            guard offset + 16 <= ascii.count else { return nil }
            return (8, Array(ascii[offset..<(offset + 16)]))
        }
        if ascii.count >= 2048, code < 128 {
            let offset = code * 16
            guard offset + 16 <= ascii.count else { return nil }
            return (8, Array(ascii[offset..<(offset + 16)]))
        }
        return nil
    }
}

final class Resources {
    let dir: URL
    let palette = Palette()
    let endPalette = Palette()
    var mmap: [Pic] = []
    var smap: [Pic] = []
    var wmap: [Pic] = []
    var heads: [Pic] = []
    var effects: [Pic] = []
    var clouds: [Pic] = []
    var titles: [Pic] = []
    var fights: [Int: [Pic]] = [:]
    var titleBig: [UInt8] = []
    var deadBig: [UInt8] = []
    var earth: [[Int]] = []
    var surface: [[Int]] = []
    var building: [[Int]] = []
    var buildX: [[Int]] = []
    var buildY: [[Int]] = []
    var kdef: [[Int]] = []
    var talks: [String] = []
    var wars: [WarInfo] = []
    var warFields: [[[Int]]] = []
    var font: FontAtlas
    var leaveChars: [Int] = []
    var leaveStartEvent: Int = Constants.beginLeaveEvent
    var initScene = Constants.beginScene
    var initSx = Constants.beginSx
    var initSy = Constants.beginSy
    var expTable: [Int] = []
    var effectFrames: [Int] = []
    var matchList: [(Int, Int, Int)] = []

    init(dir: URL) throws {
        self.dir = dir
        font = FontAtlas(dir: dir)
        try palette.load(Data(contentsOf: dir.appendingPathComponent("MMAP.COL")))
        if FileManager.default.fileExists(atPath: dir.appendingPathComponent("ENDCOL.COL").path) {
            try endPalette.load(Data(contentsOf: dir.appendingPathComponent("ENDCOL.COL")))
        } else {
            endPalette.colors = palette.colors
        }
        mmap = Self.decodePics(try Grp.load(idx: dir.appendingPathComponent("MMAP.IDX"), grp: dir.appendingPathComponent("MMAP.GRP")))
        smap = Self.decodePics(Grp.mergeNumbered(dir: dir, idxPrefix: "SDX", grpPrefix: "SMP", count: 84))
        wmap = Self.decodePics(Grp.mergeNumbered(dir: dir, idxPrefix: "WDX", grpPrefix: "WMP", count: 26))
        heads = Self.decodePics(try Grp.load(idx: dir.appendingPathComponent("HDGRP.IDX"), grp: dir.appendingPathComponent("HDGRP.GRP")))
        effects = Self.decodePics(try Grp.load(idx: dir.appendingPathComponent("EFT.IDX"), grp: dir.appendingPathComponent("EFT.GRP")))
        clouds = Self.decodePics(try Grp.load(idx: dir.appendingPathComponent("CLOUD.IDX"), grp: dir.appendingPathComponent("CLOUD.GRP")))
        titles = Self.decodePics(try Grp.load(idx: dir.appendingPathComponent("TITLE.IDX"), grp: dir.appendingPathComponent("TITLE.GRP")))
        titleBig = [UInt8](try Data(contentsOf: dir.appendingPathComponent("TITLE.BIG")))
        if FileManager.default.fileExists(atPath: dir.appendingPathComponent("DEAD.BIG").path) {
            deadBig = [UInt8](try Data(contentsOf: dir.appendingPathComponent("DEAD.BIG")))
        }
        earth = Packed.map2D(try Data(contentsOf: dir.appendingPathComponent("EARTH.002")), width: Constants.worldSize, height: Constants.worldSize)
        surface = Packed.map2D(try Data(contentsOf: dir.appendingPathComponent("SURFACE.002")), width: Constants.worldSize, height: Constants.worldSize)
        building = Packed.map2D(try Data(contentsOf: dir.appendingPathComponent("BUILDING.002")), width: Constants.worldSize, height: Constants.worldSize)
        buildX = Packed.map2D(try Data(contentsOf: dir.appendingPathComponent("BUILDX.002")), width: Constants.worldSize, height: Constants.worldSize)
        buildY = Packed.map2D(try Data(contentsOf: dir.appendingPathComponent("BUILDY.002")), width: Constants.worldSize, height: Constants.worldSize)
        let kItems = try Grp.load(idx: dir.appendingPathComponent("KDEF.IDX"), grp: dir.appendingPathComponent("KDEF.GRP"))
        kdef = kItems.map { bytes in
            var out: [Int] = []
            var i = 0
            while i + 1 < bytes.count {
                let lo = UInt16(bytes[i])
                let hi = UInt16(bytes[i + 1])
                out.append(Int(Int16(bitPattern: lo | (hi << 8))))
                i += 2
            }
            return out
        }
        let talkItems = try Grp.load(idx: dir.appendingPathComponent("TALK.IDX"), grp: dir.appendingPathComponent("TALK.GRP"))
        talks = talkItems.map { Big5.xorDecode($0) }
        let warData = try Data(contentsOf: dir.appendingPathComponent("WAR.STA"))
        var o = 0
        while o + WarInfo.byteCount <= warData.count {
            wars.append(WarInfo(bytes: [UInt8](warData.subdata(in: o..<(o + WarInfo.byteCount)))))
            o += WarInfo.byteCount
        }
        let warGrp = try Grp.load(idx: dir.appendingPathComponent("WARFLD.IDX"), grp: dir.appendingPathComponent("WARFLD.GRP"))
        warFields = warGrp.map { bytes in
            var layers = Array(
                repeating: Array(repeating: 0, count: Constants.warSize * Constants.warSize),
                count: Constants.warLayers
            )
            var p = 0
            for layer in 0..<Constants.warLayers {
                for i in 0..<(Constants.warSize * Constants.warSize) {
                    if p + 1 < bytes.count {
                        let lo = UInt16(bytes[p])
                        let hi = UInt16(bytes[p + 1])
                        layers[layer][i] = Int(Int16(bitPattern: lo | (hi << 8)))
                    }
                    p += 2
                }
            }
            return layers
        }
        loadFactors()
    }

    func fightPics(_ id: Int) -> [Pic] {
        if let cached = fights[id] { return cached }
        let name = String(format: "FIGHT%03d", id)
        let idx = dir.appendingPathComponent(name + ".IDX")
        let grp = dir.appendingPathComponent(name + ".GRP")
        guard FileManager.default.fileExists(atPath: idx.path),
              let items = try? Grp.load(idx: idx, grp: grp) else {
            fights[id] = []
            return []
        }
        let pics = Self.decodePics(items)
        fights[id] = pics
        return pics
    }

    func wavURL(_ name: String) -> URL? {
        let url = dir.appendingPathComponent(name)
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    func xmiURL(_ index: Int) -> URL? {
        let url = dir.appendingPathComponent(String(format: "GAME%02d.XMI", index))
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }

    private static func decodePics(_ items: [[UInt8]]) -> [Pic] {
        items.map { RLE.decode($0) }
    }

    private func loadFactors() {
        guard let data = try? Data(contentsOf: dir.appendingPathComponent("Z.DAT")) else { return }
        let bytes = [UInt8](data)
        func i16(_ offset: Int) -> Int {
            guard offset + 1 < bytes.count else { return 0 }
            let lo = UInt16(bytes[offset])
            let hi = UInt16(bytes[offset + 1])
            return Int(Int16(bitPattern: lo | (hi << 8)))
        }
        let leaveOff = 0x1A6E5
        leaveChars = (0..<25).map { i16(leaveOff + $0 * 2) }
        leaveStartEvent = i16(0x1F6C6)
        initScene = i16(0x2076E)
        initSx = i16(0x207B7)
        initSy = i16(0x207C0)
        expTable = (0..<29).map { i16(0x4DF90 + $0 * 2) }
        effectFrames = (0..<53).map { i16(0x4F4CE + $0 * 2) }
        matchList = (0..<7).map { i in
            let o = 0x4F538 + i * 6
            return (i16(o), i16(o + 2), i16(o + 4))
        }
    }
}

struct SaveArchive {
    var base = BaseState()
    var roles: [Role] = []
    var items: [Item] = []
    var scenes: [SceneInfo] = []
    var magics: [Magic] = []
    var shops: [Shop] = []
    var sdata: [[[[Int]]]] = [] // [scene][layer][x][y]
    var ddata: [[[Int]]] = [] // [scene][event][11]
    var entrance: [[Int]] = Array(
        repeating: Array(repeating: -1, count: Constants.worldSize),
        count: Constants.worldSize
    )

    mutating func load(dir: URL, slot: Int) throws {
        let rangerName = slot == 0 ? "RANGER" : "R\(slot)"
        let sinName = slot == 0 ? "ALLSIN" : "S\(slot)"
        let defName = slot == 0 ? "ALLDEF" : "D\(slot)"
        let ranger = try Grp.load(idx: dir.appendingPathComponent(rangerName + ".IDX"),
                                  grp: dir.appendingPathComponent(rangerName + ".GRP"))
        guard ranger.count >= 6 else { throw NSError(domain: "QunXia", code: 1) }
        parseBase(ranger[0])
        roles = chunk(ranger[1], Role.byteCount).map { Role(bytes: $0) }
        items = chunk(ranger[2], Item.byteCount).map { Item(bytes: $0) }
        scenes = chunk(ranger[3], SceneInfo.byteCount).map { SceneInfo(bytes: $0) }
        magics = chunk(ranger[4], Magic.byteCount).map { Magic(bytes: $0) }
        shops = chunk(ranger[5], Shop.byteCount).map { Shop(bytes: $0) }

        let sin = try Grp.load(idx: dir.appendingPathComponent(sinName + ".IDX"),
                               grp: dir.appendingPathComponent(sinName + ".GRP"))
        let def = try Grp.load(idx: dir.appendingPathComponent(defName + ".IDX"),
                               grp: dir.appendingPathComponent(defName + ".GRP"))
        sdata = sin.map { bytes in
            var layers = Array(
                repeating: Array(
                    repeating: Array(repeating: 0, count: Constants.subMapSize),
                    count: Constants.subMapSize
                ),
                count: Constants.subMapLayers
            )
            var p = 0
            for layer in 0..<Constants.subMapLayers {
                for x in 0..<Constants.subMapSize {
                    for y in 0..<Constants.subMapSize {
                        if p + 1 < bytes.count {
                            let lo = UInt16(bytes[p])
                            let hi = UInt16(bytes[p + 1])
                            layers[layer][x][y] = Int(Int16(bitPattern: lo | (hi << 8)))
                        }
                        p += 2
                    }
                }
            }
            return layers
        }
        ddata = def.map { bytes in
            var events = Array(
                repeating: Array(repeating: 0, count: 11),
                count: Constants.subMapEvents
            )
            var p = 0
            for e in 0..<Constants.subMapEvents {
                for f in 0..<11 {
                    if p + 1 < bytes.count {
                        let lo = UInt16(bytes[p])
                        let hi = UInt16(bytes[p + 1])
                        events[e][f] = Int(Int16(bitPattern: lo | (hi << 8)))
                    }
                    p += 2
                }
            }
            return events
        }
        rebuildEntrance()
    }

    mutating func rebuildEntrance() {
        entrance = Array(
            repeating: Array(repeating: -1, count: Constants.worldSize),
            count: Constants.worldSize
        )
        for (i, scene) in scenes.enumerated() {
            let x1 = scene.mainEntranceX1
            let y1 = scene.mainEntranceY1
            if x1 >= 0 && x1 < Constants.worldSize && y1 >= 0 && y1 < Constants.worldSize {
                entrance[x1][y1] = i
            }
            let x2 = scene.mainEntranceX2
            let y2 = scene.mainEntranceY2
            if x2 >= 0 && x2 < Constants.worldSize && y2 >= 0 && y2 < Constants.worldSize {
                entrance[x2][y2] = i
            }
        }
    }

    func money() -> Int {
        for slot in base.bag where slot.id == Constants.moneyId {
            return slot.count
        }
        return 0
    }

    mutating func addItem(_ id: Int, _ amount: Int) {
        if id == Constants.moneyId {
            if let i = base.bag.firstIndex(where: { $0.id == id }) {
                base.bag[i].count = max(0, base.bag[i].count + amount)
                if base.bag[i].count == 0 { base.bag[i].id = -1 }
                return
            }
            if amount > 0, let i = base.bag.firstIndex(where: { $0.id < 0 }) {
                base.bag[i] = ItemSlot(id: id, count: amount)
            }
            return
        }
        if let i = base.bag.firstIndex(where: { $0.id == id }) {
            base.bag[i].count = max(0, base.bag[i].count + amount)
            if base.bag[i].count == 0 { base.bag[i].id = -1 }
            return
        }
        if amount > 0, let i = base.bag.firstIndex(where: { $0.id < 0 }) {
            base.bag[i] = ItemSlot(id: id, count: amount)
        }
    }

    func hasItem(_ id: Int) -> Bool {
        base.bag.contains { $0.id == id && $0.count > 0 }
    }

    func teamFull() -> Bool {
        !base.team.contains(where: { $0 < 0 })
    }

    mutating func join(_ rnum: Int) {
        if let i = base.team.firstIndex(where: { $0 < 0 }) {
            base.team[i] = rnum
        }
    }

    mutating func leave(_ rnum: Int) {
        if let i = base.team.firstIndex(where: { $0 == rnum }) {
            base.team[i] = -1
        }
    }

    private mutating func parseBase(_ bytes: [UInt8]) {
        var br = Binary(bytes)
        base.inShip = br.i16()
        base.savedScene = br.i16()
        base.my = br.i16()
        base.mx = br.i16()
        base.sy = br.i16()
        base.sx = br.i16()
        base.face = br.i16()
        base.shipX = br.i16()
        base.shipY = br.i16()
        base.shipX1 = br.i16()
        base.shipY1 = br.i16()
        base.shipFace = br.i16()
        for i in 0..<Constants.teamCount { base.team[i] = br.i16() }
        for i in 0..<Constants.bagCount {
            base.bag[i].id = br.i16()
            base.bag[i].count = br.i16()
        }
    }

    private func chunk(_ bytes: [UInt8], _ size: Int) -> [[UInt8]] {
        guard size > 0 else { return [] }
        var out: [[UInt8]] = []
        var i = 0
        while i + size <= bytes.count {
            out.append(Array(bytes[i..<(i + size)]))
            i += size
        }
        return out
    }
}
