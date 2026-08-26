import Foundation
import Network
import CoreHost

/// Small HTTP surface so an agent can drive the DOS game.
/// Every endpoint that changes game state replies with the screen that
/// resulted from it, so one request == one action == one observation.
final class ControlAPI {
    // Four frames can fit inside one slow DOS redraw, allowing keydown and
    // keyup to be consumed in the same game-loop iteration. Ten remains well
    // below the held-key repeat delay while reliably producing one tap.
    private static let defaultTapFrames = 10

    private let listener: NWListener
    private let log: ActionLog
    private let saveDir: URL
    private let emu: Emulator
    let port: UInt16

    init(port: UInt16, log: ActionLog, saveDir: URL, emu: Emulator) throws {
        self.port = port
        self.log = log
        self.saveDir = saveDir
        self.emu = emu
        let params = NWParameters.tcp
        params.allowLocalEndpointReuse = true
        listener = try NWListener(using: params, on: NWEndpoint.Port(rawValue: port)!)
        listener.newConnectionHandler = { [weak self] conn in
            let q = DispatchQueue(label: "qunxia.api.conn")
            conn.start(queue: q)
            self?.receive(conn, buffer: Data())
        }
        // start() is async: without this a failed bind is silent and the whole
        // agent API just never answers.
        listener.stateUpdateHandler = { [weak log] state in
            switch state {
            case .ready:
                log?.add("LISTEN", "http://127.0.0.1:\(port)")
            case .failed(let err), .waiting(let err):
                let msg = "control API cannot listen on port \(port): \(err)"
                log?.add("LISTEN", ":\(port)", payload: "\(err)", ok: false)
                FileHandle.standardError.write(Data((msg + "\n").utf8))
            default:
                break
            }
        }
        listener.start(queue: DispatchQueue(label: "qunxia.api"))
    }

    // MARK: - connection

    private func receive(_ conn: NWConnection, buffer: Data) {
        conn.receive(minimumIncompleteLength: 1, maximumLength: 1 << 16) { [weak self] data, _, isComplete, err in
            guard let self else { conn.cancel(); return }
            var buf = buffer
            if let data { buf.append(data) }
            if err != nil || (isComplete && buf.isEmpty) { conn.cancel(); return }

            guard let req = Request(buf) else {
                if isComplete { conn.cancel() } else { self.receive(conn, buffer: buf) }
                return
            }
            DispatchQueue.global(qos: .userInitiated).async {
                let response = self.handle(req)
                conn.send(content: response, completion: .contentProcessed { _ in conn.cancel() })
            }
        }
    }

    private struct Request {
        let method: String
        let path: String
        let query: [String: String]
        let headers: [String: String]
        let body: String

        init?(_ data: Data) {
            guard let headEnd = data.range(of: Data("\r\n\r\n".utf8)) else { return nil }
            guard let head = String(data: data[..<headEnd.lowerBound], encoding: .utf8) else { return nil }
            var lines = head.components(separatedBy: "\r\n")
            guard !lines.isEmpty else { return nil }
            let start = lines.removeFirst().split(separator: " ", omittingEmptySubsequences: true)
            guard start.count >= 2 else { return nil }
            method = String(start[0]).uppercased()
            let target = String(start[1])
            var h: [String: String] = [:]
            for line in lines {
                guard let c = line.firstIndex(of: ":") else { continue }
                h[line[..<c].lowercased()] = line[line.index(after: c)...].trimmingCharacters(in: .whitespaces)
            }
            headers = h

            let comps = target.split(separator: "?", maxSplits: 1, omittingEmptySubsequences: false)
            path = String(comps[0])
            var q: [String: String] = [:]
            if comps.count > 1 {
                for pair in comps[1].split(separator: "&") {
                    let kv = pair.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
                    let k = String(kv[0]).removingPercentEncoding ?? String(kv[0])
                    let v = kv.count > 1 ? (String(kv[1]).removingPercentEncoding ?? String(kv[1])) : ""
                    q[k] = v
                }
            }
            query = q

            let want = Int(h["content-length"] ?? "0") ?? 0
            let bodyData = data[headEnd.upperBound...]
            if bodyData.count < want { return nil }  // need more bytes
            body = String(data: bodyData.prefix(want), encoding: .utf8) ?? ""
        }

        var json: [String: Any] {
            guard let d = body.data(using: .utf8),
                  let o = try? JSONSerialization.jsonObject(with: d) as? [String: Any] else { return [:] }
            return o
        }

        /// JSON body first, then query string. Lets `POST /key?key=down` work too.
        func value(_ key: String) -> Any? { json[key] ?? query[key] }
        func string(_ key: String) -> String? {
            if let s = json[key] as? String { return s }
            return query[key]
        }
        func int(_ key: String) -> Int? {
            if let i = json[key] as? Int { return i }
            if let d = json[key] as? Double { return Int(d) }
            if let s = query[key] { return Int(s) }
            return nil
        }
        func strings(_ key: String) -> [String]? {
            if let a = json[key] as? [String] { return a }
            if let s = json[key] as? String { return [s] }
            if let s = query[key] { return s.split(separator: ",").map(String.init) }
            return nil
        }
        var wantsRawPNG: Bool {
            query["format"] == "png" || (headers["accept"] ?? "").contains("image/png")
        }
        var wantsImage: Bool {
            !(query["image"] == "0" || query["image"] == "false" || (json["image"] as? Bool) == false)
        }
    }

    // MARK: - routing

    private func handle(_ r: Request) -> Data {
        let scale = min(6, max(1, r.int("scale") ?? 2))

        switch (r.method, r.path) {
        case ("GET", "/"), ("GET", "/help"):
            log.add("GET", r.path)
            return respond(200, "text/plain; charset=utf-8", Data(Self.help.utf8))

        case ("GET", "/screen"):
            guard let shot = emu.snapshot(scale: 1) else {
                log.add("GET", "/screen", ok: false)
                return respond(503, "application/json", json(["ok": false, "error": "no frame yet"]))
            }
            log.add("GET", "/screen", image: shot.png)
            if r.query["format"] == "png" {
                return respond(200, "image/png", shot.png)
            }
            return reply(r, ok: true, extra: [:], shot: shot)

        case ("GET", "/history"):
            log.add("GET", "/history")
            let arr = log.items.suffix(r.int("limit") ?? 100).map { rec -> [String: Any] in
                ["time": Self.iso.string(from: rec.time), "verb": rec.verb,
                 "target": rec.target, "payload": rec.payload, "ok": rec.ok]
            }
            return respond(200, "application/json", json(arr))

        case ("GET", "/keys"):
            return respond(200, "application/json", json(["keys": RetroKey.names]))

        case ("GET", "/slots"):
            let files = (try? FileManager.default.contentsOfDirectory(at: saveDir, includingPropertiesForKeys: [.fileSizeKey, .contentModificationDateKey])) ?? []
            let slots = files.filter { $0.pathExtension == "state" }.sorted { $0.lastPathComponent < $1.lastPathComponent }.map { u -> [String: Any] in
                let a = try? u.resourceValues(forKeys: [.fileSizeKey, .contentModificationDateKey])
                return ["name": u.deletingPathExtension().lastPathComponent,
                        "bytes": a?.fileSize ?? 0,
                        "modified": Self.iso.string(from: a?.contentModificationDate ?? Date(timeIntervalSince1970: 0))]
            }
            return respond(200, "application/json", json(["slots": slots]))

        case ("POST", "/key"):
            guard let name = r.string("key"), let combo = RetroKey.parseCombo(name) else {
                log.add("KEY", r.string("key") ?? "?", ok: false)
                return respond(400, "application/json", json(["ok": false, "error": "unknown key", "hint": "GET /keys"]))
            }
            let hold = max(1, r.int("hold") ?? Self.defaultTapFrames)
            // Logged before the keys go in, so the pane shows an action
            // starting rather than reporting one already over.
            log.add("KEY", name)
            let res = emu.submitSync([.press(combo, frames: hold)], settle: settle(r), scale: scale, wantShot: r.wantsImage)
            return reply(r, ok: res.ok, extra: ["key": name], shot: res.shot, changed: res.changed)

        case ("POST", "/keys"):
            guard let names = r.strings("keys"), !names.isEmpty else {
                return respond(400, "application/json", json(["ok": false, "error": "keys required"]))
            }
            let hold = max(1, r.int("hold") ?? Self.defaultTapFrames)
            let gap = max(0, r.int("gap") ?? 6)
            var steps: [Emulator.Step] = []
            var bad: [String] = []
            for (i, n) in names.enumerated() {
                guard let combo = RetroKey.parseCombo(n) else { bad.append(n); continue }
                steps.append(.press(combo, frames: hold))
                if i != names.count - 1, gap > 0 { steps.append(.wait(gap)) }
            }
            if !bad.isEmpty {
                log.add("KEYS", names.joined(separator: ","), payload: "bad: \(bad.joined(separator: ","))", ok: false)
                return respond(400, "application/json", json(["ok": false, "error": "unknown keys", "keys": bad]))
            }
            log.add("KEYS", names.joined(separator: ","))
            let res = emu.submitSync(steps, settle: settle(r), scale: scale, wantShot: r.wantsImage, timeout: 60)
            return reply(r, ok: res.ok, extra: ["keys": names], shot: res.shot, changed: res.changed)

        case ("POST", "/wait"):
            let frames = r.int("frames") ?? Int(Double(r.int("ms") ?? 500) * core_fps() / 1000.0)
            log.add("WAIT", "\(frames)f")
            let res = emu.submitSync([.wait(max(0, min(frames, 4000)))], settle: settle(r, fallbackMin: 1), scale: scale, wantShot: r.wantsImage, timeout: 120)
            return reply(r, ok: res.ok, extra: ["frames": frames], shot: res.shot, changed: res.changed)

        case ("POST", "/save"):
            let url = slotURL(r)
            let res = emu.submitSync([.save(url)], settle: .fixed(1), scale: scale, wantShot: r.wantsImage)
            log.add("SAVE", url.deletingPathExtension().lastPathComponent, payload: res.ok ? "" : res.detail, ok: res.ok)
            return reply(r, ok: res.ok, status: res.ok ? 200 : 500,
                         extra: ["slot": url.deletingPathExtension().lastPathComponent, "error": res.ok ? "" : res.detail],
                         shot: res.shot, changed: res.changed)

        case ("POST", "/load"):
            let url = slotURL(r)
            guard FileManager.default.fileExists(atPath: url.path) else {
                log.add("LOAD", url.lastPathComponent, ok: false)
                return respond(404, "application/json", json(["ok": false, "error": "no such slot"]))
            }
            let res = emu.submitSync([.load(url)], settle: settle(r), scale: scale, wantShot: r.wantsImage)
            log.add("LOAD", url.deletingPathExtension().lastPathComponent, payload: res.ok ? "" : res.detail, ok: res.ok)
            return reply(r, ok: res.ok, status: res.ok ? 200 : 500,
                         extra: ["slot": url.deletingPathExtension().lastPathComponent, "error": res.ok ? "" : res.detail],
                         shot: res.shot, changed: res.changed)

        case ("POST", "/reset"):
            let res = emu.submitSync([.reset], settle: Emulator.Settle(minFrames: 60, maxFrames: 600, stableFrames: 6), scale: scale, wantShot: r.wantsImage, timeout: 60)
            log.add("RESET", "/", ok: res.ok)
            return reply(r, ok: res.ok, extra: [:], shot: res.shot, changed: res.changed)

        default:
            log.add(r.method, r.path, ok: false)
            return respond(404, "application/json", json(["ok": false, "error": "not found", "hint": "GET /help"]))
        }
    }

    // MARK: - helpers

    private func settle(_ r: Request, fallbackMin: Int? = nil) -> Emulator.Settle {
        if let fixed = r.int("settle") { return .fixed(max(0, min(fixed, 2000))) }
        var s = Emulator.Settle.default
        if let m = fallbackMin { s.reactFrames = m }
        if let m = r.int("react") { s.reactFrames = max(0, min(m, 2000)) }
        if let m = r.int("stable") { s.stableFrames = max(1, min(m, 600)) }
        if let m = r.int("maxsettle") { s.maxFrames = max(s.minFrames, min(m, 2000)) }
        s.maxFrames = max(s.maxFrames, s.reactFrames)
        return s
    }

    private func slotURL(_ r: Request) -> URL {
        if let name = r.string("name"), !name.isEmpty {
            let safe = name.replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "..", with: "_")
            return saveDir.appendingPathComponent("\(safe).state")
        }
        return saveDir.appendingPathComponent("slot\(r.int("slot") ?? 1).state")
    }

    private func reply(_ r: Request, ok: Bool, status: Int = 200, extra: [String: Any], shot: Emulator.Shot?, changed: Bool? = nil) -> Data {
        if r.wantsRawPNG, let shot {
            return respond(status, "image/png", shot.png)
        }
        var obj: [String: Any] = [
            "ok": ok,
            "width": Int(core_width()),
            "height": Int(core_height()),
            "fps": (core_fps() * 1000).rounded() / 1000,
            "frame": Int(core_frame_serial()),
            "ticks": Int(core_ticks()),
            // Poll this to tell "still animating" from "waiting for input".
            "screen": String(core_frame_hash(), radix: 16),
        ]
        if let changed { obj["changed"] = changed }
        for (k, v) in extra where !((v as? String)?.isEmpty ?? false) { obj[k] = v }
        if let shot {
            obj["image"] = "data:image/png;base64," + shot.png.base64EncodedString()
            obj["image_width"] = shot.width
            obj["image_height"] = shot.height
            obj["scale"] = shot.scale
            obj["settled_frames"] = shot.waited
        }
        return respond(status, "application/json", json(obj))
    }

    private func json(_ obj: Any) -> Data {
        (try? JSONSerialization.data(withJSONObject: obj, options: [.sortedKeys])) ?? Data("{}".utf8)
    }

    private func respond(_ status: Int, _ ctype: String, _ payload: Data) -> Data {
        let reason = [200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error", 503: "Service Unavailable"][status] ?? "Error"
        var out = Data("""
        HTTP/1.1 \(status) \(reason)\r
        Content-Type: \(ctype)\r
        Content-Length: \(payload.count)\r
        Cache-Control: no-store\r
        Access-Control-Allow-Origin: *\r
        Connection: close\r
        \r\n
        """.replacingOccurrences(of: "\n", with: "").replacingOccurrences(of: "\r", with: "\r\n").utf8)
        out.append(payload)
        return out
    }

    private static let iso: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    static let help = """
    QunXia - 金庸群俠傳 running as the original DOS binary under DOSBox Pure.

    The game takes key presses and nothing else. There is no text entry and no
    mouse, so every interaction below is a key.

    GET  /screen[?format=png]         look at the screen
    GET  /history[?limit=100]         action log
    GET  /keys                        every accepted key name
    GET  /slots                       savestates on disk
    GET  /help

    POST /key    {"key":"kp3"}        one key; "hold" frames (default 10)
    POST /keys   {"keys":["kp9","enter"]}   several in order; "gap" between
    POST /wait   {"ms":1000}          let the game run
    POST /save   {"slot":1} | {"name":"before-boss"}
    POST /load   {"slot":1}
    POST /reset

    A POST waits for the screen to react and then to hold still, so what comes
    back is the result of the action. "changed":false means nothing visible
    happened. Add ?format=png for raw bytes, ?image=0 to skip the capture.

    Movement is isometric, so the four axes are diagonals on screen:
      kp7 up-left   kp9 up-right   kp1 down-left   kp3 down-right
    The names left/up/down/right are aliases for those same four.

    Keys: kp0-kp9, arrows, enter, space, esc, y, n, a-z, 0-9, f1-f12, tab,
    backspace, and combos such as "alt+x".
    """
}
