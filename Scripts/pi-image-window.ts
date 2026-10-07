// Keep only recent images in what pi sends to the model.
//
// Stock pi resends every image of the conversation with every request until
// compaction summarizes them away, and compaction is triggered by tokens. A
// 320x200 screenshot is a few hundred tokens, so a long run reaches a
// provider's per-request image limit (Anthropic: 100 for 200k-context models,
// 600 for the rest) or its 32 MB request limit long before the context is
// full, and every request after that fails. pi 1.0.4 documents the gap:
// `images.maxPerRequest` is known but history is not rewritten.
//
// PI_IMAGE_WINDOW=turn (the default here) keeps the images that arrived after
// the model's last message - everything it read in its latest turn, however
// many - and drops the ones it saw in earlier turns. A model that wants to
// compare frames reads them together and sees them together; it carries no
// passive memory of old screens. PI_IMAGE_WINDOW=N keeps the newest N images
// instead. Only the latest turn changes between requests, so the provider's
// prompt cache still covers the rest of the history.
//
// The session file keeps every image; only the request is trimmed. Older
// images become a short text note so the model knows a screenshot was there.
//
//   PI_IMAGE_WINDOW=turn pi -e Scripts/pi-image-window.ts ...

const SETTING = (process.env.PI_IMAGE_WINDOW ?? "turn").trim();
const COUNT = Number(SETTING);
const NOTE = { type: "text", text: "(earlier image omitted from this request)" };

export default function (pi: any) {
  const byTurn = SETTING === "turn";
  if (!byTurn && !(Number.isInteger(COUNT) && COUNT > 0)) return;
  pi.on("context", async (event: any) => {
    const messages = event.messages;
    // the latest turn: everything after the model's last message
    let boundary = -1;
    if (byTurn) {
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i]?.role === "assistant") { boundary = i; break; }
      }
    }
    let kept = 0;
    for (let i = messages.length - 1; i >= 0; i--) {
      const content = messages[i]?.content;
      if (!Array.isArray(content)) continue;
      for (let j = content.length - 1; j >= 0; j--) {
        if (content[j]?.type !== "image") continue;
        const keep = byTurn ? i > boundary : kept < COUNT;
        if (keep) kept += 1;
        else content[j] = { ...NOTE };
      }
    }
    return { messages };
  });
}
