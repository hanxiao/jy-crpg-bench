import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bench_jobs as bj

SID = "0123456789ab"
TOKEN = "f" * 32


class RedactTests(unittest.TestCase):
    def test_known_values_patterns_and_the_play_token_go(self):
        r = bj.Redactor(["literal-key-123456"], TOKEN)
        text = (f"key literal-key-123456 and sk-{'a' * 30} and AIza{'b' * 35} "
                f"at http://h/s/{SID}/t/{TOKEN}/api")
        out = r.text(text)
        for gone in ("literal-key-123456", "sk-aaaa", "AIzabbb", TOKEN):
            self.assertNotIn(gone, out)
        self.assertIn(f"/s/{SID}/t/[REDACTED]/api", out)
        self.assertTrue(r.leaks(b"x literal-key-123456 y"))
        self.assertFalse(r.leaks(b"nothing here"))

    def test_secrets_are_read_from_pi_config_and_the_environment(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "models.json").write_text(json.dumps({"providers": {
                "p": {"baseUrl": "https://example.com/v1", "apiKey": "provider-key-1",
                      "headers": {"Authorization": "Bearer header-token-22"},
                      "models": [{"id": "m"}]}}}))
            (pathlib.Path(d) / "auth.json").write_text(json.dumps(
                {"z": {"type": "api_key", "key": "auth-key-333"}}))
            env = {"PI_CODING_AGENT_DIR": d, "SOME_API_KEY": "env-secret-4444",
                   "HARMLESS": "not-a-secret-value"}
            with mock.patch.dict(os.environ, env):
                values = bj.secret_values()
        for v in ("provider-key-1", "Bearer header-token-22", "header-token-22",
                  "auth-key-333", "env-secret-4444"):
            self.assertIn(v, values)
        self.assertNotIn("https://example.com/v1", values)
        self.assertNotIn("not-a-secret-value", values)


class EnvTests(unittest.TestCase):
    def test_pi_runs_without_unrelated_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "models.json").write_text(json.dumps(
                {"providers": {"mine": {"apiKey": "MINE_KEY"}}}))
            env = {"PI_CODING_AGENT_DIR": d, "PATH": "/bin", "HOME": "/h",
                   "MINE_KEY": "m", "OTHER_API_KEY": "o", "OPENAI_API_KEY": "x"}
            with mock.patch.dict(os.environ, env, clear=True):
                out = bj.scrubbed_env("mine")
                self.assertEqual(out["MINE_KEY"], "m")
                self.assertNotIn("OTHER_API_KEY", out)
                self.assertNotIn("OPENAI_API_KEY", out)
                self.assertEqual(bj.scrubbed_env("openai")["OPENAI_API_KEY"], "x")


class EventTests(unittest.TestCase):
    def test_deltas_are_dropped_and_tool_calls_kept_short(self):
        self.assertIsNone(bj.compact_event({"type": "message_update"}, 1))
        self.assertIsNone(bj.compact_event({"type": "tool_execution_update"}, 1))
        end = bj.compact_event({"type": "tool_execution_end", "toolCallId": "c",
                                "toolName": "bash", "isError": False,
                                "result": {"content": [{"type": "text",
                                                        "text": "x" * 1000}]}}, 2)
        self.assertEqual((end["tool"], end["chars"], len(end["head"])), ("bash", 1000, 400))
        msg = bj.compact_event({"type": "message_end", "message": {
            "role": "assistant", "stopReason": "toolUse", "usage": {"input": 3},
            "content": [{"type": "toolCall", "name": "read"},
                        {"type": "image", "data": "A" * 9999}]}}, 3)
        self.assertEqual(msg["tools"], ["read"])
        self.assertNotIn("A" * 100, json.dumps(msg))
        settled = bj.compact_event({"type": "agent_end", "messages": [1, 2]}, 4)
        self.assertNotIn("messages", settled)

    def test_the_session_is_read_from_the_server_reply(self):
        with tempfile.TemporaryDirectory() as d:
            job = bj.Job(pathlib.Path(d), {"name": "m-high", "minutes": 60}, None, "pi", "0")
            job.started = time.time()
            reply = json.dumps({"ok": True, "agent": "m-high", "ends_at": 1791400000.5,
                                "base_url": f"https://x.run.app/s/{SID}/t/{TOKEN}"})
            job.spot_session(reply, time.time())
            self.assertEqual(job.session["sid"], SID)
            self.assertEqual(job.session["token"], TOKEN)
            self.assertEqual(job.session["ends_at"], 1791400000.5)
            self.assertEqual(job.session["base"], "https://x.run.app")
            # a second session is noted, not adopted
            job.spot_session(f"https://x.run.app/s/{'1' * 12}/t/{TOKEN}", time.time())
            self.assertEqual(job.session["sid"], SID)
            self.assertEqual(job.sessions_seen, [SID, "1" * 12])
            saved = json.loads((pathlib.Path(d) / "run.json").read_text())
            self.assertEqual(saved["session"]["id"], SID)


class EndAndSecondSessionTests(unittest.TestCase):
    def test_the_end_is_read_however_it_was_printed(self):
        for text in ('{"ok": true, "ended": true}', "{'ended': True, 'reason': 'time'}",
                     "This benchmark run has ended. Stop playing."):
            self.assertTrue(bj.ENDED.search(text), text)
        self.assertFalse(bj.ENDED.search('{"ended": false}'))

    def test_a_second_session_ends_the_job_and_is_withdrawn(self):
        with tempfile.TemporaryDirectory() as d:
            job = bj.Job(pathlib.Path(d), {"name": "m-high", "minutes": 60}, None, "pi", "0")
            job.started = time.time()
            job.spot_session(json.dumps({"agent": "m-high", "ends_at": 1.0,
                                         "base_url": f"http://h/s/{SID}/t/{TOKEN}"}), time.time())
            other = "2" * 12
            job.spot_session(f"{{'agent': 'm-high', 'base_url': 'http://h/s/{other}/t/{'e' * 32}'}}",
                             time.time())
            self.assertEqual([x["sid"] for x in job.extras], [other])
            calls = []
            with mock.patch.object(bj, "http", side_effect=lambda *a, **k: calls.append(a) or (200, {})):
                out = job.withdraw(job.extras[0])
            self.assertEqual(calls[0][1], f"http://h/s/{other}/t/{'e' * 32}/withdraw")
            self.assertEqual(calls[0][3], {"X-Agent": "m-high"})
            self.assertTrue(out["withdrawn"])


class ArtifactTests(unittest.TestCase):
    def test_links_and_environments_are_not_copied(self):
        with tempfile.TemporaryDirectory() as d:
            ws = pathlib.Path(d)
            work = ws / "work"
            (work / ".venv" / "lib").mkdir(parents=True)
            (work / ".venv" / "lib" / "big.py").write_text("x")
            (work / "notes.md").write_text("plan")
            (work / "keys").symlink_to(pathlib.Path.home())
            (work / "link.txt").symlink_to("/etc/hosts")
            skipped = bj.collect_artifacts(ws, None)
            copied = sorted(str(p.relative_to(ws / "artifacts"))
                            for p in (ws / "artifacts").rglob("*") if p.is_file())
            self.assertEqual(copied, ["work/notes.md"])
            self.assertIn(".venv/", skipped)
            self.assertIn("keys/", skipped)
            self.assertIn("link.txt", skipped)

    def test_writes_outside_the_folder_are_listed(self):
        with tempfile.TemporaryDirectory() as d:
            ws = pathlib.Path(d)
            (ws / "sessions").mkdir()
            calls = [{"type": "toolCall", "name": "write", "arguments": {"path": p}}
                     for p in (f"/tmp/{SID}/a.py", "/Users/x/evil.py", "rel.txt")]
            (ws / "sessions" / "s.jsonl").write_text(json.dumps(
                {"type": "message", "message": {"role": "assistant",
                                                "content": calls}}) + "\n")
            self.assertEqual(bj.outside_writes(ws, SID), ["/Users/x/evil.py"])


class ProcTreeTests(unittest.TestCase):
    def test_a_background_grandchild_outliving_its_parent_is_killed(self):
        with tempfile.TemporaryDirectory() as d:
            pidfile = pathlib.Path(d) / "pid"
            # the shell starts a sleeper in the background and exits at once,
            # so the sleeper is reparented before anyone asks to kill it
            proc = subprocess.Popen(
                ["/bin/sh", "-c", f"(sleep 60 & echo $! > {pidfile}; wait) & sleep 1"],
                start_new_session=True)
            tree = bj.ProcTree(proc.pid)
            deadline = time.time() + 5
            while not pidfile.exists() and time.time() < deadline:
                tree.sample()
                time.sleep(0.1)
            tree.sample()
            sleeper = int(pidfile.read_text())
            proc.wait()
            self.assertIn(sleeper, tree.alive())
            self.assertEqual(tree.kill(grace=3), 0)
            with self.assertRaises(OSError):
                os.kill(sleeper, 0)


class PlanTests(unittest.TestCase):
    def test_reps_are_spread_across_the_batch(self):
        specs = [{"name": "a", "reps": 2}, {"name": "b", "reps": 1}]
        self.assertEqual([(j["name"], j["rep"]) for j in bj.expand(specs)],
                         [("a", 1), ("b", 1), ("a", 2)])

    def test_selection_syntax(self):
        self.assertEqual(bj.pick("1,3-4", 5), [0, 2, 3])
        self.assertEqual(bj.pick("all", 2), [0, 1])
        with self.assertRaises(ValueError):
            bj.pick("9", 3)

    def test_names_follow_the_broker_rule(self):
        self.assertEqual(bj.default_name({"id": "Qwen3.8-27B-NVFP4"}, "high"),
                         "qwen3.8-27b-nvfp4-high")
        self.assertEqual(bj.canonical_agent_name("模型 a b"), "ab")

    def test_the_version_floor_compares_numerically(self):
        self.assertGreater(bj.version_tuple("1.0.4"), bj.MIN_PI_VERSION)
        self.assertGreater(bj.version_tuple("0.84.10"), bj.MIN_PI_VERSION)
        self.assertLess(bj.version_tuple("0.9.0"), bj.MIN_PI_VERSION)

    def test_the_image_window_is_the_one_extension(self):
        self.assertIn("--no-extensions", bj.PI_FLAGS)
        self.assertEqual(bj.PI_FLAGS[-2:], ["-e", str(bj.IMAGE_WINDOW_EXT)])
        self.assertTrue(bj.IMAGE_WINDOW_EXT.exists())

    def test_the_environment_names_the_python_a_model_gets(self):
        env = bj.environment()
        self.assertIn("python3", env)
        self.assertIn("PIL", env.get("python_modules", {}))

    def test_the_toolkit_pins_are_read_from_the_file(self):
        python, pins = bj.toolkit_spec()
        self.assertRegex(python, r"^3\.\d+\.\d+$")
        self.assertEqual(set(pins), set(bj.TOOLKIT_MODULES.values()))
        self.assertTrue(all(v[0].isdigit() for v in pins.values()))

    def test_a_missing_or_mismatched_toolkit_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(bj.toolkit_check(pathlib.Path(d)))

    def test_jobs_run_the_toolkit_python_first(self):
        with mock.patch.object(bj, "TOOLKIT", {"path": "/tk"}), \
                mock.patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            env = bj.scrubbed_env("x")
        self.assertTrue(env["PATH"].startswith("/tk/bin" + os.pathsep))
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")

    def test_brief_urls(self):
        self.assertEqual(bj.brief_url("https://h/x/", 60, "zh"), "https://h/x/60m/agents.md")
        self.assertEqual(bj.brief_url("https://h/x", 20, "en"), "https://h/x/en/20m/agents.md")


if __name__ == "__main__":
    unittest.main()
