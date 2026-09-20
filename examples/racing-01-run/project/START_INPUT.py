#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys
P=Path(__file__).resolve().parent
G=os.environ.get("GODOT", '/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot')
if not (P/".godot").exists():
    subprocess.run([G,"--headless","--editor","--import","--path",str(P),"--rendering-method","gl_compatibility","--quit"],check=True,timeout=60)
cmd=[G,"--path",str(P),"--rendering-method","gl_compatibility"]
if "--check" in sys.argv: cmd += ["--headless","--quit-after","180"]
cmd += ["--script",str(P/".input/start.gd"),"--","--scene-setup", 'default']
raise SystemExit(subprocess.call(cmd))
