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
    # The same registration order as main(): the usage route must win over
    # the catch-all proxy, or a report would be forwarded to the session
    # process, which has no such endpoint.
    app = web.Application()
    app.add_routes([
        web.post("/s/{sid}/usage", broker.api_usage),
        web.route("*", "/s/{sid}/{tail:.*}", broker.proxy),
    ])
    return app


class CanonicalAgentNameTests(unittest.TestCase):
    # The name travels back through the usage report's X-Agent header, so
    # only what a latin-1 header can carry may be accepted at creation.

    def test_the_header_carryable_charset_survives(self):
        self.assertEqual(broker.canonical_agent_name("gpt-5.2 high"),
                         "gpt-5.2high")

    def test_non_ascii_names_cannot_round_trip_the_header(self):
        self.assertEqual(broker.canonical_agent_name("\u6a21\u578b GPT5"),
                         "GPT5")
        self.assertEqual(broker.canonical_agent_name("\u6a21\u578b"), "")

    def test_the_name_is_capped_at_forty_characters(self):
        self.assertEqual(broker.canonical_agent_name("a" * 40 + "bcde"),
                         "a" * 40)

    def test_case_is_preserved_and_surrounding_space_goes(self):
        self.assertEqual(broker.canonical_agent_name("  GPT-5 "), "GPT-5")


class ValidateUsageTests(unittest.TestCase):
    def test_minimal_report(self):
        usage = broker._validate_usage(
            {"input": 1, "output": 2, "cacheRead": 3, "cacheWrite": 4,
             "totalTokens": 10})
        self.assertEqual(usage, {"input": 1, "output": 2, "cacheRead": 3,
                                 "cacheWrite": 4, "totalTokens": 10,
                                 "cost": 0.0, "turns": 0})

    def test_optional_fields_are_kept_and_capped(self):
        usage = broker._validate_usage(
            {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
             "totalTokens": 0, "cost": 1.5, "turns": 9,
             "model": "provider/model-with-newline\n", "capturedAt": "junk"})
        self.assertEqual(usage["cost"], 1.5)
        self.assertEqual(usage["turns"], 9)
        self.assertEqual(usage["model"], "provider/model-with-newline")
        self.assertNotIn("capturedAt", usage)  # unknown fields never publish

    def test_each_token_field_is_required_and_whole(self):
        for key in ("input", "output", "cacheRead", "cacheWrite", "totalTokens"):
            body = {"input": 1, "output": 2, "cacheRead": 3, "cacheWrite": 4,
                    "totalTokens": 10}
            del body[key]
            self.assertIsNone(broker._validate_usage(body))
            bad = dict(body, **{key: "1"})
            self.assertIsNone(broker._validate_usage(bad))
            bad = dict(body, **{key: 1.5})
            self.assertIsNone(broker._validate_usage(bad))

    def test_booleans_are_not_tokens(self):
        body = {"input": True, "output": 0, "cacheRead": 0, "cacheWrite": 0,
                "totalTokens": 0}
        self.assertIsNone(broker._validate_usage(body))

    def test_negative_or_huge_numbers_are_refused(self):
        for value in (-1, 10**9 + 1):
            body = {"input": value, "output": 0, "cacheRead": 0,
                    "cacheWrite": 0, "totalTokens": 0}
            self.assertIsNone(broker._validate_usage(body))

    def test_cost_and_turns_bounds(self):
        base = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
                "totalTokens": 0}
        self.assertIsNone(broker._validate_usage(dict(base, cost=-0.1)))
        self.assertIsNone(broker._validate_usage(dict(base, cost=10**6 + 1)))
        self.assertIsNone(broker._validate_usage(dict(base, cost="cheap")))
        self.assertIsNone(broker._validate_usage(dict(base, turns=-1)))
        self.assertIsNone(broker._validate_usage(dict(base, turns=100001)))
        self.assertIsNone(broker._validate_usage(dict(base, turns=True)))

    def test_non_object_bodies_are_refused(self):
        for body in ([], "a report", 42, None):
            self.assertIsNone(broker._validate_usage(body))


class MergeUsageTests(unittest.TestCase):
    def test_local_catalogue_entry_gains_the_report(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogue = pathlib.Path(directory) / "catalog.json"
            catalogue.write_text(json.dumps(
                [{"id": "other", "agent": "x"}, {"id": "run1", "agent": "y"}]))
            with mock.patch.object(broker, "bucket", return_value=None), \
                    mock.patch.dict(os.environ,
                                    {"QUNXIA_CATALOG": str(catalogue)}):
                self.assertTrue(broker.merge_usage_into_catalog(
                    "run1", {"input": 7}))
            runs = json.loads(catalogue.read_text())
            self.assertEqual(runs[1]["usage"], {"input": 7})
            self.assertEqual(runs[0], {"id": "other", "agent": "x"})

    def test_missing_entry_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogue = pathlib.Path(directory) / "catalog.json"
            catalogue.write_text(json.dumps([{"id": "other"}]))
            with mock.patch.object(broker, "bucket", return_value=None), \
                    mock.patch.dict(os.environ,
                                    {"QUNXIA_CATALOG": str(catalogue)}):
                self.assertFalse(broker.merge_usage_into_catalog(
                    "run1", {"input": 7}))
            self.assertEqual(json.loads(catalogue.read_text()),
                             [{"id": "other"}])

    def test_no_catalogue_file_yet_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogue = pathlib.Path(directory) / "catalog.json"
            with mock.patch.object(broker, "bucket", return_value=None), \
                    mock.patch.dict(os.environ,
                                    {"QUNXIA_CATALOG": str(catalogue)}):
                self.assertFalse(broker.merge_usage_into_catalog(
                    "run1", {"input": 7}))
            self.assertFalse(catalogue.exists())


class ApiUsageTests(aiohttp.test_utils.AioHTTPTestCase):
    def get_app(self):
        return make_app()

    def session(self, sid="abc123def456", agent="gpt-5"):
        proc = mock.Mock()
        proc.poll.return_value = None  # alive, so the proxy cannot answer 410
        return mock.patch.object(broker, "sessions",
                                 {sid: {"id": sid, "agent": agent,
                                        "proc": proc, "port": 1,
                                        "ended_at": 0}})

    async def post(self, sid="abc123def456", agent="gpt-5", body=None,
                   x_agent="gpt-5"):
        payload = json.dumps(
            body if body is not None else
            {"input": 1, "output": 2, "cacheRead": 3, "cacheWrite": 4,
             "totalTokens": 10, "turns": 3})
        return await self.client.post(
            f"/s/{sid}/usage", data=payload,
            headers={"Content-Type": "application/json",
                     "X-Agent": x_agent})

    async def test_unknown_session_is_not_a_run(self):
        with self.session(sid="someone-else"):
            response = await self.post(sid="missing000")
        self.assertEqual(response.status, 404)

    async def test_wrong_agent_name_is_refused(self):
        with self.session():
            response = await self.post(x_agent="impostor")
        self.assertEqual(response.status, 403)
        self.assertIn("X-Agent", (await response.json())["error"])

    async def test_an_invalid_report_is_refused(self):
        with self.session():
            response = await self.post(body={"input": -1})
            self.assertEqual(response.status, 400)
            response = await self.post(body="[1, 2]")
            self.assertEqual(response.status, 400)

    async def test_a_report_lands_on_the_catalogue_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogue = pathlib.Path(directory) / "catalog.json"
            catalogue.write_text(json.dumps(
                [{"id": "abc123def456", "agent": "gpt-5", "actions": 12}]))
            with self.session(), mock.patch.object(
                    broker, "bucket", return_value=None), \
                    mock.patch.dict(os.environ,
                                    {"QUNXIA_CATALOG": str(catalogue)}):
                response = await self.post()
            self.assertEqual(response.status, 200)
            self.assertTrue((await response.json())["merged"])
            entry = json.loads(catalogue.read_text())[0]
            self.assertEqual(entry["actions"], 12)
            self.assertEqual(entry["usage"]["totalTokens"], 10)
            self.assertEqual(entry["usage"]["turns"], 3)

    async def test_a_report_before_the_entry_waits_on_the_session(self):
        with tempfile.TemporaryDirectory() as directory:
            catalogue = pathlib.Path(directory) / "catalog.json"
            catalogue.write_text(json.dumps([{"id": "other"}]))
            sessions = {"abc123def456": {"id": "abc123def456",
                                         "agent": "gpt-5"}}
            with mock.patch.object(broker, "sessions", sessions), \
                    mock.patch.object(broker, "bucket", return_value=None), \
                    mock.patch.dict(os.environ,
                                    {"QUNXIA_CATALOG": str(catalogue)}):
                response = await self.post()
            self.assertEqual(response.status, 202)
            self.assertFalse((await response.json())["merged"])
            self.assertIn("usage", sessions["abc123def456"])
            self.assertIn("usage_since", sessions["abc123def456"])

    async def test_the_route_is_not_proxied_to_the_session_process(self):
        # If the catch-all won this route, the proxy would answer for a dead
        # session with a 410 end payload or a 502, never a 403 of its own.
        proc = mock.Mock()
        proc.poll.return_value = None
        with mock.patch.object(broker, "sessions",
                               {"abc123def456": {"id": "abc123def456",
                                                  "agent": "gpt-5",
                                                  "proc": proc, "port": 1}}):
            response = await self.post(x_agent="impostor")
        self.assertEqual(response.status, 403)


if __name__ == "__main__":
    unittest.main()
