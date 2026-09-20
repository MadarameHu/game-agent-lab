"""Machine-local Godot settings; historical run evidence is never used as config."""
import json
import os
from pathlib import Path
import shutil


def load_runtime(root):
    root = Path(root).resolve()
    config = root / "runtime.json"
    runtime = json.loads(config.read_text()) if config.exists() else {}
    runtime["godot"] = os.environ.get("GODOT_BIN") or runtime.get("godot") or shutil.which("godot") or shutil.which("godot4")
    runtime["project_root"] = str(root)
    return runtime
