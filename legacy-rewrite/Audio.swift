import AVFoundation
import Foundation

final class GameAudio {
    private var musicPlayer: AVAudioPlayer?
    private var sfxPlayers: [AVAudioPlayer] = []
    private var midiPlayer: AVMIDIPlayer?
    private let dir: URL
    var musicVolume: Float = 0.4
    var sfxVolume: Float = 0.7
    private var currentMusic = -1

    init(dir: URL) {
        self.dir = dir
    }

    func playMusic(_ index: Int, loop: Bool = true) {
        if index < 0 { stopMusic(); return }
        if currentMusic == index, musicPlayer?.isPlaying == true || midiPlayer?.isPlaying == true {
            return
        }
        stopMusic()
        currentMusic = index
        if let wav = file("GAME\(String(format: "%02d", index)).WAV") ?? file("music/\(index).mp3") ?? file("music/\(index).mid") {
            playFile(wav, loop: loop)
            return
        }
        let xmi = dir.appendingPathComponent(String(format: "GAME%02d.XMI", index))
        if FileManager.default.fileExists(atPath: xmi.path), let midi = XMI.toMIDI(url: xmi) {
            do {
                let player = try AVMIDIPlayer(data: midi, soundBankURL: nil)
                midiPlayer = player
                player.prepareToPlay()
                player.play {
                    if loop, self.currentMusic == index {
                        self.playMusic(index, loop: true)
                    }
                }
            } catch {
                // MIDI optional
            }
        }
    }

    func stopMusic() {
        musicPlayer?.stop()
        musicPlayer = nil
        midiPlayer?.stop()
        midiPlayer = nil
        currentMusic = -1
    }

    func playWav(_ name: String) {
        guard let url = file(name) else { return }
        do {
            let player = try AVAudioPlayer(contentsOf: url)
            player.volume = sfxVolume
            player.play()
            sfxPlayers.append(player)
            sfxPlayers.removeAll { !$0.isPlaying }
        } catch {}
    }

    func playEffect(_ n: Int) {
        playWav(String(format: "E%02d.WAV", n))
    }

    func playAttack(_ n: Int) {
        playWav(String(format: "ATK%02d.WAV", n))
    }

    private func playFile(_ url: URL, loop: Bool) {
        do {
            let player = try AVAudioPlayer(contentsOf: url)
            player.numberOfLoops = loop ? -1 : 0
            player.volume = musicVolume
            player.play()
            musicPlayer = player
        } catch {}
    }

    private func file(_ name: String) -> URL? {
        let url = dir.appendingPathComponent(name)
        return FileManager.default.fileExists(atPath: url.path) ? url : nil
    }
}

enum XMI {
    static func toMIDI(url: URL) -> Data? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        let bytes = [UInt8](data)
        guard let evnt = findChunk(bytes, name: "EVNT") else { return nil }
        var midi = [UInt8]()
        midi += [0x4D, 0x54, 0x68, 0x64, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x01, 0x00, 0x3C]
        var track = [UInt8]()
        var i = 0
        var running: UInt8 = 0
        while i < evnt.count {
            var delay = 0
            while i < evnt.count, evnt[i] & 0x80 != 0 {
                delay += Int(evnt[i] & 0x7F)
                i += 1
            }
            if i < evnt.count {
                delay += Int(evnt[i])
                i += 1
            }
            writeVLQ(&track, delay)
            guard i < evnt.count else { break }
            var status = evnt[i]
            if status < 0x80 {
                if running == 0 { break }
                status = running
            } else {
                i += 1
                running = status
            }
            track.append(status)
            let need: Int
            switch status & 0xF0 {
            case 0xC0, 0xD0: need = 1
            case 0xF0:
                if status == 0xFF {
                    guard i + 1 < evnt.count else { return nil }
                    track.append(evnt[i]); i += 1
                    let len = Int(evnt[i]); track.append(evnt[i]); i += 1
                    for _ in 0..<len where i < evnt.count {
                        track.append(evnt[i]); i += 1
                    }
                    continue
                }
                need = 0
            default: need = 2
            }
            for _ in 0..<need where i < evnt.count {
                track.append(evnt[i]); i += 1
            }
        }
        track += [0x00, 0xFF, 0x2F, 0x00]
        midi += [0x4D, 0x54, 0x72, 0x6B]
        let len = UInt32(track.count)
        midi += [UInt8(len >> 24), UInt8((len >> 16) & 0xFF), UInt8((len >> 8) & 0xFF), UInt8(len & 0xFF)]
        midi += track
        return Data(midi)
    }

    private static func findChunk(_ bytes: [UInt8], name: String) -> [UInt8]? {
        let tag = Array(name.utf8)
        var i = 0
        while i + 8 <= bytes.count {
            if Array(bytes[i..<(i + 4)]) == tag {
                let size = (Int(bytes[i + 4]) << 24) | (Int(bytes[i + 5]) << 16) | (Int(bytes[i + 6]) << 8) | Int(bytes[i + 7])
                let start = i + 8
                let end = min(bytes.count, start + max(0, size))
                return Array(bytes[start..<end])
            }
            i += 1
        }
        return nil
    }

    private static func writeVLQ(_ track: inout [UInt8], _ value: Int) {
        var v = max(0, value)
        var buf: [UInt8] = [UInt8(v & 0x7F)]
        v >>= 7
        while v > 0 {
            buf.insert(UInt8((v & 0x7F) | 0x80), at: 0)
            v >>= 7
        }
        track.append(contentsOf: buf)
    }
}
