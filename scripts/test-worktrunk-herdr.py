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
    (root/'queued').write_text(json.dumps(a)); sys.exit(0)
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
    pane(tab)
    f.write_text(json.dumps(s))
    if is_git and mode=='after' and not failed.exists(): failed.touch(); sys.exit(1)
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
        self.env["FAIL"] = "before"
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
        self.open()
        self.assertEqual(len(json.loads(self.session.read_text())["panes"]), 5)

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
        self.assertEqual(args[:6], ["add", "--delay", "5 seconds", "--escape", "--", sys.executable])
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
        self.run_action("queue-close", self.path)
        self.assertFalse((self.root / "queued").exists())


if __name__ == "__main__":
    unittest.main()
