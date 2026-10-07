#!/usr/bin/env python3
"""Send benchmark jobs through the local pi install, one workspace per job.

Each job is the paper's protocol: stock pi with its own four tools, one
prompt from the leaderboard page, the model creates its own session and
plays until the run answers 410. Nothing in ~/.pi is edited. Extensions,
skills, prompt templates, themes and context files are switched off with
pi's own flags for that one process, so there is nothing to restore when a
job ends, crashes or is interrupted.

    ./Scripts/bench_jobs.py                       # pick models interactively
    ./Scripts/bench_jobs.py --model omlx/X --minutes 20 --reps 1 --yes
    ./Scripts/bench_jobs.py finish <job-dir>      # bundle and file a job again

A job's workspace keeps everything needed to revisit the run:

    run.json      what was run, how it ended, the session it created
    prompt.txt    the prompt, verbatim
    work/         pi's working directory (empty at start)
    sessions/     pi's own session file: every message, tool call and result
    events.jsonl  pi's event stream without the token deltas, with wall times
    usage.json    the provider's meter, summed from the session by pi-usage.mjs
    artifacts/    what the model wrote: /tmp/<session_id>/ and work/
    trace.html    pi --export of the session, with credentials redacted
    bundle.zip    all of the above, redacted, as published

After the run the bundle and the trace go to the store through the session's
own address, and a summary lands on the run's catalogue entry beside the
usage report. Only pi's stdout events and files are read; the game is never
polled, so the run's metrics are the agent's alone.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "site"))
from agents_build import OPTIONS, PROMPT  # noqa: E402

SITE = "https://hanxiao.io/jy-crpg-bench/"
PI_FLAGS = ["--no-extensions", "--no-skills", "--no-prompt-templates",
            "--no-context-files", "--no-themes", "--offline"]
THINKING = ("off", "minimal", "low", "medium", "high", "xhigh", "max")
# The oldest pi this runner was verified with: the flags above, the json event
# stream, the session format pi-usage.mjs reads, and the context hook the
# image window uses.
MIN_PI_VERSION = (0, 84, 4)
IMAGE_WINDOW_EXT = REPO / "Scripts" / "pi-image-window.ts"
SESSION_URL = re.compile(r"(https?://[A-Za-z0-9.:\-]+)/s/([0-9a-f]{12})/t/([0-9a-f]{32})")
# Directories a model may build inside its folder that are not its work.
SKIP_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git", ".cache"}
ARTIFACT_FILE_LIMIT = 200 << 20
ARTIFACT_TOTAL_LIMIT = 1536 << 20
STORED = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".zip", ".gz", ".xz", ".mp4"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def canonical_agent_name(name):
    """The broker's rule for the names runs are listed under."""
    return "".join(c for c in str(name).strip()
                   if c.isascii() and (c.isalnum() or c in "-_."))[:40]


# ------------------------------------------------------------------ pi

def pi_version(pi):
    return subprocess.run([pi, "--version"], capture_output=True, text=True,
                          check=True).stdout.strip()


def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def pi_flags(window):
    """pi's flags for a job. The image window, when asked for, is the one
    extension loaded, by path (explicit -e paths load under --no-extensions)."""
    return PI_FLAGS + (["-e", str(IMAGE_WINDOW_EXT)] if window else [])


def pi_models(pi):
    """Every model this pi can run, as `pi --list-models` reports it."""
    out = subprocess.run([pi, "--list-models"], capture_output=True, text=True,
                         check=True).stdout
    models = []
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 6:
            continue
        provider, model, context, max_out, thinking, images = cols[:6]
        models.append({"ref": f"{provider}/{model}", "provider": provider,
                       "id": model, "context": context, "maxOut": max_out,
                       "thinking": thinking == "yes", "images": images == "yes"})
    return models


def agent_dir():
    return pathlib.Path(os.environ.get("PI_CODING_AGENT_DIR")
                        or pathlib.Path.home() / ".pi" / "agent")


def config_digest():
    """Checksums of the pi config a job could touch, to prove it did not."""
    out = {}
    for name in ("settings.json", "models.json", "auth.json"):
        path = agent_dir() / name
        if path.exists():
            out[name] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return out


def pi_compaction():
    """The context compaction a long run gets from the user's pi settings."""
    try:
        return json.loads((agent_dir() / "settings.json").read_text()).get("compaction")
    except (OSError, ValueError):
        return None


def secret_values():
    """Every credential this machine could leak into a trace: provider keys
    and headers from pi's config, and secret-looking environment values."""
    values = set()

    def walk(node, secret=False):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, secret or bool(re.search(
                    r"key|token|secret|pass|auth|access|refresh|header|cookie",
                    k, re.I)))
        elif isinstance(node, list):
            for v in node:
                walk(v, secret)
        elif isinstance(node, str) and secret and len(node) >= 8:
            values.add(node)
            # "Bearer xyz": the bare credential can travel without its scheme
            values.update(p for p in node.split() if len(p) >= 8)

    for name in ("models.json", "auth.json"):
        try:
            walk(json.loads((agent_dir() / name).read_text()))
        except (OSError, ValueError):
            pass
    for k, v in os.environ.items():
        if re.search(r"KEY|TOKEN|SECRET|PASS|CRED|AUTH", k) and len(v) >= 8:
            values.add(v)
    return sorted(values, key=len, reverse=True)


SECRET_PATTERNS = [re.compile(p) for p in (
    r"sk-[A-Za-z0-9_\-]{20,}", r"AIza[0-9A-Za-z_\-]{35}", r"jina_[A-Za-z0-9]{20,}",
    r"gh[pousr]_[A-Za-z0-9]{30,}", r"xox[abpr]-[A-Za-z0-9\-]{10,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}")]


class Redactor:
    def __init__(self, secrets, token=None):
        self.secrets = list(secrets) + ([token] if token else [])

    def text(self, s):
        for v in self.secrets:
            if v in s:
                s = s.replace(v, "[REDACTED]")
        for p in SECRET_PATTERNS:
            s = p.sub("[REDACTED]", s)
        return s

    def leaks(self, data: bytes):
        return any(v.encode() in data for v in self.secrets)


def scrubbed_env(provider):
    """The environment pi runs in: enough to work, and no credential pi does
    not need. Keys in models.json and auth.json are read by pi from disk."""
    keep = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "TERM", "TMPDIR",
            "TZ", "NVM_DIR", "NVM_BIN"}
    env = {k: v for k, v in os.environ.items()
           if k in keep or k.startswith("LC_")}
    try:
        cfg = json.loads((agent_dir() / "models.json").read_text())
        key = (cfg.get("providers", {}).get(provider) or {}).get("apiKey")
    except (OSError, ValueError):
        key = None
    # a provider configured by environment variable name, or a built-in one
    for name in ((key,) if isinstance(key, str) else ()) + (
            provider.upper().replace("-", "_") + "_API_KEY",):
        if name and re.fullmatch(r"[A-Z][A-Z0-9_]*", name) and name in os.environ:
            env[name] = os.environ[name]
    env["PI_OFFLINE"] = "1"
    return env


# ------------------------------------------------------------------ processes

class ProcTree:
    """Every process descended from one pi, remembered across reparenting.

    The model's shell can leave a loop running in the background that keeps
    pressing keys after pi exits. macOS has no session filter in pgrep, so
    the tree is sampled every two seconds and a descendant stays known by pid
    and start time after its parent dies."""

    def __init__(self, root):
        self.root = root
        self.known = {}  # pid -> start time string

    @staticmethod
    def table():
        out = subprocess.run(["ps", "-axo", "pid=,ppid=,stat=,lstart="],
                             capture_output=True, text=True).stdout
        rows = {}
        for line in out.splitlines():
            parts = line.split(None, 3)
            # a zombie has exited already; it only waits for its parent to reap it
            if len(parts) == 4 and not parts[2].startswith("Z"):
                rows[int(parts[0])] = (int(parts[1]), parts[3].strip())
        return rows

    def sample(self):
        rows = self.table()
        if self.root in rows and self.root not in self.known:
            self.known[self.root] = rows[self.root][1]
        grew = True
        while grew:
            grew = False
            for pid, (ppid, start) in rows.items():
                if pid not in self.known and ppid in self.known \
                        and rows.get(ppid, (0, ""))[1] == self.known[ppid]:
                    self.known[pid] = start
                    grew = True
        return rows

    def alive(self):
        rows = self.table()
        return [pid for pid, start in self.known.items()
                if pid in rows and rows[pid][1] == start]

    def kill(self, grace=8.0):
        self.sample()
        pids = self.alive()
        for sig in (signal.SIGTERM, signal.SIGKILL):
            for pid in pids:
                try:
                    os.kill(pid, sig)
                except OSError:
                    pass
            deadline = time.time() + grace
            while time.time() < deadline:
                pids = self.alive()
                if not pids:
                    return 0
                time.sleep(0.3)
        return len(self.alive())


# ------------------------------------------------------------------ one job

def compact_event(ev, now):
    """pi's event, minus the token stream and the repeated message bodies."""
    kind = ev.get("type")
    if kind in ("message_update", "message_start", "tool_execution_update"):
        return None
    out = {"t": round(now, 3), "type": kind}
    if kind == "message_end":
        m = ev.get("message") or {}
        out.update(role=m.get("role"), stopReason=m.get("stopReason"),
                   usage=m.get("usage"), model=m.get("model"),
                   error=m.get("errorMessage"),
                   tools=[c.get("name") for c in m.get("content") or []
                          if isinstance(c, dict) and c.get("type") == "toolCall"])
        return {k: v for k, v in out.items() if v not in (None, [])}
    if kind == "tool_execution_start":
        args = json.dumps(ev.get("args"), ensure_ascii=False)
        out.update(id=ev.get("toolCallId"), tool=ev.get("toolName"),
                   args=args[:2000])
        return out
    if kind == "tool_execution_end":
        text = result_text(ev.get("result"))
        out.update(id=ev.get("toolCallId"), tool=ev.get("toolName"),
                   isError=bool(ev.get("isError")), chars=len(text),
                   head=text[:400])
        return out
    for k, v in ev.items():
        if k not in ("type", "message", "messages", "toolResults", "partialResult"):
            out[k] = v
    return out


def result_text(result):
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    parts = result.get("content") if isinstance(result, dict) else result
    if isinstance(parts, list):
        return "".join(p.get("text", "") for p in parts
                       if isinstance(p, dict) and p.get("type") == "text")
    return json.dumps(result, ensure_ascii=False)


class Job:
    def __init__(self, ws, spec, args, pi, version):
        self.ws = ws
        self.spec = spec
        self.args = args
        self.pi = pi
        self.version = version
        self.proc = None
        self.tree = None
        self.session = None     # {"base", "sid", "token", "agent", "ends_at"}
        self.sessions_seen = []
        self.ended_seen = None
        self.started = None
        self.outcome = None
        self.stop = threading.Event()

    # manifest ----------------------------------------------------------
    def manifest(self, **extra):
        path = self.ws / "run.json"
        data = json.loads(path.read_text()) if path.exists() else {}
        data.update(extra)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return data

    def prepare(self):
        s = self.spec
        for d in ("work", "sessions", "artifacts"):
            (self.ws / d).mkdir(parents=True, exist_ok=True)
        url = brief_url(self.args.site, s["minutes"], self.args.lang)
        prompt = PROMPT[self.args.lang].format(url=url, model=s["name"])
        (self.ws / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        flags = pi_flags(self.args.image_window)
        cmd = [self.pi, *flags, "--session-dir", str(self.ws / "sessions"),
               "--model", s["ref"], "--thinking", s["thinking"],
               "--mode", "json", "-p", prompt]
        (self.ws / "README.md").write_text(
            f"# {s['name']} rep {s['rep']}\n\n"
            "Revisit the conversation in pi:\n\n"
            f"    pi --session-dir {self.ws / 'sessions'} --resume\n\n"
            "Re-export the trace:\n\n"
            f"    pi --export sessions/<file>.jsonl trace.html\n\n"
            "Rebuild and file the bundle again:\n\n"
            f"    {REPO / 'Scripts' / 'bench_jobs.py'} finish {self.ws}\n")
        self.manifest(
            harness="pi", piVersion=self.version, profile="stock",
            model={"ref": s["ref"], "thinkingLevel": s["thinking"]},
            agent=s["name"], minutes=s["minutes"], rep=s["rep"],
            batch=self.ws.parent.name,
            prompt={"language": self.args.lang, "url": url, "text": prompt},
            command=[c if c != prompt else "<prompt.txt>" for c in cmd],
            flags=flags, tools=["read", "bash", "edit", "write"],
            imageWindow=self.args.image_window or None,
            piConfig=config_digest(), piCompaction=pi_compaction(), status="ready")
        return cmd

    # run ----------------------------------------------------------------
    def run(self):
        cmd = self.prepare()
        self.started = time.time()
        self.manifest(status="running", startedAt=iso(self.started))
        events = open(self.ws / "events.jsonl", "a", encoding="utf-8")
        stderr = open(self.ws / "pi.stderr", "ab")
        env = scrubbed_env(self.spec["provider"])
        if self.args.image_window:
            env["PI_IMAGE_WINDOW"] = str(self.args.image_window)
        self.proc = subprocess.Popen(
            cmd, cwd=self.ws / "work", env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=stderr,
            start_new_session=True)
        self.tree = ProcTree(self.proc.pid)
        self.manifest(pid=self.proc.pid)
        reader = threading.Thread(target=self.read, args=(events,), daemon=True)
        reader.start()
        reason = self.watch()
        left = self.tree.kill()
        reader.join(timeout=10)
        events.close()
        stderr.close()
        ended = time.time()
        if reason is None:
            code = self.proc.returncode
            ends_at = self.session and self.session.get("ends_at")
            if self.session is None:
                reason = "no_session" if code == 0 else "pi_error"
            elif self.ended_seen or (ends_at and ended >= ends_at):
                reason = "finished"
            else:
                reason = "agent_stopped"
        self.outcome = reason
        self.manifest(status="done", outcome=reason, endedAt=iso(ended),
                      wall=round(ended - self.started, 1),
                      exitCode=self.proc.returncode, leftRunning=left,
                      session=self.public_session(), sessionsSeen=self.sessions_seen,
                      endedSeenAt=iso(self.ended_seen) if self.ended_seen else None,
                      piConfigAfter=config_digest())
        log(f"{self.ws.name}: {reason}"
            + (f", session {self.session['sid']}" if self.session else ""))

    def watch(self):
        """Wait for pi, and stop it when the run is over or never started."""
        start_deadline = self.started + self.args.start_timeout * 60
        while self.proc.poll() is None:
            if self.stop.wait(2.0):
                return "interrupted"
            self.tree.sample()
            now = time.time()
            if self.session is None:
                if now > start_deadline:
                    return "no_session"
                continue
            ends_at = self.session.get("ends_at") or (
                self.session["found"] + self.spec["minutes"] * 60)
            if now > ends_at + self.args.end_grace * 60:
                return "overtime"
            if self.ended_seen and now > self.ended_seen + 180:
                return "finished"
        return None

    def read(self, events):
        for raw in self.proc.stdout:
            now = time.time()
            try:
                ev = json.loads(raw)
            except ValueError:
                continue
            kind = ev.get("type")
            if kind == "tool_execution_end":
                text = result_text(ev.get("result"))
                self.spot_session(text, now)
                if re.search(r'"ended"\s*:\s*true', text) and self.session:
                    self.ended_seen = self.ended_seen or now
            out = compact_event(ev, now)
            if out is not None:
                events.write(json.dumps(out, ensure_ascii=False) + "\n")
                events.flush()

    def spot_session(self, text, now):
        for m in SESSION_URL.finditer(text):
            base, sid, token = m.group(1), m.group(2), m.group(3)
            if sid not in self.sessions_seen:
                self.sessions_seen.append(sid)
            if self.session is not None:
                continue
            agent = re.search(r'"agent"\s*:\s*"([^"]+)"', text)
            ends = re.search(r'"ends_at"\s*:\s*([0-9.]+)', text)
            self.session = {"base": base, "sid": sid, "token": token,
                            "agent": agent.group(1) if agent else self.spec["name"],
                            "ends_at": float(ends.group(1)) if ends else None,
                            "found": now}
            self.manifest(session=self.public_session(),
                          sessionToken=token)
            log(f"{self.ws.name}: session {sid} as {self.session['agent']}")

    def public_session(self):
        if not self.session:
            return None
        s = self.session
        return {"backend": s["base"], "id": s["sid"], "agent": s["agent"],
                "endsAt": iso(s["ends_at"]) if s["ends_at"] else None,
                "createdAfter": round(s["found"] - self.started, 1)}


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="seconds")


def brief_url(site, minutes, lang):
    site = site.rstrip("/") + "/"
    return f"{site}{'en/' if lang == 'en' else ''}{minutes}m/agents.md"


# ------------------------------------------------------------------ bundle

def session_files(ws):
    return sorted((ws / "sessions").glob("*.jsonl"))


def collect_artifacts(ws, sid):
    """Copy what the model wrote into the workspace. Symlinks are not followed:
    a link to ~/.ssh in the model's folder must not become a published file."""
    dest = ws / "artifacts"
    skipped = []
    sources = [(ws / "work", dest / "work")]
    if sid:
        sources.append((pathlib.Path("/tmp") / sid, dest / "tmp" / sid))
    for src, out in sources:
        if not src.is_dir():
            continue
        for root, dirs, files in os.walk(src, followlinks=False):
            rel = pathlib.Path(root).relative_to(src)
            for d in list(dirs):
                if d in SKIP_DIRS or (pathlib.Path(root) / d).is_symlink():
                    skipped.append(str(rel / d) + "/")
                    dirs.remove(d)
            for f in files:
                p = pathlib.Path(root) / f
                if p.is_symlink() or not p.is_file():
                    skipped.append(str(rel / f))
                    continue
                target = out / rel / f
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
    return skipped


def lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        yield from fh


def outside_writes(ws, sid):
    """Paths the model wrote with pi's own file tools outside its folder."""
    allowed = [str(ws / "work")] + ([f"/tmp/{sid}", f"/private/tmp/{sid}"] if sid else [])
    out = []
    for f in session_files(ws):
        for line in lines(f):
            if '"toolCall"' not in line:
                continue
            try:
                msg = json.loads(line).get("message") or {}
            except ValueError:
                continue
            for c in msg.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "toolCall" \
                        and c.get("name") in ("write", "edit"):
                    path = str((c.get("arguments") or {}).get("path", ""))
                    full = path if path.startswith("/") else str(ws / "work" / path)
                    if path and not any(full.startswith(a) for a in allowed):
                        out.append(path)
    return sorted(set(out))


def last_error(ws):
    """The provider's last error message, if a turn ended on one: a run that
    stops because every request is refused says why here."""
    ev, out = ws / "events.jsonl", None
    if ev.exists():
        for line in lines(ev):
            if '"error"' in line and '"message_end"' in line:
                try:
                    out = json.loads(line).get("error") or out
                except ValueError:
                    pass
    return out[:300] if out else None


def trace_stats(ws):
    """Counts from pi's session file and event stream, for the summary."""
    tools, errors, compactions, retries = {}, 0, 0, 0
    for f in session_files(ws):
        for line in lines(f):
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") == "compaction":
                compactions += 1
            msg = entry.get("message") or {}
            if msg.get("role") == "assistant":
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "toolCall":
                        tools[c.get("name")] = tools.get(c.get("name"), 0) + 1
            elif msg.get("role") == "toolResult" and msg.get("isError"):
                errors += 1
    ev = ws / "events.jsonl"
    if ev.exists():
        for line in lines(ev):
            if '"auto_retry_start"' in line:
                retries += 1
    return {"toolCalls": tools, "toolErrors": errors,
            "compactions": compactions, "retries": retries}


def build_bundle(ws, pi):
    """Redact, export, zip. Returns the summary to publish."""
    run = json.loads((ws / "run.json").read_text())
    sid = (run.get("session") or {}).get("id")
    redact = Redactor(secret_values(), run.get("sessionToken"))
    skipped = collect_artifacts(ws, sid)

    # the provider's meter, summed by the repo's existing reader
    usage = None
    r = subprocess.run(["node", str(REPO / "Scripts" / "pi-usage.mjs"), str(ws)],
                       capture_output=True, text=True)
    if r.returncode == 0 and (ws / "usage.json").exists():
        usage = json.loads((ws / "usage.json").read_text())

    stage = ws / "bundle"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir()
    dropped = []

    def put_text(src, rel):
        out = stage / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(redact.text(src.read_text(encoding="utf-8", errors="replace")),
                       encoding="utf-8")

    public_run = {k: v for k, v in run.items() if k != "sessionToken"}
    (stage / "run.json").write_text(
        redact.text(json.dumps(public_run, indent=2, ensure_ascii=False)) + "\n")
    for name in ("prompt.txt", "events.jsonl", "pi.stderr", "usage.json", "README.md"):
        if (ws / name).exists():
            put_text(ws / name, name)
    for f in session_files(ws):
        put_text(f, f"sessions/{f.name}")

    total = 0
    files = []
    art = ws / "artifacts"
    for p in sorted(art.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ws)
        size = p.stat().st_size
        if size > ARTIFACT_FILE_LIMIT or total + size > ARTIFACT_TOTAL_LIMIT:
            dropped.append(f"{rel} (size)")
            continue
        data = p.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        out = stage / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if text is not None:
            out.write_text(redact.text(text), encoding="utf-8")
        elif redact.leaks(data):
            dropped.append(f"{rel} (credential)")
            continue
        else:
            out.write_bytes(data)
        total += size
        files.append([str(p.relative_to(art)), size])

    # pi's own viewer, made from the redacted copy of the session
    trace = None
    staged = sorted((stage / "sessions").glob("*.jsonl"))
    if staged:
        r = subprocess.run([pi, "--export", str(staged[-1]), str(ws / "trace.html")],
                           capture_output=True, text=True, cwd=ws)
        if r.returncode == 0 and (ws / "trace.html").exists():
            trace = ws / "trace.html"
            html = trace.read_text(encoding="utf-8", errors="replace")
            trace.write_text(redact.text(html), encoding="utf-8")

    # the last line of defence: no credential in any byte that leaves
    for p in stage.rglob("*"):
        if p.is_file() and redact.leaks(p.read_bytes()):
            dropped.append(f"{p.relative_to(stage)} (credential after redaction)")
            p.unlink()

    zpath = ws / "bundle.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage),
                        compress_type=zipfile.ZIP_STORED
                        if p.suffix.lower() in STORED else zipfile.ZIP_DEFLATED)

    stats = trace_stats(ws)
    summary = {
        "harness": "pi", "piVersion": run.get("piVersion"), "profile": "stock",
        "model": run["model"]["ref"], "thinkingLevel": run["model"]["thinkingLevel"],
        "language": run["prompt"]["language"], "minutes": run.get("minutes"),
        "rep": run.get("rep"), "batch": run.get("batch"),
        "flags": run.get("flags"), "tools": run.get("tools"),
        "compaction": run.get("piCompaction"),
        "imageWindow": run.get("imageWindow"),
        "lastError": last_error(ws),
        "outcome": run.get("outcome"), "wall": run.get("wall"),
        "createdAfter": (run.get("session") or {}).get("createdAfter"),
        "sessionsSeen": run.get("sessionsSeen"),
        **stats,
        "tokens": None if usage is None else {
            k: usage.get(k) for k in ("input", "output", "cacheRead", "cacheWrite",
                                      "totalTokens", "cost", "turns")},
        "artifacts": {"files": len(files), "bytes": total,
                      "top": sorted(files, key=lambda f: -f[1])[:40],
                      "skipped": (skipped + dropped)[:40]},
        "outsideWrites": outside_writes(ws, sid)[:20],
        "bundleBytes": zpath.stat().st_size,
        "bundleSha256": hashlib.sha256(zpath.read_bytes()).hexdigest(),
    }
    (ws / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary, usage, trace


# ------------------------------------------------------------------ upload

def http(method, url, body=None, headers=None, timeout=60):
    data = None
    headers = dict(headers or {})
    if body is not None and not isinstance(body, (bytes, bytearray)):
        data = json.dumps(body).encode()
        headers.setdefault("Content-Type", "application/json")
    elif body is not None:
        data = body
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw[:1] in (b"{", b"[") else raw.decode())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw.decode(errors="replace")


def put_file(put_url, path, mime):
    """One PUT of the whole file to its upload address (a GCS resumable
    session, or the local broker), streamed from disk."""
    size = path.stat().st_size
    with open(path, "rb") as fh:
        req = urllib.request.Request(put_url, data=fh, method="PUT", headers={
            "Content-Type": mime, "Content-Length": str(size)})
        try:
            with urllib.request.urlopen(req, timeout=3600) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code


def upload(ws, summary, usage, trace, wait_for_end=True, stop=None):
    run = json.loads((ws / "run.json").read_text())
    s = run.get("session")
    if not s or not run.get("sessionToken"):
        log(f"{ws.name}: no session, nothing to file")
        return {"ok": False, "why": "no session"}
    base = f"{s['backend']}/s/{s['id']}/t/{run['sessionToken']}"
    hdr = {"X-Agent": canonical_agent_name(s["agent"])}
    report = {"files": {}}
    for name, path in (("bundle.zip", ws / "bundle.zip"), ("trace.html", trace)):
        if not path or not path.exists():
            continue
        code, body = http("POST", f"{base}/harness/upload",
                          {"name": name, "size": path.stat().st_size}, hdr)
        if code != 200 or not isinstance(body, dict) or not body.get("put_url"):
            report["files"][name] = {"code": code, "error": str(body)[:300]}
            continue
        status = put_file(body["put_url"], path, body["content_type"])
        report["files"][name] = {"code": status, "path": body.get("path")}
        log(f"{ws.name}: uploaded {name} ({path.stat().st_size >> 10} KB) -> {status}")
    # The catalogue entry exists only once the run is over and published, so
    # the summary and the meter are filed after the session's clock.
    ends = s.get("endsAt")
    if wait_for_end and ends:
        until = dt.datetime.fromisoformat(ends).timestamp() + 60
        while time.time() < until and not (stop and stop.is_set()):
            time.sleep(min(30, max(1, until - time.time())))
    code, body = http("POST", f"{base}/harness", summary, hdr)
    report["harness"] = {"code": code, "body": body}
    if usage is not None:
        code, body = http("POST", f"{base}/usage", usage, hdr)
        report["usage"] = {"code": code, "body": body}
    (ws / "upload.json").write_text(json.dumps(report, indent=2) + "\n")
    ok = report["harness"]["code"] in (200, 202)
    log(f"{ws.name}: harness record {'filed' if ok else 'refused'} "
        f"({report['harness']['code']})")
    return report


# ------------------------------------------------------------------ planning

def ask(prompt, default=None, check=None):
    while True:
        tail = f" [{default}]" if default is not None else ""
        try:
            got = input(f"{prompt}{tail}: ").strip()
        except EOFError:
            sys.exit(1)
        value = got or (str(default) if default is not None else "")
        if not value:
            continue
        if check is None:
            return value
        try:
            return check(value)
        except ValueError as e:
            print(f"  {e}")


def pick(text, n):
    if text.strip().lower() == "all":
        return list(range(n))
    out = []
    for part in text.replace(" ", "").split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a) - 1, int(b)))
        elif part:
            out.append(int(part) - 1)
    if not out or any(i < 0 or i >= n for i in out):
        raise ValueError(f"numbers between 1 and {n}")
    return list(dict.fromkeys(out))


def minutes_ok(v):
    """The published site has a brief for a few playtimes only; a local site
    built for testing may serve any."""
    m = int(v)
    if MINUTES_FREE and 1 <= m <= 1440:
        return m
    if m not in OPTIONS:
        raise ValueError(f"a playtime with a brief: {sorted(OPTIONS)}")
    return m


MINUTES_FREE = False


def reps_ok(v):
    r = int(v)
    if not 1 <= r <= 50:
        raise ValueError("1 to 50")
    return r


def level_ok(v):
    if v not in THINKING:
        raise ValueError(" / ".join(THINKING))
    return v


def name_ok(v):
    n = canonical_agent_name(v)
    if not n:
        raise ValueError("letters, digits and -_. only")
    return n


def default_name(model, thinking):
    return canonical_agent_name(f"{model['id'].lower()}-{thinking}")


def interactive_plan(models, args):
    print(f"\n{len(models)} models in this pi install:\n")
    for i, m in enumerate(models, 1):
        note = "" if m["images"] else "  (no image input: cannot see the screen)"
        print(f"  {i:>2}  {m['ref']:<44} {m['context']:>7} ctx"
              f"  thinking {'yes' if m['thinking'] else 'no '}{note}")
    chosen = ask("\nModels to bench (e.g. 1,3-4 or all)", check=lambda v: pick(v, len(models)))
    specs = []
    minutes, reps = args.minutes, args.reps
    for i in chosen:
        m = models[i]
        print(f"\n{m['ref']}")
        minutes = ask("  minutes per run", minutes, minutes_ok)
        reps = ask("  repetitions", reps, reps_ok)
        level = ask("  thinking", args.thinking if m["thinking"] else "off", level_ok)
        name = ask("  agent name", default_name(m, level), name_ok)
        specs.append(dict(m, minutes=minutes, reps=reps, thinking=level, name=name))
    args.image_window = ask("\nImages per request (turn = the latest turn's, N = newest N, "
                            "0 = every image, stock pi)", args.image_window, window_ok)
    return specs


def window_ok(v):
    """'turn' keeps the images of the model's latest turn; N the newest N;
    0 is stock pi, which keeps them all."""
    if str(v).strip().lower() == "turn":
        return "turn"
    try:
        n = int(v)
    except ValueError:
        raise ValueError("turn, or a number from 0 to 3000")
    if not 0 <= n <= 3000:
        raise ValueError("turn, or a number from 0 to 3000")
    return n


def flag_plan(models, args):
    by_ref = {m["ref"]: m for m in models}
    specs = []
    for i, ref in enumerate(args.model):
        if ref not in by_ref:
            sys.exit(f"{ref} is not in `pi --list-models`")
        m = by_ref[ref]
        level = level_ok(args.thinking if m["thinking"] else "off")
        name = name_ok(args.name[i]) if args.name and i < len(args.name) \
            else default_name(m, level)
        specs.append(dict(m, minutes=minutes_ok(args.minutes), reps=reps_ok(args.reps),
                          thinking=level, name=name))
    return specs


def expand(specs):
    """Jobs in the order they run: every model's first repetition, then the
    second, so the repetitions of one model are spread across the batch."""
    jobs = []
    for rep in range(1, max(s["reps"] for s in specs) + 1):
        for s in specs:
            if rep <= s["reps"]:
                jobs.append(dict(s, rep=rep))
    return jobs


# ------------------------------------------------------------------ main

class Batch:
    def __init__(self, jobs, args, pi, version):
        self.args = args
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.dir = pathlib.Path(args.runs_dir).expanduser() / stamp
        self.dir.mkdir(parents=True, exist_ok=True)
        self.jobs = [Job(self.dir / f"{i:02d}-{j['name']}-r{j['rep']}", j, args, pi, version)
                     for i, j in enumerate(jobs, 1)]
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.busy = {}          # provider -> running jobs
        self.uploads = []
        self.digest = config_digest()

    def interrupt(self, *_):
        if self.stop.is_set():
            log("second interrupt: killing every job now")
            for j in self.jobs:
                if j.tree:
                    j.tree.kill(grace=1)
            os._exit(130)
        log("interrupted: stopping running jobs, then bundling what they left")
        self.stop.set()
        for j in self.jobs:
            j.stop.set()

    def run(self):
        pending = list(self.jobs)
        threads = []
        while pending and not self.stop.is_set():
            with self.lock:
                for j in list(pending):
                    p = j.spec["provider"]
                    if self.busy.get(p, 0) < self.args.per_provider:
                        self.busy[p] = self.busy.get(p, 0) + 1
                        pending.remove(j)
                        t = threading.Thread(target=self.one, args=(j,))
                        t.start()
                        threads.append(t)
            time.sleep(1)
        for t in threads:
            t.join()
        for t in self.uploads:
            t.join()
        self.report(pending)

    def one(self, job):
        try:
            log(f"start {job.ws.name}: {job.spec['ref']} {job.spec['minutes']} min")
            job.run()
        except Exception as exc:  # a broken job must not take the batch down
            log(f"{job.ws.name}: failed: {exc!r}")
            if job.tree:
                job.tree.kill()
            job.manifest(status="done", outcome="runner_error", error=repr(exc))
        finally:
            with self.lock:
                self.busy[job.spec["provider"]] -= 1
        t = threading.Thread(target=self.finish, args=(job,))
        t.start()
        self.uploads.append(t)

    def finish(self, job):
        try:
            summary, usage, trace = build_bundle(job.ws, job.pi)
            log(f"{job.ws.name}: bundle {summary['bundleBytes'] >> 10} KB, "
                f"{summary['artifacts']['files']} artifacts")
            if not self.args.no_upload:
                upload(job.ws, summary, usage, trace,
                       wait_for_end=not self.stop.is_set(), stop=self.stop)
        except Exception as exc:
            log(f"{job.ws.name}: bundle/upload failed: {exc!r}")

    def report(self, pending):
        rows = []
        for j in self.jobs:
            run = json.loads((j.ws / "run.json").read_text()) if (j.ws / "run.json").exists() else {}
            up = j.ws / "upload.json"
            filed = json.loads(up.read_text()).get("harness", {}).get("code") if up.exists() else None
            rows.append({"job": j.ws.name, "outcome": run.get("outcome", "not run"),
                         "session": (run.get("session") or {}).get("id"),
                         "filed": filed})
        (self.dir / "batch.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(f"\nbatch {self.dir}")
        for r in rows:
            print(f"  {r['job']:<44} {r['outcome']:<14} {r['session'] or '-':<13} "
                  f"filed {r['filed'] or '-'}")
        after = config_digest()
        if after != self.digest:
            print(f"warning: pi config changed during the batch: {self.digest} -> {after}")
        else:
            print("pi config unchanged (settings.json, models.json, auth.json)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", nargs="?", default="run", choices=("run", "finish"))
    ap.add_argument("job_dir", nargs="?")
    ap.add_argument("--model", action="append", default=[],
                    help="provider/id from `pi --list-models`; repeat for several")
    ap.add_argument("--name", action="append", default=[],
                    help="agent name per --model (default <id>-<thinking>)")
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--thinking", default="high")
    ap.add_argument("--image-window", type=window_ok, default="turn",
                    help="images sent per request: turn (default) keeps what the model "
                         "read in its latest turn and drops screens from earlier turns; "
                         "N keeps the newest N; 0 is stock pi, which resends every image "
                         "and fails past a provider's per-request image limit")
    ap.add_argument("--lang", default="zh", choices=("zh", "en"))
    ap.add_argument("--site", default=SITE, help="where the briefs are served")
    ap.add_argument("--runs-dir", default="~/jy-crpg-runs")
    ap.add_argument("--per-provider", type=int, default=1,
                    help="jobs at once on one provider (different providers run together)")
    ap.add_argument("--start-timeout", type=float, default=20,
                    help="minutes for the model to create its session")
    ap.add_argument("--end-grace", type=float, default=10,
                    help="minutes past the session's end before pi is stopped")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--no-wait", action="store_true",
                    help="finish: file the summary now instead of after the run's end")
    ap.add_argument("--yes", action="store_true", help="start without asking")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pi", default=shutil.which("pi") or "pi")
    args = ap.parse_args()

    if args.command == "finish":
        if not args.job_dir:
            sys.exit("finish needs a job directory")
        ws = pathlib.Path(args.job_dir).expanduser().resolve()
        summary, usage, trace = build_bundle(ws, args.pi)
        print(json.dumps({k: summary[k] for k in ("outcome", "tokens", "toolCalls",
                                                  "bundleBytes")}, indent=2))
        if not args.no_upload:
            upload(ws, summary, usage, trace, wait_for_end=not args.no_wait)
        return

    global MINUTES_FREE
    MINUTES_FREE = args.site.rstrip("/") != SITE.rstrip("/")
    version = pi_version(args.pi)
    if version_tuple(version) < MIN_PI_VERSION:
        sys.exit(f"pi {version} is older than {'.'.join(map(str, MIN_PI_VERSION))}, "
                 "the oldest this runner is verified with; update pi first")
    models = pi_models(args.pi)
    print(f"pi {version} at {args.pi}")
    specs = flag_plan(models, args) if args.model else interactive_plan(models, args)
    jobs = expand(specs)
    print(f"\n{len(jobs)} jobs, {sum(j['minutes'] for j in jobs)} minutes of play:")
    for j in jobs:
        print(f"  {j['name']:<36} {j['ref']:<44} {j['minutes']:>4} min  rep {j['rep']}")
    print(f"pi runs with {' '.join(pi_flags(args.image_window))}, tools read,bash,edit,write; "
          f"~/.pi is not edited")
    w = args.image_window
    print("images per request: " + ("those of the model's latest turn" if w == "turn"
                                    else f"newest {w}" if w else "all (stock pi)"))
    if args.dry_run:
        return
    if not args.yes and ask("Start?", "y").lower() not in ("y", "yes"):
        return
    batch = Batch(jobs, args, args.pi, version)
    signal.signal(signal.SIGINT, batch.interrupt)
    signal.signal(signal.SIGTERM, batch.interrupt)
    signal.signal(signal.SIGHUP, batch.interrupt)
    log(f"batch {batch.dir}")
    batch.run()


if __name__ == "__main__":
    main()
