"""Shared Herdr API and session identity for local lifecycle helpers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


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



if __name__ == "__main__":
    print(hashlib.sha256(json.dumps(socket_identity()).encode()).hexdigest())
