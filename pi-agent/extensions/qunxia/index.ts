/**
 * Game tools for 金庸群俠傳. Standalone profiles return the frame after each
 * action; benchmark profiles preserve the broker's action/look split.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const API = process.env.QUNXIA_API ?? "http://127.0.0.1:8765";
const SCALE = Number(process.env.QUNXIA_SCALE ?? "1");
const OBSERVE_AFTER_ACTION = process.env.QUNXIA_OBSERVE_AFTER_ACTION !== "0";
const ACTION_RESULT = OBSERVE_AFTER_ACTION
  ? "The resulting visible frame is returned."
  : "Only action metadata is returned; call game_look when you need the next visible frame.";

type Content = { type: "text"; text: string } | { type: "image"; data: string; mimeType: string };

async function call(method: string, path: string, body?: unknown, signal?: AbortSignal) {
  const res = await fetch(API + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  return (await res.json()) as Record<string, any>;
}

function offline(err: unknown) {
  return {
    content: [{
      type: "text" as const,
      text:
        `The game is not reachable at ${API} (${err}). Check QUNXIA_API and the ` +
        `selected game or benchmark session.`,
    }],
    details: { error: String(err) },
    isError: true,
  };
}

/** Turn an API response into a status line plus the screen. */
function frame(res: Record<string, any>, note: string) {
  if (res.ended) {
    return {
      content: [{
        type: "text" as const,
        text: `BENCHMARK ENDED | ${JSON.stringify({
          reason: res.reason,
          why: res.why,
          actions: res.actions,
          played_seconds: res.played_seconds ?? res.played,
          video_url: res.video_url,
          video_pending: res.video_pending,
        })}`,
      }],
      details: res,
    };
  }
  const bits: string[] = [];
  if (res.ok === false) bits.push("FAILED");
  if ("changed" in res) {
    bits.push(res.changed ? "screen changed" : "screen did NOT change (no visible effect)");
  }
  if (res.error) bits.push(String(res.error));
  bits.push(`${res.width}x${res.height}`);

  const content: Content[] = [{ type: "text", text: `${note} | ${bits.join(" | ")}` }];
  if (typeof res.image === "string") {
    content.push({ type: "image", data: res.image.split(",", 2)[1], mimeType: "image/png" });
  }
  return { content, details: { ok: res.ok !== false, changed: res.changed, frame: res.frame } };
}

export default function (pi: ExtensionAPI) {
  const act = async (
    path: string,
    body: unknown,
    note: string,
    signal?: AbortSignal,
    query = "",
  ) => {
    try {
      const image = OBSERVE_AFTER_ACTION ? "" : "&image=0";
      const action = await call("POST", `${path}?scale=${SCALE}${image}${query}`, body, signal);
      if (action.ended || action.ok === false) {
        return frame(action, note);
      }
      if (!OBSERVE_AFTER_ACTION) {
        const { image: _ignored, ...metadata } = action;
        return frame(metadata, note);
      }
      if (typeof action.image === "string") return frame(action, note);
      const screen = await call("GET", `/screen?scale=${SCALE}`, undefined, signal);
      if (screen.ended) return frame(screen, note);
      return frame({
        ...screen,
        ok: action.ok !== false && screen.ok !== false,
        changed: action.changed,
        action: action.action,
        actionFrame: action.frame,
        settled_frames: action.settled_frames,
      }, note);
    } catch (err) {
      return offline(err);
    }
  };

  pi.registerTool({
    name: "game_look",
    label: "Look",
    description:
      "Look at the current game screen without pressing anything. Use it to re-read a " +
      "screen you did not finish reading, or to re-orient after losing track of where you are.",
    promptSnippet: "Look at the current game screen",
    parameters: Type.Object({}),
    async execute(_id, params, signal) {
      try {
        return frame(await call("GET", `/screen?scale=${SCALE}`, undefined, signal), "look");
      } catch (err) {
        return offline(err);
      }
    },
  });

  pi.registerTool({
    name: "game_press",
    label: "Press",
    description:
      "Press one key. Movement keys are kp7, kp9, kp1 and kp3 (preferred), with " +
      "left, up, down and right as equivalent aliases. Other keys: " +
      "enter, space, esc, y, n, a-z, 0-9, f1-f12, tab, backspace, or a combo like 'alt+x'. " +
      "Use times to repeat the same key, for example walking several tiles or advancing " +
      "several lines of dialogue. Remember that during a cutscene every key only advances " +
      `the dialogue. ${ACTION_RESULT}`,
    promptSnippet: "Press a key in the game",
    parameters: Type.Object({
      key: Type.String({ description: "Key name, e.g. up, enter, esc, y" }),
      times: Type.Optional(Type.Integer({ minimum: 1, maximum: 100, description: "Repeat count, default 1" })),
      hold: Type.Optional(Type.Integer({ minimum: 1, maximum: 100000,
        description: "Frames to hold the key. Omit to use the game server's safe tap default.",
      })),
      stable: Type.Optional(Type.Integer({ minimum: 1, maximum: 600,
        description: "Frames the picture must hold still before the screenshot. Raise if you get a half-written dialogue line.",
      })),
    }),
    async execute(_id, params, signal) {
      const times = params.times ?? 1;
      const stable = params.stable;
      const q = stable ? `&stable=${stable}` : "";
      const note = times > 1 ? `${params.key} x${times}` : params.key;
      const body = times > 1
        ? { keys: Array(times).fill(params.key), hold: params.hold }
        : { key: params.key, hold: params.hold };
      const path = times > 1 ? "/keys" : "/key";
      return act(path, body, note, signal, q);
    },
  });

  pi.registerTool({
    name: "game_press_sequence",
    label: "Press sequence",
    description:
      "Press several different keys in order. Use it for " +
      "a menu path you are sure about, such as ['esc','down','down','enter']. Prefer " +
      "game_press when you are unsure what a screen will do, because here you do not see " +
      `the intermediate frames. ${ACTION_RESULT}`,
    promptSnippet: "Press a sequence of keys in the game",
    parameters: Type.Object({
      keys: Type.Array(Type.String(), {
        minItems: 1, description: "Key names in order",
      }),
      gap: Type.Optional(Type.Integer({ minimum: 0,
        description: "Frames between keys, default 6" })),
      stable: Type.Optional(Type.Integer({ minimum: 1, maximum: 600,
        description: "Frames the picture must hold still after the sequence",
      })),
    }),
    execute: (_id, params, signal) =>
      act(
        "/keys",
        { keys: params.keys, gap: params.gap },
        params.keys.join(" "),
        signal,
        params.stable ? `&stable=${params.stable}` : "",
      ),
  });

  pi.registerTool({
    name: "game_move",
    label: "Move",
    description:
      "Walk. One step turns the character to face that direction and moves one tile if it " +
      "is not blocked, so walking into a person or object is how you talk to it. If nothing " +
      `moves you are either blocked by scenery or still inside a cutscene. ${ACTION_RESULT}`,
    promptSnippet: "Walk in the game world",
    parameters: Type.Object({
      direction: Type.String({
        description: "kp7/kp9/kp1/kp3, or left/up/down/right",
      }),
      steps: Type.Optional(Type.Integer({ minimum: 1, maximum: 100,
        description: "Tiles to walk, default 1" })),
    }),
    execute: (_id, params, signal) => {
      const dir = params.direction.toLowerCase();
      const aliases: Record<string, string> = {
        kp7: "kp7", left: "left", upleft: "kp7", nw: "kp7",
        kp9: "kp9", up: "up", upright: "kp9", ne: "kp9",
        kp1: "kp1", down: "down", downleft: "kp1", sw: "kp1",
        kp3: "kp3", right: "right", downright: "kp3", se: "kp3",
      };
      const key = aliases[dir];
      if (!key) {
        return Promise.resolve({
          content: [{ type: "text" as const, text: "invalid movement direction" }],
          details: {},
          isError: true,
        });
      }
      const steps = params.steps ?? 1;
      return act("/keys", { keys: Array(steps).fill(key), gap: 6 }, `move ${dir} x${steps}`, signal);
    },
  });

  pi.registerTool({
    name: "game_wait",
    label: "Wait",
    description:
      "Let the game run without pressing anything. Use during boot, " +
      `scene transitions, battle animations and travel on the world map. ${ACTION_RESULT}`,
    promptSnippet: "Let the game run for a while",
    parameters: Type.Object({
      ms: Type.Optional(Type.Integer({ minimum: 0, maximum: 60000,
        description: "Milliseconds, default 1000" })),
    }),
    execute: (_id, params, signal) =>
      act("/wait", { ms: params.ms ?? 1000 }, `wait ${params.ms ?? 1000}ms`, signal),
  });

  pi.registerTool({
    name: "game_save",
    label: "Save",
    description:
      "Snapshot the whole emulator under a name. Unlike the game's own save system this " +
      "works anywhere, including mid-scene and mid-battle. Take one before anything risky.",
    promptSnippet: "Snapshot the emulator state",
    parameters: Type.Object({ name: Type.String({ description: "Snapshot name" }) }),
    execute: (_id, params, signal) => act("/save", { name: params.name }, `save ${params.name}`, signal),
  });

  pi.registerTool({
    name: "game_load",
    label: "Load",
    description:
      "Restore a snapshot taken by game_save. A snapshot taken during a cutscene restores " +
      "into that cutscene, so movement stays ignored until you finish reading it.",
    promptSnippet: "Restore an emulator snapshot",
    parameters: Type.Object({ name: Type.String({ description: "Snapshot name" }) }),
    execute: (_id, params, signal) => act("/load", { name: params.name }, `load ${params.name}`, signal),
  });

  pi.registerTool({
    name: "game_saves",
    label: "List saves",
    description: "List the emulator snapshots on disk with their sizes and timestamps.",
    promptSnippet: "List emulator snapshots",
    parameters: Type.Object({}),
    async execute(_id, _params, signal) {
      try {
        const res = await call("GET", "/slots", undefined, signal);
        return { content: [{ type: "text" as const, text: JSON.stringify(res, null, 2) }], details: res };
      } catch (err) {
        return offline(err);
      }
    },
  });
}
