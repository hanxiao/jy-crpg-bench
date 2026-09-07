#!/usr/bin/env python3
"""MCP server exposing 金庸群俠傳 to any LLM agent.

Run:  uv run --with 'mcp>=1,<3' mcp-server/server.py
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from game_knowledge import adapt_guide, mcp_guide as build_guide

from mcp.types import ImageContent, TextContent

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ModuleNotFoundError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer
    from mcp.server.fastmcp.exceptions import ToolError

API = os.environ.get("QUNXIA_API", "http://127.0.0.1:8765").rstrip("/")
PROFILE = os.environ.get("QUNXIA_MCP_PROFILE", "standalone")
if PROFILE not in ("standalone", "benchmark"):
    raise ValueError("QUNXIA_MCP_PROFILE must be standalone or benchmark")
BENCHMARK = PROFILE == "benchmark"
try:
    DEFAULT_SCALE = max(1, min(int(os.environ.get("QUNXIA_SCALE", "1" if BENCHMARK else "2")), 6))
except ValueError:
    DEFAULT_SCALE = 1 if BENCHMARK else 2
BASE = API[:-4] if API.endswith("/api") else API
LANGUAGE = os.environ.get("QUNXIA_BENCH_LANG", "en")
AGENT = "".join(
    c for c in os.environ.get("QUNXIA_AGENT", "mcp")
    if c.isascii() and (c.isalnum() or c in "-_."))[:40] or "mcp"

# Mirrors the game server's own request limits, so a bad argument is rejected
# here with a readable message instead of a 400 from the API.
DEFAULT_TAP_FRAMES = 10
MAX_ARRAY_REPEAT = 100
MAX_HOLD_FRAMES = 1200
MAX_GAP_FRAMES = 600
MAX_STABLE_FRAMES = 600
MAX_WAIT_MS = 60000
MAX_ACTION_FRAMES = 2800


def _benchmark_guide():
    """Snapshot benchmark guidance, defaulting to the connected session."""
    url = os.environ.get("QUNXIA_BENCH_HELP_URL")
    if not url:
        url = f"{API}/help?{urllib.parse.urlencode({'lang': LANGUAGE})}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            canonical = response.read().decode("utf-8")
    except (urllib.error.URLError, UnicodeError, TimeoutError) as error:
        raise RuntimeError(f"Cannot load benchmark instructions from {url}: {error}")
    if not canonical.strip():
        raise RuntimeError(f"Benchmark instructions from {url} are empty")
    return adapt_guide(canonical, benchmark=True)


GUIDE = _benchmark_guide() if BENCHMARK else build_guide(BASE, LANGUAGE, False)

mcp = MCPServer("qunxia", instructions=GUIDE)


def expose(enabled=True):
    """Register convenience tools only outside scored benchmark mode."""
    return mcp.tool() if enabled else (lambda function: function)


class GameOffline(ToolError):
    pass


class GameAPIError(ToolError):
    pass


def _bounded_int(name, value, minimum, maximum):
    if (isinstance(value, bool) or not isinstance(value, int)
            or not minimum <= value <= maximum):
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def _action_length(count, hold=DEFAULT_TAP_FRAMES, gap=6):
    total = count * (hold + 2) + max(0, count - 1) * gap
    if total > MAX_ACTION_FRAMES:
        raise ValueError(
            f"action is too long ({total} frames; maximum {MAX_ACTION_FRAMES})")


def _state_name(name):
    if not isinstance(name, str) or not 1 <= len(name) <= 64:
        raise ValueError("name must be a string from 1 to 64 characters")
    return name


def _decode_response(raw, path):
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise GameOffline(f"{path} returned a non-object JSON response")
    return value


def _call(method, path, payload=None, timeout=240):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"Content-Type": "application/json", "X-Agent": AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _decode_response(r.read(), path)
    except urllib.error.HTTPError as e:
        try:
            return _decode_response(e.read(), path)
        except Exception:
            raise GameOffline(f"{path} failed: HTTP {e.code}")
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise GameOffline(f"Cannot reach the game at {API} ({e}). Check "
                          "QUNXIA_API and the selected game or benchmark session.")


def _result(res, note=""):
    """Turn an API response into MCP content: a short status line plus the screen."""
    if res.get("ended"):
        summary = {key: res.get(key) for key in
                   ("reason", "why", "message", "actions", "video_url",
                    "video_pending")}
        summary["played_seconds"] = res.get("played_seconds", res.get("played"))
        return [TextContent(type="text", text="BENCHMARK ENDED | "
                            + json.dumps(summary, ensure_ascii=False))]
    if res.get("ok", True) is False:
        raise GameAPIError(str(res.get("error") or "game API rejected the action"))
    bits = []
    if "changed" in res:
        bits.append("screen changed" if res["changed"] else
                    "screen did NOT change (the action had no visible effect)")
    if res.get("image_error"):
        bits.append(f'image unavailable: {res["image_error"]}')
    if res.get("observation") == "follow-up":
        bits.append("follow-up screenshot (not atomic on a shared session)")
    if res.get("width") is not None and res.get("height") is not None:
        bits.append(f'{res["width"]}x{res["height"]}')
    line = (note + " | " if note else "") + " | ".join(str(b) for b in bits)
    out = [TextContent(type="text", text=line)]
    img = res.get("image")
    if img:
        out.append(ImageContent(
            type="image",
            data=img.split(",", 1)[1],
            mimeType="image/png",
        ))
    return out


def _act(path, payload, note="", **params):
    # The server encodes a frame only when asked. Standalone mode asks inside
    # the action so action and observation are atomic; benchmark mode returns
    # metadata only and the model calls look.
    q = {"scale": DEFAULT_SCALE, "image": 0 if BENCHMARK else 1}
    q.update({k: v for k, v in params.items() if v is not None})
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    res = _call("POST", f"{path}?{qs}", payload)
    if not BENCHMARK and res.get("ok", True) and not res.get("ended") and not res.get("image"):
        # An older server ignores image=1. Look separately and say so, since
        # another controller may have acted in between.
        try:
            observed = _call("GET", "/screen")
            if observed.get("ok", True) and observed.get("image"):
                for key in ("image", "image_width", "image_height", "width",
                            "height", "frame"):
                    if key in observed:
                        res[key] = observed[key]
                res["observation"] = "follow-up"
            elif observed.get("ok", True) is False:
                res["image_error"] = str(observed.get("error") or "screen failed")
        except GameOffline as exc:
            res["image_error"] = str(exc)
    return _result(res, note)


# ---------------------------------------------------------------- observation

@mcp.tool()
def look() -> list:
    """Look at the current game screen without pressing anything.

    Use this to re-read a screen, or to check where you are after reconnecting.
    The frame comes back at its native 320x200.
    """
    return _result(_call("GET", "/screen"))


@expose(not BENCHMARK)
def guide() -> str:
    """Re-read the canonical game manual and MCP tool-name mapping.

    The MCP server also sends this text as server instructions at connection
    time. This tool is a compatibility fallback for clients that do not place
    those optional instructions into the model context.
    """
    return GUIDE


# -------------------------------------------------------------------- actions

@mcp.tool()
def press(key: str, times: int = 1, hold: int | None = None,
          stable: int | None = None) -> list:
    """Press one key. In benchmark mode, call look after acting.

    key: kp1, kp3, kp7, kp9 (preferred movement keys), up, down, left, right,
         enter (or ok), space, esc, y, n, a-z, 0-9, f1-f12, tab,
         backspace. The native runner also accepts combos like "alt+x".
    times: repeat the same key this many times (useful for walking or for
         advancing several dialogue lines).
    hold: frames to hold the key down. Omit it to use the game server's safe
         tap default; override it only for an intentional longer press.
    stable: frames the picture must hold still before the action settles.

    Read the current screen: ordinary dialogue, choices, and animations may
    respond differently. Do not assume a failed movement means a cutscene.
    """
    times = _bounded_int("times", times, 1, MAX_ARRAY_REPEAT)
    if hold is not None:
        _bounded_int("hold", hold, 1, MAX_HOLD_FRAMES)
    if stable is not None:
        _bounded_int("stable", stable, 1, MAX_STABLE_FRAMES)
    _action_length(times, hold if hold is not None else DEFAULT_TAP_FRAMES)
    payload = {"hold": hold} if hold is not None else {}
    if times > 1:
        return _act("/keys", {"keys": [key] * times, **payload},
                    note=f"{key} x{times}", stable=stable)
    return _act("/key", {"key": key, **payload}, note=key, stable=stable)


@mcp.tool()
def press_sequence(keys: list[str], gap: int = 6,
                   stable: int | None = None) -> list:
    """Press several different keys in order.

    Use for a known menu path, e.g. ["esc", "down", "down", "enter"]. Prefer
    single presses when you are unsure what a screen will do, because you only
    see the result of the last key here.
    """
    if not isinstance(keys, list) or not 1 <= len(keys) <= MAX_ARRAY_REPEAT:
        raise ValueError(f"keys must contain between 1 and {MAX_ARRAY_REPEAT} entries")
    _bounded_int("gap", gap, 0, MAX_GAP_FRAMES)
    if stable is not None:
        _bounded_int("stable", stable, 1, MAX_STABLE_FRAMES)
    _action_length(len(keys), gap=gap)
    return _act("/keys", {"keys": keys, "gap": gap},
                note=" ".join(keys), stable=stable)


@expose(not BENCHMARK)
def move(direction: str, steps: int = 1) -> list:
    """Walk. direction is kp7, kp9, kp1, kp3, or up, down, left, right.

    Obstacles may prevent movement. For an ordinary person or container, stand
    adjacent, face the target, then press enter or space to
    investigate. Stepping on a tile can trigger a separate story event. If
    movement is unclear, inspect the screen rather than assuming its cause.
    """
    direction = str(direction).lower()
    if direction not in ("up", "down", "left", "right", "kp7", "kp9", "kp1", "kp3"):
        raise ValueError("direction must be kp7, kp9, kp1, kp3, up, down, left or right")
    steps = _bounded_int("steps", steps, 1, MAX_ARRAY_REPEAT)
    _action_length(steps)
    return _act("/keys", {"keys": [direction] * steps, "gap": 6},
                note=f"move {direction} x{steps}")


@mcp.tool()
def wait(ms: int = 1000) -> list:
    """Let the game run without pressing anything.

    Use it during boot, scene transitions, battle animations, and travel on the
    world map. Benchmark mode returns metadata only; call look when you need
    the next visible frame.
    """
    _bounded_int("ms", ms, 0, MAX_WAIT_MS)
    return _act("/wait", {"ms": ms}, note=f"wait {ms}ms")


# ----------------------------------------------------------------- savestates

@expose(not BENCHMARK)
def save_state(name: str = "agent") -> list:
    """Snapshot the whole emulator under this name.

    Emulator snapshots can include scene or battle state. Check that saving
    succeeded before relying on it; the game's own save menu is limited to the
    world map.
    """
    _state_name(name)
    return _act("/save", {"name": name}, note=f"save {name}")


@expose(not BENCHMARK)
def load_state(name: str = "agent") -> list:
    """Restore a snapshot taken by save_state.

    Inspect the restored screen, including any dialogue, menu, or animation,
    before choosing the next action.
    """
    _state_name(name)
    return _act("/load", {"name": name}, note=f"load {name}")


@expose(not BENCHMARK)
def list_states() -> str:
    """List the snapshots on disk with their sizes and timestamps."""
    res = _call("GET", "/slots")
    if res.get("ok", True) is False:
        raise GameAPIError(str(res.get("error") or "listing states failed"))
    return json.dumps(res, ensure_ascii=False, indent=2)


@expose(not BENCHMARK)
def reset_game() -> list:
    """Reboot the emulator back to the title screen. Discards unsaved progress."""
    return _act("/reset", {}, note="reset")


if __name__ == "__main__":
    mcp.run()
