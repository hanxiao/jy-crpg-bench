import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
import CoreHost

/// Owns the emulation thread. Every mutation of core state goes through `submit`,
/// so the core is only ever touched from one thread and every action can report
/// back the screen it produced.
final class Emulator {

    /// A DOS game can take a dozen frames to react to a key. Waiting only for
    /// "the picture stopped changing" therefore snapshots the screen from
    /// *before* the action. So we wait for it to change first, then to settle.
    struct Settle {
        var reactFrames: Int = 30   // budget for the game to respond at all
        var minFrames: Int = 6      // floor once it has responded
        var maxFrames: Int = 120    // hard cap on the whole wait, as on the headless runner
        /// Identical frames that count as settled. Dialogue is drawn with a
        /// typewriter effect that pauses between glyphs, so a small value here
        /// returns half-written lines.
        var stableFrames: Int = 9

        static let `default` = Settle()
        static func fixed(_ n: Int) -> Settle {
            Settle(reactFrames: 0, minFrames: n, maxFrames: n, stableFrames: .max)
        }
    }

    struct Shot {
        let png: Data
        let width: Int
        let height: Int
        let scale: Int
        let waited: Int
        let frame: UInt64
    }

    struct Result {
        var ok: Bool
        var detail: String
        var shot: Shot?
        /// False means the action produced no visible change at all.
        var changed: Bool = true
        /// Frames spent settling. Carried here rather than only on the shot,
        /// so a caller that asked for no picture still learns how long the
        /// screen took to hold still.
        var waited: Int = 0
    }

    enum Step {
        case press([Int], frames: Int)   // key combo held for N frames, then released
        case wait(Int)
        case mouseMove(Int, Int)
        case mouseClick(Int)
        case save(URL)
        case load(URL)
        case reset
    }

    private struct Job {
        let steps: [Step]
        let settle: Settle
        let scale: Int
        let wantShot: Bool
        let done: (Result) -> Void
    }

    private let lock = NSCondition()
    private var jobs: [Job] = []
    private var pendingNativeKeys: [(Int, Bool)] = []
    // Native-window and API input have separate ownership. Releasing a local
    // key must not cancel the same key while an API pulse still owns it.
    private var nativeKeys: Set<Int> = []
    private var actionKeys: Set<Int> = []
    private var effectiveKeys: Set<Int> = []
    private var running = true
    private var frameBudget: Double = 1.0 / 60.0
    private(set) var lastError = ""

    let log: ActionLog
    var onFrame: (() -> Void)?

    init(log: ActionLog) {
        self.log = log
    }

    func start() {
        frameBudget = 1.0 / max(1.0, core_fps())
        let t = Thread { [weak self] in self?.loop() }
        t.name = "qunxia.emu"
        t.qualityOfService = .userInteractive
        t.stackSize = 4 << 20
        t.start()
    }

    func stop() {
        lock.lock()
        running = false
        lock.signal()
        lock.unlock()
    }

    // MARK: - public submit

    /// Handoff between the connection thread and the emulation thread. A job
    /// that finishes after its caller gave up must not write into a value the
    /// caller has already returned, so the result crosses through here under a
    /// lock and a late delivery is dropped rather than raced.
    private final class Slot {
        private let lock = NSLock()
        private let sem = DispatchSemaphore(value: 0)
        private var value: Result?
        private var abandoned = false

        func deliver(_ result: Result) {
            lock.lock()
            if !abandoned { value = result }
            lock.unlock()
            sem.signal()
        }

        func take(timeout: TimeInterval) -> Result? {
            let arrived = sem.wait(timeout: .now() + timeout) == .success
            lock.lock()
            defer { lock.unlock() }
            if !arrived { abandoned = true }
            return value
        }
    }

    /// How long a job may take before the caller stops believing in it.
    ///
    /// A constant here was a ceiling below the work the request asked for: an
    /// action of 2794 frames followed by a 2000-frame settle needs 68 seconds
    /// and the ceiling was 60, so the caller was told the action failed while
    /// the emulator went on pressing its keys. Size it from the frames the job
    /// contains instead, at a fifth of nominal speed, the way the headless
    /// server sizes its own input budget. `minimum` stays a floor for the
    /// native calls that are not measured in frames.
    private static func budget(_ steps: [Step], _ settle: Settle, minimum: TimeInterval) -> TimeInterval {
        var frames = 0
        for step in steps {
            switch step {
            case .press(_, let hold): frames += max(1, hold) + 2
            case .wait(let n): frames += max(0, n)
            case .mouseMove: frames += 2
            case .mouseClick: frames += 5
            case .save, .load, .reset: frames += 30
            }
        }
        // stableFrames is Int.max for a fixed settle; the cap is maxFrames.
        frames += max(settle.maxFrames, settle.reactFrames + min(settle.stableFrames, settle.maxFrames))
        return max(minimum, Double(frames) / max(1.0, core_fps()) * 5 + 0.5)
    }

    /// Blocks the caller (an API connection thread) until the action has been
    /// applied and the screen has settled.
    func submitSync(_ steps: [Step], settle: Settle = .default, scale: Int = 2,
                    wantShot: Bool = true, atLeast: TimeInterval = 20) -> Result {
        let slot = Slot()
        lock.lock()
        jobs.append(Job(steps: steps, settle: settle, scale: scale, wantShot: wantShot) { r in
            slot.deliver(r)
        })
        lock.signal()
        lock.unlock()
        return slot.take(timeout: Self.budget(steps, settle, minimum: atLeast))
            ?? Result(ok: false, detail: "timeout", shot: nil, changed: false)
    }

    /// Fire-and-forget, used by the native key handler in the window.
    func setKey(_ retrok: Int, down: Bool) {
        lock.lock()
        pendingNativeKeys.append((retrok, down))
        lock.signal()
        lock.unlock()
    }

    func snapshot(scale: Int = 2) -> Shot? {
        Self.capture(scale: scale)
    }

    // MARK: - loop

    private func loop() {
        var next = CFAbsoluteTimeGetCurrent()
        while true {
            lock.lock()
            let alive = running
            let job = jobs.isEmpty ? nil : jobs.removeFirst()
            lock.unlock()
            if !alive { return }

            if let job {
                run(job)
                next = CFAbsoluteTimeGetCurrent()
                continue
            }

            step()
            next += frameBudget
            let now = CFAbsoluteTimeGetCurrent()
            if next > now {
                Thread.sleep(forTimeInterval: next - now)
            } else if now - next > 0.25 {
                next = now  // fell far behind (window drag, breakpoint): resync
            }
        }
    }

    private func step() {
        applyPendingNativeKeys()
        core_run_frame()
        onFrame?()
    }

    private func applyPendingNativeKeys() {
        lock.lock()
        let pending = pendingNativeKeys
        pendingNativeKeys.removeAll(keepingCapacity: true)
        lock.unlock()
        for (key, down) in pending {
            if down { nativeKeys.insert(key) } else { nativeKeys.remove(key) }
            syncKey(key)
        }
    }

    private func setActionKey(_ key: Int, down: Bool) {
        if down { actionKeys.insert(key) } else { actionKeys.remove(key) }
        syncKey(key)
    }

    private func syncKey(_ key: Int) {
        let down = nativeKeys.contains(key) || actionKeys.contains(key)
        if down == effectiveKeys.contains(key) { return }
        if down { effectiveKeys.insert(key) } else { effectiveKeys.remove(key) }
        core_key(Int32(key), down)
    }

    private func resyncKeysAfterCoreReset() {
        effectiveKeys.removeAll()
        actionKeys.removeAll()
        for key in nativeKeys { syncKey(key) }
    }

    private func run(_ job: Job) {
        var ok = true
        var detail = "ok"
        let baseline = core_frame_hash()

        for s in job.steps {
            switch s {
            case .press(let combo, let frames):
                for k in combo { setActionKey(k, down: true) }
                pump(max(1, frames))
                for k in combo.reversed() { setActionKey(k, down: false) }
                pump(2)
            case .wait(let n):
                pump(max(0, n))
            case .mouseMove(let dx, let dy):
                core_mouse_move(Int32(dx), Int32(dy))
                pump(2)
            case .mouseClick(let b):
                core_mouse_button(Int32(b), true)
                pump(3)
                core_mouse_button(Int32(b), false)
                pump(2)
            case .save(let url):
                ok = core_save_state(url.path)
                if !ok { detail = String(cString: core_last_error()) }
            case .load(let url):
                ok = core_load_state(url.path)
                if ok { resyncKeysAfterCoreReset() }
                if !ok { detail = String(cString: core_last_error()) }
            case .reset:
                core_reset()
                resyncKeysAfterCoreReset()
                pump(30)
            }
            if !ok { break }
        }

        let (waited, changed) = settleFrames(job.settle, baseline: baseline)
        let shot = job.wantShot ? Self.capture(scale: job.scale, waited: waited) : nil
        job.done(Result(ok: ok, detail: detail, shot: shot, changed: changed, waited: waited))
    }

    private func pump(_ n: Int) {
        guard n > 0 else { return }
        var next = CFAbsoluteTimeGetCurrent()
        for _ in 0..<n {
            step()
            next += frameBudget
            let now = CFAbsoluteTimeGetCurrent()
            if next > now { Thread.sleep(forTimeInterval: next - now) } else { next = now }
        }
    }

    /// Phase 1: give the game `reactFrames` to move at all.
    /// Phase 2: once it has moved, run until the picture holds still.
    /// Returns (frames waited, whether anything changed).
    private func settleFrames(_ s: Settle, baseline: UInt64) -> (Int, Bool) {
        var lastHash = baseline
        var stable = 0
        var n = 0
        var reacted = s.reactFrames == 0
        var next = CFAbsoluteTimeGetCurrent()
        while n < s.maxFrames {
            step()
            n += 1
            let h = core_frame_hash()
            if !reacted {
                if h != baseline { reacted = true; stable = 0; lastHash = h }
                else if n >= s.reactFrames { break }   // the action did nothing visible
            } else {
                if h == lastHash { stable += 1 } else { stable = 0; lastHash = h }
                if n >= s.minFrames && stable >= s.stableFrames { break }
            }
            next += frameBudget
            let now = CFAbsoluteTimeGetCurrent()
            if next > now { Thread.sleep(forTimeInterval: next - now) } else { next = now }
        }
        return (n, reacted)
    }

    // MARK: - capture

    static func capture(scale rawScale: Int, waited: Int = 0) -> Shot? {
        let scale = min(6, max(1, rawScale))
        core_lock()
        let w = Int(core_width())
        let h = Int(core_height())
        let pitch = Int(core_pitch())
        guard w > 0, h > 0, let src = core_pixels() else {
            core_unlock()
            return nil
        }
        let ow = w * scale
        let oh = h * scale
        var rgba = [UInt8](repeating: 255, count: ow * oh * 4)
        rgba.withUnsafeMutableBufferPointer { dst in
            guard let out = dst.baseAddress else { return }
            for y in 0..<h {
                let row = src.advanced(by: y * pitch).assumingMemoryBound(to: UInt32.self)
                for x in 0..<w {
                    let p = row[x]
                    let r = UInt8((p >> 16) & 0xFF)
                    let g = UInt8((p >> 8) & 0xFF)
                    let b = UInt8(p & 0xFF)
                    for sy in 0..<scale {
                        let base = ((y * scale + sy) * ow + x * scale) * 4
                        for sx in 0..<scale {
                            let o = base + sx * 4
                            out[o] = r
                            out[o + 1] = g
                            out[o + 2] = b
                            out[o + 3] = 255
                        }
                    }
                }
            }
        }
        let serial = core_frame_serial()
        core_unlock()

        guard let provider = CGDataProvider(data: Data(rgba) as CFData),
              let image = CGImage(
                width: ow, height: oh, bitsPerComponent: 8, bitsPerPixel: 32,
                bytesPerRow: ow * 4, space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.noneSkipLast.rawValue),
                provider: provider, decode: nil, shouldInterpolate: false, intent: .defaultIntent
              ) else { return nil }

        let out = NSMutableData()
        guard let dest = CGImageDestinationCreateWithData(out, UTType.png.identifier as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(dest, image, nil)
        guard CGImageDestinationFinalize(dest) else { return nil }
        return Shot(png: out as Data, width: ow, height: oh, scale: scale, waited: waited, frame: serial)
    }
}
