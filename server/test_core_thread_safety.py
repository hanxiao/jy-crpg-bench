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
                                 "-o", str(host), "-ldl"], check=True)
        cls.lib = ctypes.CDLL(str(host))
        cls.probe = ctypes.CDLL(str(cls.core_path))
        cls.lib.core_init.argtypes = [ctypes.c_char_p] * 3
        cls.lib.core_init.restype = ctypes.c_bool
        cls.lib.core_state_size.restype = ctypes.c_size_t
        cls.lib.core_state_copy.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.core_state_copy.restype = ctypes.c_int
        cls.lib.core_state_peek.argtypes = [ctypes.POINTER(ctypes.c_size_t), ctypes.c_int,
                                          ctypes.POINTER(ctypes.c_int16)]
        cls.lib.core_key.argtypes = [ctypes.c_int, ctypes.c_bool]
        cls.lib.core_ticks.restype = ctypes.c_uint64
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

    def test_state_size_waits_for_frame(self):
        self.assertEqual(self.assert_serialized(self.lib.core_state_size), 16)

    def test_state_copy_waits_for_frame_and_preserves_bytes(self):
        buf = ctypes.create_string_buffer(16)
        self.assertEqual(self.assert_serialized(lambda: self.lib.core_state_copy(buf, 16)), 16)
        self.assertEqual(buf.raw[0], 123)

    def test_state_peek_waits_for_frame(self):
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
        self.assertEqual(self.lib.core_state_size(), 0)
        self.lib.core_run_frame()  # must not call the deinitialized core

    def test_memory_size_waits_for_frame(self):
        self.assertEqual(self.assert_serialized(lambda: self.lib.core_mem_size(0)), 16)

    def test_memory_read_waits_for_frame(self):
        buf = ctypes.create_string_buffer(16)
        self.assertTrue(self.assert_serialized(lambda: self.lib.core_mem_read(0, 0, buf, 16)))
        self.assertEqual(buf.raw[0], 42)

    def test_mouse_move_waits_for_frame(self):
        self.assert_serialized(lambda: self.lib.core_mouse_move(1, 2))

    def test_mouse_button_waits_for_frame(self):
        self.assert_serialized(lambda: self.lib.core_mouse_button(0, True))

    def test_failure_paths_release_execution_lock(self):
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


if __name__ == "__main__":
    unittest.main()
