"""Quota lifecycle regressions; Herdr and network fetches are local stubs."""

import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "codex_account", ROOT / "dot_codex/herdr-codex-account.py"
)
account = importlib.util.module_from_spec(spec)
spec.loader.exec_module(account)


def wait_for(predicate):
    deadline = time.monotonic() + 5
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("Timed out waiting for test fixture")
        time.sleep(0.01)


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.home = self.root / ".codex_work1"
        self.home.mkdir()
        payload = base64.urlsafe_b64encode(json.dumps({
            "https://api.openai.com/auth": {"chatgpt_plan_type": "pro"}
        }).encode()).decode().rstrip("=")
        (self.home / "auth.json").write_text(json.dumps({
            "tokens": {"id_token": f"test.{payload}.test"}
        }))
        self.env = dict(os.environ, HERDR_ENV="1", HERDR_PANE_ID="test-pane",
                        HERDR_SOCKET_PATH="test-server", CODEX_HOME=str(self.home),
                        XDG_CACHE_HOME=str(self.root / "cache"), MOCK_DIR=str(self.root),
                        PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        self.env.pop("HERDR_CODEX_RUN_ID", None)
        self.env.pop("CODEX_THREAD_ID", None)
        self.executable("herdr", '''import fcntl, json, os, pathlib, sys
with open(pathlib.Path(os.environ['MOCK_DIR']) / 'reports.jsonl', 'a') as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    f.write(json.dumps(sys.argv[1:]) + '\\n')
''')
        self.usage = self.executable("usage", '''import os, pathlib, sys, time
root = pathlib.Path(os.environ['MOCK_DIR'])
if '--cache-only' in sys.argv:
    print('W cached')
else:
    label = os.environ.get('MOCK_FETCH', 'live')
    (root / (label + '.ready')).touch()
    if os.environ.get('MOCK_WAIT'):
        deadline = time.monotonic() + 5
        while not (root / (label + '.release')).exists():
            if time.monotonic() > deadline:
                raise SystemExit(1)
            time.sleep(0.01)
    if not os.environ.get('MOCK_FAIL'):
        print('W ' + label)
    else:
        raise SystemExit(1)
''')
        self.pool = ThreadPoolExecutor(max_workers=3)
        self.addCleanup(self.pool.shutdown, wait=True)

    def executable(self, name, source):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + source)
        path.chmod(0o755)
        return str(path)

    def reporter(self, **extra):
        return account.Reporter(dict(self.env, **extra), usage_command=self.usage)

    def start(self):
        owner = self.reporter().start()
        self.env["HERDR_CODEX_RUN_ID"] = owner
        return self.reporter()

    def event(self, name="SessionStart", session="session-a", **extra):
        return dict(hook_event_name=name, session_id=session, source="startup", **extra)

    def reports(self):
        path = self.root / "reports.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def pending(self, reporter, event, label):
        reporter.env = dict(reporter.env, MOCK_FETCH=label, MOCK_WAIT="1")
        task = self.pool.submit(reporter.refresh, event)
        wait_for(lambda: (self.root / f"{label}.ready").exists())
        return task

    def release(self, task, label):
        (self.root / f"{label}.release").touch()
        task.result(timeout=5)

    def test_start_only_reads_cache_and_clear_works_before_first_prompt(self):
        reporter = self.start()
        args = self.reports()[-1]
        self.assertIn("wcodex1 · W cached", args)
        self.assertIn("--ttl-ms", args)
        self.assertNotIn("--agent", args)
        self.assertFalse((self.root / "live.ready").exists())
        reporter.clear({})
        args = self.reports()[-1]
        self.assertIn("--clear-display-agent", args)
        self.assertIn("account", args)
        self.assertIn("launch", args)
        self.assertNotIn("--agent", args)

    def test_late_fetch_cannot_restore_cleared_label(self):
        reporter = self.start()
        task = self.pending(reporter, self.event(), "old")
        self.reporter().clear(self.event("SessionEnd"))
        cleared = self.reports()
        self.release(task, "old")
        self.assertEqual(self.reports(), cleared)
        self.assertIn("--clear-display-agent", cleared[-1])

    def test_newest_request_wins_when_fetches_finish_backwards(self):
        self.start()
        task = self.pending(self.reporter(), self.event(), "old")
        self.reporter(MOCK_FETCH="new").refresh(self.event("Stop"))
        latest = self.reports()
        self.release(task, "old")
        self.assertEqual(self.reports(), latest)
        self.assertIn("wcodex1 · W new", latest[-1])
        seqs = [int(args[args.index("--seq") + 1]) for args in latest]
        self.assertEqual(seqs, sorted(set(seqs)))

    def test_same_session_resume_rejects_old_fetch_and_old_cleanup(self):
        old = self.start()
        task = self.pending(old, self.event(), "old")
        old.clear({})
        new = self.start()
        new.refresh(self.event())
        latest = self.reports()
        self.release(task, "old")
        old.clear(self.event("SessionEnd"))
        old.clear({})
        old.refresh(self.event())
        self.assertEqual(self.reports(), latest)

    def test_direct_launch_gets_session_end_cleanup(self):
        reporter = self.reporter()
        task = self.pending(reporter, self.event(), "direct")
        self.reporter().clear(self.event("SessionEnd"))
        cleared = self.reports()
        self.release(task, "direct")
        self.assertEqual(self.reports(), cleared)

    def test_old_session_end_does_not_clear_new_session_in_same_cli(self):
        reporter = self.start()
        reporter.refresh(self.event())
        reporter.refresh(self.event(session="session-b"))
        latest = self.reports()
        reporter.clear(self.event("SessionEnd"))
        self.assertEqual(self.reports(), latest)

    def test_new_thread_can_start_after_session_end_with_same_wrapper(self):
        reporter = self.start()
        reporter.refresh(self.event())
        reporter.clear(self.event("SessionEnd"))
        cleared = self.reports()
        reporter.refresh(self.event())
        self.assertEqual(self.reports(), cleared)
        reporter.refresh(self.event(session="session-b"))
        self.assertIn("wcodex1 · W live", self.reports()[-1])

    def test_explicit_resume_can_reopen_ended_thread_in_same_cli(self):
        reporter = self.start()
        reporter.refresh(self.event())
        reporter.clear(self.event("SessionEnd"))
        event = self.event()
        event["source"] = "resume"
        reporter.refresh(event)
        self.assertIn("wcodex1 · W live", self.reports()[-1])

    def test_clear_cannot_slip_between_ownership_check_and_report(self):
        reporter = self.start()
        before_write = threading.Event()
        allow_write = threading.Event()
        original = reporter.report

        def paused(seq, **fields):
            if fields.get("label", "").endswith("W live"):
                before_write.set()
                if not allow_write.wait(timeout=3):
                    raise AssertionError("Test did not release the report")
            original(seq, **fields)

        reporter.report = paused
        writing = self.pool.submit(reporter.refresh, self.event())
        self.assertTrue(before_write.wait(timeout=3))
        clear_started = threading.Event()

        def clear():
            clear_started.set()
            self.reporter().clear({})

        clearing = self.pool.submit(clear)
        self.assertTrue(clear_started.wait(timeout=3))
        try:
            self.assertFalse(clearing.done())
        finally:
            allow_write.set()
        writing.result(timeout=3)
        clearing.result(timeout=3)
        self.assertIn("--clear-display-agent", self.reports()[-1])

    def test_live_updates_have_agent_guard_without_expiry(self):
        reporter = self.start()
        reporter.refresh(self.event())
        for args in self.reports()[1:]:
            self.assertEqual(args[args.index("--agent") + 1], "codex")
            self.assertNotIn("--ttl-ms", args)

    def test_failed_stop_fetch_preserves_existing_quota(self):
        reporter = self.start()
        reporter.refresh(self.event())
        latest = self.reports()
        self.reporter(MOCK_FAIL="1").refresh(self.event("Stop"))
        self.assertEqual(self.reports(), latest)

    def test_compaction_and_subagents_do_not_change_main_label(self):
        reporter = self.start()
        latest = self.reports()
        event = self.event()
        event["source"] = "compact"
        reporter.refresh(event)
        self.reporter(CODEX_THREAD_ID="parent").refresh(self.event())
        self.assertEqual(self.reports(), latest)

    def test_server_identity_separates_same_pane_ids(self):
        reporter = self.start()
        other = self.reporter(HERDR_SOCKET_PATH="other-server")
        self.assertNotEqual(reporter.state_path, other.state_path)

    def test_home_falls_back_to_transcript_and_missing_auth_is_supported(self):
        reporter = self.reporter(CODEX_HOME="")
        home = reporter.home({"transcript_path": str(self.home / "sessions/file.jsonl")})
        self.assertEqual(home, self.home)
        self.assertEqual(reporter.identity(home), ("wcodex1", "Pro 20x"))
        (self.home / "auth.json").unlink()
        self.assertEqual(reporter.identity(home), ("wcodex1", None))
        (self.home / "auth.json").write_text('{"tokens": {"id_token": null}}')
        self.assertEqual(reporter.identity(home), ("wcodex1", None))


class HookConfigTests(unittest.TestCase):
    def render(self, current):
        return subprocess.run(
            ["chezmoi", "execute-template", "--with-stdin", "--file",
             str(ROOT / "dot_codex/modify_hooks.json")], input=current,
            capture_output=True, text=True, check=True, cwd=ROOT,
        ).stdout

    def test_new_config_has_managed_async_updates_and_sync_cleanup(self):
        config = json.loads(self.render(""))["hooks"]
        for event in ("SessionStart", "Stop", "SessionEnd"):
            hook = config[event][0]["hooks"][0]
            self.assertEqual(hook["async"], event != "SessionEnd")
            self.assertEqual(hook["timeout"], 3 if event == "SessionEnd" else 25)

    def test_migration_preserves_other_hooks_and_their_indices(self):
        command = json.loads(self.render(""))["hooks"]["Stop"][0]["hooks"][0]["command"]
        before = {"description": "keep", "hooks": {"Stop": [
            {"matcher": "keep", "hooks": [
                {"command": "first", "type": "command", "timeout": 7},
                {"command": command, "type": "command", "timeout": 5},
                {"command": "third", "type": "command", "async": True}]},
            {"hooks": [{"command": "last", "type": "command"}]}],
            "PreToolUse": [{"hooks": [{"command": "untouched"}]}]}}
        result = json.loads(self.render(json.dumps(before)))
        expected = json.loads(json.dumps(before))
        expected["hooks"]["Stop"][0]["hooks"][1].update(timeout=25, **{"async": True})
        self.assertEqual(result["hooks"]["Stop"], expected["hooks"]["Stop"])
        self.assertEqual(result["hooks"]["PreToolUse"], before["hooks"]["PreToolUse"])
        self.assertEqual(result["description"], "keep")

    def test_second_render_is_byte_identical(self):
        first = self.render("")
        self.assertEqual(self.render(first), first)


class CacheTests(unittest.TestCase):
    def test_cache_only_without_credentials_and_missing_or_expired_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / "no-credentials"
            cache = root / "cache/codex-usage"
            cache.mkdir(parents=True)
            key = hashlib.sha256(str(codex_home).encode()).hexdigest()[:8]
            cached = cache / f"{key}.json"
            env = dict(os.environ, XDG_CACHE_HOME=str(root / "cache"))
            args = ["bash", str(ROOT / "dot_local/bin/executable_codex-usage"),
                    "--codex-home", str(codex_home), "--cache-only", "--compact"]
            def run():
                return subprocess.run(args, env=env, capture_output=True, text=True, timeout=3)
            self.assertEqual(run().returncode, 1)
            cached.write_text(json.dumps({"rate_limit": {"primary_window": {
                "used_percent": 14, "limit_window_seconds": 18000,
                "reset_at": 1800000000}, "secondary_window": None}}))
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("14%", result.stdout)
            self.assertIn("⚠", result.stdout)
            old = time.time() - 25 * 3600
            os.utime(cached, (old, old))
            self.assertEqual(run().returncode, 1)


class WrapperTests(unittest.TestCase):
    def test_shell_syntax(self):
        subprocess.run(["shellcheck", str(ROOT / "dot_codex/executable_herdr-codex-account.sh"),
                        str(ROOT / "dot_local/bin/executable_codex-usage")], check=True)

    def test_preserves_exit_code_arguments_stdin_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Only replace the hook path in the extracted real zsh function.
            source = (ROOT / "dot_zshrc.tmpl").read_text()
            function = source[source.index("codex() {"):source.index("\n{{- if .work }}", source.index("codex() {"))]
            hook = root / "hook.sh"
            hook.write_text('''#!/bin/sh
printf '%s %s\\n' "$1" "${HERDR_CODEX_RUN_ID:-}" >> "$MOCK_LOG"
[ "$1" != start ] || printf 'run-id\\n'
''')
            subprocess.run(["shellcheck", str(hook)], check=True, capture_output=True)
            function = function.replace('$HOME/.codex/herdr-codex-account.sh', str(hook))
            binary = root / "codex"
            binary.write_text(f"#!{sys.executable}\n" + '''import json, os, sys
print(json.dumps([sys.argv[1:], sys.stdin.read(), os.environ.get('HERDR_CODEX_RUN_ID')]))
raise SystemExit(42)
''')
            binary.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                       HERDR_ENV="1", MOCK_LOG=str(root / "log"))
            shell = function + '\ncodex "arg with spaces"\n'
            result = subprocess.run(["zsh", "-f", "-c", shell], input="keep stdin",
                                    env=env, text=True, capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 42, result.stderr)
            self.assertEqual(json.loads(result.stdout), [["arg with spaces"], "keep stdin", "run-id"])
            self.assertEqual((root / "log").read_text().splitlines(), ["start ", "clear run-id"])
            binary.write_text(f"#!{sys.executable}\n" +
                              "import os, signal\nos.kill(os.getpid(), signal.SIGINT)\n")
            interrupted = subprocess.run(["zsh", "-f", "-c", shell],
                                         env=env, text=True, capture_output=True, timeout=3)
            self.assertEqual(interrupted.returncode, 130, interrupted.stderr)
            self.assertEqual((root / "log").read_text().splitlines()[-1], "clear run-id")


if __name__ == "__main__":
    unittest.main()
