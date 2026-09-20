#!/usr/bin/env python3
"""Verify input references and actual native launch evidence, not task solutions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 c=json.loads((ROOT/'catalog.json').read_text());assert len(c['tasks'])==12 and len(c['bases'])==3
 assets=0
 for t in c['tasks']:
  d=ROOT/'tasks'/t['id'];assert (d/'QUERY.md').is_file()
  assert json.loads((d/'task.json').read_text())==t
  assert sha(ROOT/t['source_manifest'])==t['source_manifest_sha256']
  project=(ROOT/t['initial_project']).resolve();assert project.is_relative_to(ROOT)
  assert (project/'project.godot').is_file()
  for asset in t['available_assets']:
   p=(project/asset).resolve();assert p.is_relative_to(project) and p.exists(),p;assets+=1
  assert t['status']=='input_ready_task_not_executed'
 checks=[]
 for b in c['bases']:
  out=ROOT/'previews'/b['id'];meta=json.loads((out/'preview.json').read_text());execution=json.loads((out/'execution.json').read_text());log=(out/'native.log').read_text()
  assert execution['exit_code']==0 and meta['screenshot_error']==0 and meta['node_count']>0
  assert 'SCRIPT ERROR:' not in log and (out/'scene.png').stat().st_size>10000
  if b['id']=='city-builder':assert 'cells=122 cash=5860' in log
  project=ROOT/'bases'/b['id']/'project'
  files={str(p.relative_to(project)):sha(p) for p in sorted(project.rglob('*')) if p.is_file() and '.godot' not in p.relative_to(project).parts and '.git' not in p.relative_to(project).parts}
  (ROOT/'bases'/b['id']/'effective-snapshot.json').write_text(json.dumps(files,indent=2)+'\n')
  checks.append({'base_id':b['id'],'native_start':'passed','scene_setup':meta['initial_setup'],'node_count':meta['node_count'],'screenshot_sha256':sha(out/'scene.png'),'script_errors':0,'warning_or_error_lines':[line for line in log.splitlines() if 'WARNING:' in line or line.startswith('ERROR:')],'source_file_count':len(files)})
 report={'task_count':12,'base_count':3,'referenced_resources_checked':assets,'bases':checks,'scope':'Import/start/render and input integrity only; the twelve requested tasks have not been executed or scored.','city_compatibility_patch':'Mouse ray/ground plane null guard, tracked under bases/city-builder/patches','native_previews':'Actual local Godot 4.7.2, gl_compatibility; 120 frames each'}
 (ROOT/'VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
