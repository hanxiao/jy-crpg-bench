import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent


def executable(path, source):
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


class CodexLauncherTest(unittest.TestCase):
    def test_registration_is_absolute_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()
            marker = tmp_path / "registered"
            calls = tmp_path / "calls.jsonl"
            executable(
                bin_dir / "codex",
                f"""#!/usr/bin/env python3
import json, pathlib, sys
marker = pathlib.Path({str(marker)!r})
calls = pathlib.Path({str(calls)!r})
with calls.open("a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["mcp", "get"] and not marker.exists():
    raise SystemExit(1)
if sys.argv[1:3] == ["mcp", "add"]:
    marker.write_text("yes", encoding="utf-8")
print("ok")
""",
            )
            executable(bin_dir / "uv", "#!/bin/sh\nexit 0\n")
            env = os.environ.copy()
            env.update({
                "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                "QUNXIA_API": "http://127.0.0.1:9999/api/",
                "QUNXIA_CODEX_MCP_NAME": "qunxia-test",
            })
            command = ["zsh", str(ROOT / "Scripts/setup-codex.sh")]
            first = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                   capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                    capture_output=True, timeout=15)
            self.assertEqual(second.returncode, 0, second.stderr)

            recorded = [json.loads(line) for line in calls.read_text().splitlines()]
            adds = [args for args in recorded if args[:2] == ["mcp", "add"]]
            self.assertEqual(len(adds), 1)
            add = adds[0]
            self.assertIn("QUNXIA_API=http://127.0.0.1:9999/api", add)
            self.assertIn("QUNXIA_AGENT=codex", add)
            self.assertIn("mcp>=1,<3", add)
            self.assertIn(str((ROOT / "mcp-server/server.py").resolve()), add)


class PlayClientTest(unittest.TestCase):
    """The command-line client must speak the same API to both runners."""

    def _game_server(self, recorded):
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class Handler(BaseHTTPRequestHandler):
            def reply(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else None
                recorded.append({"path": self.path,
                                 "body": body.decode() if body else None})
                payload = json.dumps({"ok": True}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = reply

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server

    def _run_client(self, server, *args, **env_overrides):
        env = dict(os.environ)
        env.pop("QUNXIA_RESET_TOKEN", None)
        env["QUNXIA_API"] = "http://127.0.0.1:%d/api" % server.server_address[1]
        env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(ROOT / "Scripts" / "play.py"), *args],
            env=env, capture_output=True, text=True, timeout=15)

    def test_reset_sends_the_token_from_the_environment(self):
        recorded = []
        server = self._game_server(recorded)
        try:
            result = self._run_client(server, "reset", QUNXIA_RESET_TOKEN="secret-token")
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(recorded[0]["path"], "/api/reset?token=secret-token")

    def test_reset_without_a_token_still_reaches_the_local_runner(self):
        recorded = []
        server = self._game_server(recorded)
        try:
            result = self._run_client(server, "reset")
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(recorded[0]["path"], "/api/reset")


if __name__ == "__main__":
    unittest.main()
