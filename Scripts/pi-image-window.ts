// Send the model the images of its latest turn and the few before them.
//
// Stock pi resends every image of the conversation with every request until
// compaction summarizes them away, and compaction is triggered by tokens. A
// 320x200 screenshot is a few hundred tokens, so a long run reaches a
// provider's per-request image limit (Anthropic: 100 for 200k-context models,
// 600 for the rest) or its 32 MB request limit long before the context is
// full, and every request after that fails. pi 1.0.4 documents the gap:
// `images.maxPerRequest` is known but history is not rewritten.
//
// This keeps the images that arrived after the model's last message -
// everything it read in its latest turn, however many - and the EARLIER
// images before them, so a model can still see where it just was. Older images
// are dropped. Keeping only the latest turn was not enough: in batch
// 20261010-120518 the Claude models wrote almost nothing about what they saw
// (one Opus run: 466 characters of text in an hour) and said, over and over,
// that they had lost track because the earlier screenshots were gone.
//
// Each request drops at most a few images more than the one before, all near
// the end of the history, so the provider's prompt cache still covers the
// rest of it.
//
// The session file keeps every image; only the request is trimmed. Older
// images become a short text note so the model knows a screenshot was there.
//
//   pi -e Scripts/pi-image-window.ts ...

export const EARLIER = 4;
const NOTE = { type: "text", text: "(earlier image omitted from this request)" };

export default function (pi: any) {
  pi.on("context", async (event: any) => {
    const messages = event.messages;
    let latest = -1;  // the model's last message; the turn after it is kept
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i]?.role === "assistant") { latest = i; break; }
    }
    let kept = 0;  // images kept from before the latest turn, newest first
    for (let i = latest - 1; i >= 0; i--) {
      const content = messages[i]?.content;
      if (!Array.isArray(content)) continue;
      for (let j = content.length - 1; j >= 0; j--) {
        if (content[j]?.type !== "image") continue;
        if (kept < EARLIER) kept++;
        else content[j] = { ...NOTE };
      }
    }
    return { messages };
  });
}
