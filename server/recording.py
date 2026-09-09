"""Bounded reads of an immutable prefix of the append-only recording."""
import json
import os
import time
from pathlib import Path

from recording_files import RecordingFiles, archive_name, download

MAX_LINE = 4 << 20


class Snapshot:
    def __init__(self, path, fd, end, last_timestamp=0):
        self.path, self.fd, self.end = Path(path), fd, end
        self.closed = False
        try:
            _, header = next(self.lines(0))
            self.header = json.loads(header)
            self.begin = len(header)
            self.duration = last_timestamp
            self.elapsed = round(max(0, time.time() - self.header["started"]), 2)
        except BaseException:
            self.close()
            raise

    def lines(self, start):
        # dup pins the inode but shares the writer's file offset. pread uses
        # an independent cursor even while the writer appends or resets.
        offset, pending = start, b''
        while offset + len(pending) < self.end:
            chunk = os.pread(self.fd, min(64 << 10, self.end-offset-len(pending)), offset+len(pending))
            if not chunk:
                raise ValueError('recording was truncated')
            pending += chunk
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                line += b'\n'
                if len(line) > MAX_LINE:
                    raise ValueError('recording event is too large')
                yield offset, line
                offset += len(line)
            if len(pending) > MAX_LINE:
                raise ValueError('recording event is too large')
        if pending:
            raise ValueError('recording has an incomplete trailing event')

    def __iter__(self):
        for _, line in self.lines(self.begin):
            event = json.loads(line)
            if not isinstance(event, dict) or 't' not in event:
                raise ValueError('invalid recording event; raw JSONL remains available')
            yield event

    def page(self, start=None, byte_limit=1 << 20):
        start = self.begin if start is None else int(start)
        if not self.begin <= start <= self.end or (start > self.begin and os.pread(self.fd, 1, start-1) != b'\n'):
            raise ValueError('invalid recording cursor')
        events, size, cursor = [], 0, start
        for offset, line in self.lines(start):
            if events and (size + len(line) > byte_limit or len(events) >= 2048):
                break
            event = json.loads(line)
            if not isinstance(event, dict) or 't' not in event:
                raise ValueError('invalid recording event; raw JSONL remains available')
            events.append(event)
            size += len(line)
            cursor = offset + len(line)
        return {'events': events, 'next': cursor, 'end': self.end,
                'done': cursor == self.end, 'duration': self.duration,
                'started': self.header.get('started')}

    def close(self):
        if not self.closed:
            self.closed = True
            os.close(self.fd)

    def __del__(self):
        if hasattr(self, 'closed'):
            self.close()


class RecordingAPI:
    def __init__(self, store, archives=True):
        self.store = store
        self.archives = archives
        self.readers = {}

    @property
    def files(self):
        # Follow a replaced writer as the original current-recording API did.
        return RecordingFiles(self.store)

    def pin(self, name='current'):
        if name != 'current' and not self.archives:
            raise FileNotFoundError('recording archives are disabled')
        return self.files.pin(name)

    def snapshot(self, name='current'):
        return Snapshot(**self.pin(name))

    async def list_files(self, request):
        from aiohttp import web
        if not self.archives:
            raise web.HTTPNotFound()
        return web.json_response({'files': self.files.listing()}, headers={'Cache-Control': 'no-store'})

    async def download_file(self, request):
        from aiohttp import web
        if not self.archives:
            raise web.HTTPNotFound()
        try:
            pin = self.pin(request.match_info['name'])
        except FileNotFoundError:
            raise web.HTTPNotFound()
        return await download(pin, request)

    def install(self, app):
        from aiohttp import web
        if self.archives:
            app.add_routes([web.get('/api/recordings', self.list_files),
                            web.get('/api/recordings/{name}', self.download_file)])

    async def handle(self, request):
        from aiohttp import web
        import uuid
        name = request.query.get('recording', 'current')
        if name != 'current' and (not self.archives or not archive_name(name)):
            raise web.HTTPNotFound()
        if request.query.get('view') == 'paged':
            now = time.monotonic()
            for token, (reader, touched) in list(self.readers.items()):
                if now - touched > 120:
                    reader.close()
                    del self.readers[token]
            token = request.query.get('token')
            if not token:
                if len(self.readers) >= 4:
                    return web.json_response({'error': 'too many replay readers'}, status=429)
                token = uuid.uuid4().hex
                try:
                    self.readers[token] = (self.snapshot(name), now)
                except FileNotFoundError:
                    raise web.HTTPNotFound()
            elif token not in self.readers:
                return web.json_response({'error': 'replay expired; reopen it'}, status=410)
            reader, _ = self.readers[token]
            if request.query.get('close') == '1':
                reader.close()
                del self.readers[token]
                return web.json_response({'ok': True})
            self.readers[token] = (reader, now)
            if request.query.get('touch') == '1':
                return web.json_response({'ok': True})
            try:
                return web.json_response(dict(reader.page(request.query.get('start')), token=token))
            except ValueError as exc:
                return web.json_response({'error': str(exc)}, status=400)

        try:
            pin = self.pin(name)
        except FileNotFoundError:
            raise web.HTTPNotFound()
        raw = request.query.get('format') == 'jsonl'
        response = web.StreamResponse(headers={'Content-Type': 'application/x-ndjson' if raw else 'application/json'})
        reader = None
        try:
            if not raw:
                reader = Snapshot(**pin)
            await response.prepare(request)
            if raw:
                for start in range(0, pin['end'], 64 << 10):
                    await response.write(os.pread(pin['fd'], min(64 << 10, pin['end']-start), start))
            else:
                head = json.dumps({'started': reader.header['started'],
                                   'duration': reader.elapsed if name == 'current' else reader.duration})[:-1]
                await response.write((head + ',"events":[').encode())
                first = True
                payload_bytes = 0
                for event in reader:
                    data = event.get("d", "")
                    payload_bytes += len(data) * 3 // 4 - (len(data) - len(data.rstrip("=")))
                    await response.write((('' if first else ',')+json.dumps(event, separators=(',', ':'))).encode())
                    first = False
                await response.write(('],"bytes":' + str(payload_bytes) + '}').encode())
            await response.write_eof()
            return response
        finally:
            if reader:
                reader.close()
            elif raw:
                os.close(pin['fd'])

    def close(self):
        for reader, _ in self.readers.values():
            reader.close()
        self.readers.clear()
