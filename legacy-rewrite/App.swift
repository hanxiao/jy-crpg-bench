import AppKit
import Metal
import MetalKit

@main
final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var game: Game!
    var metalView: MetalView!

    static func main() {
        let app = NSApplication.shared
        let delegate = AppDelegate()
        app.delegate = delegate
        app.setActivationPolicy(.regular)
        app.run()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            let dir = Self.resolveGameDir()
            let res = try Resources(dir: dir)
            game = try Game(res: res)
            if CommandLine.arguments.contains("--probe") {
                Self.probe(game)
                exit(0)
            }
        } catch {
            let alert = NSAlert()
            alert.messageText = "無法載入金庸群俠傳資料"
            alert.informativeText = "把原版 DOS 資料放到 game/ 目錄，或用參數傳入路徑。\n\(error)"
            alert.runModal()
            NSApp.terminate(nil)
            return
        }

        guard let device = MTLCreateSystemDefaultDevice(),
              let view = MetalView(device: device) else {
            NSApp.terminate(nil)
            return
        }
        metalView = view
        view.setPalette(game.res.palette)
        view.onDraw = { [weak self] fb in
            guard let self else { return }
            self.game.tick()
            self.game.draw(into: fb)
        }

        let scale = 2
        let rect = NSRect(x: 0, y: 0, width: Screen.width * scale, height: Screen.height * scale)
        window = NSWindow(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "金庸群俠傳"
        window.contentView = view
        let keys = KeyView(game: game)
        keys.frame = view.bounds
        keys.autoresizingMask = [.width, .height]
        view.addSubview(keys)
        window.center()
        window.makeKeyAndOrderFront(nil)
        window.acceptsMouseMovedEvents = true
        window.makeFirstResponder(keys)
        NSApp.activate(ignoringOtherApps: true)

        let menu = NSMenu()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "離開", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let appItem = NSMenuItem()
        appItem.submenu = appMenu
        menu.addItem(appItem)
        NSApp.mainMenu = menu
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    private static func probe(_ game: Game) {
        print("roles \(game.save.roles.count) items \(game.save.items.count) scenes \(game.save.scenes.count)")
        print("magics \(game.save.magics.count) shops \(game.save.shops.count)")
        print("mmap \(game.res.mmap.count) smap \(game.res.smap.count) wmap \(game.res.wmap.count) heads \(game.res.heads.count)")
        print("kdef \(game.res.kdef.count) talks \(game.res.talks.count) wars \(game.res.wars.count)")
        print("start \(game.save.roles.first?.name ?? "?") at \(game.save.base.mx),\(game.save.base.my)")
        if let talk = game.res.talks.first(where: { !$0.isEmpty }) {
            print("talk0 \(talk.prefix(40))")
        }
        let fb = Framebuffer()
        game.draw(into: fb)
        func writePPM(_ path: String) {
            var rgb = [UInt8]()
            rgb.reserveCapacity(Screen.width * Screen.height * 3)
            for p in fb.pixels {
                let (r, g, b, _) = game.res.palette.rgba(p)
                rgb.append(UInt8(max(0, min(255, Int(r * 255)))))
                rgb.append(UInt8(max(0, min(255, Int(g * 255)))))
                rgb.append(UInt8(max(0, min(255, Int(b * 255)))))
            }
            var data = Data("P6\n\(Screen.width) \(Screen.height)\n255\n".utf8)
            data.append(contentsOf: rgb)
            try? data.write(to: URL(fileURLWithPath: path))
            print("wrote \(path)")
        }
        writePPM("/tmp/qunxia-title.ppm")
        game.whereMode = .world
        game.mx = game.save.base.mx
        game.my = game.save.base.my
        game.draw(into: fb)
        writePPM("/tmp/qunxia-world.ppm")
        if game.save.scenes.indices.contains(70) {
            game.whereMode = .scene
            game.curScene = 70
            game.sx = game.save.scenes[70].enterX
            game.sy = game.save.scenes[70].enterY
            game.draw(into: fb)
            writePPM("/tmp/qunxia-scene.ppm")
        }
    }

    private static func resolveGameDir() -> URL {
        let args = CommandLine.arguments.dropFirst().filter { !$0.hasPrefix("-") }
        if let path = args.first {
            return URL(fileURLWithPath: path).standardizedFileURL
        }
        let cwd = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        let candidates = [
            cwd.appendingPathComponent("game"),
            cwd.appendingPathComponent("jy-metal/game"),
            URL(fileURLWithPath: "/Users/hanxiao/Documents/jy-metal/game"),
        ]
        for url in candidates where FileManager.default.fileExists(atPath: url.appendingPathComponent("MMAP.GRP").path) {
            return url
        }
        return cwd.appendingPathComponent("game")
    }
}

final class KeyView: NSView {
    weak var game: Game?
    init(game: Game) {
        self.game = game
        super.init(frame: .zero)
        autoresizingMask = [.width, .height]
    }
    required init?(coder: NSCoder) { fatalError() }
    override var acceptsFirstResponder: Bool { true }

    override func keyDown(with event: NSEvent) {
        game?.handleKey(Self.map(event))
    }

    override func keyUp(with event: NSEvent) {
        game?.handleKeyUp(Self.map(event))
    }

    private static func map(_ event: NSEvent) -> Key {
        switch event.keyCode {
        case 126, 13: return .up      // up / W
        case 125, 1: return .down     // down / S
        case 123, 0: return .left     // left / A
        case 124, 2: return .right    // right / D
        case 36, 49: return .ok       // enter / space
        case 53, 51: return .cancel   // esc / delete
        case 16: return .yes          // Y
        case 45: return .no           // N
        default: return .other(event.keyCode)
        }
    }
}
