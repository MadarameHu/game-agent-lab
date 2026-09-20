"""Start/stop only the isolated task server, preserving audit and inference budget."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "server.py"
PYTHON = ROOT / ".venv/bin/python"
PID_FILE = ROOT / "server.pid"
PORT = int(os.environ.get("GAME_MODEL_PORT", "18745"))

def task_pid():
    """Return live owned PID, None for absent/stale; reject PID reuse."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError as exc:
        raise RuntimeError("Invalid server.pid; inspect it manually") from exc
    if pid <= 1:
        raise RuntimeError("Unsafe PID in server.pid")
    proc = Path(f"/proc/{pid}")
    try:
        cmdline = (proc / "cmdline").read_bytes().split(b"\0")
        argv = [os.fsdecode(x) for x in cmdline if x]
        if not argv:
            return None  # Exited or zombie process.
        expected = [str(PYTHON), "-u", str(SERVER)]
        if argv != expected:
            raise RuntimeError(f"PID {pid} is not this task's exact server command; refusing to signal it")
        return pid
    except FileNotFoundError:
        return None

def health():
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3) as response:
        return json.load(response)

def start():
    pid = task_pid()
    if pid is not None:
        print(json.dumps({"status":"already_running", "pid":pid, "health":health()},ensure_ascii=False))
        return
    if not PYTHON.is_file() or not SERVER.is_file():
        raise RuntimeError("Missing task .venv/bin/python or server.py; follow README setup")
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1",PORT)) == 0:
            raise RuntimeError("Port already occupied without verified task PID; refusing to launch")
    gpu = os.environ.get("GAME_MODEL_GPU")
    if not gpu or not gpu.isdigit():
        raise RuntimeError("Set GAME_MODEL_GPU to a single physical GPU index")
    used = int(subprocess.check_output(["nvidia-smi",f"--id={gpu}","--query-gpu=memory.used","--format=csv,noheader,nounits"],text=True).strip())
    if used > 100:
        raise RuntimeError(f"GPU {gpu} occupied ({used} MiB); refusing launch")
    with (ROOT/"server.log").open("a") as log:
        process = subprocess.Popen([str(PYTHON),"-u",str(SERVER)],cwd=ROOT,
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    PID_FILE.write_text(str(process.pid)+"\n")
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Task server exited ({process.returncode}); inspect {ROOT/'server.log'}")
        try:
            result=health()
            print(json.dumps({"status":"started","pid":process.pid,"health":result},ensure_ascii=False))
            return
        except (OSError,ValueError):
            time.sleep(0.5)
    raise RuntimeError("Startup health timeout; process left intact for inspection (do not launch a duplicate)")

def stop():
    pid=task_pid()
    if pid is None:
        print(json.dumps({"status":"not_running"}))
        return
    # Verify ownership again immediately before the only signal in this script.
    if task_pid()!=pid:
        raise RuntimeError("Task PID changed before stop")
    os.kill(pid,signal.SIGTERM)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if task_pid() is None:
            if PID_FILE.exists() and PID_FILE.read_text().strip()==str(pid):
                PID_FILE.unlink()
            print(json.dumps({"status":"stopped","pid":pid,"budget_preserved":True}))
            return
        time.sleep(0.2)
    raise RuntimeError("Task did not exit after SIGTERM; inspect it manually. No other process was signaled")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["start","stop","restart","status"])
    action=parser.parse_args().action
    if action=="start":start()
    elif action=="stop":stop()
    elif action=="restart":stop();start()
    else:
        pid=task_pid()
        print(json.dumps({"pid":pid,"health":health() if pid else None},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
