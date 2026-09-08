"""The paper's reproducibility claim, exercised against the real core.

The golden in bench/golden/ is one regeneration of the committed start
state under the committed input script, by this driver.  These tests are
the claim:

* regenerating twice, in two fresh processes, gives byte-identical
  machine states - the whole pipeline (emulator, game, filesystem,
  build) is deterministic for fixed inputs;
* regenerating matches the committed golden, on the platform that
  produced it;
* the load lands on the same machine state however long the game had
  been running when it arrived - the start state is a well-defined
  origin, not a moving target.

Each case runs the driver in a subprocess: the core cannot be
re-initialised inside an already-running process, and a fresh process
is the stronger claim anyway.  Where the core, game, or start state is
absent the driver exits 3 and the case is skipped, as on a CI runner
that builds no game.
"""
import json
import os
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GOLDEN = HERE / "golden" / f"repro-{platform.system().lower()}.json"


def regenerate(extra=0, env=None):
    """One regeneration in a fresh process; the signature, or an exit code."""
    proc = subprocess.run(
        [sys.executable, str(HERE / "repro.py"),
         *([f"--extra={extra}"] if extra else [])],
        cwd=str(ROOT), capture_output=True, text=True,
        env={**os.environ, **(env or {})})
    if proc.returncode == 0:
        return json.loads(proc.stdout)
    if proc.returncode == 3:
        return proc.returncode
    raise AssertionError(
        f"regeneration failed (exit {proc.returncode}):\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}")


class ReproTests(unittest.TestCase):
    def _signature(self, value):
        """Skip unless the driver actually ran: exit 3 means the runner has
        no core, game, or start state to regenerate with."""
        if isinstance(value, int):
            self.skipTest(f"the driver exits {value}: the core, game, or "
                          "start state is absent on this runner")
        return value

    def test_double_regeneration(self):
        a = self._signature(regenerate())
        b = self._signature(regenerate())
        self.assertEqual(a, b, "two fresh regenerations differ")

    def test_golden(self):
        if not GOLDEN.exists():
            self.skipTest("no committed golden on this platform")
        signature = self._signature(regenerate())
        self.assertEqual(signature, json.loads(GOLDEN.read_text()),
                         "the regenerated run differs from the committed golden")

    def test_load_is_invariant_to_park_length(self):
        # The live server loads seconds after the title parked; a run that
        # loads later must land on the same machine state.  (Loading
        # mid-boot must never be tried: the core pauses its emulation
        # thread at the load only outside the boot phase, so a mid-boot
        # load lands wherever the boot happens to be.)
        parked = self._signature(regenerate())
        longer = self._signature(regenerate(extra=600))
        self.assertEqual(parked["state_sha256"], longer["state_sha256"])


if __name__ == "__main__":
    main = unittest.main()
