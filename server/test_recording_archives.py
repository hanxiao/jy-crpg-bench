"""HTTP regressions for immutable current and archived recording reads."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from urllib.parse import quote

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from recording import RecordingAPI
from recording_store import RecordingStore


class RecordingArchiveTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'current.jsonl'
        self.store = RecordingStore(self.path, started=10)
        self.addCleanup(self.store.close)
        self.old_events = [
            {'t': 1, 'key': 'up', 'down': True},
            {'t': 7.25, 'key': 'up', 'down': False, 'note': '旧录像'},
        ]
        for event in self.old_events:
            self.assertTrue(self.store.append(event))
        self.archive = self.store.reset(20)
        self.current_events = [{'t': 2, 'key': 'left', 'down': True}]
        for event in self.current_events:
            self.assertTrue(self.store.append(event))
        self.api, self.client = await self.make_client(archives=True)

    async def make_client(self, archives):
        api = RecordingAPI(self.store, archives=archives)
        self.addCleanup(api.close)
        app = web.Application()
        app.router.add_get('/api/recording', api.handle)
        api.install(app)
        client = TestClient(TestServer(app))
        await client.start_server()
        self.addAsyncCleanup(client.close)
        return api, client

    async def get_json(self, query, client=None, status=200):
        async with (client or self.client).get('/api/recording', params=query) as response:
            self.assertEqual(response.status, status, await response.text())
            return await response.json()

    def download_path(self, name):
        return '/api/recordings/' + quote(name, safe='')

    async def inventory(self):
        async with self.client.get('/api/recordings') as response:
            self.assertEqual(response.status, 200, await response.text())
            return (await response.json())['files']

    async def test_inventory_includes_current_and_archive_sizes(self):
        entries = {entry['id']: entry for entry in await self.inventory()}
        self.assertEqual(set(entries), {'current', self.archive.name})
        self.assertEqual(entries['current']['bytes'], self.path.stat().st_size)
        self.assertEqual(entries[self.archive.name]['bytes'], self.archive.stat().st_size)
        self.assertEqual(entries[self.archive.name]['name'], self.archive.name)
        self.assertTrue(entries['current']['name'])

    async def test_full_current_and_archive_downloads_are_exact_attachments(self):
        for name, path in [('current', self.path), (self.archive.name, self.archive)]:
            with self.subTest(recording=name):
                expected = path.read_bytes()
                async with self.client.get(self.download_path(name)) as response:
                    self.assertEqual(response.status, 200, await response.text())
                    self.assertEqual(await response.read(), expected)
                    self.assertEqual(response.headers['Content-Length'], str(len(expected)))
                    self.assertEqual(response.headers['Accept-Ranges'], 'bytes')
                    self.assertIn('attachment;', response.headers['Content-Disposition'])
                    self.assertIn('.jsonl', response.headers['Content-Disposition'])
                    self.assertEqual(response.content_type, 'application/x-ndjson')

    async def test_bounded_open_ended_suffix_and_clamped_ranges_are_exact(self):
        for name, path in [('current', self.path), (self.archive.name, self.archive)]:
            expected = path.read_bytes()
            ranges = [
                ('bytes=3-31', 3, 31),
                ('bytes=5-', 5, len(expected) - 1),
                ('bytes=-19', len(expected) - 19, len(expected) - 1),
                ('bytes=0-999999', 0, len(expected) - 1),
                ('bytes=-999999', 0, len(expected) - 1),
            ]
            for header, start, end in ranges:
                with self.subTest(recording=name, range=header):
                    async with self.client.get(self.download_path(name), headers={'Range': header}) as response:
                        self.assertEqual(response.status, 206, await response.text())
                        self.assertEqual(await response.read(), expected[start:end + 1])
                        self.assertEqual(response.headers['Content-Length'], str(end - start + 1))
                        self.assertEqual(response.headers['Content-Range'], f'bytes {start}-{end}/{len(expected)}')

    async def test_malformed_multiple_and_unsatisfiable_ranges_return_416(self):
        for name, path in [('current', self.path), (self.archive.name, self.archive)]:
            size = path.stat().st_size
            for header in [
                'bytes=wrong', 'bytes=', 'bytes=8-3', 'bytes=-0',
                'bytes=0-1,3-4', 'items=0-4', f'bytes={size}-',
            ]:
                with self.subTest(recording=name, range=header):
                    async with self.client.get(self.download_path(name), headers={'Range': header}) as response:
                        self.assertEqual(response.status, 416, await response.text())
                        self.assertEqual(response.headers['Content-Range'], f'bytes */{size}')

    async def test_if_range_requires_the_matching_validator(self):
        expected = self.archive.read_bytes()
        url = self.download_path(self.archive.name)
        async with self.client.get(url) as response:
            self.assertEqual(response.status, 200)
            validators = [response.headers['ETag'], response.headers['Last-Modified']]
            await response.read()
        for validator in validators:
            with self.subTest(validator=validator):
                async with self.client.get(url, headers={'Range': 'bytes=1-9', 'If-Range': validator}) as response:
                    self.assertEqual(response.status, 206, await response.text())
                    self.assertEqual(await response.read(), expected[1:10])
        for validator in ['"unrelated-recording"', 'Wed, 21 Oct 2015 07:28:00 GMT']:
            with self.subTest(stale_validator=validator):
                async with self.client.get(url, headers={'Range': 'bytes=1-9', 'If-Range': validator}) as response:
                    self.assertEqual(response.status, 200, await response.text())
                    self.assertEqual(await response.read(), expected)
                    self.assertNotIn('Content-Range', response.headers)

    async def test_current_download_keeps_its_prefix_during_append_and_reset(self):
        self.assertTrue(self.store.append({'t': 3, 'd': 'x' * (192 << 10)}))
        expected = self.path.read_bytes()
        first_write = asyncio.Event()
        release_write = asyncio.Event()
        original_write = web.StreamResponse.write
        write_count = 0

        async def gated_write(response, data):
            nonlocal write_count
            write_count += 1
            if write_count == 1:
                first_write.set()
                await release_write.wait()
            return await original_write(response, data)

        async def download():
            async with self.client.get(self.download_path('current')) as response:
                return response.status, dict(response.headers), await response.read()

        with mock.patch.object(web.StreamResponse, 'write', new=gated_write):
            transfer = asyncio.create_task(download())
            try:
                await asyncio.wait_for(first_write.wait(), 5)
                self.assertTrue(self.store.append({'t': 4, 'note': 'late old-session append'}))
                archived = self.store.reset(30)
                self.assertTrue(self.store.append({'t': 1, 'note': 'new session'}))
                release_write.set()
                status, headers, actual = await asyncio.wait_for(transfer, 5)
            finally:
                release_write.set()
                if not transfer.done():
                    transfer.cancel()
                    await asyncio.gather(transfer, return_exceptions=True)
        self.assertEqual(status, 200)
        self.assertGreater(write_count, 1)
        self.assertEqual(actual, expected)
        self.assertEqual(headers['Content-Length'], str(len(expected)))
        self.assertIn(b'late old-session append', archived.read_bytes())
        self.assertIn(b'new session', self.path.read_bytes())

    async def test_current_range_still_reads_the_old_inode_after_headers_are_sent(self):
        expected = self.path.read_bytes()
        original_prepare = web.StreamResponse.prepare
        replaced = False

        async def reset_after_headers(response, request):
            nonlocal replaced
            result = await original_prepare(response, request)
            if response.status == 206 and not replaced:
                replaced = True
                self.store.reset(30)
                self.store.append({'t': 1, 'note': 'replacement current recording'})
            return result

        with mock.patch.object(web.StreamResponse, 'prepare', new=reset_after_headers):
            async with self.client.get(self.download_path('current'), headers={'Range': 'bytes=7-55'}) as response:
                self.assertEqual(response.status, 206)
                self.assertEqual(await response.read(), expected[7:56])
                self.assertEqual(response.headers['Content-Range'], f'bytes 7-55/{len(expected)}')
        self.assertTrue(replaced)
        self.assertIn(b'replacement current recording', self.path.read_bytes())

    async def test_current_listing_and_download_exclude_an_uncommitted_suffix(self):
        expected = self.path.read_bytes()
        os.write(self.store.fd, b'{"t":999,"incomplete":')
        current = next(row for row in await self.inventory() if row['id'] == 'current')
        self.assertEqual(current['bytes'], len(expected))
        async with self.client.get(self.download_path('current')) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(await response.read(), expected)
            self.assertEqual(response.headers['Content-Length'], str(len(expected)))

    async def test_archive_reader_and_duration_survive_name_replacement(self):
        first = await self.get_json({'view': 'paged', 'recording': self.archive.name})
        self.assertEqual(first['events'], self.old_events)
        self.assertEqual(first['duration'], 7.25)
        replacement = self.root / 'replacement.jsonl'
        replacement_events = [{'t': 90, 'note': 'replacement'}]
        replacement.write_bytes(
            (json.dumps({'version': 1, 'started': 80}) + '\n' +
             json.dumps(replacement_events[0]) + '\n').encode())
        os.replace(replacement, self.archive)
        self.store.reset(30)
        old = await self.get_json({'view': 'paged', 'token': first['token']})
        self.assertEqual(old, first)
        fresh = await self.get_json({'view': 'paged', 'recording': self.archive.name})
        self.assertEqual(fresh['events'], replacement_events)
        self.assertEqual(fresh['started'], 80)
        self.assertEqual(fresh['duration'], 90)

    async def test_archive_tail_duration_and_reads_do_not_open_a_writer(self):
        # Enough data to put the origin outside the bounded timestamp tail.
        for index in range(5):
            self.assertTrue(self.store.append({'t': index * 37.5, 'd': 'a' * (1 << 20)}))
        self.assertTrue(self.store.append({'t': 187.5, 'key': 'esc', 'down': True}))
        archive = self.store.reset(30)
        expected = archive.read_bytes()
        names_before = set(archive.parent.iterdir())
        with mock.patch.object(RecordingStore, '__init__', side_effect=AssertionError('archive opened as a writer')):
            reader = self.api.snapshot(archive.name)
            try:
                self.assertEqual(reader.duration, 187.5)
                self.assertEqual(reader.header['started'], 20)
                self.assertEqual(reader.end, len(expected))
            finally:
                reader.close()
            async with self.client.get(self.download_path(archive.name)) as response:
                self.assertEqual(response.status, 200, await response.text())
                self.assertEqual(await response.read(), expected)
        self.assertEqual(archive.read_bytes(), expected)
        self.assertEqual(set(archive.parent.iterdir()), names_before)

    async def test_replacing_writer_updates_new_reads_without_repointing_old_tokens(self):
        old = await self.get_json({'view': 'paged'})
        self.store.close()
        replacement = RecordingStore(self.root / 'other' / 'replacement.jsonl', started=99)
        self.addCleanup(replacement.close)
        replacement.append({'t': 3, 'key': 'down', 'down': True})
        self.api.store = replacement
        fresh = await self.get_json({'view': 'paged'})
        retained = await self.get_json({'view': 'paged', 'token': old['token']})
        self.assertEqual(fresh['started'], 99)
        self.assertEqual(retained['started'], 20)
        response = await self.client.get('/api/recordings')
        files = (await response.json())['files']
        self.assertEqual([file['name'] for file in files], ['replacement.jsonl'])
        response = await self.client.get('/api/recordings/current')
        self.assertEqual(await response.read(), replacement.path.read_bytes())

    async def test_archive_pages_can_traverse_refetch_touch_and_close(self):
        events = [{'t': index + 10, 'd': str(index) * (550 << 10)} for index in range(5)]
        for event in events:
            self.assertTrue(self.store.append(event))
        archive = self.store.reset(30)
        expected = self.current_events + events
        first = await self.get_json({'view': 'paged', 'recording': archive.name})
        self.assertFalse(first['done'])
        token = first['token']
        collected = list(first['events'])
        cursor = first['next']
        starts = []
        while not first['done']:
            starts.append(cursor)
            page = await self.get_json({'view': 'paged', 'token': token, 'start': str(cursor)})
            repeated = await self.get_json({'view': 'paged', 'token': token, 'start': str(cursor)})
            self.assertEqual(repeated, page)
            self.assertEqual(page['token'], token)
            self.assertGreater(page['next'], cursor)
            self.assertEqual(page['end'], first['end'])
            collected.extend(page['events'])
            cursor = page['next']
            if page['done']:
                self.assertEqual(cursor, page['end'])
                break
        self.assertGreaterEqual(len(starts), 2)
        self.assertEqual(collected, expected)
        self.assertEqual(await self.get_json({'view': 'paged', 'token': token, 'touch': '1'}), {'ok': True})
        closed = await self.get_json({'view': 'paged', 'token': token, 'close': '1'})
        self.assertEqual(closed, {'ok': True})
        self.assertNotIn(token, self.api.readers)
        await self.get_json({'view': 'paged', 'token': token}, status=410)

    async def test_invalid_names_and_traversal_are_rejected(self):
        names = [
            '../current.jsonl', '../recordings/' + self.archive.name,
            '/etc/passwd', 'current.jsonl', self.archive.name.upper(),
            '20260909-123456-123456789ab.jsonl',
            '20260909-123456-123456789abc.jsonl.bak',
            '20260909-123456-123456789abc.jsonl',
        ]
        for name in names:
            with self.subTest(recording=name):
                async with self.client.get('/api/recording', params={'view': 'paged', 'recording': name}) as response:
                    self.assertEqual(response.status, 404, await response.text())
                async with self.client.get(self.download_path(name)) as response:
                    self.assertEqual(response.status, 404, await response.text())
        self.assertFalse(self.api.readers)

    async def test_inventory_omits_foreign_files_directories_and_file_symlinks(self):
        folder = self.archive.parent
        (folder / 'README.txt').write_text('not a recording')
        (folder / '20260909-123456-aaaaaaaaaaaa.jsonl').mkdir()
        linked_name = '20260909-123456-bbbbbbbbbbbb.jsonl'
        (folder / linked_name).symlink_to(self.path)
        entries = {entry['id'] for entry in await self.inventory()}
        self.assertEqual(entries, {'current', self.archive.name})
        async with self.client.get(self.download_path(linked_name)) as response:
            self.assertEqual(response.status, 404, await response.text())
        async with self.client.get('/api/recording', params={'view': 'paged', 'recording': linked_name}) as response:
            self.assertEqual(response.status, 404, await response.text())

    async def test_symlink_archive_directory_is_not_followed(self):
        folder = self.archive.parent
        target = self.root / 'outside-recordings'
        original = self.archive.read_bytes()
        folder.rename(target)
        folder.symlink_to(target, target_is_directory=True)
        self.assertEqual({entry['id'] for entry in await self.inventory()}, {'current'})
        async with self.client.get(self.download_path(self.archive.name)) as response:
            self.assertEqual(response.status, 404, await response.text())
        async with self.client.get('/api/recording', params={'view': 'paged', 'recording': self.archive.name}) as response:
            self.assertEqual(response.status, 404, await response.text())
        async with self.client.get(self.download_path('current')) as response:
            self.assertEqual(response.status, 200, await response.text())
            self.assertEqual(await response.read(), self.path.read_bytes())
        self.assertEqual((target / self.archive.name).read_bytes(), original)

    async def test_benchmark_mode_has_no_archive_routes_or_selection(self):
        api, client = await self.make_client(archives=False)
        for url in ['/api/recordings', self.download_path('current'), self.download_path(self.archive.name)]:
            async with client.get(url) as response:
                self.assertEqual(response.status, 404, await response.text())
        for query in [
            {'view': 'paged', 'recording': self.archive.name},
            {'format': 'jsonl', 'recording': self.archive.name},
            {'recording': self.archive.name},
        ]:
            async with client.get('/api/recording', params=query) as response:
                self.assertEqual(response.status, 404, await response.text())
        self.assertFalse(api.readers)
        for query in [{'format': 'jsonl'}, {'format': 'jsonl', 'recording': 'current'}]:
            async with client.get('/api/recording', params=query) as response:
                self.assertEqual(response.status, 200, await response.text())
                self.assertEqual(await response.read(), self.path.read_bytes())
        page = await self.get_json({'view': 'paged'}, client=client)
        self.assertEqual(page['events'], self.current_events)


if __name__ == '__main__':
    unittest.main()
