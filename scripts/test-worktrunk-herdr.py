"""Exercise Herdr lifecycle against a fake CLI, including concurrent hooks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dot_config/herdr/scripts/worktree.py"
STUB = r'''
import json, os, pathlib, sys
root=pathlib.Path(os.environ['FIXTURE'])
a=sys.argv[1:]
with (root/'calls').open('a') as f: f.write(json.dumps([pathlib.Path(sys.argv[0]).name,*a])+'\n')
if pathlib.Path(sys.argv[0]).name=='pueue':
    if os.environ.get('FAIL')=='pueue': sys.exit(1)
    (root/'queued').write_text(json.dumps(a)); print('41'); sys.exit(0)
f=root/'session.json'
s=json.loads(f.read_text())
def value(key): return a[a.index(key)+1]
def pane(tab):
    i=len(s['panes'])+1
    p=dict(pane_id=f'w1:p{i}',terminal_id=f'terminal-{i}',workspace_id='w1',tab_id=tab)
    s['panes'].append(p); return p
result={}
if a==['api','snapshot']: result={'type':'session_snapshot','snapshot':s}
elif a[:2]==['worktree','open']: result={'workspace':s['workspaces'][0]}
elif a[:3]==['plugin','pane','open'] or a[:2] in (['tab','create'],['pane','split']):
    failed=root/'failed'
    is_git='herdr-lazygit' in a
    mode=os.environ.get('FAIL','')
    if is_git and mode=='before' and not failed.exists(): failed.touch(); sys.exit(1)
    tab='w1:t1' if 'herdr-file-viewer' in a else 'w1:t2' if is_git else 'w1:t3'
    created=pane(tab)
    if a[:3]==['plugin','pane','open']: result={'plugin_pane':{'pane':created}}
    elif a[:2]==['tab','create']: result={'root_pane':created}
    else: result={'pane':created}
    if is_git and os.environ.get('EXTRA'): pane('w1:manual')
    f.write_text(json.dumps(s))
    if is_git and mode=='after' and not failed.exists(): failed.touch(); sys.exit(1)
elif a[:2]==['tab','rename'] and os.environ.get('FAIL')=='rename' and not (root/'failed').exists():
    (root/'failed').touch(); sys.exit(1)
elif a[:2]==['pane','run'] and os.environ.get('FAIL')=='yazi' and not (root/'failed').exists():
    (root/'failed').touch(); sys.exit(1)
elif a[:2]==['workspace','close']:
    s['workspaces']=[]; s['panes']=[]
elif a[:2] not in (['tab','rename'],['pane','rename'],['pane','run']):
    sys.exit('Unexpected Herdr argv: '+repr(a))
f.write_text(json.dumps(s))
print(json.dumps({'ok':True,'result':result}))
'''


class HerdrTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="herdr lifecycle ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / "o'reilly worktree"
        self.path.mkdir()
        self.socket = self.root / "herdr.sock"
        self.socket.touch()
        self.env = dict(os.environ, FIXTURE=str(self.root), HERDR_SOCKET_PATH=str(self.socket),
                        XDG_STATE_HOME=str(self.root / "state"), PATH=f"{self.root}:{os.environ['PATH']}")
        for name in ("herdr", "pueue"):
            stub = self.root / name
            stub.write_text(f"#!{sys.executable}\n{STUB}")
            stub.chmod(0o755)
        self.session = self.root / "session.json"
        self.session.write_text(json.dumps(dict(
            workspaces=[dict(workspace_id="w1", worktree=dict(checkout_path=str(self.path)))],
            panes=[dict(pane_id="w1:p1", terminal_id="terminal-1", workspace_id="w1", tab_id="w1:t1")],
            tabs=[], agents=[], layouts=[])))

    def run_action(self, action, *args, check=True):
        return subprocess.run([sys.executable, str(SCRIPT), action, *map(str, args)],
                              env=self.env, check=check, text=True, capture_output=True)

    def open(self, check=True):
        return self.run_action("open", self.root, self.path, "feature/o'reilly", check=check)

    def test_retry_and_completed_layout(self):
        self.env["FAIL"] = "rename"
        self.assertNotEqual(self.open(check=False).returncode, 0)
        self.open()
        data = json.loads(self.session.read_text())
        self.assertEqual(len(data["panes"]), 5)
        # A pane closed by the user after completion must stay closed.
        data["panes"].pop()
        self.session.write_text(json.dumps(data))
        self.open()
        self.assertEqual(json.loads(self.session.read_text()), data)
        calls = (self.root / "calls").read_text().splitlines()
        self.assertEqual(sum(json.loads(c)[1:3] == ["pane", "run"] for c in calls), 1)
        self.assertTrue(all("--no-focus" in json.loads(c) for c in calls
                            if '"create"' in c or '"split"' in c or '"open"' in c))

    def test_lost_creation_response(self):
        self.env["FAIL"] = "after"
        self.assertNotEqual(self.open(check=False).returncode, 0)
        before = self.session.read_text()
        self.assertNotEqual(self.open(check=False).returncode, 0)
        self.assertEqual(self.session.read_text(), before)

    def test_manual_pane_after_failure_is_not_adopted(self):
        self.env["FAIL"] = "before"
        self.assertNotEqual(self.open(check=False).returncode, 0)
        data = json.loads(self.session.read_text())
        data["panes"].append(dict(pane_id="w1:p3", terminal_id="manual", workspace_id="w1", tab_id="w1:t2"))
        self.session.write_text(json.dumps(data))
        self.assertNotEqual(self.open(check=False).returncode, 0)
        self.assertEqual(json.loads(self.session.read_text()), data)

    def test_concurrent_open(self):
        argv = [sys.executable, str(SCRIPT), "open", str(self.root), str(self.path), "branch"]
        processes = [subprocess.Popen(argv, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(3)]
        for process in processes:
            _, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(len(json.loads(self.session.read_text())["panes"]), 5)

    def test_customized_layout_is_preserved(self):
        data = json.loads(self.session.read_text())
        data["panes"].append(dict(data["panes"][0], pane_id="w1:p2", terminal_id="custom"))
        self.session.write_text(json.dumps(data))
        self.open()
        self.assertEqual(json.loads(self.session.read_text()), data)

    def queued_close(self):
        self.run_action("capture", self.path)
        self.path.rmdir()
        self.run_action("queue-close", self.path)
        args = json.loads((self.root / "queued").read_text())
        self.assertEqual(args[:7], ["add", "--delay", "5 seconds", "--escape", "--print-task-id", "--", sys.executable])
        return args[-1]

    def test_removed_workspace_closes(self):
        captured = self.queued_close()
        self.run_action("close", captured)
        self.assertEqual(json.loads(self.session.read_text())["workspaces"], [])

    def test_recreated_path_keeps_workspace(self):
        captured = self.queued_close()
        self.path.mkdir()
        self.run_action("close", captured)
        self.assertTrue(json.loads(self.session.read_text())["workspaces"])

    def test_replaced_terminal_keeps_workspace(self):
        captured = self.queued_close()
        data = json.loads(self.session.read_text())
        data["panes"][0]["terminal_id"] = "replacement"
        self.session.write_text(json.dumps(data))
        self.run_action("close", captured)
        self.assertTrue(json.loads(self.session.read_text())["workspaces"])

    def test_restarted_server_keeps_workspace(self):
        captured = self.queued_close()
        os.utime(self.socket, ns=(1, 1))
        self.run_action("close", captured)
        self.assertTrue(json.loads(self.session.read_text())["workspaces"])

    def test_plugin_already_closed_workspace(self):
        captured = self.queued_close()
        self.session.write_text(json.dumps(dict(workspaces=[], panes=[])))
        self.run_action("close", captured)
        self.assertFalse(any(json.loads(line)[1:3] == ["workspace", "close"]
                             for line in (self.root / "calls").read_text().splitlines()))

    def test_failed_removal_does_not_queue(self):
        self.run_action("capture", self.path)
        self.assertNotEqual(self.run_action("queue-close", self.path, check=False).returncode, 0)
        self.assertFalse((self.root / "queued").exists())

    def test_creation_response_wins_over_concurrent_manual_pane(self):
        self.env["EXTRA"] = "1"
        self.open()
        state = json.loads(next((self.root / "state/herdr/worktrunk").glob("*.layout.json")).read_text())
        self.assertEqual(state["git"]["pane_id"], "w1:p3")
        self.assertEqual(len(json.loads(self.session.read_text())["panes"]), 6)

    def test_resume_confirmed_creation_and_reject_wrong_pane(self):
        self.env["FAIL"] = "after"
        self.open(check=False)
        self.assertNotEqual(self.run_action("resume", self.path, "--adopt-pane", "w1:p1", check=False).returncode, 0)
        self.run_action("resume", self.path, "--adopt-pane", "w1:p3")
        self.assertEqual(len(json.loads(self.session.read_text())["panes"]), 5)

    def test_explicit_retry_when_no_pane_was_created(self):
        self.env["FAIL"] = "before"
        self.open(check=False)
        self.run_action("resume", self.path, "--retry-pending")
        self.assertEqual(len(json.loads(self.session.read_text())["panes"]), 5)

    def test_retry_refuses_changed_pane_set(self):
        self.env["FAIL"] = "after"
        self.open(check=False)
        before = self.session.read_text()
        self.assertNotEqual(self.run_action("resume", self.path, "--retry-pending", check=False).returncode, 0)
        self.assertEqual(self.session.read_text(), before)

    def test_status_works_without_server_and_does_not_call_cli(self):
        self.env["FAIL"] = "before"
        self.open(check=False)
        self.socket.unlink()
        before = (self.root / "calls").read_text()
        rows = json.loads(self.run_action("status", self.path, "--json").stdout)
        self.assertEqual(rows[0]["phase"], "creation-unconfirmed")
        self.assertEqual(rows[0]["pending"]["key"], "git")
        self.assertEqual((self.root / "calls").read_text(), before)

    def test_yazi_acknowledgement_does_not_resend_input(self):
        self.env["FAIL"] = "yazi"
        self.open(check=False)
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["phase"], "yazi-unconfirmed")
        self.run_action("resume", self.path, "--yazi-running")
        calls = [json.loads(line)[1:3] for line in (self.root / "calls").read_text().splitlines()]
        self.assertEqual(calls.count(["pane", "run"]), 1)
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["phase"], "complete")

    def test_yazi_retry_requires_explicit_resolution(self):
        self.env["FAIL"] = "yazi"
        self.open(check=False)
        self.assertNotEqual(self.run_action("resume", self.path, check=False).returncode, 0)
        self.run_action("resume", self.path, "--retry-yazi")
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["phase"], "complete")

    def test_failed_queue_can_be_retried_and_closed(self):
        self.run_action("capture", self.path)
        self.path.rmdir()
        self.env["FAIL"] = "pueue"
        self.assertNotEqual(self.run_action("queue-close", self.path, check=False).returncode, 0)
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["phase"], "queue-failed")
        self.env.pop("FAIL")
        self.run_action("retry-close", self.path)
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["task"], "41")
        captured = json.loads((self.root / "queued").read_text())[-1]
        self.run_action("close", captured)
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["phase"], "closed")

    def test_queued_close_is_not_duplicated_without_confirmation(self):
        self.queued_close()
        self.assertNotEqual(self.run_action("retry-close", self.path, check=False).returncode, 0)
        self.run_action("retry-close", self.path, "--confirm-task-stopped")

    def test_worker_failure_is_recorded(self):
        captured = self.queued_close()
        self.socket.unlink()
        self.assertNotEqual(self.run_action("close", captured, check=False).returncode, 0)
        self.assertEqual(json.loads(self.run_action("status", "--json").stdout)[0]["phase"], "close-failed")


if __name__ == "__main__":
    unittest.main()
