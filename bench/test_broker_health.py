import asyncio
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import broker


class WorkerFailureTests(unittest.IsolatedAsyncioTestCase):
    # result_of remembers a result once it is complete; these tests reuse
    # fixed ids across fresh temporary result directories, so a stale entry
    # must not survive one test into the next.
    def setUp(self):
        self.addCleanup(broker._results.clear)

    async def test_stopped_worker_is_reaped_without_touching_good_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            bad=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
            good=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
            try:
                sessions={}
                for sid,proc in [('bad',bad),('good',good)]:
                    work=root/sid
                    sessions[sid]=dict(id=sid,agent='test',proc=proc,work=work,started_clock=broker.clock()-1)
                    broker.write_json(work/'health/heartbeat.json',dict(pid=proc.pid,at=broker.clock()-(20 if sid=='bad' else 0),phase='running'))
                os.kill(bad.pid,signal.SIGSTOP)
                with mock.patch.object(broker,'sessions',sessions),mock.patch.object(broker,'RESULT_DIR',root/'results'):
                    await broker.check_workers()
                    result=broker.result_of('bad')
                self.assertIsNotNone(bad.poll())
                self.assertIsNone(good.poll())
                self.assertFalse(result['valid'])
                self.assertEqual(result['reason'],'worker_unresponsive')
                self.assertFalse((root/'results/good.json').exists())
            finally:
                for proc in (bad,good):
                    if proc.poll() is None:proc.kill()
                    proc.wait()

    async def test_diagnostics_survive_work_directory_reclamation(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc = mock.Mock(pid=12345)
            proc.poll.return_value = 75
            work = root / 'scratch'
            sess = dict(id='run', agent='test', proc=proc, work=work)
            fault = dict(broker.failure('input_frame_timeout'), source='input_wait')
            broker.write_json(work / 'health/failure.json', fault)
            broker.write_json(work / 'health/heartbeat.json', dict(pid=12345, core_ticks=42))
            with mock.patch.object(broker, 'RESULT_DIR', root / 'results'):
                await broker.fail_worker(sess, 'input_frame_timeout')
                shutil.rmtree(work)
            retained = root / 'results/run.diagnostics'
            self.assertEqual(broker.read_json(retained / 'failure.json'), fault)
            self.assertEqual(broker.read_json(retained / 'heartbeat.json')['core_ticks'], 42)
            self.assertEqual(broker.read_json(retained / 'worker.json')['exit_code'], 75)

    async def test_missing_result_is_not_reported_as_success(self):
        result=broker.ended_payload({'id':'missing','agent':'test'},None)
        self.assertFalse(result['ok'])
        self.assertFalse(result['valid'])

    async def test_stall_at_time_limit_cannot_write_a_normal_result(self):
        import warden
        old=dict(warden.run)
        health=mock.Mock()
        async def stalled(_frames):
            raise RuntimeError('frame clock stalled')
        try:
            warden.run.update(playable=__import__('time').time()-warden.BUDGET-1,done=None,credit=0,deadline=warden.clock()-1,last_clock=warden.clock())
            with mock.patch.object(warden,'write_result') as write:
                await warden.warden({'events':[]},health,asyncio.Lock(),stalled)
                write.assert_not_called()
                health.fail.assert_called_once_with('finalization_wait_failed', source='finalization', exception_type='RuntimeError')
        finally:
            warden.run.clear();warden.run.update(old)

    async def test_finalization_fault_preserves_validated_run(self):
        for exited in (False, True):
            with self.subTest(exited=exited), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                proc=mock.Mock(pid=12345)
                proc.poll.return_value=75 if exited else None
                sess=dict(id='run',agent='test',proc=proc,work=root/'work',started_clock=broker.clock()-400)
                before=dict(id='run',valid=True,complete=False,actions=7,played=90,reason='time',error=None)
                broker.write_json(root/'results/run.json',before)
                broker.write_json(sess['work']/'health/heartbeat.json',dict(pid=proc.pid,at=broker.clock(),phase='finalizing',phase_at=broker.clock()-400))
                if exited:
                    broker.write_json(sess['work']/'health/failure.json',broker.failure('finalization_stalled'))
                with mock.patch.object(broker,'RESULT_DIR',root/'results'),mock.patch.object(broker,'sessions',{'run':sess}),mock.patch.object(broker,'stop_worker'):
                    await broker.check_workers()
                    after=broker.result_of('run')
                self.assertTrue(after['valid'])
                self.assertTrue(after['complete'])
                self.assertEqual((after['actions'],after['played'],after['reason']),(7,90,'time'))
                self.assertIn('artifact finalization failed',after['error'])

    async def test_failure_rechecks_result_after_reaping(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            sess=dict(id='run',agent='test',proc=mock.Mock())
            def finish_while_stopping(_proc):
                broker.write_json(root/'run.json',dict(valid=True,complete=False,actions=9,reason='time'))
            with mock.patch.object(broker,'RESULT_DIR',root),mock.patch.object(broker,'stop_worker',finish_while_stopping):
                await broker.fail_worker(sess,'finalization_stalled')
                after=broker.result_of('run')
            self.assertTrue(after['valid'])
            self.assertEqual(after['actions'],9)
