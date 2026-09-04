import importlib.util
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


SERVER_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))
SPEC = importlib.util.spec_from_file_location("qunxia_game_server", SERVER_DIR / "server.py")
game_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(game_server)


class BigMapSignalTests(unittest.TestCase):
    def setUp(self):
        self.original = dict(game_server.world)
        game_server.world.update(
            scenes=1,
            bigmap=False,
            checked_refs=False,
            dark=False,
        )

    def tearDown(self):
        game_server.world.clear()
        game_server.world.update(self.original)

    def test_reference_cannot_latch_before_a_full_black_boundary(self):
        reference = game_server.BIGMAP_REFS[0]
        interior = bytes((value + 32) % 256 for value in reference)

        game_server.note_bigmap(interior)
        self.assertTrue(game_server.world["checked_refs"])
        self.assertFalse(game_server.world["bigmap"])

        game_server.note_bigmap(reference)
        self.assertFalse(game_server.world["bigmap"])

        game_server.world["scenes"] = 2
        game_server.note_bigmap(reference)
        self.assertTrue(game_server.world["bigmap"])

    def test_transition_is_committed_before_bigmap_detection(self):
        reference = game_server.BIGMAP_REFS[0]
        interior = bytes((value + 32) % 256 for value in reference)
        game_server.note_bigmap(interior)
        game_server.world["dark"] = True

        game_server.note_move()
        game_server.note_bigmap(reference)

        self.assertEqual(game_server.world["scenes"], 2)
        self.assertTrue(game_server.world["bigmap"])


class InputContractTests(unittest.IsolatedAsyncioTestCase):
    class Request:
        def __init__(self, body, query=None):
            self.body = body
            self.query = query or {}

        async def json(self):
            return self.body

    async def test_repeat_and_hold_preserve_the_existing_api_limits(self):
        action = AsyncMock(return_value="ok")
        with patch.object(game_server, "run_action", action):
            await game_server.api_key(self.Request({
                "key": "enter", "times": 1000000, "hold": 1000000,
            }))
        steps = action.await_args.args[1]
        self.assertEqual(len(steps), 100 * 2 - 1)
        key_steps = [step for step in steps if len(step) > 2]
        self.assertEqual(len(key_steps), 100)
        self.assertTrue(all(step[1] == 100000 for step in key_steps))

    async def test_sequence_honors_gap_and_stable_parameters(self):
        action = AsyncMock(return_value="ok")
        with patch.object(game_server, "run_action", action):
            await game_server.api_keys(self.Request(
                {"keys": ["kp3", "enter"], "gap": 17},
                {"stable": "23"},
            ))
        steps = action.await_args.args[1]
        self.assertEqual(steps[1], ("frames", 17))
        self.assertEqual(action.await_args.kwargs["stable"], 23)

    async def test_sequence_requires_a_list(self):
        response = await game_server.api_keys(self.Request({"keys": "enter"}))
        self.assertEqual(response.status, 400)

    async def test_settle_budget_can_fit_reaction_and_stability(self):
        fake_lib = SimpleNamespace(
            core_fps=lambda: 60.0,
            fb_luma=lambda: 100,
            core_frame_hash=lambda: 2,
        )
        with (patch.object(game_server, "LIB", fake_lib),
              patch.object(game_server.asyncio, "sleep", AsyncMock())):
            waited, changed = await game_server.settle(
                1, react=30, stable=5, maxframes=1)
        self.assertTrue(changed)
        self.assertEqual(waited, 6)


if __name__ == "__main__":
    unittest.main()
