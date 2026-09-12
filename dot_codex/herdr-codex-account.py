"""Report Codex quota only while the pane still belongs to this invocation."""

import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid


class Reporter:
    def __init__(self, env, usage_command=None):
        self.env = env
        self.pane = env["HERDR_PANE_ID"]
        self.owner = env.get("HERDR_CODEX_RUN_ID", "")
        self.usage_command = usage_command or str(Path.home() / ".local/bin/codex-usage")
        # IDs are unique within one server. Use the inherited ID so hooks and
        # their shell wrapper agree even after a pane move.
        key = hashlib.sha256(
            f'{env.get("HERDR_SOCKET_PATH", "")}\0{self.pane}'.encode()
        ).hexdigest()
        cache = Path(env.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
        self.state_path = cache / "herdr-codex" / f"{key}.json"

    @contextmanager
    def locked(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        # Never unlink the lock: two different lock inodes could allow a
        # delayed writer to race with clear or the next launch.
        with self.state_path.with_suffix(".lock").open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

            def save():
                # A cancelled hook must not leave a truncated owner record.
                with tempfile.NamedTemporaryFile(mode="w", dir=self.state_path.parent,
                                                 delete=False) as output:
                    json.dump(state, output)
                os.replace(output.name, self.state_path)

            yield state, save

    @staticmethod
    def sequence(state):
        state["seq"] = max(state.get("seq", 0) + 1, time.time_ns())
        return state["seq"]

    def report(self, seq, *, label=None, account=None, launch=None, clear=False,
               live=False, startup=False):
        args = ["herdr", "pane", "report-metadata", self.pane,
                "--source", "codex-account", "--seq", str(seq)]
        if clear:
            # --agent would cause Herdr to reject token cleanup after exit.
            args += ["--clear-display-agent", "--clear-token", "launch",
                     "--clear-token", "account"]
        else:
            if live:
                args += ["--agent", "codex"]
            if startup:
                # Bound the unguarded preview if the shell dies before the
                # first prompt / SessionStart can attach a live-agent guard.
                args += ["--ttl-ms", "60000"]
            if label is not None:
                args += ["--display-agent", label]
            args += ["--token", f"launch={launch}"]
            args += (["--token", f"account={account}"] if account else
                     ["--clear-token", "account"])
        # Hold the lock through the report, so ownership cannot change between
        # its check and the write to Herdr. Never hold it during a usage fetch.
        try:
            subprocess.run(args, env=self.env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=0.75, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def home(self, event):
        if self.env.get("CODEX_HOME"):
            return Path(self.env["CODEX_HOME"])
        transcript = event.get("transcript_path") or ""
        if "/sessions/" in transcript:
            return Path(transcript.split("/sessions/", 1)[0])
        return Path.home() / ".codex"

    @staticmethod
    def identity(home):
        launch = "wcodex" + home.name.removeprefix(".codex_work") if home.name.startswith(".codex_work") else "codex"
        try:
            auth = json.loads((home / "auth.json").read_text())
            token = auth["tokens"]["id_token"]
            if not isinstance(token, str):
                return launch, None
            payload = token.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            plan = claims["https://api.openai.com/auth"]["chatgpt_plan_type"]
            if not isinstance(plan, str):
                return launch, None
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            return launch, None
        return launch, {"pro": "Pro 20x", "prolite": "Pro 5x", "plus": "Plus",
                        "self_serve_business_prolite": "Business"}.get(plan, plan)

    def usage(self, home, cached=False):
        args = [self.usage_command, "--codex-home", str(home), "--compact"]
        if cached:
            args += ["--cache-only"]
        try:
            result = subprocess.run(args, env=self.env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True,
                                    timeout=1 if cached else 22, check=False)
            return result.stdout.strip() if result.returncode == 0 else ""
        except (OSError, subprocess.TimeoutExpired):
            return ""

    def start(self):
        home = self.home({})
        launch, account = self.identity(home)
        usage = self.usage(home, cached=True)
        owner = uuid.uuid4().hex
        with self.locked() as (state, save):
            state.update(owner=owner, session_id="", active=True, closed=False)
            seq = self.sequence(state)
            state["request"] = seq
            save()
            self.report(seq, label=f"{launch} · {usage}" if usage else launch,
                        account=account, launch=launch, startup=True)
        return owner

    def matches(self, state, event, *, active=True):
        if active and not state.get("active"):
            return False
        if self.owner and self.owner != state.get("owner"):
            return False
        session = event.get("session_id")
        if session and state.get("session_id") != session:
            return False
        return bool(self.owner or session)

    def clear(self, event):
        with self.locked() as (state, save):
            if not self.matches(state, event, active=False):
                return
            state["active"] = False
            if not event:
                state["closed"] = True
            seq = self.sequence(state)
            save()
            self.report(seq, clear=True)

    def refresh(self, event):
        session = event.get("session_id")
        if not session or event.get("source") == "compact":
            return
        inherited = self.env.get("CODEX_THREAD_ID")
        if inherited and inherited != session:
            return
        starting = event["hook_event_name"] == "SessionStart"
        home = self.home(event)
        launch, account = self.identity(home)
        with self.locked() as (state, save):
            if self.owner:
                if self.owner != state.get("owner") or state.get("closed"):
                    return
                # /new can end a thread while keeping the same CLI alive.
                # A startup left over from the ended thread stays rejected;
                # an explicit /resume can reopen it without restarting the CLI.
                if starting and (state.get("session_id") != session
                                 or event.get("source") == "resume"):
                    state["active"] = True
                if starting or not state.get("session_id"):
                    state["session_id"] = session
            elif starting:
                # Direct launches bypassing the wrapper still get an owner
                # captured by each fetch, plus SessionEnd cleanup.
                if not state.get("active") or state.get("session_id") != session:
                    state.update(owner=uuid.uuid4().hex, session_id=session, active=True)
            if not self.matches(state, event):
                return
            if starting:
                seq = self.sequence(state)
                save()
                self.report(seq, label=launch, account=account, launch=launch, live=True)
            owner = state["owner"]
            ticket = self.sequence(state)
            state["request"] = ticket
            save()

        # No detached processes: Codex owns this async hook and cancels it on
        # session end. The lock is not held during the network request.
        usage = self.usage(home)
        if not usage:
            return
        with self.locked() as (state, save):
            if (not self.matches(state, event) or state.get("owner") != owner
                    or state.get("request") != ticket):
                return
            self.report(ticket, label=f"{launch} · {usage}", account=account,
                        launch=launch, live=True)


def main():
    if os.environ.get("HERDR_ENV") != "1" or not os.environ.get("HERDR_PANE_ID"):
        return
    reporter = Reporter(dict(os.environ))
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "start":
        print(reporter.start())
    elif action == "clear":
        reporter.clear({})
    elif not action and not sys.stdin.isatty():
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            return
        if event.get("hook_event_name") == "SessionEnd":
            reporter.clear(event)
        elif event.get("hook_event_name") in {"SessionStart", "Stop"}:
            reporter.refresh(event)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.TimeoutExpired):
        # Metadata must never block launching Codex or produce hook output.
        pass
