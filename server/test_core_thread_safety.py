"""Build a tiny fake core so concurrency regressions need no game assets."""
import ctypes
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("cc"), "C compiler required")
class CoreThreadSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="qunxia-thread-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = pathlib.Path(cls.temp.name)
        shared = "-dynamiclib" if sys.platform == "darwin" else "-shared"
        common = ["cc", "-std=c11", "-O2", "-fPIC", shared, "-pthread",
                  "-I" + str(ROOT / "Sources/CoreHost/include")]
        cls.core_path = cls.directory / "probe-core.so"
        host = cls.directory / "host.so"
        subprocess.run(common + [str(ROOT / "server/test_fixtures/thread_probe_core.c"),
                                 "-o", str(cls.core_path)], check=True)
        subprocess.run(common + [str(ROOT / "Sources/CoreHost/CoreHost.c"),
                                 "-o", str(host)] + ([] if sys.platform == "darwin" else ["-ldl"]), check=True)
        cls.lib = ctypes.CDLL(str(host))
        cls.probe = ctypes.CDLL(str(cls.core_path))
        cls.lib.core_init.argtypes = [ctypes.c_char_p] * 3
        cls.lib.core_init.restype = ctypes.c_bool
        cls.has_state_access = hasattr(cls.lib, "core_state_size")
        if cls.has_state_access:
            cls.lib.core_state_size.restype = ctypes.c_size_t
            cls.lib.core_state_copy.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
            cls.lib.core_state_copy.restype = ctypes.c_int
            cls.lib.core_state_peek.argtypes = [ctypes.POINTER(ctypes.c_size_t), ctypes.c_int,
                                              ctypes.POINTER(ctypes.c_int16)]
        cls.lib.core_key.argtypes = [ctypes.c_int, ctypes.c_bool]
        cls.lib.core_key_before_deadline.argtypes = [ctypes.c_int, ctypes.c_bool, ctypes.c_double]
        cls.lib.core_key_before_deadline.restype = ctypes.c_bool
        cls.lib.core_ticks.restype = ctypes.c_uint64
        cls.lib.core_last_error.restype = ctypes.c_char_p
        if cls.has_state_access:
            cls.lib.core_mem_size.argtypes = [ctypes.c_uint]
            cls.lib.core_mem_size.restype = ctypes.c_size_t
            cls.lib.core_mem_read.argtypes = [ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
            cls.lib.core_mem_read.restype = ctypes.c_bool
        for name in ("core_save_state", "core_load_state"):
            getattr(cls.lib, name).argtypes = [ctypes.c_char_p]
            getattr(cls.lib, name).restype = ctypes.c_bool

    def setUp(self):
        self.probe.probe_reset()
        self.assertTrue(self.lib.core_init(str(self.core_path).encode(), b"unused", str(self.directory).encode()))
        self.lib.core_release_all_keys()

    def tearDown(self):
        # One lifecycle per test: the host refuses to initialize over a live
        # core, so the next setUp's core_init is a clean post-shutdown init.
        self.lib.core_shutdown()

    def assert_serialized(self, operation):
        runner = threading.Thread(target=self.lib.core_run_frame, daemon=True)
        runner.start()
        deadline = time.monotonic() + 2
        while not self.probe.probe_running() and time.monotonic() < deadline:
            time.sleep(.001)
        self.assertTrue(self.probe.probe_running())
        started, finished = threading.Event(), threading.Event()
        result = []
        def invoke():
            started.set()
            result.append(operation())
            finished.set()
        reader = threading.Thread(target=invoke, daemon=True)
        reader.start()
        try:
            self.assertTrue(started.wait(1))
            self.assertFalse(finished.wait(.05), "core access overlapped retro_run")
        finally:
            self.probe.probe_release()
            runner.join(2)
            reader.join(2)
        self.assertFalse(runner.is_alive(), "video callback deadlocked on the execution lock")
        self.assertFalse(reader.is_alive(), "core operation failed to release its lock")
        self.assertEqual(self.probe.probe_overlaps(), 0)
        return result[0]

    def test_key_deadline_is_checked_after_native_lock_and_never_blocks_keyup(self):
        from health import clock
        accepted = self.assert_serialized(
            lambda: self.lib.core_key_before_deadline(13, True, clock() + .02))
        self.assertFalse(accepted)
        self.assertEqual(self.probe.probe_keydowns(), 0)
        self.assertTrue(self.lib.core_key_before_deadline(13, True, clock() + 1))
        self.assertEqual(self.probe.probe_keydowns(), 1)
        self.assertTrue(self.lib.core_key_before_deadline(13, False, clock() - 1))
        self.assertTrue(self.lib.core_key_before_deadline(13, True, clock() + 1))
        self.assertEqual(self.probe.probe_keydowns(), 2)

    def test_init_over_a_live_core_is_refused(self):
        # The libretro contract is one initialization per process; a second
        # retro_init over a live core is what took DOSBox Pure down (it
        # accepted the init, logged "core loaded" and died on the next frame).
        # The host must refuse the second call cleanly, leaving the live core
        # untouched.
        self.assertFalse(
            self.lib.core_init(str(self.core_path).encode(), b"unused", str(self.directory).encode()))
        self.assertIn(b"already initialized", self.lib.core_last_error())
        self.assert_serialized(lambda: self.lib.core_key(13, True))
        self.assertEqual(self.probe.probe_keydowns(), 1)

    def test_state_size_waits_for_frame(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        self.assertEqual(self.assert_serialized(self.lib.core_state_size), 16)

    def test_state_copy_waits_for_frame_and_preserves_bytes(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        buf = ctypes.create_string_buffer(16)
        self.assertEqual(self.assert_serialized(lambda: self.lib.core_state_copy(buf, 16)), 16)
        self.assertEqual(buf.raw[0], 123)

    def test_state_peek_waits_for_frame(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        offsets = (ctypes.c_size_t * 1)(0)
        values = (ctypes.c_int16 * 1)()
        self.assertEqual(self.assert_serialized(lambda: self.lib.core_state_peek(offsets, 1, values)), 0)
        self.assertEqual(values[0], 123)

    def test_save_waits_for_frame(self):
        path = self.directory / "save.state"
        self.assertTrue(self.assert_serialized(lambda: self.lib.core_save_state(str(path).encode())))
        self.assertEqual(path.read_bytes()[0], 123)

    def test_load_waits_for_frame(self):
        path = self.directory / "load.state"
        path.write_bytes(bytes(16))
        self.assertTrue(self.assert_serialized(lambda: self.lib.core_load_state(str(path).encode())))

    def test_keyboard_callback_waits_for_frame(self):
        self.assert_serialized(lambda: self.lib.core_key(13, True))

    def test_release_keys_waits_for_frame(self):
        self.lib.core_key(13, True)
        self.assert_serialized(self.lib.core_release_all_keys)

    def test_reset_waits_for_frame_without_recursive_locking(self):
        self.lib.core_key(13, True)
        self.assert_serialized(self.lib.core_reset)

    def test_shutdown_waits_for_frame_and_clears_callbacks(self):
        self.assert_serialized(self.lib.core_shutdown)
        if self.has_state_access:
            self.assertEqual(self.lib.core_state_size(), 0)
        self.lib.core_run_frame()  # must not call the deinitialized core

    def test_load_after_shutdown_returns_failure(self):
        path = self.directory / "shutdown-load.state"
        path.write_bytes(bytes(16))
        self.lib.core_shutdown()
        self.assertFalse(self.lib.core_load_state(str(path).encode()))

    def test_shutdown_unloads_game_before_deinit_and_only_once(self):
        self.lib.core_shutdown()
        self.assertEqual(self.probe.probe_unloads(), 1)
        self.assertEqual(self.probe.probe_premature_deinit(), 0)
        self.lib.core_shutdown()
        self.assertEqual(self.probe.probe_unloads(), 1)

    def test_memory_size_waits_for_frame(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        self.assertEqual(self.assert_serialized(lambda: self.lib.core_mem_size(0)), 16)

    def test_memory_read_waits_for_frame(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        buf = ctypes.create_string_buffer(16)
        self.assertTrue(self.assert_serialized(lambda: self.lib.core_mem_read(0, 0, buf, 16)))
        self.assertEqual(buf.raw[0], 42)

    def test_mouse_move_waits_for_frame(self):
        self.assert_serialized(lambda: self.lib.core_mouse_move(1, 2))

    def test_mouse_button_waits_for_frame(self):
        self.assert_serialized(lambda: self.lib.core_mouse_button(0, True))

    def test_failure_paths_release_execution_lock(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        buf = ctypes.create_string_buffer(16)
        self.assertEqual(self.lib.core_state_copy(buf, 0), -1)
        self.probe.probe_fail_serialize(1)
        self.assertEqual(self.lib.core_state_copy(buf, 16), -1)
        self.assertFalse(self.lib.core_save_state(str(self.directory / "failed.state").encode()))
        self.probe.probe_fail_serialize(0)
        offsets = (ctypes.c_size_t * 1)(16)
        values = (ctypes.c_int16 * 1)()
        self.assertEqual(self.lib.core_state_peek(offsets, 1, values), -1)
        path = self.directory / "invalid.state"
        path.write_bytes(b"invalid")
        self.assertFalse(self.lib.core_load_state(str(path).encode()))
        before = self.lib.core_ticks()
        self.probe.probe_release()
        runner = threading.Thread(target=self.lib.core_run_frame, daemon=True)
        runner.start()
        runner.join(2)
        self.assertFalse(runner.is_alive())
        self.assertGreater(self.lib.core_ticks(), before)

    def test_zero_state_size_keeps_existing_save_diagnostic(self):
        self.probe.probe_state_size(0)
        self.assertFalse(self.lib.core_save_state(str(self.directory / "zero.state").encode()))
        self.assertEqual(self.lib.core_last_error(), b"core reports zero savestate size")
        self.probe.probe_state_size(16)
        if self.has_state_access:
            self.assertEqual(self.lib.core_state_size(), 16)


    def test_shutdown_does_not_report_frames_that_never_ran(self):
        self.lib.core_shutdown()
        before = self.lib.core_ticks()
        self.lib.core_run_frame()
        self.assertEqual(self.lib.core_ticks(), before)

    def test_failed_save_releases_gate_for_the_next_frame(self):
        self.probe.probe_fail_serialize(1)
        self.assertFalse(self.lib.core_save_state(str(self.directory / "failed.state").encode()))
        self.probe.probe_fail_serialize(0)
        self.probe.probe_release()
        before = self.lib.core_ticks()
        runner = threading.Thread(target=self.lib.core_run_frame, daemon=True)
        runner.start()
        runner.join(2)
        self.assertFalse(runner.is_alive())
        self.assertGreater(self.lib.core_ticks(), before)

    def test_state_peek_rejects_overflow_and_null_arguments(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        offsets = (ctypes.c_size_t * 1)(ctypes.c_size_t(-1).value)
        values = (ctypes.c_int16 * 1)()
        self.assertEqual(self.lib.core_state_peek(offsets, 1, values), -1)
        self.assertEqual(self.lib.core_state_peek(None, 1, values), -1)
        self.assertEqual(self.lib.core_state_peek(offsets, -1, values), -1)

    def test_memory_read_rejects_wrapped_range(self):
        if not self.has_state_access:
            self.skipTest("benchmark-only private state access")
        data = ctypes.create_string_buffer(16)
        self.assertFalse(self.lib.core_mem_read(0, ctypes.c_size_t(-1).value, data, 2))
        self.assertFalse(self.lib.core_mem_read(0, 0, None, 1))


if __name__ == "__main__":
    unittest.main()
