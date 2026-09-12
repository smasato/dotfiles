"""Worktrunk's Herdr lifecycle: serialized layout and identity-bound deferred close."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def call(*args):
    output = subprocess.check_output(["herdr", *args], text=True, timeout=15)
    response = json.loads(output)
    if response.get("ok") is False or "error" in response:
        raise RuntimeError(f"Herdr rejected {args}: {response}")
    return response["result"]


def snapshot():
    return call("api", "snapshot")["snapshot"]


def socket_path():
    if os.environ.get("HERDR_SOCKET_PATH"):
        return Path(os.environ["HERDR_SOCKET_PATH"]).resolve()
    directory = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "herdr"
    session = os.environ.get("HERDR_SESSION", "default")
    if session != "default":
        directory = directory / "sessions" / session
    return (directory / "herdr.sock").resolve()


def socket_identity():
    path = socket_path()
    stat = path.stat()
    return [str(path), stat.st_dev, stat.st_ino, stat.st_mtime_ns]


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value))
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def panes_for(data, workspace):
    return [pane for pane in data["panes"] if pane["workspace_id"] == workspace]


def ensure_layout(repo, path, branch, state_path, identity):
    ws = call("worktree", "open", "--cwd", repo, "--path", path,
              "--label", branch, "--no-focus")["workspace"]["workspace_id"]
    for _ in range(10):
        panes = panes_for(snapshot(), ws)
        if panes:
            break
        time.sleep(0.2)
    state = read(state_path)
    if state.get("socket") != identity or state.get("workspace") != ws:
        state = {}
    if state and not any(p["terminal_id"] == state["shell"]["terminal_id"] for p in panes):
        return  # The original shell was replaced; leave the user's layout alone.
    if not state:
        if len(panes) != 1:
            return  # Adopt only a bare workspace, including one opened by the picker.
        state = dict(socket=identity, workspace=ws, shell=panes[0])
        save(state_path, state)
    if state.get("complete"):
        return

    def create(key, *args):
        if key in state:
            return state[key]
        if "pending" not in state:
            state["pending"] = dict(key=key, before=[p["pane_id"] for p in panes_for(snapshot(), ws)])
            save(state_path, state)
        pending = state["pending"]
        if pending["key"] != key:
            raise RuntimeError("Unexpected layout checkpoint")
        # Recover a successful creation whose CLI response or checkpoint was lost.
        def added():
            return [p for p in panes_for(snapshot(), ws) if p["pane_id"] not in pending["before"]]
        new = added()
        if not new:
            call(*args)
            for _ in range(10):
                new = added()
                if new:
                    break
                time.sleep(0.2)
        if len(new) != 1:
            raise RuntimeError(f"Cannot identify {key} pane; leave layout unchanged and inspect workspace {ws}")
        state[key] = new[0]
        del state["pending"]
        save(state_path, state)
        return new[0]

    create("viewer", "plugin", "pane", "open", "--plugin", "herdr-file-viewer",
           "--entrypoint", "file-viewer", "--placement", "split", "--direction", "right",
           "--target-pane", state["shell"]["pane_id"], "--no-focus")
    # Viewer commands resolve relative to the plugin root: do not pass --cwd.
    git = create("git", "plugin", "pane", "open", "--plugin", "herdr-lazygit",
                 "--entrypoint", "lazygit", "--placement", "tab", "--workspace", ws,
                 "--cwd", path, "--no-focus")
    call("tab", "rename", git["tab_id"], "lazygit")
    shell = create("yazi_shell", "tab", "create", "--workspace", ws,
                   "--cwd", path, "--label", "yazi", "--no-focus")
    yazi = create("yazi", "pane", "split", shell["pane_id"], "--direction", "right",
                  "--cwd", path, "--no-focus")
    call("pane", "rename", yazi["pane_id"], "yazi")
    if state.get("launching"):
        raise RuntimeError(f"Yazi launch response was lost; inspect pane {yazi['pane_id']} before retrying manually")
    # Sending terminal input cannot be safely replayed after an ambiguous failure.
    state["launching"] = True
    save(state_path, state)
    call("pane", "run", yazi["pane_id"], "yazi")
    state["complete"] = True
    save(state_path, state)


def capture(path, capture_path, identity):
    # Clear stale captures even if the new snapshot fails.
    capture_path.unlink(missing_ok=True)
    data = snapshot()
    targets = []
    for ws in data["workspaces"]:
        provenance = ws.get("worktree") or {}
        if Path(provenance.get("checkout_path", "/")).resolve() == Path(path):
            terminals = sorted(p["terminal_id"] for p in panes_for(data, ws["workspace_id"]))
            if terminals:
                targets.append(dict(workspace=ws["workspace_id"], worktree=provenance, terminals=terminals))
    save(capture_path, dict(path=path, socket=identity, targets=targets))


def queue_close(path, capture_path, identity):
    captured = read(capture_path)
    if captured.get("socket") != identity or os.path.lexists(path):
        return
    if captured.get("targets"):
        # Pueue reconstructs a shell command; --escape preserves the JSON as one argv.
        subprocess.run(["pueue", "add", "--delay", "5 seconds", "--escape", "--",
                        sys.executable, str(Path(__file__).resolve()), "close", json.dumps(captured)],
                       check=True, timeout=15)
    capture_path.unlink(missing_ok=True)


def close(captured):
    path = captured["path"]
    if socket_identity() != captured["socket"] or os.path.lexists(path):
        return
    for target in captured["targets"]:
        data = snapshot()
        ws = next((w for w in data["workspaces"] if w["workspace_id"] == target["workspace"]), None)
        terminals = sorted(p["terminal_id"] for p in panes_for(data, target["workspace"]))
        if (ws and ws.get("worktree") == target["worktree"] and terminals == target["terminals"]
                and socket_identity() == captured["socket"] and not os.path.lexists(path)):
            call("workspace", "close", target["workspace"])  # Never --group.


def main():
    action, *args = sys.argv[1:]
    if action == "close":
        captured = json.loads(args[0])
        # Bind the delayed CLI calls to the socket captured before removal.
        os.environ["HERDR_SOCKET_PATH"] = captured["socket"][0]
        path = captured["path"]
    else:
        path = str(Path(args[1] if action == "open" else args[0]).resolve())
    identity = socket_identity()
    directory = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "herdr/worktrunk"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = hashlib.sha256(f"{identity[0]}\0{path}".encode()).hexdigest()
    # Lock file is persistent: unlinking it would let waiters lock different inodes.
    with (directory / f"{key}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == "open":
            ensure_layout(args[0], path, args[2], directory / f"{key}.layout.json", identity)
        elif action == "capture":
            capture(path, directory / f"{key}.remove.json", identity)
        elif action == "queue-close":
            queue_close(path, directory / f"{key}.remove.json", identity)
        elif action == "close":
            close(captured)
        else:
            raise ValueError(f"Unknown action: {action}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"worktrunk/herdr: {error}", file=sys.stderr)
        sys.exit(1)
