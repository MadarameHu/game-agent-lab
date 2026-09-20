#!/usr/bin/env python3
"""Check bundled historical evidence; does not rerun game behavior tests."""
import importlib.util
import json
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
demo = ROOT / 'examples/game-trajectory-demo'
runpy.run_path(str(demo / 'build_data.py'), run_name='__main__')
spec = importlib.util.spec_from_file_location('viewer', demo / 'server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.Demo(root=demo)
results = {key: app.integrity(key) for key in app.cases}
assert len(results) == 12, len(results)
failures = {key: value for key, value in results.items() if value['integrity'] != 'verified'}
assert not failures, json.dumps(failures, ensure_ascii=False, indent=2)
print(json.dumps({'cases': 12, 'historical_integrity': 'verified', 'behavior_tests_rerun': False}))
