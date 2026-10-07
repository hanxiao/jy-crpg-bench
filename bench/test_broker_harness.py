import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import aiohttp.test_utils
from aiohttp import web

BENCH_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import broker


def make_app():
    # Through the proxy, as in production: the harness record has no route
    # of its own, so the token check in front of it is part of what is tested.
    app = web.Application()
    app.add_routes([web.route("*", "/s/{sid}/{tail:.*}", broker.proxy)])
    app.on_startup.append(broker.open_http)
    app.on_cleanup.append(broker.close_http)
    return app


SID = "abc123def456"


class CleanTests(unittest.TestCase):
    def test_plain_json_survives(self):
        body = {"a": 1, "b": [1, 2.5, "x"], "c": {"d": None, "e": True}}
        self.assertEqual(broker._clean(body), body)

    def test_strings_lists_and_depth_are_bounded(self):
        out = broker._clean({"s": "x" * 1000, "l": list(range(500)),
                             "deep": {"a": {"b": {"c": {"d": 1}}}}})
        self.assertEqual(len(out["s"]), 300)
        self.assertEqual(len(out["l"]), 200)
        self.assertIsNone(out["deep"]["a"]["b"]["c"])

    def test_control_characters_are_dropped(self):
        self.assertEqual(broker._clean("a\nb\x00c"), "abc")


class HarnessApiTests(aiohttp.test_utils.AioHTTPTestCase):
    def get_app(self):
        return make_app()

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        proc = mock.Mock()
        proc.poll.return_value = None
        self.sessions = {SID: {"id": SID, "agent": "gpt-5", "token": "tok",
                               "proc": proc, "port": 1, "ends_at": 0}}
        self.catalogue = self.root / "catalog.json"
        self.patches = [
            mock.patch.object(broker, "sessions", self.sessions),
            mock.patch.object(broker, "bucket", return_value=None),
            mock.patch.object(broker, "LOCAL", self.root / "public"),
            mock.patch.dict(os.environ, {"QUNXIA_CATALOG": str(self.catalogue)}),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()
        super().tearDown()

    async def post(self, tail, body, token="tok", agent="gpt-5"):
        return await self.client.post(
            f"/s/{SID}/t/{token}/{tail}", data=json.dumps(body),
            headers={"Content-Type": "application/json", "X-Agent": agent})

    async def upload(self, name, data):
        r = await self.post("harness/upload", {"name": name, "size": len(data)})
        self.assertEqual(r.status, 200)
        body = await r.json()
        path = body["put_url"].split(str(self.server.port), 1)[1]
        # the address is the whole credential, as a bucket upload session is
        put = await self.client.put(path, data=data)
        self.assertEqual(put.status, 200)
        return body

    async def test_the_bare_address_cannot_file(self):
        r = await self.client.post(f"/s/{SID}/harness", data=b"{}",
                                   headers={"X-Agent": "gpt-5"})
        self.assertEqual(r.status, 403)

    async def test_the_agent_name_must_match(self):
        r = await self.post("harness", {}, agent="someone")
        self.assertEqual(r.status, 403)

    async def test_only_the_two_files_can_be_uploaded(self):
        r = await self.post("harness/upload", {"name": "../x", "size": 3})
        self.assertEqual(r.status, 400)
        r = await self.post("harness/upload", {"name": "bundle.zip", "size": 0})
        self.assertEqual(r.status, 400)
        r = await self.post("harness/upload", {"name": "bundle.zip",
                                               "size": (2 << 30) + 1})
        self.assertEqual(r.status, 400)

    async def test_a_local_upload_lands_under_the_runs_prefix(self):
        body = await self.upload("bundle.zip", b"PK\x03\x04data")
        stored = self.root / "public" / body["path"]
        self.assertEqual(stored.read_bytes(), b"PK\x03\x04data")
        self.assertTrue(body["path"].startswith(f"harness/gpt-5-{SID}-"))
        again = await (await self.post("harness/upload",
                                       {"name": "trace.html", "size": 3})).json()
        # one folder per run, however many calls
        self.assertEqual(again["path"].rsplit("/", 1)[0],
                         body["path"].rsplit("/", 1)[0])

    async def test_an_upload_over_its_declared_limit_is_refused(self):
        with mock.patch.dict(broker.HARNESS_FILES,
                             {"trace.html": ("text/html", 4)}):
            r = await self.post("harness/upload", {"name": "trace.html", "size": 4})
            path = (await r.json())["put_url"].split(str(self.server.port), 1)[1]
            put = await self.client.put(path, data=b"x" * 10,
                                        headers={"X-Agent": "gpt-5"})
        self.assertEqual(put.status, 413)

    async def test_the_summary_lands_with_the_files_the_store_holds(self):
        self.catalogue.write_text(json.dumps([{"id": SID, "agent": "gpt-5"}]))
        await self.upload("bundle.zip", b"zipdata")
        r = await self.post("harness", {"outcome": "finished", "toolCalls": {"bash": 3},
                                        "files": {"bundle": {"path": "elsewhere"}}})
        self.assertEqual(r.status, 200)
        entry = json.loads(self.catalogue.read_text())[0]
        h = entry["harness"]
        self.assertEqual(h["outcome"], "finished")
        self.assertEqual(h["toolCalls"], {"bash": 3})
        # the report cannot name files: the service names what it stored
        self.assertEqual(set(h["files"]), {"bundle"})
        self.assertTrue(h["files"]["bundle"]["path"].startswith("harness/"))
        self.assertEqual(h["files"]["bundle"]["bytes"], 7)

    async def test_a_summary_before_the_entry_waits_on_the_session(self):
        self.catalogue.write_text(json.dumps([]))
        r = await self.post("harness", {"outcome": "agent_stopped"})
        self.assertEqual(r.status, 202)
        self.assertEqual(self.sessions[SID]["harness"]["outcome"], "agent_stopped")
        self.assertIn("harness_since", self.sessions[SID])

    async def test_a_summary_over_64kb_is_refused(self):
        r = await self.post("harness", {"pad": "x" * 70000})
        self.assertEqual(r.status, 413)

    async def test_an_ended_run_still_takes_its_record(self):
        # Records are filed after the run, when every play call answers 410.
        self.sessions[SID]["proc"].poll.return_value = 0
        self.catalogue.write_text(json.dumps([{"id": SID, "agent": "gpt-5"}]))
        r = await self.post("harness", {"outcome": "finished"})
        self.assertEqual(r.status, 200)


class PendingRecordTests(unittest.TestCase):
    def test_a_held_record_keeps_the_entry_from_being_reaped(self):
        proc = mock.Mock()
        proc.poll.return_value = 0
        sess = {"id": SID, "proc": proc, "harness": {"outcome": "x"}}
        with mock.patch.object(broker, "result_of",
                               return_value={"complete": True}):
            self.assertEqual(broker.reap_decision(sess, 100.0, 10), "keep")
            sess.pop("harness")
            self.assertEqual(broker.reap_decision(sess, 100.0, 10), "mark")


if __name__ == "__main__":
    unittest.main()
