"""Exercise catalogue retries without a cloud SDK, credentials or network."""
import json
import sys
import types
import unittest
from unittest import mock

import warden


class PreconditionFailed(Exception):
    pass


class CatalogueDownloadTests(unittest.TestCase):
    def setUp(self):
        self.runs = [{"id": "a"}, {"id": "b"}]
        self.generation = 5
        self.downloads = []
        self.failures = []
        self.uploads = []
        self.conflict = False
        self.missing = False
        case = self

        class Blob:
            def __init__(self):
                self.generation = case.generation

            def download_as_bytes(self):
                case.downloads.append(self.generation)
                if case.failures:
                    failure = case.failures.pop(0)
                    if isinstance(failure, Exception):
                        raise failure
                    return failure
                return json.dumps(case.runs).encode()

            def upload_from_string(self, data, content_type=None,
                                   if_generation_match=None):
                case.uploads.append(if_generation_match)
                if case.conflict:
                    case.conflict = False
                    case.generation += 1
                    case.runs.append({"id": "concurrent"})
                if if_generation_match != case.generation:
                    raise PreconditionFailed
                case.generation += 1
                case.missing = False
                case.runs = json.loads(data)

            def patch(self):
                pass  # Also lets the pre-fix implementation reach its assertion.

        bucket = types.SimpleNamespace(
            get_blob=lambda _name: None if self.missing else Blob(),
            blob=lambda _name: Blob())
        exceptions = types.ModuleType("google.api_core.exceptions")
        exceptions.PreconditionFailed = PreconditionFailed
        patches = [
            mock.patch.object(warden, "_bucket", return_value=bucket),
            mock.patch.dict(sys.modules, {"google.api_core.exceptions": exceptions}),
            mock.patch.object(warden.time, "sleep"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def append(self):
        warden.append_catalog({"id": "c", "complete": True})

    def test_failed_download_retries_without_overwriting_existing_runs(self):
        self.failures = [IOError("transient download failure")]
        self.append()
        self.assertEqual([r["id"] for r in self.runs], ["c", "a", "b"])
        self.assertEqual(self.downloads, [5, 5])
        self.assertEqual(self.uploads, [5])

    def test_corrupt_json_is_retried_without_uploading_it(self):
        self.failures = [b"truncated {"]
        self.append()
        self.assertEqual([r["id"] for r in self.runs], ["c", "a", "b"])
        self.assertEqual(self.downloads, [5, 5])
        self.assertEqual(len(self.uploads), 1)

    def test_persistent_failure_exhausts_retries_without_a_write(self):
        self.failures = [IOError("unavailable")] * 12
        with self.assertRaises(RuntimeError):
            self.append()
        self.assertEqual(self.runs, [{"id": "a"}, {"id": "b"}])
        self.assertEqual(self.downloads, [5] * 12)
        self.assertEqual(self.uploads, [])

    def test_only_a_missing_object_creates_an_empty_catalogue(self):
        self.missing, self.generation = True, 0
        self.append()
        self.assertEqual(self.runs, [{"id": "c", "complete": True}])
        self.assertEqual(self.downloads, [])
        self.assertEqual(self.uploads, [0])

    def test_conflict_rereads_the_generation_and_concurrent_entry(self):
        self.conflict = True
        self.append()
        self.assertEqual([r["id"] for r in self.runs],
                         ["c", "a", "b", "concurrent"])
        self.assertEqual(self.downloads, [5, 6])
        self.assertEqual(self.uploads, [5, 6])


if __name__ == "__main__":
    unittest.main()
