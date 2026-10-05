import AppKit
import Metal
import MetalKit
import CoreHost

private let shader = """
#include <metal_stdlib>
using namespace metal;
struct VOut { float4 position [[position]]; float2 uv; };
vertex VOut vs(uint vid [[vertex_id]]) {
    float2 p[3] = { float2(-1,-1), float2(3,-1), float2(-1,3) };
    VOut o;
    o.position = float4(p[vid], 0, 1);
    o.uv = float2(p[vid].x * 0.5 + 0.5, 1.0 - (p[vid].y * 0.5 + 0.5));
    return o;
}
fragment float4 fs(VOut in [[stage_in]], texture2d<float> tex [[texture(0)]]) {
    constexpr sampler s(coord::normalized, mag_filter::nearest, min_filter::linear);
    return float4(tex.sample(s, in.uv).rgb, 1.0);
}
"""

final class MetalView: MTKView, MTKViewDelegate {
    /// (macOS keycode, charactersIgnoringModifiers, isDown)
    var onKey: ((UInt16, String?, Bool) -> Void)?
    /// A key repeat from macOS, at the user's own delay and rate.
    var onRepeat: ((UInt16, String?) -> Void)?
    var onFlags: ((NSEvent.ModifierFlags) -> Void)?

    private let queue: MTLCommandQueue
    private let pipeline: MTLRenderPipelineState
    private var texture: MTLTexture?
    private var texW = 0
    private var texH = 0
    private var shownSerial: UInt64 = 0

    /// 320x200 was displayed on a 4:3 CRT, so square pixels are technically wrong.
    /// Off by default because it is what makes the art look sharp on a Retina panel.
    var stretchTo43 = false

    init?(device: MTLDevice) {
        guard let q = device.makeCommandQueue() else { return nil }
        queue = q
        let opt = MTLCompileOptions()
        opt.languageVersion = .version2_4
        guard let lib = try? device.makeLibrary(source: shader, options: opt),
              let vs = lib.makeFunction(name: "vs"),
              let fs = lib.makeFunction(name: "fs") else { return nil }
        let desc = MTLRenderPipelineDescriptor()
        desc.vertexFunction = vs
        desc.fragmentFunction = fs
        desc.colorAttachments[0].pixelFormat = .bgra8Unorm
        guard let p = try? device.makeRenderPipelineState(descriptor: desc) else { return nil }
        pipeline = p
        super.init(frame: .zero, device: device)
        delegate = self
        colorPixelFormat = .bgra8Unorm
        preferredFramesPerSecond = 60
        framebufferOnly = true
        isPaused = false
        enableSetNeedsDisplay = false
        autoResizeDrawable = true
        clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
    }

    required init(coder: NSCoder) { fatalError() }

    // The view is the first responder itself: no transparent overlay in the way.
    override var acceptsFirstResponder: Bool { true }
    override func becomeFirstResponder() -> Bool { true }
    override func keyDown(with event: NSEvent) {
        if event.isARepeat {
            onRepeat?(event.keyCode, event.charactersIgnoringModifiers)
            return
        }
        onKey?(event.keyCode, event.charactersIgnoringModifiers, true)
    }
    override func keyUp(with event: NSEvent) { onKey?(event.keyCode, event.charactersIgnoringModifiers, false) }
    override func flagsChanged(with event: NSEvent) { onFlags?(event.modifierFlags) }
    override func mouseDown(with event: NSEvent) { window?.makeFirstResponder(self) }

    /// The core hands us XRGB8888 little-endian, which is byte-identical to
    /// bgra8Unorm, so the whole frame goes up in one blit - no per-pixel work.
    private func syncTexture() {
        core_lock()
        defer { core_unlock() }
        let serial = core_frame_serial()
        guard serial != shownSerial else { return }
        let w = Int(core_width())
        let h = Int(core_height())
        let pitch = Int(core_pitch())
        guard w > 0, h > 0, let px = core_pixels(), let device else { return }

        if texture == nil || texW != w || texH != h {
            let d = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm, width: w, height: h, mipmapped: false)
            d.usage = .shaderRead
            d.storageMode = .shared
            texture = device.makeTexture(descriptor: d)
            texW = w
            texH = h
        }
        texture?.replace(
            region: MTLRegionMake2D(0, 0, w, h),
            mipmapLevel: 0,
            withBytes: px,
            bytesPerRow: pitch
        )
        shownSerial = serial
    }

    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {}

    func draw(in view: MTKView) {
        syncTexture()
        guard let drawable = currentDrawable,
              let rpd = currentRenderPassDescriptor,
              let cmd = queue.makeCommandBuffer(),
              let enc = cmd.makeRenderCommandEncoder(descriptor: rpd) else { return }
        if let texture {
            enc.setRenderPipelineState(pipeline)
            enc.setViewport(viewport(drawableWidth: drawable.texture.width, drawableHeight: drawable.texture.height))
            enc.setFragmentTexture(texture, index: 0)
            enc.drawPrimitives(type: .triangle, vertexStart: 0, vertexCount: 3)
        }
        enc.endEncoding()
        cmd.present(drawable)
        cmd.commit()
    }

    /// The window is snapped to the game's aspect (see AppDelegate.snap), so this
    /// normally fills the pane exactly and leaves no letterbox. The fit is kept
    /// anyway for fullscreen and for the moment a mode change lands.
    private func viewport(drawableWidth vw: Int, drawableHeight vh: Int) -> MTLViewport {
        let srcAspect = stretchTo43 ? 4.0 / 3.0 : Double(texW) / Double(max(1, texH))
        var dw = Double(vw)
        var dh = dw / srcAspect
        if dh > Double(vh) {
            dh = Double(vh)
            dw = dh * srcAspect
        }
        return MTLViewport(
            originX: ((Double(vw) - dw) / 2).rounded(), originY: ((Double(vh) - dh) / 2).rounded(),
            width: dw, height: dh, znear: 0, zfar: 1
        )
    }
}
