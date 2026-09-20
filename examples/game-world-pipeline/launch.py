#!/usr/bin/env python3
"""Local helper: review UI, manual play, engine import or independent recheck."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from review.server import ReviewStore
from pipeline.runtime import load_runtime
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('mode', choices=['review', 'play', 'check', 'import', 'configure'])
p.add_argument('--run-id', default='warehouse-repair-01')
p.add_argument('--godot', help='Absolute path to the Godot executable for configure mode')
p.add_argument('--port', type=int, default=8765)
a = p.parse_args()
runtime = load_runtime(ROOT)
if a.mode == 'configure':
    if not a.godot or not Path(a.godot).is_file():
        p.error('configure requires --godot /absolute/path/to/Godot')
    runtime.update(godot=str(Path(a.godot).resolve()), project_root=str(ROOT))
    (ROOT/'runtime.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2)+'\n')
    print('Runtime configured. Next: python3 launch.py import')
elif a.mode == 'review':
    raise SystemExit(subprocess.call([sys.executable, str(ROOT/'review/server.py'), '--root', str(ROOT), '--port', str(a.port)]))
else:
    if not runtime['godot'] or not Path(runtime['godot']).is_file():
        p.error('Godot executable missing. Install official Godot, then use configure --godot PATH.')
    command = [runtime['godot']]
    if a.mode == 'import':
        command += ['--headless', '--editor', '--import', '--path', str(ROOT/'engine'), '--quit']
    else:
        store = ReviewStore(ROOT)
        directory, manifest = store.run(a.run_id)
        candidate, _ = store.final(directory, manifest)
        if a.mode == 'check': command += ['--headless']
        out = directory/('play_sessions' if a.mode == 'play' else 'rechecks')/datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        out.mkdir(parents=True)
        command += ['--path', str(ROOT/'engine'), '--', '--spec', str(directory/candidate['spec']), '--out', str(out)]
        if a.mode == 'play': command += ['--play']
        print('Output:', out, flush=True)
    raise SystemExit(subprocess.call(command))
