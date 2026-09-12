"""Keep lazygit tab rename/return inside the captured workspace and session."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "dot_config/herdr/scripts/executable_lazygit-tab.sh"
STUB = r'''
import json, os, pathlib, sys
root=pathlib.Path(os.environ['FIXTURE'])
a=sys.argv[1:]
with (root/'calls').open('a') as f: f.write(json.dumps(a)+'\n')
tabs=[dict(tab_id=t,workspace_id=w,label=l,number=n) for t,w,l,n in (
 ('w1:t1','w1','shell',1),('w1:t2','w1','lazygit',2),('w1:t3','w1','shell',3),
 ('w2:t1','w2','lazygit',1))]
panes=[dict(pane_id='w1:p2',tab_id='w1:t2',workspace_id='w1',label='Git'),
       dict(pane_id='w2:p1',tab_id='w2:t1',workspace_id='w2',label='Git')]
if a[:3]==['tab','get','w2:t1'] and os.environ.get('FAIL_GET'): sys.exit(1)
if a[:2]==['tab','get']: result={'tab':next(t for t in tabs if t['tab_id']==a[2])}
elif a[:2]==['tab','list']: result={'tabs':tabs}
elif a[:2]==['pane','list']: result={'panes':panes}
elif a[:2] in (['tab','focus'],['tab','rename']) or a[:3]==['plugin','action','invoke']: result={}
else: sys.exit('unexpected argv '+repr(a))
print(json.dumps({'ok':True,'result':result}))
'''


class LazygitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ("a.sock", "b.sock"):
            (self.root / name).touch()
        stub = self.root / "herdr"
        stub.write_text(f"#!{sys.executable}\n{STUB}")
        stub.chmod(0o755)
        self.env = dict(os.environ, FIXTURE=str(self.root), TMPDIR=str(self.root),
                        PATH=f"{self.root}:{os.environ['PATH']}", HERDR_ACTIVE_WORKSPACE_ID="w1",
                        HERDR_ACTIVE_PANE_ID="w1:p1", HERDR_ACTIVE_PANE_CWD="/tmp/repo")

    def run_tab(self, tab="w1:t1", session="a"):
        subprocess.run(["bash", str(SCRIPT)], check=True, capture_output=True, text=True,
                       env=dict(self.env, HERDR_ACTIVE_TAB_ID=tab,
                                HERDR_SOCKET_PATH=str(self.root / f"{session}.sock")))

    def calls(self):
        return [json.loads(line) for line in (self.root / "calls").read_text().splitlines()]

    def test_rename_only_target_workspace(self):
        self.run_tab()
        self.assertEqual([a for a in self.calls() if a[:2] == ["tab", "rename"]],
                         [["tab", "rename", "w1:t2", "lazygit"]])

    def test_return_state_is_scoped_to_session(self):
        self.run_tab()
        self.run_tab("w1:t3", "b")
        self.run_tab("w1:t2", "a")
        self.assertEqual(self.calls()[-1], ["tab", "focus", "w1:t1"])

    def test_stale_return_cannot_focus_another_workspace(self):
        self.run_tab()
        for state in (self.root / "herdr-lazygit-return").iterdir():
            state.write_text("w2:t1\n")
        self.run_tab("w1:t2")
        self.assertEqual(self.calls()[-1], ["tab", "focus", "w1:t1"])
        self.assertNotIn(["tab", "focus", "w2:t1"], self.calls())

    def test_failed_lookup_cannot_authorize_return(self):
        self.env["FAIL_GET"] = "1"
        self.test_stale_return_cannot_focus_another_workspace()


if __name__ == "__main__":
    unittest.main()
