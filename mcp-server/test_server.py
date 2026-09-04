import asyncio
import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
import pathlib
import threading
import unittest
import urllib.parse
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).with_name("server.py")
SESSION_GUIDE = "# guide served by the active benchmark session"
SESSION_GUIDE_URL = "data:text/plain," + urllib.parse.quote(SESSION_GUIDE)


def load_server(profile, **overrides):
    environment = {"QUNXIA_MCP_PROFILE": profile, **overrides}
    if profile == "benchmark":
        environment.setdefault("QUNXIA_BENCH_HELP_URL", SESSION_GUIDE_URL)
    environment = {
        **{key: value for key, value in os.environ.items()
           if not key.startswith("QUNXIA_")},
        **environment,
    }
    with patch.dict(os.environ, environment, clear=True):
        spec = importlib.util.spec_from_file_location(
            f"qunxia_mcp_server_{profile}", MODULE_PATH)
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        return server


SERVER = load_server("standalone")


def tool_names(server):
    return {tool.name for tool in asyncio.run(server.mcp.list_tools())}


@contextmanager
def http_fixture(responses):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.respond()

        def do_POST(self):
            self.respond()

        def respond(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            requests.append((self.command, self.path, json.loads(body) if body else None))
            status, content_type, payload = responses[len(requests) - 1]
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{http.server_port}", requests
    finally:
        http.shutdown()
        thread.join()
        http.server_close()


class PressContractTests(unittest.TestCase):
    def test_omitted_hold_uses_http_server_default(self):
        with patch.object(SERVER, "_act", return_value=[]) as act:
            SERVER.press("esc")
        act.assert_called_once_with(
            "/key", {"key": "esc"}, note="esc", stable=None,
        )

    def test_explicit_hold_is_forwarded(self):
        with patch.object(SERVER, "_act", return_value=[]) as act:
            SERVER.press("kp3", times=2, hold=14, stable=8)
        act.assert_called_once_with(
            "/keys", {"keys": ["kp3", "kp3"], "hold": 14},
            note="kp3 x2", stable=8,
        )

    def test_locally_expanded_action_batches_are_bounded(self):
        with self.assertRaisesRegex(
                ValueError, "times must be an integer from 1 to 100"):
            SERVER.press("kp3", times=101)
        with self.assertRaisesRegex(
                ValueError, "steps must be an integer from 1 to 100"):
            SERVER.move("right", steps=101)

    def test_broker_end_payload_keeps_played_seconds(self):
        result = SERVER._result({"ended": True, "played": 42})
        self.assertIn('"played_seconds": 42', result[0].text)

    def test_benchmark_actions_suppress_images(self):
        benchmark = load_server("benchmark")
        with patch.object(benchmark, "_call", return_value={"ok": True}) as call:
            benchmark._act("/key", {"key": "esc"})
        path = call.call_args.args[1]
        self.assertIn("scale=1", path)
        self.assertIn("image=0", path)

    def test_profiles_register_the_expected_tools(self):
        standalone = tool_names(SERVER)
        benchmark = load_server("benchmark")
        self.assertEqual(
            standalone,
            {
                "guide", "look", "press", "press_sequence", "move", "wait",
                "save_state", "load_state", "list_states", "reset_game",
            },
        )
        self.assertEqual(
            tool_names(benchmark),
            {"look", "press", "press_sequence", "wait"},
        )
        self.assertNotIn("interact", standalone)
        self.assertNotIn("open_menu", standalone)

    def test_benchmark_uses_the_connected_session_guide(self):
        benchmark = load_server("benchmark")
        self.assertTrue(benchmark.GUIDE.endswith(SESSION_GUIDE))


class MCPHTTPContractTests(unittest.TestCase):
    # A tiny synthetic PNG checks transport without requiring a running game.
    PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="

    def call_tool(self, server, name, arguments):
        return asyncio.run(server.mcp.call_tool(name, arguments))

    def test_null_optional_timing_arguments_use_the_server_defaults(self):
        for profile in ("standalone", "benchmark"):
            server = load_server(profile)
            for name, arguments, expected_body in (
                ("press", {"key": "esc", "hold": None, "stable": None}, {"key": "esc"}),
                ("press_sequence", {"keys": ["esc"], "stable": None},
                 {"keys": ["esc"], "gap": 6}),
            ):
                with self.subTest(profile=profile, tool=name), patch.object(
                        server, "_call", return_value={"ok": True}) as call:
                    self.call_tool(server, name, arguments)
                    self.assertEqual(call.call_args.args[2], expected_body)
                    self.assertNotIn("stable=", call.call_args.args[1])

    def test_standalone_action_preserves_png_image_content(self):
        response = json.dumps({
            "ok": True, "changed": True, "width": 320, "height": 200,
            "image_width": 640, "image_height": 400,
            "image": "data:image/png;base64," + self.PNG,
        }).encode()
        with http_fixture([(200, "application/json", response)]) as (origin, requests):
            server = load_server("standalone", QUNXIA_API=origin)
            result = self.call_tool(server, "press", {"key": "esc"})
        self.assertEqual(requests, [("POST", "/key?scale=2", {"key": "esc"})])
        self.assertEqual([part.type for part in result.content], ["text", "image"])
        self.assertEqual(result.content[1].data, self.PNG)
        self.assertEqual(result.content[1].model_dump(by_alias=True)["mimeType"], "image/png")
        self.assertTrue(base64.b64decode(result.content[1].data).startswith(b"\x89PNG\r\n\x1a\n"))

    def test_benchmark_uses_session_help_and_separate_json_observation(self):
        metadata = {"ok": True, "changed": True, "width": 320, "height": 200, "frame": 7}
        screen = {"ok": True, "width": 320, "height": 200,
                  "image": "data:image/png;base64," + self.PNG}
        responses = [(200, "text/plain", SESSION_GUIDE.encode()),
                     (200, "application/json", json.dumps(metadata).encode()),
                     (200, "application/json", json.dumps(screen).encode())]
        with http_fixture(responses) as (origin, requests):
            server = load_server("benchmark", QUNXIA_API=origin + "/s/test/api/",
                                 QUNXIA_BENCH_HELP_URL="", QUNXIA_BENCH_LANG="zh")
            action = self.call_tool(server, "press", {"key": "kp3", "hold": 14})
            look = self.call_tool(server, "look", {})
        self.assertEqual(requests, [
            ("GET", "/s/test/api/help?lang=zh", None),
            ("POST", "/s/test/api/key?scale=1&image=0", {"key": "kp3", "hold": 14}),
            ("GET", "/s/test/api/screen", None),
        ])
        self.assertTrue(server.GUIDE.endswith(SESSION_GUIDE))
        self.assertEqual([part.type for part in action.content], ["text"])
        self.assertEqual([part.type for part in look.content], ["text", "image"])
        self.assertEqual(look.content[1].data, self.PNG)

    def test_http_410_retains_broker_and_warden_timing(self):
        for timing in ({"played": 42}, {"played_seconds": 42}):
            ended = {"ok": True, "ended": True, "reason": "budget",
                     "actions": 7, "video_url": "https://example.invalid/run.mp4", **timing}
            with self.subTest(timing=timing), http_fixture([
                    (410, "application/json", json.dumps(ended).encode())]) as (origin, _requests):
                server = load_server("benchmark", QUNXIA_API=origin + "/api")
                result = self.call_tool(server, "wait", {"ms": 1500})
            self.assertEqual(len(result.content), 1)
            prefix, summary = result.content[0].text.split(" | ", 1)
            self.assertEqual(prefix, "BENCHMARK ENDED")
            summary = json.loads(summary)
            self.assertEqual(summary["played_seconds"], 42)
            self.assertEqual(summary["actions"], 7)
            self.assertEqual(summary["video_url"], ended["video_url"])


if __name__ == "__main__":
    unittest.main()
