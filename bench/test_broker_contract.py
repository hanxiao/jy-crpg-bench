import json
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


class LivePayloadTests(unittest.TestCase):
    def test_live_hero_preserves_inventory_progress(self):
        summary = {key: index for index, key in enumerate(broker.LIVE_HERO_FIELDS)}
        live = broker.live_hero(summary)
        self.assertEqual(set(live), set(broker.LIVE_HERO_FIELDS))
        self.assertEqual(live["inventory_distinct"], summary["inventory_distinct"])
        self.assertEqual(live["picked_item"], summary["picked_item"])

    def test_live_timing_contract_includes_submitted_input_totals(self):
        summary = {key: index for index, key in enumerate(broker.LIVE_TIMING_FIELDS)}
        live = broker.live_timing(summary)
        for field in ("decision_calls", "key_events", "input_frames", "wait_calls"):
            self.assertEqual(live[field], summary[field])


class ResultCacheTests(unittest.TestCase):
    # The hot loops ask result_of several times a second for as long as the
    # container lives; a finished run's file will not change under them, so a
    # result seen complete is remembered.

    def setUp(self):
        self.addCleanup(broker._results.clear)

    def test_a_complete_result_is_remembered(self):
        with tempfile.TemporaryDirectory() as directory:
            results = pathlib.Path(directory)
            (results / "sid1.json").write_text(
                json.dumps({"id": "sid1", "complete": True, "actions": 1}))
            with mock.patch.object(broker, "RESULT_DIR", results):
                first = broker.result_of("sid1")
                (results / "sid1.json").write_text(
                    json.dumps({"id": "sid1", "complete": True, "actions": 9}))
                second = broker.result_of("sid1")
            self.assertIs(first, second)
            self.assertEqual(second["actions"], 1)

    def test_an_unfinished_result_is_re_read(self):
        # The file is written twice: the summary while the video renders,
        # then the same result with the video up. Until it is complete it is
        # not remembered, so the second write is not missed.
        with tempfile.TemporaryDirectory() as directory:
            results = pathlib.Path(directory)
            (results / "sid1.json").write_text(
                json.dumps({"id": "sid1", "complete": False}))
            with mock.patch.object(broker, "RESULT_DIR", results):
                first = broker.result_of("sid1")
                (results / "sid1.json").write_text(
                    json.dumps({"id": "sid1", "complete": False,
                                "actions": 4}))
                second = broker.result_of("sid1")
            self.assertIsNot(first, second)
            self.assertEqual(second["actions"], 4)


def echo_app():
    """A stand-in session server: it says back what it was sent."""
    app = web.Application()

    async def echo(request):
        return web.json_response({
            "method": request.method,
            "path": request.path,
            "x_agent": request.headers.get("X-Agent"),
            "x_forwarded_host": request.headers.get("X-Forwarded-Host"),
            "x_forwarded_proto": request.headers.get("X-Forwarded-Proto")})

    app.add_routes([web.route("*", "/{tail:.*}", echo)])
    return app


class ProxyTests(aiohttp.test_utils.AioHTTPTestCase):
    """The token in the URL is the run's play credential: the session's own
    address plays, and an address without it only watches."""

    SID = "p1x2y3z4w5v6"
    TOKEN = "0f1e2d3c4b5a6978876543210fedcba9"

    async def asyncSetUp(self):
        self.addCleanup(broker._results.clear)
        self.upstream = echo_app()
        self.upstream_runner = web.AppRunner(self.upstream)
        await self.upstream_runner.setup()
        self.port = broker.free_port()
        await web.TCPSite(self.upstream_runner, "127.0.0.1",
                          self.port).start()
        self.results_dir = tempfile.TemporaryDirectory()
        self.results_dir_patch = mock.patch.object(
            broker, "RESULT_DIR", pathlib.Path(self.results_dir.name))
        self.results_dir_patch.start()
        await super().asyncSetUp()

    async def asyncTearDown(self):
        await super().asyncTearDown()
        await self.upstream_runner.cleanup()
        self.results_dir_patch.stop()
        self.results_dir.cleanup()

    def get_app(self):
        app = web.Application()
        app.add_routes([web.route("*", "/s/{sid}/{tail:.*}", broker.proxy)])
        app.on_startup.append(broker.open_http)
        app.on_cleanup.append(broker.close_http)
        return app

    def with_session(self):
        proc = mock.Mock()
        proc.poll.return_value = None  # the run is still going
        return mock.patch.object(
            broker, "sessions",
            {self.SID: {"id": self.SID, "agent": "gpt-5",
                        "token": self.TOKEN, "proc": proc,
                        "port": self.port,
                        "ends_at": 9e9}})

    async def test_the_bare_address_watches_and_the_record_names_the_run(self):
        with self.with_session():
            response = await self.client.get(
                f"/s/{self.SID}/status", headers={"X-Agent": "impostor"})
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(body["path"], "/status")
        # The record attributes the action to the run's agent, not to what
        # the caller claimed.
        self.assertEqual(body["x_agent"], "gpt-5")

    async def test_the_bare_address_cannot_play(self):
        with self.with_session():
            response = await self.client.post(
                f"/s/{self.SID}/api/key", data='{"steps": []}',
                headers={"Content-Type": "application/json"})
        self.assertEqual(response.status, 403)
        self.assertIn("watches", (await response.json())["error"])

    async def test_the_token_address_plays(self):
        with self.with_session():
            response = await self.client.post(
                f"/s/{self.SID}/t/{self.TOKEN}/api/key",
                data='{"steps": []}',
                headers={"Content-Type": "application/json",
                         "X-Agent": "impostor"})
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(body["path"], "/api/key")
        self.assertEqual(body["x_agent"], "gpt-5")

    async def test_a_wrong_token_cannot_play(self):
        with self.with_session():
            response = await self.client.post(
                f"/s/{self.SID}/t/not-the-token/api/key", data="{}",
                headers={"Content-Type": "application/json"})
        self.assertEqual(response.status, 403)

    async def test_usage_reaches_the_broker_through_the_token_address(self):
        # Answered by the broker before the proxy forwards anything, even
        # though the run is still going; a malformed report proves the
        # broker's own handler ran, not the upstream.
        with self.with_session():
            response = await self.client.post(
                f"/s/{self.SID}/t/{self.TOKEN}/usage", data='{"input": -1}',
                headers={"Content-Type": "application/json",
                         "X-Agent": "gpt-5"})
        self.assertEqual(response.status, 400)
        self.assertIn("usage", (await response.json())["error"].lower())

    async def test_a_finished_run_answers_every_address_with_the_end(self):
        (pathlib.Path(self.results_dir.name) / f"{self.SID}.json").write_text(
            json.dumps({"id": self.SID, "complete": True, "valid": True,
                        "reason": "time", "actions": 3}))
        with self.with_session():
            response = await self.client.get(
                f"/s/{self.SID}/t/{self.TOKEN}/api/screen")
        self.assertEqual(response.status, 410)
        body = await response.json()
        self.assertTrue(body["ended"])
        self.assertEqual(body["agent"], "gpt-5")

    async def test_the_proxy_states_its_own_origin_to_the_session(self):
        # The session server builds the help page's URLs from the
        # X-Forwarded pair, so it can only trust them; the proxy is the
        # only path to the server, and it states what it knows itself
        # whatever the caller sent.
        with self.with_session():
            response = await self.client.get(
                f"/s/{self.SID}/api/help",
                headers={"X-Forwarded-Host": "evil.example",
                         "X-Forwarded-Proto": "http"})
        self.assertEqual(response.status, 200)
        body = await response.json()
        # The host the proxy itself was reached under - its own address, not
        # the caller's claim and not the session's loopback port.
        self.assertEqual(body["x_forwarded_host"],
                         f"127.0.0.1:{self.server.port}")
        self.assertEqual(body["x_forwarded_proto"], "http")


class NewSessionUrlTests(aiohttp.test_utils.AioHTTPTestCase):
    # The credential contract: the only address that can play the run is the
    # one the session creation hands back, and the token that makes it so
    # rides in its path.

    async def asyncSetUp(self):
        self.addCleanup(broker._results.clear)
        await super().asyncSetUp()

    def get_app(self):
        app = web.Application()
        app.add_routes([web.post("/session", broker.api_new)])
        app.on_startup.append(broker.open_http)
        app.on_cleanup.append(broker.close_http)
        return app

    async def test_the_base_url_carries_the_play_token(self):
        spawned = {"id": "abc123def456", "agent": "gpt-5", "token": "tok123",
                   "ends_at": 1e9, "budget": 1200, "spawned": True}
        with mock.patch.object(broker, "start_session", new=mock.AsyncMock(
                return_value=spawned)):
            response = await self.client.post(
                "/session", json={"agent": "gpt-5", "minutes": 20})
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(body["session"], "abc123def456")
        self.assertTrue(body["base_url"].endswith("/s/abc123def456/t/tok123"))
        self.assertEqual(body["help_url"], body["base_url"] + "/api/help")
        # The token has no field of its own: it is visible only as the path
        # of the addresses the reply hands out.
        self.assertNotIn("token", body)
        self.assertIn(body["base_url"], body["message"])

    async def test_the_base_url_ignores_a_clients_origin_claims(self):
        # The play address carries the run's token in its path; a caller
        # must not be able to point that credential at a host of their own
        # choosing, so a client-supplied X-Forwarded-Host is ignored.
        spawned = {"id": "abc123def456", "agent": "gpt-5", "token": "tok123",
                   "ends_at": 1e9, "budget": 1200, "spawned": True}
        with mock.patch.object(broker, "start_session", new=mock.AsyncMock(
                return_value=spawned)):
            response = await self.client.post(
                "/session", json={"agent": "gpt-5", "minutes": 20},
                headers={"X-Forwarded-Host": "evil.example",
                         "X-Forwarded-Proto": "http"})
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertNotIn("evil.example", body["base_url"])
        self.assertTrue(body["base_url"].startswith("http://127.0.0.1:"))
        self.assertTrue(body["base_url"].endswith("/s/abc123def456/t/tok123"))

    async def test_the_scheme_is_the_front_doors_not_the_callers(self):
        # A front door appends its own observation after the client's;
        # the scheme must come from the innermost hop, so a caller
        # prepending http cannot turn play addresses into http.
        spawned = {"id": "abc123def456", "agent": "gpt-5", "token": "tok123",
                   "ends_at": 1e9, "budget": 1200, "spawned": True}
        with mock.patch.object(broker, "start_session", new=mock.AsyncMock(
                return_value=spawned)):
            response = await self.client.post(
                "/session", json={"agent": "gpt-5", "minutes": 20},
                headers={"X-Forwarded-Proto": "http,https"})
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertTrue(body["base_url"].startswith("https://127.0.0.1:"))


if __name__ == "__main__":
    unittest.main()
