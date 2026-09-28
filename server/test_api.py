import asyncio
import base64
import json
import os
import pathlib
import re
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock


with mock.patch("ctypes.CDLL", return_value=mock.MagicMock()):
    import server


class FakeRequest:
    def __init__(self, body=None, query=None):
        self._body = {} if body is None else body
        self.query = {} if query is None else query
        self.headers = {}
        self.remote = "127.0.0.1"

    async def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def response_json(response):
    return json.loads(response.body)


class InputValidationTest(unittest.IsolatedAsyncioTestCase):
    async def test_key_rejects_a_hold_the_game_can_miss(self):
        """Below MIN_HOLD_FRAMES a keydown and keyup can be consumed inside
        one game-loop iteration and the press never reaches the game. Measured
        over 24 taps a point: 1 frame lands 0-29% of the time, 4 frames
        96-100%, 5 and up 100%. Silently unreliable input is worse for an
        agent than a refusal it can read."""
        for hold in range(1, server.MIN_HOLD_FRAMES):
            response = await server.api_key(
                FakeRequest({"key": "right", "hold": hold}))
            self.assertEqual(response.status, 400, f"hold={hold}")
            self.assertIn(str(server.MIN_HOLD_FRAMES),
                          response_json(response)["error"])

    async def test_a_list_of_keys_rejects_a_hold_the_game_can_miss(self):
        response = await server.api_key(
            FakeRequest({"key": ["right"], "hold": 1}))
        self.assertEqual(response.status, 400)
        self.assertIn(str(server.MIN_HOLD_FRAMES),
                      response_json(response)["error"])

    async def test_key_rejects_fractional_hold(self):
        response = await server.api_key(FakeRequest({"key": "right", "hold": 1.5}))
        self.assertEqual(response.status, 400)
        self.assertIn("integer", response_json(response)["error"])

    async def test_a_list_of_keys_is_pressed_in_order_with_the_fixed_gap(self):
        captured = {}

        async def fake_run(_request, steps, note, verb="KEY"):
            captured.update(steps=steps, note=note, verb=verb)
            return object()

        with mock.patch.object(server, "run_action", fake_run):
            marker = await server.api_key(
                FakeRequest({"key": ["up", "enter"], "hold": 10})
            )

        self.assertIsNotNone(marker)
        self.assertEqual(
            captured["steps"],
            [(server.KEYS["up"], 10, "up"), ("frames", server.BETWEEN_TAPS_FRAMES),
             (server.KEYS["enter"], 10, "enter")],
        )
        self.assertEqual((captured["note"], captured["verb"]), ("up enter", "KEYS"))

    async def test_oversized_action_is_rejected(self):
        response = await server.api_key(
            FakeRequest({"key": ["right"] * 100, "hold": 100})
        )
        self.assertEqual(response.status, 400)
        self.assertIn("too long", response_json(response)["error"])

    async def test_a_list_must_hold_key_names(self):
        for body in ({"key": []}, {"key": ["right"] * 101}, {"key": ["right", 5]},
                     {"key": ["right", "no-such-key"]}, {"key": 7}):
            response = await server.api_key(FakeRequest(body))
            self.assertEqual(response.status, 400, body)

    async def test_non_object_json_is_rejected(self):
        response = await server.api_key(FakeRequest([1000]))
        self.assertEqual(response.status, 400)


def _native_key_table():
    """RetroKey.table from Sources/QunXia/Keys.swift, rebuilt from the Swift
    source.

    The table is a literal dict, four loops, and a set of overrides; this
    mirrors that construction in file order, so the test fails if the native
    vocabulary grows or drifts, rather than the next agent finding out by
    typing a name the headless API rejects.
    """
    swift = (pathlib.Path(__file__).resolve().parent.parent
             / "Sources" / "QunXia" / "Keys.swift").read_text()
    block = swift[swift.index("static let table"): swift.index("static func parse")]
    table = dict(re.findall(r'"([A-Za-z0-9_]+)":\s*(\d+)', block))
    for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):   # letter loop
        table[c] = str(97 + i)
    for d in range(10):                                  # digit loop
        table[str(d)] = str(48 + d)
    for f in range(1, 13):                               # f-key loop
        table[f"f{f}"] = str(281 + f)
    for k in range(10):                                  # numpad loop
        table[f"kp{k}"] = str(256 + k)
    # Overrides, including the punctuation keys, whose name is the glyph.
    # The loops above are written the same way, so skip interpolated names.
    for name, code in re.findall(r'\["((?:[^"\\]|\\.)+)"\]\s*=\s*(\d+)', block):
        if "\\(" in name:
            continue
        table[name.replace("\\\\", "\\")] = code
    return {name: int(code) for name, code in table.items()}


class UnknownFieldTest(unittest.IsolatedAsyncioTestCase):
    """A body field a call does not read is a bad request, not a no-op.

    Accepting it silently answers 200 while the game does something other than
    what was asked, and the caller has no way to find that out.
    """

    async def test_each_call_names_the_field_it_cannot_use(self):
        for handler, body, unknown in (
                (server.api_key, {"key": "right", "frames": 70}, "frames"),
                (server.api_key, {"key": ["right"], "times": 3}, "times"),
                (server.api_key, {"key": ["right", "enter"], "gap": 0}, "gap"),
                (server.api_key, {"keys": ["right"]}, "keys"),
                (server.api_save, {"name": "x", "slot": 1}, "slot"),
                (server.api_load, {"name": "x", "slot": 1}, "slot"),
        ):
            response = await handler(FakeRequest(body))
            self.assertEqual(response.status, 400, unknown)
            self.assertIn(unknown, response_json(response)["error"])

    async def test_the_fields_a_call_does_read_are_accepted(self):
        seen = {}

        async def fake_run(_request, steps, note, verb="KEY"):
            seen.update(steps=steps)
            return object()

        with mock.patch.object(server, "run_action", fake_run):
            await server.api_key(
                FakeRequest({"key": ["right", "right"], "hold": 12}))
        self.assertEqual(len(seen["steps"]), 3)   # tap, gap, tap


class ScreenFormatTest(unittest.IsolatedAsyncioTestCase):
    """An encoding this server cannot produce is a 400, not a JSON reply.

    The briefing names `png` because it is the one both runners write; webp
    and jpeg are here for the browser client and the catalogue thumbnails.
    """

    async def test_an_unsupported_format_is_refused(self):
        response = await server.api_screen(
            FakeRequest(query={"format": "avif"}))
        self.assertEqual(response.status, 400)
        self.assertIn("png", response_json(response)["error"])

    def test_the_briefing_only_promises_what_both_runners_write(self):
        native = (pathlib.Path(server.__file__).resolve().parent.parent
                  / "Sources" / "QunXia" / "ControlAPI.swift").read_text()
        # The native runner writes PNG only: ImageIO cannot encode WebP.
        self.assertIn('format == "png"', native)
        for brief in ("play.en", "play.zh"):
            text = (pathlib.Path(server.__file__).resolve().parent.parent
                    / "skills" / f"{brief}.md").read_text(encoding="utf-8")
            self.assertIn("?format=png", text)
            self.assertNotIn("?format=webp", text)


class StateNameTest(unittest.TestCase):
    """A saved state has one name. "slot" was that same name spelled twice."""

    def test_a_state_is_named(self):
        path, name = server.state_path({"name": "before-boss"})
        self.assertEqual(name, "before-boss")
        self.assertTrue(str(path).endswith("before-boss.state"))

    def test_a_nameless_save_lands_on_the_quick_slot(self):
        _, name = server.state_path({})
        self.assertEqual(name, server.QUICK_STATE)

    def test_a_state_name_cannot_escape_its_directory(self):
        for raw in ("../../etc/passwd", "a/b", "..", ""):
            try:
                _, name = server.state_path({"name": raw})
            except ValueError:
                continue
            self.assertNotIn("/", name)
            self.assertNotIn("..", name)


class SettleOptionsTest(unittest.TestCase):
    """One way to size the settle: the three phases, bounded, on both runners.

    ``Sources/QunXia/ControlAPI.swift`` takes the same three and nothing else.
    """

    def test_the_reaction_window_fits_inside_the_wait(self):
        options = server.settle_options(
            FakeRequest(query={"react": "300", "maxsettle": "10"}))
        self.assertEqual(options["maxframes"], 300)

    def test_settle_phases_are_bounded(self):
        for query in ({"react": "9999"}, {"maxsettle": "9999"},
                      {"stable": "9999"}, {"stable": "0"}):
            with self.assertRaises(ValueError):
                server.settle_options(FakeRequest(query=query))

    def test_a_scored_session_keeps_the_settle_rule(self):
        was = server.warden.ON
        server.warden.ON = True
        try:
            with self.assertRaises(ValueError):
                server.settle_options(FakeRequest(query={"react": "0"}))
            self.assertEqual(server.settle_options(FakeRequest())["react"],
                             server.DEFAULT_REACT_FRAMES)
        finally:
            server.warden.ON = was

    def test_settle_phases_have_defaults(self):
        options = server.settle_options(FakeRequest())
        self.assertEqual(options, {"react": 30,
                                   "stable": server.DEFAULT_STABLE_FRAMES,
                                   "maxframes": server.DEFAULT_SETTLE_MAX_FRAMES})


class KeyVocabularyTest(unittest.TestCase):
    """The two tables are one vocabulary: same names, same codes, both ways.

    They used to diverge on kp1/kp3/kp7/kp9, which the native table remapped
    to the arrow codes. The game accepts either, so nothing was visibly wrong,
    but the same key name reached the emulated keyboard as a different
    scancode depending on which runner an agent had - and as a third one when
    the same key was pressed on the window's own numpad.
    """

    def test_the_two_tables_are_the_same_vocabulary(self):
        native = _native_key_table()
        # The guard, not the assertion: if the Swift source ever stops
        # parsing, the assertion below passes vacuously.
        self.assertGreaterEqual(len(native), 100)
        missing = {name: code for name, code in native.items()
                   if name not in server.KEYS}
        self.assertEqual(missing, {},
                         "names the native Control API accepts and the "
                         "headless API would reject")
        extra = {name for name in server.KEYS if name not in native}
        self.assertEqual(extra, set(),
                         "names the headless API accepts and the native "
                         "Control API would reject")
        for name, code in native.items():
            self.assertEqual(server.KEYS[name], code,
                             f"{name} resolves to a different code")


class HistoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_history_limit_returns_only_newest_entries(self):
        old = server.history
        server.history = server.collections.deque(
            ({"id": i} for i in range(8)), maxlen=server.MAX_HISTORY_LIMIT
        )
        try:
            response = await server.api_history(FakeRequest(query={"limit": "3"}))
        finally:
            server.history = old
        self.assertEqual([item["id"] for item in response_json(response)["history"]], [5, 6, 7])

    async def test_history_rejects_invalid_limit(self):
        response = await server.api_history(FakeRequest(query={"limit": "all"}))
        self.assertEqual(response.status, 400)


class StatePathTest(unittest.TestCase):
    def test_state_name_cannot_escape_state_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(server, "STATE_DIR", tmp):
                path, name = server.state_path({"name": "../../checkpoint"})
            self.assertEqual(path.parent, pathlib.Path(tmp))
            self.assertEqual(path.name, f"{name}.state")
            self.assertNotIn("..", path.name)


class AtomicObservationTest(unittest.IsolatedAsyncioTestCase):
    async def test_action_lock_is_created_on_the_serving_event_loop(self):
        app = {}
        old_lock = server.api_lock
        await server.startup(app)
        waiter = None
        try:
            lock = server.action_lock()
            await lock.acquire()
            waiter = asyncio.create_task(server.acquire_action_lock())
            await asyncio.sleep(0)
            self.assertFalse(waiter.done())
            lock.release()
            self.assertTrue(await waiter)
            lock.release()
        finally:
            if waiter and not waiter.done():
                waiter.cancel()
            for task in app.values():
                task.cancel()
            await asyncio.gather(*app.values(), return_exceptions=True)
            server.api_lock = old_lock

    async def test_requested_image_is_captured_before_action_lock_releases(self):
        fake_lib = mock.MagicMock()
        fake_lib.core_frame_hash.return_value = 1
        fake_lib.core_width.return_value = 320
        fake_lib.core_height.return_value = 200
        fake_lib.core_frame_serial.return_value = 42
        fake_lib.core_ticks.return_value = 42
        fake_lib.core_fps.return_value = 70.0

        async def fake_tap(*_args):
            return None

        async def fake_settle(*_args, **_kwargs):
            return 9, True

        def fake_snapshot(_format):
            self.assertTrue(server.api_lock.locked())
            return b"png", 320, 200, "image/png"

        old_lock = server.api_lock
        test_lock = asyncio.Lock()
        server.api_lock = test_lock
        try:
            with mock.patch.object(server, "LIB", fake_lib), \
                 mock.patch.object(server, "tap", fake_tap), \
                 mock.patch.object(server, "settle", fake_settle), \
                 mock.patch.object(server, "snapshot", fake_snapshot), \
                 mock.patch.object(server, "note_move", lambda: None), \
                 mock.patch.object(server, "note_screen", lambda: None), \
                 mock.patch.object(server, "read_stats", lambda: None), \
                 mock.patch.object(server, "log_action", lambda *_a, **_k: None):
                response = await server.run_action(
                    FakeRequest(query={"image": "1"}),
                    [(server.KEYS["right"], 10, "right")],
                    "right",
                )
        finally:
            server.api_lock = old_lock

        result = response_json(response)
        self.assertFalse(test_lock.locked())
        self.assertEqual(base64.b64decode(result["image"].split(",", 1)[1]), b"png")


class ScreenWardenTest(unittest.IsolatedAsyncioTestCase):
    """The end of a benchmark run must be visible on /api/screen.

    The agent's brief is "wait for a tool to report BENCHMARK ENDED", and look
    is the tool it calls most often. If only key-sending tools answered with
    410, an agent that finishes by watching would stare at a finished run
    until its own deadline.
    """

    def setUp(self):
        import warden
        self._warden = warden
        self.old_on = warden.ON
        self.addCleanup(setattr, warden, "ON", self.old_on)
        warden.ON = True

    async def test_ended_run_answers_looks_with_410(self):
        payload = {"ended": True, "reason": "time", "actions": 3}
        with mock.patch.object(self._warden, "ended_payload", return_value=payload):
            response = await server.api_screen(FakeRequest())
        self.assertEqual(response.status, 410)
        self.assertEqual(response_json(response), payload)

    async def test_spectating_looks_are_not_wardened(self):
        payload = {"ended": True, "reason": "time"}
        with mock.patch.object(self._warden, "ended_payload", return_value=payload), \
                mock.patch.object(server, "snapshot",
                                  lambda _fmt: (b"x", 2, 2, "image/png")):
            response = await server.api_screen(
                FakeRequest(query={"format": "png", "spectate": "1"}))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, b"x")

    async def test_live_run_still_serves_frames_and_counts_the_read(self):
        reads = []
        with mock.patch.object(self._warden, "ended_payload", return_value=None), \
                mock.patch.object(self._warden, "note_read",
                                  lambda: reads.append(1)), \
                mock.patch.object(server, "snapshot",
                                  lambda _fmt: (b"x", 2, 2, "image/png")), \
                mock.patch.object(server, "log_action", lambda *_a, **_k: None):
            response = await server.api_screen(
                FakeRequest(query={"format": "png"}))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, b"x")
        self.assertEqual(reads, [1])


class BaseUrlTest(unittest.TestCase):
    """The help page must name an address the reader can actually reach:
    the origin the proxy reports, and - in a benchmark session - the
    session's own address under it, never the loopback address the
    session server sits on."""

    @staticmethod
    def request(host="127.0.0.1:8765", scheme="http", headers=None):
        return SimpleNamespace(host=host, scheme=scheme,
                               url=SimpleNamespace(scheme=scheme),
                               headers=headers or {})

    def test_a_direct_caller_uses_its_own_host(self):
        self.assertEqual(server.base_url(self.request()),
                         "http://127.0.0.1:8765")

    def test_the_proxy_reports_the_public_origin(self):
        request = self.request(headers={
            "X-Forwarded-Host": "bench.example.com",
            "X-Forwarded-Proto": "https"})
        self.assertEqual(server.base_url(request),
                         "https://bench.example.com")

    def test_a_benchmark_session_is_named_under_its_own_address(self):
        request = self.request(headers={
            "X-Forwarded-Host": "bench.example.com",
            "X-Forwarded-Proto": "https"})
        with mock.patch.dict(os.environ, {"QUNXIA_BENCH": "1",
                                         "QUNXIA_BENCH_SID": "abc123"}):
            self.assertEqual(server.base_url(request),
                             "https://bench.example.com/s/abc123")

    def test_a_malformed_forwarded_host_is_ignored(self):
        for evil in ("", "\t", "\\nEvil", "http://evil", "..?.."):
            request = self.request(headers={"X-Forwarded-Host": evil})
            self.assertEqual(server.base_url(request),
                             "http://127.0.0.1:8765")


if __name__ == "__main__":
    unittest.main()
