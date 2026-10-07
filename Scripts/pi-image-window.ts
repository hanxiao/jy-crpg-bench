// Send the model only the images of its latest turn.
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
// everything it read in its latest turn, however many - and drops the ones it
// saw in earlier turns, which it has already described in its own words. A
// model that wants to compare frames reads them together and sees them
// together. Only the latest turn changes between requests, so the provider's
// prompt cache still covers the rest of the history.
//
// The session file keeps every image; only the request is trimmed. Older
// images become a short text note so the model knows a screenshot was there.
//
//   pi -e Scripts/pi-image-window.ts ...

const NOTE = { type: "text", text: "(earlier image omitted from this request)" };

export default function (pi: any) {
  pi.on("context", async (event: any) => {
    const messages = event.messages;
    let latest = -1;  // the model's last message; the turn after it is kept
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i]?.role === "assistant") { latest = i; break; }
    }
    for (let i = 0; i < latest; i++) {
      const content = messages[i]?.content;
      if (!Array.isArray(content)) continue;
      for (let j = 0; j < content.length; j++) {
        if (content[j]?.type === "image") content[j] = { ...NOTE };
      }
    }
    return { messages };
  });
}
