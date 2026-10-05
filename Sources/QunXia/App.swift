import AppKit
import Metal
import Foundation
import CoreHost

@main
final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var content: ContentView!
    var metal: MetalView!
    var api: ControlAPI!
    var emu: Emulator!
    var audio: AudioOut!
    var saver: GameSave!
    let log = ActionLog()

    static func main() {
        let app = NSApplication.shared
        let d = AppDelegate()
        app.delegate = d
        app.setActivationPolicy(.regular)
        app.run()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        let root = Self.repoRoot()
        let core = root.appendingPathComponent("Cores/dosbox_pure_libretro.dylib")
        let game = Self.gamePath(root: root)
        let saves = root.appendingPathComponent("saves")
        try? FileManager.default.createDirectory(at: saves, withIntermediateDirectories: true)

        core_set_log { ptr in
            guard let ptr else { return }
            FileHandle.standardError.write(Data((String(cString: ptr) + "\n").utf8))
        }

        Self.applyOptionOverrides(log: log)

        guard core_init(core.path, game.path, saves.path) else {
            fail("無法啟動模擬器", String(cString: core_last_error()) + "\ncore: \(core.path)\ngame: \(game.path)")
            return
        }

        emu = Emulator(log: log)
        emu.start()

        audio = AudioOut()
        if !audio.start(sampleRate: core_sample_rate()) {
            log.add("AUDIO", "unavailable", ok: false)
        }

        let port = UInt16(Self.flagValue("--port").flatMap(UInt16.init) ?? 8765)
        saver = GameSave(emu: emu, gameDir: game.deletingLastPathComponent())
        do {
            api = try ControlAPI(port: port, log: log, saveDir: saves,
                                 skillsDir: root.appendingPathComponent("skills"), emu: emu,
                                 saver: saver)
        } catch {
            log.add("LISTEN", ":\(port)", payload: "\(error)", ok: false)
        }

        guard let device = MTLCreateSystemDefaultDevice(), let view = MetalView(device: device) else {
            fail("無法建立 Metal 裝置", "MTLCreateSystemDefaultDevice returned nil")
            return
        }
        metal = view

        view.onKey = { [weak self] code, chars, down in self?.handleNativeKey(code, chars, down: down) }
        view.onRepeat = { [weak self] code, chars in self?.handleNativeRepeat(code, chars) }
        view.onFlags = { [weak self] flags in self?.handleModifiers(flags) }

        let pane = ContentView()
        pane.metal = view
        pane.history = HistoryView(log: log, port: port)
        pane.progress = ProgressView(saver: saver)
        pane.progress.start()
        content = pane

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 320 * 3 + ContentView.sidebarWidth, height: 200 * 3),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "金庸群俠傳"
        window.delegate = self
        window.contentView = pane
        window.setContentSize(pane.contentSize(forScale: 3))

        buildMenu()
        window.center()
        window.makeKeyAndOrderFront(nil)
        window.makeFirstResponder(view)
        NSApp.activate(ignoringOtherApps: true)

        log.add("BOOT", game.path.replacingOccurrences(of: root.path + "/", with: ""),
                payload: String(format: "%.2f fps · %.0f Hz", core_fps(), core_sample_rate()))
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        audio?.stop()
        emu?.stop()
        core_shutdown()
    }

    // MARK: - input

    private var heldModifiers: NSEvent.ModifierFlags = []

    private func handleNativeKey(_ keyCode: UInt16, _ chars: String?, down: Bool) {
        guard let k = RetroKey.fromMacKeyCode(keyCode, characters: chars) else { return }
        emu.setKey(k, down: down)
        if down { log.add("KEY", RetroKey.label(for: k), payload: "local") }
    }

    /// Only the directions repeat faster than the emulated keyboard: a held
    /// enter or escape repeating every 30 ms would skip dialogue unread.
    private func handleNativeRepeat(_ keyCode: UInt16, _ chars: String?) {
        guard let k = RetroKey.fromMacKeyCode(keyCode, characters: chars),
              RetroKey.windowRepeats.contains(k) else { return }
        emu.repeatKey(k)
    }

    /// A key held while the window loses focus never sends its keyUp here,
    /// and it would stay down in the game: walking on, and hiding the API's
    /// own presses of that key.
    func windowDidResignKey(_ notification: Notification) {
        emu?.releaseNativeKeys()
        heldModifiers = []
    }

    private func handleModifiers(_ flags: NSEvent.ModifierFlags) {
        // AppKit drops the keyUp of a key released while ⌘ is down, so a ⌘
        // shortcut lets go of everything first; the loop below then presses
        // again whichever of shift, control and option are still held.
        if flags.contains(.command) && !heldModifiers.contains(.command) {
            emu.releaseNativeKeys()
            heldModifiers = []
        }
        let map: [(NSEvent.ModifierFlags, Int)] = [(.shift, 304), (.control, 306), (.option, 308)]
        for (flag, key) in map {
            let was = heldModifiers.contains(flag)
            let now = flags.contains(flag)
            if was != now { emu.setKey(key, down: now) }
        }
        heldModifiers = flags
    }

    // MARK: - menu

    private func buildMenu() {
        let menu = NSMenu()

        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "關於", action: nil, keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "離開", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        menu.addItem(appItem)

        let gameItem = NSMenuItem()
        let gameMenu = NSMenu(title: "遊戲")
        add(gameMenu, "快速存檔", #selector(quickSave), "s")
        add(gameMenu, "快速讀檔", #selector(quickLoad), "l")
        gameMenu.addItem(.separator())
        add(gameMenu, "重新啟動模擬器", #selector(resetCore), "r")
        gameItem.submenu = gameMenu
        menu.addItem(gameItem)

        let viewItem = NSMenuItem()
        let viewMenu = NSMenu(title: "顯示")
        for k in 1...5 {
            let item = NSMenuItem(title: "\(k)× (\(320 * k)×\(200 * k))", action: #selector(setScale(_:)), keyEquivalent: "\(k)")
            item.tag = k
            item.target = self
            viewMenu.addItem(item)
        }
        viewMenu.addItem(.separator())
        add(viewMenu, "顯示 API 紀錄", #selector(toggleLog), "i")
        add(viewMenu, "4:3 比例", #selector(toggleAspect), "0")
        add(viewMenu, "靜音", #selector(toggleMute), "m")
        viewMenu.addItem(.separator())
        let fs = NSMenuItem(title: "全螢幕", action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f")
        fs.keyEquivalentModifierMask = [.command, .control]
        viewMenu.addItem(fs)
        viewItem.submenu = viewMenu
        menu.addItem(viewItem)

        NSApp.mainMenu = menu
    }

    private func add(_ menu: NSMenu, _ title: String, _ sel: Selector, _ key: String) {
        let item = NSMenuItem(title: title, action: sel, keyEquivalent: key)
        item.target = self
        menu.addItem(item)
    }

    /// submitSync blocks until the emulator has run the job, so menu actions go
    /// off the main thread or the window freezes for the duration.
    private func background(_ verb: String, _ target: String, _ work: @escaping () -> Emulator.Result) {
        DispatchQueue.global(qos: .userInitiated).async { [log] in
            let r = work()
            log.add(verb, target, payload: r.ok ? "local" : r.detail, ok: r.ok)
        }
    }

    @objc private func quickSave() {
        let url = Self.repoRoot().appendingPathComponent("saves/slot1.state")
        background("SAVE", "slot1") { [emu] in emu!.submitSync([.save(url)], settle: .fixed(1), wantShot: false) }
    }

    @objc private func quickLoad() {
        let url = Self.repoRoot().appendingPathComponent("saves/slot1.state")
        background("LOAD", "slot1") { [emu] in emu!.submitSync([.load(url)], settle: .fixed(4), wantShot: false) }
    }

    @objc private func resetCore() {
        background("RESET", "/") { [emu] in emu!.submitSync([.reset], settle: .fixed(60), wantShot: false, atLeast: 60) }
    }

    @objc private func toggleAspect(_ sender: NSMenuItem) {
        metal.stretchTo43.toggle()
        sender.state = metal.stretchTo43 ? .on : .off
        resize(toScale: content.currentScale(contentWidth: window.contentLayoutRect.width))
    }

    @objc private func setScale(_ sender: NSMenuItem) {
        resize(toScale: CGFloat(sender.tag))
    }

    @objc private func toggleLog(_ sender: NSMenuItem) {
        let scale = content.currentScale(contentWidth: window.contentLayoutRect.width)
        content.showLog.toggle()
        sender.state = content.showLog ? .on : .off
        resize(toScale: scale)
    }

    private func resize(toScale scale: CGFloat) {
        guard !(window.styleMask.contains(.fullScreen)) else { return }
        window.setContentSize(content.contentSize(forScale: scale))
        content.needsLayout = true
    }

    /// Snap every resize so the game pane is an exact multiple of 320x200:
    /// no letterbox, and nearest sampling stays even.
    func windowWillResize(_ sender: NSWindow, to frameSize: NSSize) -> NSSize {
        let chrome = sender.frame.height - sender.contentLayoutRect.height
        let contentH = frameSize.height - chrome
        let scale = max(1, (contentH / ContentView.baseHeight).rounded())
        let size = content.contentSize(forScale: scale)
        return NSSize(width: size.width, height: size.height + chrome)
    }

    @objc private func toggleMute(_ sender: NSMenuItem) {
        audio.setMuted(!audio.muted)
        sender.state = audio.muted ? .on : .off
    }

    // MARK: - paths

    private func fail(_ title: String, _ detail: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = detail
        alert.runModal()
        NSApp.terminate(nil)
    }

    /// `--set dosbox_pure_cycles=77000` on the command line, or QUNXIA_SET="k=v,k=v".
    static func applyOptionOverrides(log: ActionLog) {
        var pairs: [String] = []
        var args = Array(CommandLine.arguments.dropFirst())
        while let i = args.firstIndex(of: "--set"), i + 1 < args.count {
            pairs.append(args[i + 1])
            args.removeSubrange(i...(i + 1))
        }
        if let env = ProcessInfo.processInfo.environment["QUNXIA_SET"] {
            pairs.append(contentsOf: env.split(separator: ",").map(String.init))
        }
        for pair in pairs {
            let kv = pair.split(separator: "=", maxSplits: 1)
            guard kv.count == 2 else { continue }
            core_set_option(String(kv[0]), String(kv[1]))
            log.add("OPT", String(kv[0]), payload: String(kv[1]))
        }
    }

    static func flagValue(_ name: String) -> String? {
        let args = CommandLine.arguments
        guard let i = args.firstIndex(of: name), i + 1 < args.count else { return nil }
        return args[i + 1]
    }

    static func repoRoot() -> URL {
        let cwd = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        if FileManager.default.fileExists(atPath: cwd.appendingPathComponent("Cores/dosbox_pure_libretro.dylib").path) {
            return cwd
        }
        // Running from .build/release/QunXia: walk up to the package root.
        var exe = URL(fileURLWithPath: CommandLine.arguments[0]).resolvingSymlinksInPath().deletingLastPathComponent()
        for _ in 0..<5 {
            if FileManager.default.fileExists(atPath: exe.appendingPathComponent("Cores/dosbox_pure_libretro.dylib").path) {
                return exe
            }
            exe.deleteLastPathComponent()
        }
        return cwd
    }

    static func gamePath(root: URL) -> URL {
        let args = CommandLine.arguments.dropFirst()
        var skip = false
        for a in args {
            if skip { skip = false; continue }
            if a == "--port" || a == "--set" { skip = true; continue }
            if a.hasPrefix("-") { continue }
            return URL(fileURLWithPath: a)
        }
        let game = root.appendingPathComponent("game")
        let play = game.appendingPathComponent("PLAY.BAT")
        if FileManager.default.fileExists(atPath: play.path) { return play }
        return game
    }
}


/// Game pane plus an optional fixed-width log sidebar. Sized in whole multiples
/// of the DOS resolution so the game never sits inside a black border.
final class ContentView: NSView {
    static let sidebarWidth: CGFloat = 340
    static let baseWidth: CGFloat = 320
    static let baseHeight: CGFloat = 200

    var metal: MetalView! { didSet { swap(old: oldValue, new: metal) } }
    var history: HistoryView! { didSet { swap(old: oldValue, new: history) } }
    var progress: ProgressView! { didSet { swap(old: oldValue, new: progress) } }
    var showLog = true {
        didSet {
            history?.isHidden = !showLog
            progress?.isHidden = !showLog
            needsLayout = true
        }
    }

    private func swap(old: NSView?, new: NSView?) {
        old?.removeFromSuperview()
        guard let new else { return }
        new.translatesAutoresizingMaskIntoConstraints = true
        addSubview(new)
        needsLayout = true
    }

    var sidebar: CGFloat { showLog ? Self.sidebarWidth : 0 }

    func contentSize(forScale scale: CGFloat) -> NSSize {
        let k = max(1, scale.rounded())
        return NSSize(width: Self.baseWidth * k + sidebar, height: Self.baseHeight * k)
    }

    func currentScale(contentWidth: CGFloat) -> CGFloat {
        max(1, ((contentWidth - sidebar) / Self.baseWidth).rounded())
    }

    override var isFlipped: Bool { false }

    override func layout() {
        super.layout()
        let w = bounds.width, h = bounds.height
        let side = min(sidebar, max(0, w - Self.baseWidth))
        let x = (w - side).rounded()
        // The progress panel is a fixed strip at the top of the sidebar; the
        // log takes whatever is left, which is what grows with the window.
        let panel = side <= 1 ? 0 : min(h, progress?.intrinsicContentSize.height ?? 0)
        metal?.frame = NSRect(x: 0, y: 0, width: x, height: h)
        progress?.frame = NSRect(x: x, y: h - panel, width: side, height: panel)
        history?.frame = NSRect(x: x, y: 0, width: side, height: h - panel)
        history?.isHidden = !showLog || side <= 1
        progress?.isHidden = !showLog || side <= 1
    }
}
