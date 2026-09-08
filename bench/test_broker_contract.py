import asyncio
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import aiohttp
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

    async def last_frames(request):
        # A game that speaks once and dies: the view must end with it.
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.send_str("last-frame")
        await ws.close()
        return ws

    async def echo(request):
        return web.json_response({
            "method": request.method,
            "path": request.path,
            "x_agent": request.headers.get("X-Agent"),
            "x_forwarded_host": request.headers.get("X-Forwarded-Host"),
            "x_forwarded_proto": request.headers.get("X-Forwarded-Proto")})

    app.add_routes([web.get("/ws", last_frames),
                    web.route("*", "/{tail:.*}", echo)])
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

    async def test_a_view_ends_when_the_run_ends(self):
        # When the game's socket dies, the view must die with it: a
        # spectator is not left holding a live socket on a frozen frame.
        with self.with_session():
            async with self.client.ws_connect(f"/s/{self.SID}/ws") as down:
                frame = await asyncio.wait_for(down.receive(), timeout=5)
                self.assertEqual(frame.data, "last-frame")
                close = await asyncio.wait_for(down.receive(), timeout=5)
                self.assertEqual(close.type, aiohttp.WSMsgType.CLOSE)

    async def test_a_reaped_session_address_is_gone(self):
        # Past the grace the sweep pops the entry. The address must then
        # answer the way every unknown session does - 404, not a crash -
        # and the on-disk result stays: it is the bounded evidence, and it
        # is what a proxy call that lost its race with a dying worker
        # re-reads to answer 410 instead of 502.
        proc = mock.Mock()
        proc.poll.return_value = 0
        sess = {"id": self.SID, "agent": "gpt-5", "token": self.TOKEN,
                "proc": proc, "port": self.port, "ends_at": 0,
                "eligible_at": 0}
        patch = mock.patch.object(broker, "sessions", {self.SID: sess})
        patch.start()
        self.addCleanup(patch.stop)
        broker._results[self.SID] = {"complete": True, "reason": "time"}
        (broker.RESULT_DIR / f"{self.SID}.json").write_text(
            json.dumps({"complete": True, "reason": "time"}))
        self.assertEqual(broker.reap_finished(1e9), [self.SID])
        response = await self.client.get(
            f"/s/{self.SID}/t/{self.TOKEN}/status")
        self.assertEqual(response.status, 404)
        self.assertTrue((broker.RESULT_DIR / f"{self.SID}.json").exists())


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


class CapacityTests(aiohttp.test_utils.AioHTTPTestCase):
    # The capacity check and the hold of a start's slot are one atomic step
    # on this loop: a burst of concurrent /session calls must not all read
    # "one under capacity" and all start.

    async def asyncSetUp(self):
        self.addCleanup(setattr, broker, "_reservations", 0)
        await super().asyncSetUp()

    def get_app(self):
        app = web.Application()
        app.add_routes([web.post("/session", broker.api_new)])
        app.on_startup.append(broker.open_http)
        app.on_cleanup.append(broker.close_http)
        return app

    async def test_two_callers_cannot_take_the_last_slot(self):
        gate = asyncio.Event()
        holding = asyncio.Event()
        starts = []

        async def fake_start(app, agent, budget, publish=True):
            starts.append(agent)
            holding.set()                 # admitted, and holding the slot
            await gate.wait()
            return {"id": "abc123def456", "agent": agent, "token": "tok",
                    "ends_at": 1e9, "budget": budget, "spawned": True}

        with mock.patch.object(broker, "MAX_SESSIONS", 2), \
             mock.patch.object(broker, "running_count", lambda: 1), \
             mock.patch.object(broker, "_start_session", new=fake_start):
            first = asyncio.create_task(
                self.client.post("/session", json={"agent": "a"}))
            # The first caller is admitted and now holds the last slot,
            # mid-start - the moment a real start (copied game dir, booted
            # worker) occupies it for seconds.
            await asyncio.wait_for(holding.wait(), timeout=5)
            second = await self.client.post("/session", json={"agent": "b"})
            self.assertEqual(second.status, 503)
            body = await second.json()
            self.assertEqual(body["running"], 2)
            self.assertEqual(body["capacity"], 2)
            gate.set()
            first = await asyncio.wait_for(first, timeout=5)
            self.assertEqual(first.status, 200)
        self.assertEqual(len(starts), 1)
        self.assertEqual(broker._reservations, 0)

    async def test_a_refused_start_releases_its_slot(self):
        async def refusing(app, agent, budget, publish=True):
            raise web.HTTPServiceUnavailable(text="{}")

        with mock.patch.object(broker, "MAX_SESSIONS", 1), \
             mock.patch.object(broker, "running_count", lambda: 0), \
             mock.patch.object(broker, "_start_session", new=refusing):
            response = await self.client.post("/session", json={"agent": "a"})
        self.assertEqual(response.status, 503)
        self.assertEqual(broker._reservations, 0)


class StartStateTests(aiohttp.test_utils.AioHTTPTestCase):
    # The opening savestate is authored on the machine that uses it. While it
    # is missing, no session may be handed a worker to boot and a load to
    # fail - and a failed burst may not be the last one.

    async def asyncSetUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        await super().asyncSetUp()

    def get_app(self):
        app = web.Application()
        app.add_routes([web.post("/session", broker.api_new)])
        app.on_startup.append(broker.open_http)
        app.on_cleanup.append(broker.close_http)
        return app

    async def test_sessions_refuse_fast_while_authoring(self):
        self.app["booting"] = True
        response = await self.client.post("/session", json={"agent": "a"})
        self.assertEqual(response.status, 503)
        body = await response.json()
        self.assertEqual(body["error"], "the opening savestate is not ready")

    async def test_sessions_refuse_while_the_state_is_missing(self):
        # Between failed bursts the state is still missing, so the refusal
        # stays on: the hint promises a rebuild, and there must be one.
        self.app["bootstrap_failed"] = True
        response = await self.client.post("/session", json={"agent": "a"})
        self.assertEqual(response.status, 503)
        body = await response.json()
        self.assertEqual(body["error"], "the opening savestate is not ready")

    async def test_failed_bursts_keep_offering_until_the_state_lands(self):
        # A slow host burns the opening-scene budget and loses; authoring must
        # keep offering bursts until the state exists, not stop after the
        # first three tries.
        state = pathlib.Path(self.tempdir.name) / "start.state"
        calls = []

        async def failing_then_good(state_, attempt):
            calls.append(attempt)
            if len(calls) < 3:
                raise RuntimeError("burned the opening-scene budget")
            state_.write_bytes(b"state")

        with mock.patch.dict(os.environ,
                             {"QUNXIA_START_STATE": str(state)}), \
             mock.patch.object(broker, "author_start_state",
                               new=failing_then_good):
            await broker.ensure_start_state(self.app)
        self.assertEqual(calls, [1, 2, 3])
        self.assertTrue(state.exists())
        self.assertFalse(self.app.get("booting"))
        self.assertFalse(self.app.get("bootstrap_failed"))

    async def test_a_broken_state_is_reauthored(self):
        # A state that exists but will not load is not worth retrying the load
        # for: it goes, and a fresh one is authored. An in-flight burst is not
        # doubled by a second broken session.
        state = pathlib.Path(self.tempdir.name) / "start.state"
        state.write_bytes(b"corrupt")
        made = []

        async def fresh(state_, attempt):
            made.append(attempt)
            state_.write_bytes(b"fresh")

        with mock.patch.dict(os.environ,
                             {"QUNXIA_START_STATE": str(state)}), \
             mock.patch.object(broker, "author_start_state", new=fresh):
            broker.reauthor_start_state(self.app)
            self.assertFalse(state.exists())
            self.assertTrue(self.app["bootstrap_failed"])
            task = self.app["bootstrap"]
            broker.reauthor_start_state(self.app)
            self.assertIs(self.app["bootstrap"], task)
            await asyncio.wait_for(task, timeout=10)
        self.assertEqual(made, [1])
        self.assertEqual(state.read_bytes(), b"fresh")
        self.assertFalse(self.app.get("booting"))
        self.assertFalse(self.app.get("bootstrap_failed"))


class ReapTests(unittest.TestCase):
    # The only residue that outlives a run is the entry itself: a dict, a
    # Popen handle and a cached result. It is reclaimable once every last
    # caller has had its time - the agent's 410 and the one-shot usage
    # report both land within the grace - and the grace is what keeps them
    # from being cut off. Without it the entries grew for the life of the
    # container, and memory is the resource that OOMed it at 33 runs.

    def setUp(self):
        self.sessions = broker.sessions
        self.results = broker._results
        broker.sessions = {}
        broker._results = {}

    def tearDown(self):
        broker.sessions = self.sessions
        broker._results = self.results

    def finished(self, sid, poll=0, complete=True, usage=None,
                 eligible_at=None):
        sess = {"id": sid, "agent": "a", "proc": mock.Mock()}
        sess["proc"].poll.return_value = poll
        if usage is not None:
            sess["usage"] = usage
            sess["usage_since"] = 0.0
        if eligible_at is not None:
            sess["eligible_at"] = eligible_at
        broker.sessions[sid] = sess
        if complete:
            broker._results[sid] = {"complete": True}
        return sess

    def test_a_running_session_is_never_touched(self):
        self.finished("a" * 12, poll=None)
        self.assertEqual(broker.reap_finished(1e9), [])
        self.assertEqual(len(broker.sessions), 1)

    def test_a_dead_session_without_a_final_result_is_kept(self):
        self.finished("b" * 12, complete=False)
        self.assertEqual(broker.reap_finished(1e9), [])

    def test_a_result_still_rendering_is_kept(self):
        # The first write carries the summary while the video renders; only
        # the second is complete. An in-flight render keeps its entry.
        broker._results["c" * 12] = {"complete": False}
        self.finished("c" * 12, complete=False)
        self.assertEqual(broker.reap_finished(1e9), [])

    def test_a_held_usage_report_holds_back_the_grace(self):
        sess = self.finished("d" * 12, usage={"input": 1})
        self.assertEqual(broker.reap_finished(1e9), [])
        # The clock does not run while a report is held: it starts when the
        # report is resolved, not when the run ended.
        self.assertNotIn("eligible_at", sess)

    def test_the_grace_clock_starts_once(self):
        sess = self.finished("e" * 12)
        self.assertEqual(broker.reap_finished(1000.0), [])
        self.assertEqual(sess["eligible_at"], 1000.0)

    def test_the_grace_is_honored(self):
        self.finished("f" * 12, eligible_at=1000.0)
        self.assertEqual(
            broker.reap_finished(1000.0 + broker.REAP_GRACE - 1), [])

    def test_the_entry_is_popped_when_the_grace_has_run(self):
        sid = "g" * 12
        self.finished(sid, eligible_at=1000.0)
        reaped = broker.reap_finished(1000.0 + broker.REAP_GRACE)
        self.assertEqual(reaped, [sid])
        self.assertNotIn(sid, broker.sessions)
        self.assertNotIn(sid, broker._results)

    def test_reaping_touches_only_the_graced(self):
        self.finished("h" * 12, poll=None, complete=False)  # still running
        self.finished("i" * 12, eligible_at=900.0)         # inside the grace
        sid = "j" * 12
        self.finished(sid, eligible_at=0.0)                # past it
        self.assertEqual(broker.reap_finished(1000.0), [sid])
        self.assertEqual(set(broker.sessions), {"h" * 12, "i" * 12})
        self.assertEqual(set(broker._results), {"i" * 12})


if __name__ == "__main__":
    unittest.main()
