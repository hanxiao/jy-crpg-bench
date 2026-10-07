// Keep only the newest images in what pi sends to the model.
//
// Stock pi resends every image of the conversation with every request until
// compaction summarizes them away, and compaction is triggered by tokens. A
// 320x200 screenshot is a few hundred tokens, so a long run reaches a
// provider's per-request image limit (Anthropic: 100 for 200k-context models,
// 600 for the rest) or its 32 MB request limit long before the context is
// full, and every request after that fails. pi 1.0.4 documents the gap:
// `images.maxPerRequest` is known but history is not rewritten.
//
// The session file keeps every image; only the request is trimmed. Older
// images become a short text note so the model knows a screenshot was there.
//
//   PI_IMAGE_WINDOW=50 pi -e Scripts/pi-image-window.ts ...

const WINDOW = Number(process.env.PI_IMAGE_WINDOW ?? "0");

export default function (pi: any) {
  if (!Number.isInteger(WINDOW) || WINDOW <= 0) return;
  pi.on("context", async (event: any) => {
    let kept = 0;
    const messages = event.messages;
    for (let i = messages.length - 1; i >= 0; i--) {
      const content = messages[i]?.content;
      if (!Array.isArray(content)) continue;
      for (let j = content.length - 1; j >= 0; j--) {
        if (content[j]?.type !== "image") continue;
        if (kept < WINDOW) {
          kept += 1;
        } else {
          content[j] = { type: "text", text: "(earlier image omitted from this request)" };
        }
      }
    }
    return { messages };
  });
}
