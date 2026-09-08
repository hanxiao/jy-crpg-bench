import asyncio
import unittest
from unittest import mock


# server.py binds the native core at import time. These tests exercise only the
# input scheduler, so use a placeholder library and replace it per test.
with mock.patch("ctypes.CDLL", return_value=mock.MagicMock()):
    import server


class FakeLib:
    def __init__(self):
        self.tick = 0
        self.events = []

    def core_fps(self):
        return 60.0

    def core_ticks(self):
        return self.tick

    def core_key(self, code, down):
        self.events.append((self.tick, code, down))


class BrowserInputTimingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.lib = FakeLib()
        self.waits = []
        self.key_events = []

        async def wait_frames(frames):
            self.waits.append(frames)
            self.lib.tick += frames

        self.patches = [
            mock.patch.object(server, "LIB", self.lib),
            mock.patch.object(server, "wait_core_frames", wait_frames),
            mock.patch.object(
                server, "key_event",
                lambda name, down: self.key_events.append((name, down)),
            ),
        ]
        for patch in self.patches:
            patch.start()

    async def asyncTearDown(self):
        for patch in reversed(self.patches):
            patch.stop()

    async def test_short_tap_is_held_for_minimum_core_frames(self):
        holding = {}
        self.assertTrue(await server.press_web_key("right", 275, holding))
        self.lib.tick = 1

        self.assertTrue(await server.release_web_key("right", 275, holding))

        self.assertEqual(self.lib.events, [(0, 275, True), (10, 275, False)])
        self.assertEqual(self.waits, [9, server.KEY_RELEASE_FRAMES])
        self.assertEqual(self.key_events, [("right", True), ("right", False)])
        self.assertEqual(holding, {})

    async def test_long_human_hold_releases_without_added_hold_delay(self):
        holding = {}
        await server.press_web_key("up", 273, holding)
        self.lib.tick = server.DEFAULT_TAP_FRAMES + 5

        await server.release_web_key("up", 273, holding)

        self.assertEqual(
            self.lib.events,
            [(0, 273, True), (server.DEFAULT_TAP_FRAMES + 5, 273, False)],
        )
        self.assertEqual(self.waits, [server.KEY_RELEASE_FRAMES])

    async def test_duplicate_keydown_does_not_restart_the_hold_window(self):
        holding = {}
        self.assertTrue(await server.press_web_key("left", 276, holding))
        self.lib.tick = 4
        self.assertFalse(await server.press_web_key("left", 276, holding))

        await server.release_web_key("left", 276, holding)

        self.assertEqual(self.lib.events, [(0, 276, True), (10, 276, False)])
        self.assertEqual(self.key_events, [("left", True), ("left", False)])

    async def test_release_of_a_never_pressed_key_is_a_noop(self):
        holding = {}

        self.assertFalse(await server.release_web_key("esc", 27, holding))

        self.assertEqual(self.lib.events, [])
        self.assertEqual(self.key_events, [])
        self.assertEqual(self.waits, [])
        self.assertEqual(holding, {})

    async def test_cancelled_wait_still_releases_the_key(self):
        holding = {}
        await server.press_web_key("down", 274, holding)

        async def cancel_wait(_frames):
            raise asyncio.CancelledError

        with mock.patch.object(server, "wait_core_frames", cancel_wait):
            with self.assertRaises(asyncio.CancelledError):
                await server.release_web_key("down", 274, holding)

        self.assertEqual(self.lib.events, [(0, 274, True), (0, 274, False)])
        self.assertEqual(holding, {})


if __name__ == "__main__":
    unittest.main()
