import Foundation
import Metal
import MetalKit

final class Framebuffer {
    let width: Int
    let height: Int
    var pixels: [UInt8]

    init(width: Int = Screen.width, height: Int = Screen.height) {
        self.width = width
        self.height = height
        pixels = [UInt8](repeating: 0, count: width * height)
    }

    func clear(_ color: UInt8 = 0) {
        pixels.withUnsafeMutableBufferPointer { buf in
            if let p = buf.baseAddress {
                memset(p, Int32(color), buf.count)
            }
        }
    }

    func put(_ x: Int, _ y: Int, _ color: UInt8) {
        if color == 0 { return }
        if x < 0 || y < 0 || x >= width || y >= height { return }
        pixels[y * width + x] = color
    }

    func fill(_ x: Int, _ y: Int, _ w: Int, _ h: Int, _ color: UInt8) {
        let x0 = max(0, x)
        let y0 = max(0, y)
        let x1 = min(width, x + w)
        let y1 = min(height, y + h)
        if x0 >= x1 || y0 >= y1 { return }
        for yy in y0..<y1 {
            let row = yy * width
            for xx in x0..<x1 {
                pixels[row + xx] = color
            }
        }
    }

    func blit(_ pic: Pic, x: Int, y: Int, shadow: Bool = false) {
        if pic.empty { return }
        let dx = x - pic.originX
        let dy = y - pic.originY
        let w = pic.width
        let h = pic.height
        for row in 0..<h {
            let yy = dy + row
            if yy < 0 || yy >= height { continue }
            let srcRow = row * w
            let dstRow = yy * width
            for col in 0..<w {
                let color = pic.pixels[srcRow + col]
                if color == 0 { continue }
                let xx = dx + col
                if xx < 0 || xx >= width { continue }
                pixels[dstRow + xx] = shadow ? UInt8(clamping: Int(color) &+ 1) : color
            }
        }
    }

    func blitRaw(_ data: [UInt8], width srcW: Int, height srcH: Int, x: Int, y: Int, scale: Int = 1) {
        guard srcW > 0, srcH > 0, !data.isEmpty else { return }
        for row in 0..<srcH {
            for col in 0..<srcW {
                let idx = row * srcW + col
                if idx >= data.count { continue }
                let color = data[idx]
                if color == 0 { continue }
                if scale == 1 {
                    put(x + col, y + row, color)
                } else {
                    for sy in 0..<scale {
                        for sx in 0..<scale {
                            put(x + col * scale + sx, y + row * scale + sy, color)
                        }
                    }
                }
            }
        }
    }

    func rect(_ x: Int, _ y: Int, _ w: Int, _ h: Int, _ color: UInt8) {
        fill(x, y, w, 1, color)
        fill(x, y + h - 1, w, 1, color)
        fill(x, y, 1, h, color)
        fill(x + w - 1, y, 1, h, color)
    }
}

final class TextRenderer {
    let font: FontAtlas
    init(font: FontAtlas) { self.font = font }

    func width(_ text: String) -> Int {
        var w = 0
        for ch in text {
            w += font.glyph(for: ch)?.width ?? 8
        }
        return w
    }

    func draw(_ text: String, x: Int, y: Int, color: UInt8, shadow: UInt8, onto fb: Framebuffer) {
        var cx = x
        for ch in text {
            guard let glyph = font.glyph(for: ch) else { continue }
            blitGlyph(glyph.rows, width: glyph.width, x: cx + 1, y: y + 1, color: shadow, onto: fb)
            blitGlyph(glyph.rows, width: glyph.width, x: cx, y: y, color: color, onto: fb)
            cx += glyph.width
        }
    }

    private func blitGlyph(_ rows: [UInt8], width: Int, x: Int, y: Int, color: UInt8, onto fb: Framebuffer) {
        let height = width == 16 ? 16 : min(16, rows.count)
        let rowBytes = width == 16 ? 2 : 1
        for row in 0..<height {
            let base = row * rowBytes
            if base >= rows.count { break }
            var bits = Int(rows[base]) << 8
            if rowBytes > 1, base + 1 < rows.count {
                bits |= Int(rows[base + 1])
            }
            for col in 0..<width {
                if bits & (0x8000 >> col) != 0 {
                    fb.put(x + col, y + row, color)
                }
            }
        }
    }
}

private let shaderSource = """
#include <metal_stdlib>
using namespace metal;

struct VOut {
    float4 position [[position]];
    float2 uv;
};

vertex VOut vs(uint vid [[vertex_id]]) {
    float2 pos[3] = { float2(-1.0, -1.0), float2(3.0, -1.0), float2(-1.0, 3.0) };
    VOut o;
    o.position = float4(pos[vid], 0.0, 1.0);
    o.uv = float2(pos[vid].x * 0.5 + 0.5, 1.0 - (pos[vid].y * 0.5 + 0.5));
    return o;
}

fragment float4 fs(VOut in [[stage_in]],
                   texture2d<float, access::sample> fb [[texture(0)]],
                   constant float4 *palette [[buffer(0)]]) {
    constexpr sampler nearestSampler(coord::normalized, mag_filter::nearest, min_filter::nearest, address::clamp_to_edge);
    float idx = fb.sample(nearestSampler, in.uv).r * 255.0 + 0.5;
    uint i = min(uint(idx), 255u);
    return palette[i];
}
"""

final class MetalView: MTKView, MTKViewDelegate {
    private let commandQueue: MTLCommandQueue
    private let pipeline: MTLRenderPipelineState
    private let indexTexture: MTLTexture
    private let paletteBuffer: MTLBuffer
    private var paletteCPU = [SIMD4<Float>](repeating: .zero, count: 256)
    let framebuffer = Framebuffer()
    var onDraw: ((Framebuffer) -> Void)?

    init?(device: MTLDevice) {
        guard let queue = device.makeCommandQueue() else { return nil }
        commandQueue = queue
        let options = MTLCompileOptions()
        options.languageVersion = .version2_4
        guard let library = try? device.makeLibrary(source: shaderSource, options: options),
              let vs = library.makeFunction(name: "vs"),
              let fs = library.makeFunction(name: "fs") else { return nil }
        let desc = MTLRenderPipelineDescriptor()
        desc.vertexFunction = vs
        desc.fragmentFunction = fs
        desc.colorAttachments[0].pixelFormat = .bgra8Unorm
        guard let state = try? device.makeRenderPipelineState(descriptor: desc) else { return nil }
        pipeline = state
        let texDesc = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: .r8Unorm,
            width: Screen.width,
            height: Screen.height,
            mipmapped: false
        )
        texDesc.usage = [.shaderRead]
        texDesc.storageMode = .shared
        guard let tex = device.makeTexture(descriptor: texDesc) else { return nil }
        indexTexture = tex
        guard let pbuf = device.makeBuffer(length: 256 * MemoryLayout<SIMD4<Float>>.stride, options: .storageModeShared) else { return nil }
        paletteBuffer = pbuf
        super.init(frame: .zero, device: device)
        self.delegate = self
        self.framebufferOnly = true
        self.colorPixelFormat = .bgra8Unorm
        self.preferredFramesPerSecond = 60
        self.enableSetNeedsDisplay = false
        self.isPaused = false
        self.clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
    }

    required init(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func setPalette(_ palette: Palette) {
        for i in 0..<256 {
            let (r, g, b, a) = palette.rgba(UInt8(i))
            paletteCPU[i] = SIMD4<Float>(r, g, b, a)
        }
        paletteCPU.withUnsafeBytes { src in
            if let base = src.baseAddress {
                memcpy(paletteBuffer.contents(), base, 256 * MemoryLayout<SIMD4<Float>>.stride)
            }
        }
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        onDraw?(framebuffer)
        framebuffer.pixels.withUnsafeBytes { src in
            if let base = src.baseAddress {
                indexTexture.replace(
                    region: MTLRegionMake2D(0, 0, Screen.width, Screen.height),
                    mipmapLevel: 0,
                    withBytes: base,
                    bytesPerRow: Screen.width
                )
            }
        }
        guard let drawable = currentDrawable,
              let rpd = currentRenderPassDescriptor,
              let cmd = commandQueue.makeCommandBuffer(),
              let enc = cmd.makeRenderCommandEncoder(descriptor: rpd) else { return }
        let vw = drawable.texture.width
        let vh = drawable.texture.height
        let scale = max(1, min(vw / Screen.width, vh / Screen.height))
        let dw = Screen.width * scale
        let dh = Screen.height * scale
        let ox = (vw - dw) / 2
        let oy = (vh - dh) / 2
        enc.setViewport(MTLViewport(originX: Double(ox), originY: Double(oy), width: Double(dw), height: Double(dh), znear: 0, zfar: 1))
        enc.setRenderPipelineState(pipeline)
        enc.setFragmentTexture(indexTexture, index: 0)
        enc.setFragmentBuffer(paletteBuffer, offset: 0, index: 0)
        enc.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        enc.endEncoding()
        cmd.present(drawable)
        cmd.commit()
    }
}

func screenPos(x: Int, y: Int, cx: Int, cy: Int) -> (Int, Int) {
    let px = -(x - cx) * 18 + (y - cy) * 18 + Screen.cx
    let py = (x - cx) * 9 + (y - cy) * 9 + Screen.cy
    return (px, py)
}
