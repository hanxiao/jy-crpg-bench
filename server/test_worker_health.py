"""Real worker processes and real native calls; no model/provider requests."""
import asyncio
import contextlib
import ctypes
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

import aiohttp
from health import read_json

def stop_process(p, timeout=.5):
    if p.poll() is None:
        p.terminate()
        try: p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(timeout=timeout)

ROOT = Path(__file__).resolve().parent


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def request(port, path, body=None, timeout=5):
    req=Request(f'http://127.0.0.1:{port}{path}', data=json.dumps(body).encode() if body is not None else None,
                headers={'Content-Type':'application/json'})
    try:
        response=urlopen(req,timeout=timeout)
    except HTTPError as e:
        response=e
    with response:
        return response.status,response.read()


def wait_for(fn, seconds=5):
    deadline=time.monotonic()+seconds
    last=None
    while time.monotonic()<deadline:
        try:
            last=fn()
            if last: return last
        except (OSError, ValueError):
            pass
        time.sleep(.03)
    raise AssertionError(f'timed out, last={last!r}')


@unittest.skipUnless(shutil.which('cc'), 'C compiler required')
class WorkerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=tempfile.TemporaryDirectory(prefix='qunxia-worker-tests-')
        cls.addClassCleanup(cls.build.cleanup)
        cls.core=Path(cls.build.name)/'probe.so'
        shared='-dynamiclib' if sys.platform=='darwin' else '-shared'
        subprocess.run(['cc','-std=c11','-O2','-fPIC',shared,'-pthread',
                        '-I'+str(ROOT.parent/'Sources/CoreHost/include'),
                        str(ROOT/'test_fixtures/thread_probe_core.c'),'-o',str(cls.core)],check=True)
        # The production bridge/tiles implementation is exercised in a private
        # copy so tests never overwrite a library used by another server.
        cls.server=Path(cls.build.name)/'server'
        shutil.copytree(ROOT,cls.server,ignore=shutil.ignore_patterns('__pycache__','libqunxia.so*'))
        sources=Path(cls.build.name)/'Sources'
        shutil.copytree(ROOT.parent/'Sources/CoreHost',sources/'CoreHost')
        subprocess.run(['sh',str(cls.server/'build.sh')],stdout=subprocess.DEVNULL,check=True)
        # Bench warden imports its renderer from the sibling bench directory.
        if (ROOT.parent/'bench').exists():
            shutil.copytree(ROOT.parent/'bench',Path(cls.build.name)/'bench')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='qunxia-test-session-')
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.port=free_port()
        self.procs=[]
        self.addCleanup(lambda:[stop_process(p,timeout=.5) for p in self.procs])

    def launch(self, **extra):
        start=self.folder/'start.state'
        start.write_bytes(b'{' + bytes(15))
        env=dict(os.environ,PORT=str(self.port),QUNXIA_CORE=str(self.core),QUNXIA_GAME='unused',
                 QUNXIA_SAVES=str(self.folder/'saves'),QUNXIA_STATE_DIR=str(self.folder/'slots'),
                 QUNXIA_START_STATE=str(start),QUNXIA_RESET_TOKEN='test',
                 QUNXIA_RECORDING_DIR=str(self.folder/'recordings'),QUNXIA_RUN_ID='test-run',
                 QUNXIA_RUNTIME_CHILD='1',QUNXIA_STALL_SECONDS='1.5',QUNXIA_STARTUP_SECONDS='4',
                 QUNXIA_BOOT_WAIT='0.1',QUNXIA_CHECKPOINT_SECONDS='0.3',QUNXIA_BENCH='0',
                 QUNXIA_FINALIZATION_SECONDS='20',QUNXIA_RECOVERY_LIMIT='1',PROBE_AUTORUN='1')
        env.pop('QUNXIA_SESSION_DIR',None)
        env.pop('QUNXIA_RUNTIME_DIR',None)
        env.pop('QUNXIA_PARENT_PID',None)
        env.update(extra)
        with (self.folder/'worker.log').open('ab') as log:
            p=subprocess.Popen([sys.executable,str(self.server/'server.py')],env=env,cwd=self.server,
                               stdout=log,stderr=log,start_new_session=True)
        p.qunxia_group=True
        self.procs.append(p)
        return p

    def healthy(self):
        status,body=request(self.port,'/status')
        value=json.loads(body)
        return value if status==200 and value.get('healthy') else None


    def test_static_pixels_still_report_execution_progress(self):
        self.launch()
        before=wait_for(self.healthy)
        time.sleep(.15)
        after=self.healthy()
        self.assertGreater(after['core_ticks'],before['core_ticks'])

    def test_a_wrong_token_is_not_a_server_error(self):
        self.launch()
        wait_for(self.healthy)
        # Non-ASCII included: the comparison must answer 404, not 500.
        status, body = request(self.port, '/api/reset?token=%C3%A9', {}, timeout=10)
        self.assertEqual(status, 404, body)
        status, body = request(self.port, '/api/reset?token=not-the-token', {}, timeout=10)
        self.assertEqual(status, 404, body)
        status, body = request(self.port, '/api/snapshot?token=not-the-token', {}, timeout=10)
        self.assertEqual(status, 404, body)

    def test_slow_advancing_native_core_completes_one_key_without_retry(self):
        self.launch(PROBE_FRAME_DELAY_MS='180', QUNXIA_STALL_SECONDS='15')
        wait_for(self.healthy)
        status, body = request(self.port, '/api/key?react=0&stable=1&maxsettle=6',
                               {'key': 'right', 'hold': 10}, timeout=20)
        self.assertEqual(status, 200, body)
        events = json.loads(request(self.port, '/api/recording')[1])['events']
        keys = [e['down'] for e in events if e.get('key') == 'right']
        self.assertEqual(keys, [True, False])
        self.assertTrue(self.healthy())

    def test_benchmark_time_limit_releases_partial_key_and_validates_result(self):
        result_dir = self.folder / 'results'
        self.launch(PROBE_FRAME_DELAY_MS='180', QUNXIA_STALL_SECONDS='15',
                    QUNXIA_BENCH='1', QUNXIA_BENCH_BUDGET='10',
                    QUNXIA_BENCH_SID='deadline', QUNXIA_RESULT_DIR=str(result_dir),
                    QUNXIA_RECORDING_FILE=str(self.folder / 'deadline.jsonl'),
                    QUNXIA_VIDEO_DIR=str(self.folder / 'videos'), QUNXIA_PUBLISH='0')
        wait_for(self.healthy)
        status, body = request(self.port, '/api/reset?token=test', {}, timeout=10)
        self.assertEqual(status, 200, body)
        # The clock starts when the worker becomes playable, which this test
        # only sees from outside: on a fast runner the budget is nearly whole
        # here, on a loaded one it may be nearly spent, and betting on where
        # the deadline lands is how this test flaked in CI. So drain it down
        # instead, to a ~3 s margin. That margin has to sit in a window:
        # far enough ahead of the key request that the down is recorded
        # before the deadline (request-to-down is HTTP dispatch, fsynced
        # journal writes and the execution-gate wait; a loaded CI runner
        # consumed a whole 1 s of the original margin, and the down was
        # never recorded), and far enough behind it that the hold cannot
        # finish first (100 frames at the probe's 180 ms frame delay is
        # ~18 s of real time, while the warden's absolute deadline still
        # beats the input budget's ~19 s wall). The 10 s budget and the
        # wide client timeouts (15 s / 20 s) are for a third flake mode
        # found on CI: a loaded runner can stall the server's event loop
        # for several seconds (the journal fsyncs run on it, and so can a
        # noisy neighbor), freezing the warden and every handler with it;
        # the wide timeouts let a stalled response land late instead of
        # failing the test, while a poll that drops must not abort the
        # drain, and the 15 s stall watchdog still kills a truly wedged
        # server. The 0.6 s floor is unchanged: a runner that spends the
        # budget before the first read still sends the key at whatever
        # remains, as before.
        def remaining():
            try:
                status, body = request(self.port, '/status', None, timeout=15)
            except OSError:
                return None
            if status != 200:
                return None
            return json.loads(body).get('session', {}).get('remaining')
        margin = 3.0
        wait_for(lambda: (remaining() or 0) > 0.6, seconds=8)
        land = time.monotonic() + 15
        r = None
        while time.monotonic() < land:
            v = remaining()
            if v is not None:
                r = v
                if v <= margin + 0.15:
                    break
            time.sleep(0.05)
        self.assertIsNotNone(r, "drain never read a remaining")
        self.assertLessEqual(r, margin + 0.15, f"drain did not land: {r}")
        self.assertGreater(r, 0.6, f"deadline consumed: {r}")
        time.sleep(max(0.0, r - margin))
        status, body = request(self.port, '/api/key', {'key': 'right', 'hold': 100}, timeout=20)
        self.assertEqual(status, 410, body)
        result = wait_for(lambda: read_json(result_dir / 'deadline.json'))
        self.assertTrue(result['valid'])
        self.assertEqual(result['reason'], 'time')
        journal = self.folder / 'deadline.jsonl'
        records = [json.loads(line) for line in journal.read_text().splitlines()]
        downs = [e['down'] for e in records if e.get('key') == 'right']
        self.assertEqual(downs, [True, False])

    def test_native_key_deadlock_becomes_environment_failure(self):
        p=self.launch(PROBE_HANG_ON_KEY='1')
        wait_for(self.healthy)
        with contextlib.suppress(OSError):
            request(self.port,'/api/key',{'key':'enter'},timeout=4)
        p.wait(timeout=5)
        fault=read_json(self.folder/'saves/.health/failure.json')
        self.assertEqual(p.returncode,75)
        self.assertFalse(fault['valid'])
        self.assertIn(fault['reason'],('core_stalled','event_loop_stalled'))

    def test_native_run_deadlock_without_http_requests_is_detected(self):
        p=self.launch(PROBE_HANG_AFTER_FRAMES='20')
        wait_for(self.healthy)
        p.wait(timeout=5)
        fault=read_json(self.folder/'saves/.health/failure.json')
        self.assertEqual(p.returncode,75)
        self.assertIn(fault['reason'],('core_stalled','pause_stalled'))


    def test_websocket_disconnect_releases_input_lease(self):
        self.launch()
        wait_for(self.healthy)
        async def run():
            async with aiohttp.ClientSession() as http:
                async with http.ws_connect(f'http://127.0.0.1:{self.port}/ws',compress=15) as ws:
                    self.assertEqual(ws.compress,0)
                    await ws.send_json({'t':'key','k':'right','down':True})
                    await asyncio.sleep(.1)
                async with http.post(f'http://127.0.0.1:{self.port}/api/key',json={'key':'up'}) as r:
                    self.assertEqual(r.status,200,await r.text())
        asyncio.run(run())
        events=json.loads(request(self.port,'/api/recording')[1])['events']
        downs=[e['down'] for e in events if e.get('key')=='right']
        self.assertEqual(downs,[True,False])
