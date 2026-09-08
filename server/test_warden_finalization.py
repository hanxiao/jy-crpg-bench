"""What finalization publishes, where, and in what state.

The run result file and the catalogue entry are written at different moments
and by different paths; these tests pin the ordering and the state each copy
carries, plus the dev-catalogue path that previously drifted from the shared
one.
"""
import asyncio
import json
import os
import pathlib
import sys
import tempfile
import time
import types
import unittest
from copy import deepcopy
from unittest import mock

import warden


class FinalizationStateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.old_run = deepcopy(warden.run)
        self.addCleanup(lambda: (warden.run.clear(),
                                 warden.run.update(self.old_run)))
        self.tmp = tempfile.TemporaryDirectory(prefix="qunxia-warden-final-")
        self.addCleanup(self.tmp.cleanup)
        self.results = pathlib.Path(self.tmp.name) / "results"
        self.catalog = pathlib.Path(self.tmp.name) / "catalog.json"
        patches = [
            mock.patch.object(warden, "RESULTS", self.results),
            mock.patch.object(warden, "VIDEOS", pathlib.Path(self.tmp.name) / "videos"),
            mock.patch.object(warden, "SID", "test-sid"),
            mock.patch.object(warden, "BUCKET", ""),
            mock.patch.object(warden, "PUBLISH", True),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.exit_mock = mock.patch("os._exit").start()
        self.addCleanup(self.exit_mock.stop)
        old_catalog = os.environ.get("QUNXIA_CATALOG")
        os.environ["QUNXIA_CATALOG"] = str(self.catalog)
        if old_catalog is None:
            self.addCleanup(os.environ.pop, "QUNXIA_CATALOG")
        else:
            self.addCleanup(os.environ.__setitem__, "QUNXIA_CATALOG", old_catalog)
        warden.run.update(playable=time.time(), last_clock=warden.clock(),
                          deadline=warden.clock() + 1, done="time", result=None)

    async def test_catalog_entry_is_published_complete(self):
        health = mock.Mock()

        async def wait_frames(n):
            pass

        def fake_render(snap, out, agent, timeline_extra=None):
            return {"frames": 0, "poster": None, "timeline": None,
                    "path": str(out)}

        with mock.patch("render.render", side_effect=fake_render):
            await warden.warden({"events": []}, health, asyncio.Lock(), wait_frames)

        self.exit_mock.assert_called_once_with(0)
        entry = json.loads(self.catalog.read_text())[0]
        # The entry only exists once finalization is done, so the published
        # record must agree with the result file.
        self.assertTrue(entry["complete"])
        self.assertEqual(entry["id"], "test-sid")
        result = json.loads((self.results / "test-sid.json").read_text())
        self.assertTrue(result["complete"])
        self.assertEqual(result["valid"], True)
        self.assertEqual(result["reason"], "time")
        self.assertIsNone(result["error"])
        health.set_phase.assert_called_with("finalizing")

    def test_local_catalog_upserts_and_caps_like_the_shared_one(self):
        seed = [{"id": f"s{i:03d}"} for i in range(500)]
        self.catalog.write_text(json.dumps(seed))
        warden.append_catalog({"id": "s499", "complete": True})
        runs = json.loads(self.catalog.read_text())
        self.assertEqual(len(runs), 500)
        self.assertEqual(runs[0]["id"], "s499")
        self.assertEqual(sum(r["id"] == "s499" for r in runs), 1)
        warden.append_catalog({"id": "new", "complete": True})
        runs = json.loads(self.catalog.read_text())
        self.assertEqual(len(runs), 500)
        self.assertEqual(runs[0]["id"], "new")
        self.assertNotIn("s498", {r["id"] for r in runs})


class SharedAppendPreconditionTests(unittest.TestCase):
    """The shared object's generation precondition is the only thing keeping
    two nodes' finalizations from last-write-wins on each other. The fakes
    below stand in for google.cloud so the lazy imports resolve without the
    SDK installed."""

    def test_conflicting_append_rereads_the_generation_and_retries(self):
        class PreconditionFailed(Exception):
            pass

        store = {"runs": [{"id": "a"}], "generation": 5, "uploads": [],
                 "conflict_first": True}

        class FakeBlob:
            cache_control = None

            def download_as_bytes(self):
                return json.dumps(store["runs"]).encode()

            def upload_from_string(self, data, content_type=None,
                                   if_generation_match=None):
                store["uploads"].append(if_generation_match)
                if store["conflict_first"]:
                    # The concurrent writer lands between this writer's
                    # metadata read and its upload.
                    store["conflict_first"] = False
                    store["generation"] += 1
                    raise PreconditionFailed
                if if_generation_match != store["generation"]:
                    raise PreconditionFailed
                store["generation"] += 1
                store["runs"] = json.loads(data)

            def patch(self):
                pass

        class FakeBucket:
            def get_blob(self, name):
                blob = FakeBlob()
                blob.generation = store["generation"]
                return blob

            def blob(self, name):
                return self.get_blob(name)

        conf = types.ModuleType("google.api_core.exceptions")
        conf.PreconditionFailed = PreconditionFailed
        api_core = types.ModuleType("google.api_core")
        api_core.exceptions = conf
        storage = types.ModuleType("google.cloud.storage")
        storage.Client = lambda: types.SimpleNamespace(
            bucket=lambda name: FakeBucket())
        cloud = types.ModuleType("google.cloud")
        cloud.storage = storage
        google = types.ModuleType("google")
        google.cloud = cloud
        google.api_core = api_core
        with mock.patch.dict(sys.modules, {
                "google": google, "google.api_core": api_core,
                "google.api_core.exceptions": conf,
                "google.cloud": cloud, "google.cloud.storage": storage}), \
                mock.patch.object(warden, "BUCKET", "bench-test"), \
                mock.patch.object(warden, "PUBLISH", True):
            warden.append_catalog({"id": "b", "complete": True})

        self.assertEqual([r["id"] for r in store["runs"]], ["b", "a"])
        # The first attempt raced the fake concurrent writer; the retry had
        # to read the fresh generation back from the object, not reuse 5.
        self.assertEqual(store["uploads"], [5, 6])
        self.assertEqual(store["generation"], 7)
