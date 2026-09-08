"""Run real publication and broker cleanup against isolated marker files."""
import asyncio
from copy import deepcopy
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import broker
import render
import warden


class ArtifactRetentionTests(unittest.IsolatedAsyncioTestCase):
    SID, AGENT = "retention-test", "probe"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="qunxia-retention-")
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name)
        self.videos, self.results = self.root / "videos", self.root / "results"
        self.recordings = self.root / "recordings"
        self.videos.mkdir()
        self.rendered = [self.videos / f"{self.AGENT}-{self.SID}.{suffix}"
                         for suffix in ("mp4", "jpg", "timeline.json")]
        self.journals = [self.recordings / self.SID / name
                         for name in ("recording.jsonl", "recordings/old.jsonl")]
        for path in self.journals:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"original recording marker")
        self.session = {"id": self.SID, "agent": self.AGENT, "work": None,
                        "proc": types.SimpleNamespace(poll=lambda: 0)}
        old_run = deepcopy(warden.run)
        self.addCleanup(lambda: (warden.run.clear(), warden.run.update(old_run)))
        patches = [
            mock.patch.object(warden, "RESULTS", self.results),
            mock.patch.object(warden, "VIDEOS", self.videos),
            mock.patch.object(warden, "SID", self.SID),
            mock.patch.object(warden, "AGENT", self.AGENT),
            mock.patch.object(warden, "PUBLIC_BASE", "http://127.0.0.1:12345"),
            mock.patch.object(broker, "RESULT_DIR", self.results),
            mock.patch.object(broker, "VIDEO_DIR", self.videos),
            mock.patch.object(broker, "RECORDING_DIR", self.recordings),
            mock.patch.object(broker, "sessions", {self.SID: self.session}),
            mock.patch.object(broker, "_results", {}),
            mock.patch.object(broker, "put"),
            mock.patch.object(broker, "live_payload", return_value={}),
            mock.patch.dict("os.environ", {"QUNXIA_LOCAL_PUBLIC": str(self.root / "public")}),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def render(self, _snap, out, _agent, timeline_extra=None):
        for path in self.rendered:
            path.write_bytes(b"rendered marker")
        return {"path": str(out), "frames": 1,
                "poster": str(self.rendered[1]), "timeline": str(self.rendered[2])}

    async def finalize(self, *, publish=True, bucket="test-bucket", fail=None,
                       catalog_error=False):
        remote = {}

        class Blob:
            def __init__(self, name):
                self.name = name

            def upload_from_filename(self, filename, content_type=None):
                if self.name == fail:
                    raise IOError("fixture upload failed")
                remote[self.name] = pathlib.Path(filename).read_bytes()

        storage = types.ModuleType("google.cloud.storage")
        storage.Client = lambda: types.SimpleNamespace(
            bucket=lambda _name: types.SimpleNamespace(blob=Blob))
        cloud = types.ModuleType("google.cloud")
        cloud.storage = storage
        google = types.ModuleType("google")
        google.cloud = cloud
        warden.run.update(playable=1, done="time", result=None)
        with mock.patch.dict(sys.modules, {"google": google, "google.cloud": cloud,
                                           "google.cloud.storage": storage}), \
                mock.patch.object(warden, "PUBLISH", publish), \
                mock.patch.object(warden, "BUCKET", bucket), \
                mock.patch.object(render, "render", side_effect=self.render), \
                mock.patch.object(warden, "append_catalog",
                                  side_effect=IOError("catalogue unavailable") if catalog_error else None), \
                mock.patch.object(warden.os, "_exit"), \
                mock.patch.object(warden.asyncio, "sleep", new=mock.AsyncMock()):
            await warden.warden({"events": []}, mock.Mock(), asyncio.Lock(), mock.AsyncMock())
        result = json.loads((self.results / f"{self.SID}.json").read_text())
        self.assertTrue(result["complete"])
        return result, remote

    async def sweep(self, result):
        warden.write_result(result)
        ticks = 0

        async def bounded_sleep(_seconds):
            nonlocal ticks
            ticks += 1
            if ticks > 30:
                raise asyncio.CancelledError

        with mock.patch.object(broker.asyncio, "sleep", bounded_sleep):
            with self.assertRaises(asyncio.CancelledError):
                await broker.sweep({})
        self.assertEqual(ticks, 31)
        for journal in self.journals:
            self.assertEqual(journal.read_bytes(), b"original recording marker")

    async def assert_retained(self, result):
        await self.sweep(result)
        for path in self.rendered:
            self.assertEqual(path.read_bytes(), b"rendered marker")
        self.assertFalse(self.session.get("artifacts_dropped", False))

    async def test_disabled_publication_keeps_local_files_even_with_a_bucket(self):
        result, remote = await self.finalize(publish=False)
        self.assertTrue(result["video_url"].startswith("http://127.0.0.1:12345/videos/"))
        self.assertEqual(remote, {})
        await self.assert_retained(result)

    async def test_missing_bucket_keeps_local_files(self):
        result, remote = await self.finalize(bucket="")
        self.assertTrue(result["video_url"])
        self.assertEqual(remote, {})
        await self.assert_retained(result)

    async def test_failed_video_upload_keeps_every_file(self):
        result, remote = await self.finalize(fail=self.rendered[0].name)
        self.assertIsNone(result["video_url"])
        self.assertEqual(remote, {})
        await self.assert_retained(result)

    async def test_failed_poster_after_video_upload_keeps_every_file(self):
        result, remote = await self.finalize(fail=self.rendered[1].name)
        self.assertTrue(result["video_url"])
        self.assertEqual(set(remote), {self.rendered[0].name})
        await self.assert_retained(result)

    async def test_failed_timeline_after_video_upload_keeps_every_file(self):
        result, remote = await self.finalize(fail=f"runs/{self.SID}.json")
        self.assertTrue(result["video_url"])
        self.assertEqual(set(remote), {path.name for path in self.rendered[:2]})
        await self.assert_retained(result)

    async def test_successful_upload_drops_only_rendered_copies(self):
        result, remote = await self.finalize()
        self.assertIsNone(result["error"])
        self.assertEqual(set(remote), {self.rendered[0].name, self.rendered[1].name,
                                       f"runs/{self.SID}.json"})
        await self.sweep(result)
        self.assertTrue(self.session.get("artifacts_dropped"))
        self.assertFalse(any(path.exists() for path in self.rendered))

    async def test_catalogue_failure_does_not_undo_successful_artifact_uploads(self):
        result, remote = await self.finalize(catalog_error=True)
        self.assertIn("catalogue unavailable", result["error"])
        self.assertEqual(len(remote), 3)
        await self.sweep(result)
        self.assertFalse(any(path.exists() for path in self.rendered))

    async def test_legacy_result_without_upload_confirmation_keeps_local_files(self):
        result, _remote = await self.finalize()
        result.pop("rendered_artifacts_uploaded", None)
        await self.assert_retained(result)

    async def test_incomplete_result_keeps_local_files(self):
        result, _remote = await self.finalize()
        result["complete"] = False
        await self.assert_retained(result)


if __name__ == "__main__":
    unittest.main()
