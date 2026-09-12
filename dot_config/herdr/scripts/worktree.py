"""Worktrunk's Herdr lifecycle: serialized layout and identity-bound deferred close."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
from herdr_common import call, snapshot, socket_identity, save, read, panes_for


def require_pane(data, saved, workspace):
    pane = next((p for p in panes_for(data, workspace)
                 if p["pane_id"] == saved["pane_id"] and p["terminal_id"] == saved["terminal_id"]
                 and p["tab_id"] == saved["tab_id"]), None)
    if pane is None:
        raise RuntimeError(f"Saved pane {saved['pane_id']} was removed or replaced; inspect the workspace")
    return pane


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
        state = dict(socket=identity, workspace=ws, shell=panes[0], repo=repo, path=path, branch=branch)
        save(state_path, state)
    if state.get("complete"):
        return
    state.update(repo=repo, path=path, branch=branch)
    save(state_path, state)

    def create(key, *args):
        if key in state:
            require_pane(snapshot(), state[key], ws)
            return state[key]
        if "pending" in state:
            raise RuntimeError(f"Unconfirmed {state['pending']['key']} creation in {ws}; use herdr-worktrees status and resume")
        state["pending"] = dict(key=key, before=[p["pane_id"] for p in panes_for(snapshot(), ws)])
        save(state_path, state)
        result = call(*args)
        pane = (result["plugin_pane"]["pane"] if key in ("viewer", "git") else
                result["root_pane"] if key == "yazi_shell" else result["pane"])
        # Only the returned identity proves which pane this request created.
        # A lost response remains pending even if exactly one new pane appears.
        if (pane["workspace_id"] != ws or pane["pane_id"] in state["pending"]["before"]
                or not pane.get("terminal_id")):
            raise RuntimeError(f"Unexpected {key} creation response for {ws}")
        state[key] = pane
        del state["pending"]
        save(state_path, state)
        return pane

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
    state.pop("last_error", None)
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
    save(capture_path, dict(path=path, socket=identity, targets=targets, state="captured", token=uuid.uuid4().hex))


def queue_close(path, capture_path, identity):
    captured = read(capture_path)
    if not captured:
        raise RuntimeError("No removal capture exists for this worktree")
    if captured.get("socket") != identity or os.path.lexists(path):
        raise RuntimeError("Checkout still exists or the captured Herdr server changed; close was not queued")
    if captured.get("state") in ("queued", "closed", "queue-unconfirmed"):
        raise RuntimeError(f"Close is {captured['state']}; inspect pueue before submitting another task")
    if not captured.get("targets"):
        captured["state"] = "closed"
        save(capture_path, captured)
        return
    # Retain the capture for diagnostics and retries. Pueue reconstructs a shell
    # command; --escape preserves the JSON as one argument.
    captured.update(state="queue-unconfirmed")
    save(capture_path, captured)
    try:
        task = subprocess.check_output([
            "pueue", "add", "--delay", "5 seconds", "--escape", "--print-task-id", "--",
            sys.executable, str(Path(__file__).resolve()), "close", json.dumps(captured)],
            text=True, timeout=15).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        captured.update(state="queue-failed", last_error=str(error))
        save(capture_path, captured)
        raise
    captured.update(state="queued", task=task)
    captured.pop("last_error", None)
    save(capture_path, captured)


def close(captured):
    path = captured["path"]
    if socket_identity() != captured["socket"] or os.path.lexists(path):
        return "skipped"
    outcome = "closed"
    for target in captured["targets"]:
        data = snapshot()
        ws = next((w for w in data["workspaces"] if w["workspace_id"] == target["workspace"]), None)
        terminals = sorted(p["terminal_id"] for p in panes_for(data, target["workspace"]))
        if (ws and ws.get("worktree") == target["worktree"] and terminals == target["terminals"]
                and socket_identity() == captured["socket"] and not os.path.lexists(path)):
            call("workspace", "close", target["workspace"])  # Never --group.
        elif ws:
            outcome = "skipped"
    return outcome


def state_directory():
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "herdr/worktrunk"


def state_key(socket, path):
    return hashlib.sha256(f"{socket}\0{path}".encode()).hexdigest()


def status(path, as_json):
    """Read saved records only; this command works even when Herdr is stopped."""
    records = []
    for file in sorted(state_directory().glob("*.json")):
        try:
            saved = read(file)
            if path and saved.get("path") != path and file.stem.split(".")[0] != state_key(saved["socket"][0], path):
                continue
            kind = "layout" if file.name.endswith(".layout.json") else "close"
            phase = saved.get("state", "captured")
            if kind == "layout":
                phase = ("complete" if saved.get("complete") else "creation-unconfirmed" if saved.get("pending")
                         else "yazi-unconfirmed" if saved.get("launching") else "incomplete")
            records.append(dict(kind=kind, phase=phase, **saved))
        except (ValueError, KeyError) as error:
            records.append(dict(kind="invalid", phase="unreadable", file=str(file), last_error=str(error)))
    if as_json:
        print(json.dumps(records, indent=2))
    else:
        print("KIND\tSAVED_STATE\tWORKSPACE\tPATH\tDETAIL")
        for row in records:
            detail = row.get("last_error") or row.get("pending", {}).get("key") or row.get("task", "-")
            print("\t".join(str(value).replace("\n", " ").replace("\t", " ") for value in (
                row["kind"], row["phase"], row.get("workspace", "-"), row.get("path", row.get("file", "unknown")), detail)))


def resume(path, file, identity, options):
    state = read(file)
    if not state or state.get("socket") != identity:
        raise RuntimeError("No layout checkpoint for this Herdr server; use wt switch to open the worktree")
    data = snapshot()
    ws = state["workspace"]
    workspace = next((w for w in data["workspaces"] if w["workspace_id"] == ws), None)
    if not workspace or Path((workspace.get("worktree") or {}).get("checkout_path", "/")).resolve() != Path(path):
        raise RuntimeError("The saved workspace no longer belongs to this checkout")
    for key in ("shell", "viewer", "git", "yazi_shell", "yazi"):
        if key in state:
            require_pane(data, state[key], ws)
    pending = state.get("pending")
    if options.adopt_pane or options.retry_pending:
        if not pending:
            raise RuntimeError("No unconfirmed pane creation to resolve")
        new = [p for p in panes_for(data, ws) if p["pane_id"] not in pending["before"]]
        if options.adopt_pane:
            pane = next((p for p in new if p["pane_id"] == options.adopt_pane), None)
            if pane is None:
                raise RuntimeError("The selected pane is not a new pane in this workspace")
            key = pending["key"]
            target = state["shell"] if key == "viewer" else state.get("yazi_shell") if key == "yazi" else None
            existing_tabs = {state[k]["tab_id"] for k in ("shell", "git") if k in state}
            if (target and pane["tab_id"] != target["tab_id"]) or (not target and pane["tab_id"] in existing_tabs):
                raise RuntimeError("The selected pane is in the wrong tab for this layout step")
            state[key] = pane
        elif {p["pane_id"] for p in panes_for(data, ws)} != set(pending["before"]):
            raise RuntimeError("Panes changed since the request; inspect them and use --adopt-pane for the confirmed result")
        del state["pending"]
    if options.yazi_running or options.retry_yazi:
        if not state.get("launching") or state.get("complete"):
            raise RuntimeError("No unconfirmed yazi launch to resolve")
        if options.yazi_running:
            state["complete"] = True
        else:
            state.pop("launching", None)
    # Old checkpoints acquire their launch context from workspace provenance.
    state.update(path=path, repo=state.get("repo") or workspace["worktree"]["repo_root"],
                 branch=state.get("branch") or workspace["label"])
    state.pop("last_error", None)
    save(file, state)
    ensure_layout(state["repo"], path, state["branch"], file, identity)


def main():
    parser = argparse.ArgumentParser(description="Inspect and recover Worktrunk's Herdr lifecycle")
    commands = parser.add_subparsers(dest="action", required=True)
    command = commands.add_parser("open", help="Open the standard worktree layout (hook entry point)")
    for name in ("repo", "path", "branch"):
        command.add_argument(name)
    for name in ("capture", "queue-close", "retry-close"):
        command = commands.add_parser(name)
        command.add_argument("path")
        if name == "retry-close":
            command.add_argument("--confirm-task-stopped", action="store_true",
                                 help="Requeue only after confirming the old task is stopped or absent in pueue")
    commands.add_parser("close", help="Deferred close worker (internal)").add_argument("capture")
    command = commands.add_parser("status", help="List cached lifecycle state without contacting Herdr")
    command.add_argument("path", nargs="?")
    command.add_argument("--json", action="store_true")
    command = commands.add_parser("resume", help="Resume one layout after inspecting its workspace")
    command.add_argument("path")
    resolution = command.add_mutually_exclusive_group()
    resolution.add_argument("--adopt-pane", metavar="PANE_ID", help="Confirm which pane the pending request created")
    resolution.add_argument("--retry-pending", action="store_true", help="Retry creation only if the pane set is unchanged")
    resolution.add_argument("--yazi-running", action="store_true", help="Confirm yazi is already running; do not resend input")
    resolution.add_argument("--retry-yazi", action="store_true", help="Explicitly resend yazi after checking the target shell")
    options = parser.parse_args()
    action = options.action
    if action == "status":
        status(str(Path(options.path).resolve()) if options.path else None, options.json)
        return
    if action == "close":
        captured = json.loads(options.capture)
        os.environ["HERDR_SOCKET_PATH"] = captured["socket"][0]
        path = captured["path"]
    else:
        path = str(Path(options.path).resolve())
    identity = captured["socket"] if action == "close" else socket_identity()
    directory = state_directory()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = state_key(identity[0], path)
    layout_file = directory / f"{key}.layout.json"
    capture_file = directory / f"{key}.remove.json"
    # Keep the lock inode: unlinking it would let waiters lock different files.
    with (directory / f"{key}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if action == "open":
                ensure_layout(options.repo, path, options.branch, layout_file, identity)
            elif action == "resume":
                resume(path, layout_file, identity, options)
            elif action == "capture":
                capture(path, capture_file, identity)
            elif action in ("queue-close", "retry-close"):
                if action == "retry-close" and options.confirm_task_stopped:
                    saved = read(capture_file)
                    if saved.get("state") not in ("queued", "queue-unconfirmed"):
                        raise RuntimeError("There is no queued or unconfirmed task to resolve")
                    saved["state"] = "queue-failed"
                    save(capture_file, saved)
                queue_close(path, capture_file, identity)
            elif action == "close":
                result = close(captured)
                current = read(capture_file)
                if current and current.get("token") == captured.get("token"):
                    current.update(state=result)
                    current.pop("last_error", None)
                    save(capture_file, current)
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
            file = layout_file if action in ("open", "resume") else capture_file
            saved = read(file)
            if saved and (action != "close" or saved.get("token") == captured.get("token")):
                saved["last_error"] = str(error)
                if action == "close":
                    saved["state"] = "close-failed"
                save(file, saved)
            raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"worktrunk/herdr: {error}", file=sys.stderr)
        sys.exit(1)
