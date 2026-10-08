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
    // Measured floor, 24 taps per point against a key whose effect is certain:
    // 1 frame lands 0-29% of the time, 2 frames 33-67%, 3 frames 79-88%,
    // 4 frames 96-100%, 5 frames and up 100%. Below five the game and the
    // caller disagree about whether a key was pressed, which is worse for an
    // agent than a refusal, so a shorter hold is a bad request.
    private static let minHoldFrames = 5
    private static let maxHoldFrames = 1200
    private static let maxKeysPerAction = 100
    private static let maxActionFrames = 2800

    private let listener: NWListener
    private let log: ActionLog
    private let saveDir: URL
    private let skillsDir: URL
    private let emu: Emulator
    /// The benchmark's own save. It runs between an agent's decisions, in the
    /// connection thread that has just finished one, so it never lands beside
    /// an action rather than after it.
    private let saver: GameSave?
    let port: UInt16

    init(port: UInt16, log: ActionLog, saveDir: URL, skillsDir: URL, emu: Emulator,
         saver: GameSave? = nil) throws {
        self.port = port
        self.log = log
        self.saveDir = saveDir
        self.skillsDir = skillsDir
        self.emu = emu
        self.saver = saver
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
                if isComplete || buf.count > Request.maxBytes { conn.cancel() }
                else { self.receive(conn, buffer: buf) }
                return
            }
            DispatchQueue.global(qos: .userInitiated).async {
                let response = self.handle(req)
                conn.send(content: response, completion: .contentProcessed { _ in conn.cancel() })
            }
        }
    }

    private struct Request {
        /// The largest request, head and body, the API reads.
        static let maxBytes = 1 << 20

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

            let want = min(max(Int(h["content-length"] ?? "0") ?? 0, 0), Request.maxBytes)
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
            // `is Bool` is not the test. JSONSerialization gives back an
            // NSNumber, and on Darwin an NSNumber holding 0 or 1 bridges to
            // Bool - so `{"times": 1}` and `{"gap": 0}`, the most ordinary
            // requests there are, were refused as if a boolean had been sent.
            // Only a real JSON true/false is a CFBoolean.
            if let number = json[key] as? NSNumber {
                if CFGetTypeID(number) == CFBooleanGetTypeID() { return nil }
                let value = number.doubleValue
                // Int(value) traps for a Double which is just beyond Int.max:
                // Double(Int.max) rounds to 2^63.  The exact conversion checks
                // representability without first converting through a trap.
                return Int(exactly: value)
            }
            if json[key] is Bool { return nil }
            if let i = json[key] as? Int { return i }
            if let d = json[key] as? Double { return Int(exactly: d) }
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
        /// Query only, as on the headless runner: one place to ask for the
        /// picture rather than two that can disagree.
        var wantsImage: Bool {
            !(query["image"] == "0" || query["image"] == "false")
        }
    }

    // MARK: - routing

    private func handle(_ r: Request) -> Data {
        let scale = min(6, max(1, r.int("scale") ?? 2))

        switch (r.method, Self.route(r.path)) {
        case ("GET", "/"):
            log.add("GET", r.path)
            return respond(200, "text/plain; charset=utf-8", Data(Self.help.utf8))

        case ("GET", "/help"):
            log.add("GET", r.path)
            // The same briefing the headless runner serves, from the same
            // files, with this host substituted in. It is the text an agent is
            // told to read, so it cannot differ between the two runners.
            if let text = briefing(lang: r.string("lang") ?? "en",
                                   coreOnly: r.string("part") == "core",
                                   base: Self.origin(r, port: port)) {
                return respond(200, "text/plain; charset=utf-8", Data(text.utf8))
            }
            return respond(200, "text/plain; charset=utf-8", Data(Self.help.utf8))

        case ("GET", "/screen"):
            // PNG is the only raw encoding here: ImageIO cannot write WebP, and
            // the headless runner's WebP and JPEG exist to save bytes on a wire
            // this runner does not have. An unsupported format says so rather
            // than quietly answering with JSON.
            let format = r.query["format"] ?? ""
            guard format.isEmpty || format == "png" else {
                return respond(400, "application/json", json(["ok": false,
                    "error": "format must be png; omit it for JSON with a base64 PNG"]))
            }
            guard let shot = emu.snapshot(scale: scale) else {
                log.add("GET", "/screen", ok: false)
                return respond(503, "application/json", json(["ok": false, "error": "no frame yet"]))
            }
            log.add("GET", "/screen", image: shot.png)
            if format == "png" {
                return respond(200, "image/png", shot.png)
            }
            return reply(r, ok: true, extra: [:], shot: shot)

        case ("GET", "/history"):
            log.add("GET", "/history")
            guard let limit = bounded(r, "limit", default: 100, min: 0, max: 500) else {
                return respond(400, "application/json", json(["ok": false, "error": "limit must be an integer from 0 to 500"]))
            }
            let arr = log.items.suffix(limit).map { rec -> [String: Any] in
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
            // One key or several in order, with an optional hold for every
            // key. A repeat is a list of the same key; there is no wait call,
            // because an action returns when the screen has settled.
            if let bad = unknownFields(r, ["key", "hold"]) {
                return respond(400, "application/json", json(["ok": false, "error": bad]))
            }
            guard let names = r.strings("key"), 1...Self.maxKeysPerAction ~= names.count else {
                return respond(400, "application/json", json(["ok": false,
                    "error": "key must be one key name or a list of 1 to \(Self.maxKeysPerAction)"]))
            }
            guard let hold = bounded(r, "hold", default: Self.defaultTapFrames,
                                     min: Self.minHoldFrames, max: Self.maxHoldFrames) else {
                return respond(400, "application/json", json(["ok": false,
                    "error": "hold must be \(Self.minHoldFrames) to \(Self.maxHoldFrames) frames"]))
            }
            let gap = 6
            let total = names.count * (hold + 2) + max(0, names.count - 1) * gap
            guard total <= Self.maxActionFrames else {
                return respond(400, "application/json", json(["ok": false, "error": "action exceeds \(Self.maxActionFrames) frames"]))
            }
            var steps: [Emulator.Step] = []
            var bad: [String] = []
            for (i, n) in names.enumerated() {
                guard let combo = RetroKey.parseCombo(n) else { bad.append(n); continue }
                steps.append(.press(combo, frames: hold))
                if i != names.count - 1 { steps.append(.wait(gap)) }
            }
            if !bad.isEmpty {
                log.add("KEY", names.joined(separator: ","), payload: "bad: \(bad.joined(separator: ","))", ok: false)
                return respond(400, "application/json", json(["ok": false, "error": "unknown key: " + bad.joined(separator: ", "), "hint": "GET /keys"]))
            }
            // Logged before the keys go in, so the pane shows an action
            // starting rather than reporting one already over.
            let note = names.joined(separator: " ")
            log.add(names.count == 1 ? "KEY" : "KEYS", note)
            let res = emu.submitSync(steps, settle: settle(r), scale: scale,
                                     wantShot: r.wantsImage, atLeast: 60)
            let out = reply(r, ok: res.ok, extra: ["action": note], shot: res.shot)
            saver?.maybeSnapshot()
            return out

        case ("POST", "/save"):
            if let bad = unknownFields(r, ["name"]) {
                return respond(400, "application/json", json(["ok": false, "error": bad]))
            }
            let url = slotURL(r)
            let res = emu.submitSync([.save(url)], settle: .fixed(1), scale: scale, wantShot: r.wantsImage)
            log.add("SAVE", url.deletingPathExtension().lastPathComponent, payload: res.ok ? "" : res.detail, ok: res.ok)
            return reply(r, ok: res.ok, status: res.ok ? 200 : 500,
                         extra: ["action": "save", "slot": url.deletingPathExtension().lastPathComponent,
                                 "error": res.ok ? "" : res.detail],
                         shot: res.shot)

        case ("POST", "/load"):
            if let bad = unknownFields(r, ["name"]) {
                return respond(400, "application/json", json(["ok": false, "error": bad]))
            }
            let url = slotURL(r)
            guard FileManager.default.fileExists(atPath: url.path) else {
                log.add("LOAD", url.lastPathComponent, ok: false)
                return respond(404, "application/json", json(["ok": false, "error": "no such slot"]))
            }
            let res = emu.submitSync([.load(url)], settle: settle(r), scale: scale, wantShot: r.wantsImage)
            log.add("LOAD", url.deletingPathExtension().lastPathComponent, payload: res.ok ? "" : res.detail, ok: res.ok)
            return reply(r, ok: res.ok, status: res.ok ? 200 : 500,
                         extra: ["action": "load", "slot": url.deletingPathExtension().lastPathComponent,
                                 "error": res.ok ? "" : res.detail],
                         shot: res.shot)

        case ("POST", "/reset"):
            let res = emu.submitSync([.reset], settle: Emulator.Settle(minFrames: 60, maxFrames: 600, stableFrames: 6), scale: scale, wantShot: r.wantsImage, atLeast: 60)
            log.add("RESET", "/", ok: res.ok)
            return reply(r, ok: res.ok, extra: ["action": "reset"],
                         shot: res.shot, changed: res.changed, settled: res.waited)

        default:
            log.add(r.method, r.path, ok: false)
            return respond(404, "application/json", json(["ok": false, "error": "not found", "hint": "GET /help"]))
        }
    }

    // MARK: - helpers

    /// The headless runner serves the control API under `/api` and the
    /// briefing names it that way, so both spellings route here. One agent
    /// loop, and one briefing, then work against either runner unchanged.
    private static func route(_ path: String) -> String {
        if path == "/api" { return "/" }
        if path.hasPrefix("/api/") { return String(path.dropFirst(4)) }
        return path
    }

    /// The address this server was reached at, for the URLs in the briefing.
    /// A Host header that is not a plain name and port cannot rewrite them.
    private static func origin(_ r: Request, port: UInt16) -> String {
        let host = r.headers["host"] ?? ""
        let plain = host.range(of: "^[A-Za-z0-9._-]+(:[0-9]{1,5})?$",
                               options: .regularExpression) != nil
        return "http://" + (plain ? host : "127.0.0.1:\(port)")
    }

    /// The briefing in `skills/`, or nil when it is not beside the binary.
    /// Mirrors server/prompt.py: play first, then the field manual unless the
    /// caller asked for the core only, with `{BASE}` substituted and the
    /// doubled braces that keep JSON examples editable folded back down.
    private func briefing(lang: String, coreOnly: Bool, base: String) -> String? {
        let name = lang.lowercased().hasPrefix("zh") ? "zh" : "en"
        func read(_ stem: String) -> String? {
            try? String(contentsOf: skillsDir.appendingPathComponent("\(stem).md"),
                        encoding: .utf8)
        }
        guard var text = read("play.\(name)") else { return nil }
        if !coreOnly, let manual = read("speedrun.\(name)") {
            while let last = text.last, last == "\n" || last == " " || last == "\t" {
                text.removeLast()
            }
            text += "\n\n" + manual
        }
        return text
            .replacingOccurrences(of: "{BASE}", with: base)
            .replacingOccurrences(of: "{{", with: "{")
            .replacingOccurrences(of: "}}", with: "}")
    }

    /// Refuse a body field this call does not read.
    ///
    /// Ignoring it silently is the failure this API is built to avoid: the
    /// caller is told 200 and the game does something else. Returns the error
    /// text, or nil when every field is one this call uses. The query string
    /// is not checked here - it carries the shared options (scale, image, the
    /// settle phases) rather than this call's own arguments.
    private func unknownFields(_ r: Request, _ known: [String]) -> String? {
        let extra = r.json.keys.filter { !known.contains($0) }.sorted()
        guard !extra.isEmpty else { return nil }
        return "unknown field\(extra.count > 1 ? "s" : ""): \(extra.joined(separator: ", ")); "
             + "this call takes \(known.joined(separator: ", "))"
    }

    private func bounded(_ r: Request, _ key: String, default fallback: Int,
                         min: Int, max: Int) -> Int? {
        if r.value(key) == nil { return fallback }
        guard let value = r.int(key), min...max ~= value else { return nil }
        return value
    }

    /// ?react, ?stable and ?maxsettle, the same three the headless runner
    /// takes. There is no fourth spelling of the same wait.
    private func settle(_ r: Request, fallbackMin: Int? = nil) -> Emulator.Settle {
        var s = Emulator.Settle.default
        if let m = fallbackMin { s.reactFrames = m }
        if let m = r.int("react") { s.reactFrames = max(0, min(m, 2000)) }
        if let m = r.int("stable") { s.stableFrames = max(1, min(m, 600)) }
        if let m = r.int("maxsettle") { s.maxFrames = max(s.minFrames, min(m, 2000)) }
        s.maxFrames = max(s.maxFrames, s.reactFrames)
        return s
    }

    /// The window's quick save writes here too, so ⌘S and a nameless POST mean
    /// the same slot. "slot" was this same name spelled a second way.
    private static let quickState = "slot1"

    private func slotURL(_ r: Request) -> URL {
        guard let name = r.string("name"), !name.isEmpty else {
            return saveDir.appendingPathComponent("\(Self.quickState).state")
        }
        let safe = name.replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "..", with: "_")
        return saveDir.appendingPathComponent("\(safe).state")
    }

    private func reply(_ r: Request, ok: Bool, status: Int = 200, extra: [String: Any],
                       shot: Emulator.Shot?, changed: Bool? = nil, settled: Int? = nil) -> Data {
        if r.wantsRawPNG, let shot {
            return respond(status, "image/png", shot.png)
        }
        // frame names the picture. No hash of the screen and no "changed"
        // flag: both flip on an idle animation as readily as on a step, and an
        // agent that trusted them counted steps it never took. What happened
        // is read from the picture; the headless runner answers the same way.
        var obj: [String: Any] = [
            "ok": ok,
            "width": Int(core_width()),
            "height": Int(core_height()),
            "frame": Int(core_frame_serial()),
        ]
        _ = (changed, settled)
        for (k, v) in extra where !((v as? String)?.isEmpty ?? false) { obj[k] = v }
        if let shot {
            obj["image"] = "data:image/png;base64," + shot.png.base64EncodedString()
            obj["image_width"] = shot.width
            obj["image_height"] = shot.height
            obj["scale"] = shot.scale
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

    Every path below also answers under /api, the prefix the headless runner
    uses, so one agent loop drives either runner unchanged.

    GET  /screen[?format=png]         look at the screen
    GET  /history[?limit=100]         action log
    GET  /keys                        every accepted key name
    GET  /slots                       savestates on disk
    GET  /help[?lang=en|zh][&part=core]     the full briefing

    POST /key    {"key":"kp3"}        one key; optional "hold" in frames
    POST /key    {"key":["kp9","enter"]}    several in order, same "hold"
    POST /save   {"name":"before-boss"}    a name of its own, or none
    POST /load   {"name":"before-boss"}
    POST /reset

    A POST waits for the screen to react and then to hold still, so the picture
    that comes back is the result of the action; the reply itself says only
    what was pressed and which frame followed. Add ?format=png for raw bytes,
    ?image=0 to skip the capture.
    ?react, ?stable and ?maxsettle tune that wait in frames.

    A body field a call does not read is a 400 naming it, not a silent no-op.

    Movement is isometric, so the four axes are diagonals on screen:
      kp7 up-left   kp9 up-right   kp1 down-left   kp3 down-right
    The names left/up/down/right are aliases for those same four.

    Keys: kp0-kp9, arrows, enter, space, esc, y, n, a-z, 0-9, f1-f12, tab,
    backspace, and combos such as "alt+x".
    """
}
