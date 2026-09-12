"""File recording regressions: complete history, stable readers and exact retry."""
import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from recording import Snapshot, RecordingAPI
from recording_store import RecordingStore
from storage import validate_recording_directory


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'run.jsonl'
        self.store=RecordingStore(self.path,started=10)
        self.addCleanup(self.store.close)

    def snapshot(self):
        snap=Snapshot(**self.store.pin())
        self.addCleanup(snap.close)
        return snap

    def test_reset_keeps_full_old_recording_and_open_reader(self):
        self.store.append({'t':0,'d':'old'})
        old=self.snapshot()
        archive=self.store.reset(20)
        self.store.append({'t':1,'d':'new'})
        self.assertEqual(list(old),[{'t':0,'d':'old'}])
        self.assertEqual(list(self.snapshot()),[{'t':1,'d':'new'}])
        self.assertIn(b'old',archive.read_bytes())
        self.assertEqual(old.header['started'],10)

    def test_reopen_drops_torn_final_line_instead_of_closing_it(self):
        self.store.append({'t':0,'key':'up','down':True})
        self.store.append({'t':1,'key':'up','down':False})
        self.store.close()
        raw=self.path.read_bytes()
        torn=raw[:-7]                       # crash mid-append: no trailing newline
        self.path.write_bytes(torn)
        self.store=RecordingStore(self.path)
        self.assertEqual(self.store.started,10)
        self.assertEqual([e['down'] for e in self.snapshot()],[True])
        self.assertTrue(self.store.append({'t':2,'key':'esc','down':True}))
        self.assertEqual([e['key'] for e in self.snapshot()],['up','esc'])
        self.assertEqual(self.store.committed_size,self.path.stat().st_size)

    def test_reopen_header_only_file_without_newline_is_terminated(self):
        self.store.close()
        raw=self.path.read_bytes().rstrip(b'\n')
        self.path.write_bytes(raw)
        self.store=RecordingStore(self.path)
        self.assertEqual(self.path.read_bytes(),raw+b'\n')
        self.assertTrue(self.store.append({'t':3,'key':'up','down':True}))
        self.assertEqual([e['key'] for e in self.snapshot()],['up'])

    def test_failed_partial_append_and_fsync_retry_exactly_once(self):
        self.store.append({'t':0,'key':'up','down':True})
        before=self.path.read_bytes()
        real=os.write
        calls=[0]
        def broken(fd,data):
            calls[0]+=1
            if calls[0]==1:return real(fd,data[:4])
            raise OSError('disk full')
        with mock.patch('recording_store.os.write',side_effect=broken):
            self.assertFalse(self.store.append({'t':1,'key':'up','down':False}))
        self.assertEqual(self.path.read_bytes(),before)
        with mock.patch('recording_store.os.fsync',side_effect=OSError('flush failed')):
            self.assertFalse(self.store.flush())
        self.assertEqual(self.path.read_bytes(),before)
        self.assertTrue(self.store.flush())
        self.assertEqual([e['down'] for e in self.snapshot()],[True,False])
        self.assertEqual(self.store.pending_bytes,0)

    def test_complete_history_exceeds_old_memory_cap_with_bounded_pages(self):
        payload=base64.b64encode(b'x'*(768<<10)).decode()
        for i in range(14):self.store.append({'t':i*40,'d':payload})
        self.assertGreater(self.path.stat().st_size,12<<20)
        snap=self.snapshot()
        start=None;count=0
        while True:
            page=snap.page(start)
            self.assertLessEqual(len(page['events']),1)
            count+=len(page['events'])
            if page['done']:break
            start=page['next']
        self.assertEqual(count,14)
        self.assertEqual(snap.duration,520)
        self.assertEqual(self.store.pending_bytes,0)

    def test_reader_excludes_later_appends_and_rejects_midline_cursor(self):
        self.store.append({'t':1,'key':'up','down':True})
        old=self.snapshot()
        self.store.append({'t':2,'key':'up','down':False})
        self.assertEqual(len(list(old)),1)
        with self.assertRaises(ValueError):old.page(old.begin+1)

    def test_reset_failure_keeps_active_file_and_lease(self):
        self.store.append({'t':0,'key':'up','down':True})
        before=self.path.read_bytes()
        with mock.patch.object(self.store,'_prepare_file',side_effect=OSError('full')):
            with self.assertRaises(OSError):self.store.reset(20)
        self.assertEqual(self.path.read_bytes(),before)
        with self.assertRaises(RuntimeError):RecordingStore(self.path)
        self.store.reset(20)
        with self.assertRaises(RuntimeError):RecordingStore(self.path)

    def test_cloud_container_root_is_not_accepted_as_disk(self):
        mount='1 0 0:1 / / rw - overlay overlay rw\n'
        with self.assertRaises(RuntimeError):
            validate_recording_directory(self.temp.name,cloud=True,mountinfo=mount)

    def test_cloud_container_root_is_accepted_with_the_ephemeral_opt_in(self):
        # A run cannot outlive its instance, so a deployment that says so
        # explicitly may record on instance memory; the journal is just
        # gone once the instance is.
        mount='1 0 0:1 / / rw - overlay overlay rw\n'
        with mock.patch.dict(os.environ,{'QUNXIA_RECORDING_ALLOW_EPHEMERAL':'1'}):
            result=validate_recording_directory(self.temp.name,cloud=True,mountinfo=mount)
        self.assertTrue(result['memory_backed'])

    def test_the_ephemeral_opt_in_does_not_weaken_local_tmpfs(self):
        resolved=Path(self.temp.name).resolve()
        mount=f'1 0 0:1 {resolved} {resolved} rw - tmpfs tmpfs rw\n'
        with mock.patch.dict(os.environ,{'QUNXIA_RECORDING_ALLOW_EPHEMERAL':'1'}):
            with self.assertRaises(RuntimeError):
                validate_recording_directory(self.temp.name,cloud=False,mountinfo=mount)


class RecordingApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_paged_reader_survives_reset_and_can_close(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            store=RecordingStore(Path(directory)/'run.jsonl',started=10)
            api=RecordingAPI(store)
            try:
                store.append({'t':1,'key':'up','down':True})
                response=await api.handle(SimpleNamespace(query={'view':'paged'}))
                page=json.loads(response.body)
                store.reset(20)
                response=await api.handle(SimpleNamespace(query={'view':'paged','token':page['token']}))
                self.assertEqual(json.loads(response.body)['events'],page['events'])
                await api.handle(SimpleNamespace(query={'view':'paged','token':page['token'],'close':'1'}))
                self.assertFalse(api.readers)
            finally:
                api.close();store.close()

    async def test_benchmark_view_can_hide_recorder_only_trajectory_events(self):
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer
        with tempfile.TemporaryDirectory() as directory:
            store = RecordingStore(Path(directory) / 'run.jsonl', started=10)
            api = RecordingAPI(store, archives=False)
            store.append({'t': 1, 'act': 'KEY', 'on': 'right'})
            store.append({'t': 1.1, 'trajectory': True, 'x': 4, 'y': 5})
            async def handle(request):
                return await api.handle(request, include_trajectory=False)
            app = web.Application()
            app.router.add_get('/api/recording', handle)
            try:
                async with TestClient(TestServer(app)) as client:
                    for query in ('?view=paged', '', '?format=jsonl'):
                        async with client.get('/api/recording' + query) as response:
                            self.assertEqual(response.status, 200)
                            body = await response.text()
                            events = ([json.loads(line) for line in body.splitlines()][1:]
                                      if 'jsonl' in query else json.loads(body)['events'])
                            self.assertEqual([event.get('act') for event in events], ['KEY'])
            finally:
                api.close(); store.close()


class RecordingWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_worker_health as workers
        workers.WorkerIntegrationTests.setUpClass.__func__(cls)

    def setUp(self):
        import test_worker_health as workers
        workers.WorkerIntegrationTests.setUp(self)

    def test_reset_without_viewers_records_full_frame_and_preserves_old_reader(self):
        import test_worker_health as workers
        import zlib
        workers.WorkerIntegrationTests.launch(self)
        def healthy():return workers.WorkerIntegrationTests.healthy(self)
        workers.wait_for(healthy)
        status,body=workers.request(self.port,'/api/reset?token=test',{})
        self.assertEqual(status,200,body)
        page=json.loads(workers.request(self.port,'/api/recording?view=paged')[1])
        picture=next(e for e in page['events'] if 'd' in e)
        self.assertEqual(zlib.decompress(base64.b64decode(picture['d']))[0],1)
        status,body=workers.request(self.port,'/api/reset?token=test',{})
        self.assertEqual(status,200,body)
        old=json.loads(workers.request(self.port,'/api/recording?view=paged&token='+page['token'])[1])
        self.assertEqual(old['events'],page['events'])
        raw=workers.request(self.port,'/api/recording?format=jsonl')[1]
        self.assertIn('version',json.loads(raw.splitlines()[0]))
        exported=json.loads(workers.request(self.port,'/api/recording')[1])
        self.assertTrue(any('d' in e for e in exported['events']))
        self.assertEqual(healthy()['recording']['cache_bytes'],0)

    def run_storage_pause(self, benchmark=False):
        import subprocess
        import sys
        import test_worker_health as workers
        launcher=self.server/'storage_pause_probe.py'
        launcher.write_text('''import json, os, pathlib, time
import server
server.KEYFRAME_EVERY = .05
original_event = server.key_event
original_write = server.RecordingStore._write
original_key = server.LIB.core_key
original_guarded_key = server.LIB.core_key_before_deadline
armed = False
fail_until = 0.0
def key_event(name, down):
    global armed
    original_event(name, down)
    if down: armed = True
def fail_write(self, data):
    global fail_until
    if armed and not fail_until and "d" in json.loads(data):
        fail_until = time.monotonic() + 2.0
    if time.monotonic() < fail_until:
        raise OSError("injected recording write failure")
    return original_write(self, data)
def core_key(code, down):
    result = original_key(code, down)
    with pathlib.Path(os.environ["KEY_LOG"]).open("a") as stream:
        stream.write(json.dumps([code, bool(down)]) + "\\n")
    return result
def guarded_key(code, down, deadline):
    result = original_guarded_key(code, down, deadline)
    if result:
        with pathlib.Path(os.environ["KEY_LOG"]).open("a") as stream:
            stream.write(json.dumps([code, bool(down)]) + "\\n")
    return result
server.LIB.core_key_before_deadline = guarded_key
server.key_event = key_event
server.RecordingStore._write = fail_write
server.LIB.core_key = core_key
server.main()
''')
        env=dict(os.environ,PORT=str(self.port),QUNXIA_CORE=str(self.core),QUNXIA_GAME='unused',
                 QUNXIA_SAVES=str(self.folder/'saves'),QUNXIA_RECORDING_DIR=str(self.folder/'recordings'),
                 QUNXIA_STALL_SECONDS='15',QUNXIA_BENCH='1' if benchmark else '0',
                 PROBE_AUTORUN='1',KEY_LOG=str(self.folder/'keys.jsonl'))
        with (self.folder/'worker.log').open('wb') as log:
            process=subprocess.Popen([sys.executable,str(launcher)],env=env,cwd=self.server,stdout=log,stderr=log)
        self.procs.append(process)
        def healthy():return workers.WorkerIntegrationTests.healthy(self)
        before=workers.wait_for(healthy)
        status,body=workers.request(self.port,'/api/key?react=0&stable=1&maxsettle=6',{'key':'right','hold':6})
        self.assertEqual(status,503,body)
        self.assertEqual(json.loads(body)['error'],'recording_unavailable')
        keys=[json.loads(row) for row in (self.folder/'keys.jsonl').read_text().splitlines()]
        self.assertEqual(keys[-1],[275,False])  # completed real native key-up
        if benchmark:
            process.wait(timeout=4)
            self.assertEqual(process.returncode,75)
            fault=workers.read_json(self.folder/'saves/.health/failure.json')
            self.assertEqual(fault['reason'],'recording_failed')
        else:
            after=workers.wait_for(healthy,seconds=5)
            self.assertIsNone(process.poll())
            self.assertGreater(after['core_ticks'],before['core_ticks'])
            self.assertEqual(after['recording']['pending_bytes'],0)
            self.assertFalse((self.folder/'saves/.health/failure.json').exists())
            # server.MIN_HOLD_FRAMES; spelled out because this module talks to
            # the worker over HTTP rather than importing the server.
            status,body=workers.request(self.port,'/api/key?react=0&stable=1&maxsettle=6',{'key':'up','hold':5})
            self.assertEqual(status,200,body)

    def test_recoverable_recording_pause_does_not_become_core_stall(self):
        self.run_storage_pause()

    def test_formal_benchmark_recording_failure_remains_invalid(self):
        if not (self.server/'warden.py').exists():
            self.skipTest('benchmark worker only')
        self.run_storage_pause(benchmark=True)
