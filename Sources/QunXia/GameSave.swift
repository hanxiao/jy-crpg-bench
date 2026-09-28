import Foundation
import CoreHost

/// Has the game save itself, then reads what it wrote.
///
/// The game writes its save slots as `R<n>.GRP` into the directory it was
/// mounted from, and that archive is the only place the party roster and the
/// world square are true. It only offers 存檔 from the world map, and it says
/// so itself: the menu has six rows there and four inside a scene, so an
/// attempt opens the menu, counts its rows, and backs out again when saving
/// is not on offer. An attempt that finds a scene costs two taps and leaves
/// the screen exactly as it was.
///
/// Nothing here is reachable from the Control API. An agent that could save
/// could also load, and a run that can rewind is not a measurement.
///
/// Off unless `QUNXIA_SNAPSHOT_EVERY` gives an interval in seconds, as on the
/// headless runner.
final class GameSave {
    /// The panel's left border is a white column at a fixed x, and the panel
    /// grows by one row height per entry: measured at 122 pixels for the
    /// six-row world-map menu and 82 for the four-row one, both from y 23.
    static let menuX = 21
    static let menuTop = 15...30
    static let rowHeight = 20
    static let rowPad = 2
    static let worldMenuRows = 6
    static let systemRow = 5          // 醫療 解毒 物品 狀態 離隊 系統
    static let saveRow = 1            // 讀檔 存檔 離開
    static let tapFrames = 10
    static let redrawFrames = 24

    private let emu: Emulator
    private let gameDir: URL
    private let slot: Int
    private let every: TimeInterval
    private let lock = NSLock()
    private var lastTry = Date.distantPast
    private(set) var party: GameState.Party?
    private(set) var savedAt: Date?
    private(set) var why = "not tried yet"

    init(emu: Emulator, gameDir: URL, slot: Int = 3,
         every: TimeInterval = TimeInterval(
             ProcessInfo.processInfo.environment["QUNXIA_SNAPSHOT_EVERY"] ?? "") ?? 0) {
        self.emu = emu
        self.gameDir = gameDir
        self.slot = slot
        self.every = every
        if every <= 0 { why = "off" }
    }

    private var archive: (grp: URL, idx: URL) {
        (gameDir.appendingPathComponent("R\(slot).GRP"),
         gameDir.appendingPathComponent("R\(slot).IDX"))
    }

    private func written() -> Date? {
        try? archive.grp.resourceValues(forKeys: [.contentModificationDateKey])
            .contentModificationDate
    }

    /// Try, but only if one is due. Called from an API action, so it runs
    /// between an agent's decisions and never beside one.
    func maybeSnapshot() {
        guard every > 0 else { return }
        lock.lock()
        guard Date().timeIntervalSince(lastTry) >= every else { lock.unlock(); return }
        lastTry = Date()
        lock.unlock()
        snapshot()
    }

    @discardableResult
    func snapshot() -> Bool {
        // the player left a menu open; an escape now would close it under them
        guard Self.menuRows() == 0 else { why = "a menu is open"; return false }
        tap(RetroKey.parse("escape"))
        let rows = Self.menuRows()
        guard rows == Self.worldMenuRows else {
            closeMenus()
            why = "the menu offered \(rows) rows, not \(Self.worldMenuRows); "
                + "the game only saves from the world map"
            return false
        }
        tap(RetroKey.parse("down"), times: Self.systemRow)
        tap(RetroKey.parse("enter"))
        tap(RetroKey.parse("down"), times: Self.saveRow)
        tap(RetroKey.parse("enter"))
        tap(RetroKey.parse("down"), times: slot - 1)
        let before = written()
        tap(RetroKey.parse("enter"))
        // The game writes the file a moment after it says 請稍候; wait for the
        // file itself rather than for a number of frames.
        var landed = false
        for _ in 0..<40 {
            emu.submitSync([.wait(20)], settle: .fixed(1), wantShot: false, atLeast: 10)
            if let now = written(), now != before { landed = true; break }
        }
        closeMenus()
        guard landed else { why = "the slot file did not change"; return false }
        guard let grp = try? Data(contentsOf: archive.grp),
              let idx = try? Data(contentsOf: archive.idx),
              let read = GameState.party(grp: [UInt8](grp), idx: [UInt8](idx)) else {
            why = "the slot the game wrote would not decode"
            return false
        }
        party = read
        savedAt = Date()
        why = "saved"
        return true
    }

    /// Escape until nothing is open. One escape too many reopens the menu, so
    /// this asks the screen rather than pressing a fixed number of times.
    private func closeMenus() {
        for _ in 0..<4 {
            if Self.menuRows() == 0 { return }
            tap(RetroKey.parse("escape"))
        }
    }

    private func tap(_ code: Int?, times: Int = 1) {
        guard let code, times > 0 else { return }
        var steps: [Emulator.Step] = []
        for _ in 0..<times {
            steps.append(.press([code], frames: Self.tapFrames))
            steps.append(.wait(Self.redrawFrames))
        }
        emu.submitSync(steps, settle: .fixed(1), wantShot: false, atLeast: 30)
    }

    /// How many rows the game's menu panel has, or 0 when none is open.
    ///
    /// Read straight off the core's framebuffer, which is XRGB8888. The
    /// emulation thread may be painting the next frame while this runs, but
    /// the panel is static between taps, so a torn read of that column reads
    /// the same values.
    static func menuRows() -> Int {
        let w = Int(core_width()), h = Int(core_height()), pitch = Int(core_pitch())
        guard w > menuX, h > 0, let base = core_pixels() else { return 0 }
        let px = base.assumingMemoryBound(to: UInt8.self)
        var best = 0, top = 0, run = 0, start = 0
        for y in 0..<h {
            let at = y * pitch + menuX * 4
            let white = px[at] >= 250 && px[at + 1] >= 250 && px[at + 2] >= 250
            if white {
                if run == 0 { start = y }
                run += 1
                if run > best { best = run; top = start }
            } else {
                run = 0
            }
        }
        guard best >= rowHeight * 2, menuTop.contains(top) else { return 0 }
        return Int((Double(best - rowPad) / Double(rowHeight)).rounded())
    }
}
