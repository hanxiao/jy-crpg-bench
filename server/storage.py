"""Validate the recording location without confusing a file with a disk."""
import os
from pathlib import Path
import platform
import re
import tempfile

MEMORY_FILESYSTEMS = {'tmpfs', 'ramfs', 'devtmpfs'}


def mount_for(path, mountinfo=None):
    path = Path(path).resolve()
    if mountinfo is None:
        try:
            mountinfo = Path('/proc/self/mountinfo').read_text()
        except OSError:
            return {'mount': '/', 'filesystem': 'apfs' if platform.system() == 'Darwin' else 'unknown'}
    matches = []
    for line in mountinfo.splitlines():
        try:
            before, after = line.split(' - ', 1)
            raw = before.split()[4]
            mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), raw)
            root = Path(mount)
            if path == root or root in path.parents:
                matches.append({'mount': str(root), 'filesystem': after.split()[0]})
        except (ValueError, IndexError):
            continue
    return max(matches, key=lambda item: len(item['mount'])) if matches else {'mount': '/', 'filesystem': 'unknown'}


def validate_recording_directory(path, *, cloud=None, mountinfo=None):
    path = Path(path).expanduser().resolve()
    if cloud is None:
        cloud = any(os.environ.get(name) for name in ('K_SERVICE', 'CLOUD_RUN_JOB', 'CLOUD_RUN_WORKER_POOL'))
    backing = mount_for(path, mountinfo)
    memory = backing['filesystem'] in MEMORY_FILESYSTEMS or (cloud and backing['mount'] == '/')
    ephemeral = cloud and os.environ.get("QUNXIA_RECORDING_ALLOW_EPHEMERAL") == "1"
    if memory:
        # In a container a run cannot outlive its instance: the session
        # process is a child of the broker and a finished run has already
        # published its video, so instance memory loses nothing the run
        # itself would lose - only the journal read back after the instance
        # stops. A deployment that will not accept that keeps the hard
        # failure; one that does says so explicitly, so the choice shows up
        # in the service configuration and in every start-up log.
        if ephemeral:
            print("recording storage is instance memory: journals are lost "
                  "when the container stops (mount a persistent volume for "
                  "durable journals)", flush=True)
        else:
            raise RuntimeError('recording directory uses instance memory; mount real persistent storage '
                               'and set QUNXIA_RECORDING_DIR (container /tmp is not durable storage)')
    if cloud and not ephemeral and (backing['mount'] == '/'
                                    or backing['filesystem'] not in (
                                        'nfs', 'nfs4', 'ext4', 'xfs', 'btrfs')):
        raise RuntimeError('Cloud Run recording storage must be an explicit POSIX persistent volume; '
                           'GCS/FUSE append semantics are not implemented by this file recorder')
    path.mkdir(parents=True, exist_ok=True)
    # Fail before starting a game if basic write/sync/rename semantics fail.
    fd, probe = tempfile.mkstemp(prefix='.storage-check-', dir=path)
    probe = Path(probe)
    moved = probe.with_suffix('.moved')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(b'qunxia recording storage probe\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(probe, moved)
        if moved.read_bytes() != b'qunxia recording storage probe\n':
            raise RuntimeError('recording storage readback did not match')
    finally:
        probe.unlink(missing_ok=True)
        moved.unlink(missing_ok=True)
    return {'path': str(path), **backing, 'memory_backed': memory,
            'cloud_run': bool(cloud), 'persistent_mount': backing['mount'] != '/',
            'python_history_cache_bytes': 0,
            'scope': 'file write/sync/rename checked; host/container memory is a separate resource limit'}
