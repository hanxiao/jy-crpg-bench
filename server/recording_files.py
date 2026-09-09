"""Read-only access to the current journal and its named reset archives."""
import json
import math
import os
import re
import stat
from email.utils import formatdate, parsedate_to_datetime


ARCHIVE_NAME = re.compile(r'\d{8}-\d{6}-[a-f0-9]{12}\.jsonl', re.ASCII)
TAIL_BYTES = (4 << 20) + (64 << 10)


def archive_name(name):
    return isinstance(name, str) and ARCHIVE_NAME.fullmatch(name) is not None


def tail_timestamp(fd, end):
    """Recover replay duration from one bounded tail without opening a writer."""
    start = max(0, end - TAIL_BYTES)
    data = os.pread(fd, end - start, start)
    if start:
        _, _, data = data.partition(b'\n')  # discard a possible partial first line
    last = 0.0
    for line in data.splitlines():
        try:
            event = json.loads(line)
            when = float(event.get('t', 0))
            if math.isfinite(when) and when >= 0:
                last = max(last, when)
        except (ValueError, TypeError, AttributeError):
            continue
    return last


def byte_range(value, size):
    """One inclusive HTTP range, returned as a bounded Python interval."""
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', value.strip(), re.ASCII)
    if match is None or not any(match.groups()) or not size:
        raise ValueError('invalid range')
    first, last = match.groups()
    if not first:
        length = int(last)
        if length <= 0:
            raise ValueError('invalid suffix range')
        return max(0, size - length), size
    start = int(first)
    end = min(size, int(last) + 1) if last else size
    if start >= size or end <= start:
        raise ValueError('unsatisfiable range')
    return start, end


def matches_if_range(value, etag, modified):
    if value.startswith(('"', 'W/')):
        return value == etag  # a weak validator is never a match
    try:
        date = parsedate_to_datetime(value)
        return date.tzinfo is not None and int(modified) <= date.timestamp()
    except (ValueError, TypeError, OverflowError):
        return False


async def download(pin, request):
    """Stream a pinned prefix; a reset cannot switch a download to a new inode."""
    from aiohttp import web
    from aiohttp.helpers import content_disposition_header

    fd, size = pin['fd'], pin['end']
    try:
        status = os.fstat(fd)
        etag = f'"{status.st_dev:x}-{status.st_ino:x}-{size:x}-{status.st_mtime_ns:x}"'
        headers = {
            'Content-Type': 'application/x-ndjson; charset=utf-8',
            'Content-Disposition': content_disposition_header('attachment', filename=pin['path'].name),
            'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store', 'ETag': etag,
            'Last-Modified': formatdate(status.st_mtime, usegmt=True),
        }
        start, end, response_status = 0, size, 200
        selected = request.headers.get('Range')
        condition = request.headers.get('If-Range')
        if selected and (not condition or matches_if_range(condition, etag, status.st_mtime)):
            try:
                start, end = byte_range(selected, size)
            except ValueError:
                raise web.HTTPRequestRangeNotSatisfiable(headers={'Content-Range': f'bytes */{size}'})
            response_status = 206
            headers['Content-Range'] = f'bytes {start}-{end-1}/{size}'
        headers['Content-Length'] = str(end - start)
        response = web.StreamResponse(status=response_status, headers=headers)
        await response.prepare(request)
        if request.method != 'HEAD':
            while start < end:
                data = os.pread(fd, min(64 << 10, end - start), start)
                if not data:
                    raise OSError('pinned recording was truncated')
                await response.write(data)
                start += len(data)
        await response.write_eof()
        return response
    finally:
        os.close(fd)


class RecordingFiles:
    def __init__(self, store):
        self.store = store

    def _directory(self):
        # The configured journal directory is trusted; the selectable archive
        # directory and its entries must never redirect readers through links.
        parent = os.open(self.store.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            return os.open('recordings', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                           dir_fd=parent)
        finally:
            os.close(parent)

    def pin(self, name='current'):
        if name == 'current':
            return self.store.pin()
        if not archive_name(name):
            raise FileNotFoundError('invalid recording name')
        folder = fd = None
        try:
            folder = self._directory()
            # NONBLOCK prevents a substituted FIFO from blocking before fstat;
            # NOFOLLOW and dir_fd also cover swaps between validation and open.
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
            status = os.fstat(fd)
            if not stat.S_ISREG(status.st_mode):
                raise FileNotFoundError('recording is not a regular file')
            result = {'path': self.store.path.parent / 'recordings' / name,
                      'fd': fd, 'end': status.st_size,
                      'last_timestamp': tail_timestamp(fd, status.st_size)}
            fd = None
            return result
        except OSError as error:
            raise FileNotFoundError('recording is unavailable') from error
        finally:
            if fd is not None:
                os.close(fd)
            if folder is not None:
                os.close(folder)

    def listing(self):
        pin = self.store.pin()
        try:
            files = [{'id': 'current', 'name': self.store.path.name, 'bytes': pin['end']}]
        finally:
            os.close(pin['fd'])
        try:
            folder = self._directory()
        except OSError:
            return files
        try:
            for name in sorted(os.listdir(folder), reverse=True):
                if not archive_name(name):
                    continue
                try:
                    status = os.stat(name, dir_fd=folder, follow_symlinks=False)
                except OSError:
                    continue
                if stat.S_ISREG(status.st_mode):
                    files.append({'id': name, 'name': name, 'bytes': status.st_size})
        finally:
            os.close(folder)
        return files
