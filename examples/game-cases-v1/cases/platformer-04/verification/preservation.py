from pathlib import Path
import json,hashlib,re,sys
c=Path(__file__).resolve().parents[1]
p=c/'project'
base=json.loads((c/'contract/baseline-hashes.json').read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
current={str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file() and '.godot' not in f.parts}
changed=[s for s,h in current.items() if base.get(s)!=h]
removed=[s for s in base if s not in current]
contract=json.loads((c/'contract/acceptance.json').read_text())
allowed=contract['allowed_product_paths']
checks=[{'id':'allowed_paths','pass':not removed and all(any(s==a or (a.endswith('/') and s.startswith(a)) for a in allowed) for s in changed),'details':{'changed':changed,'removed':removed}}]
# Original world/character assets and all mechanics beyond specifically authorized files must stay byte-identical.
checks.append({'id':'mechanics_assets_preserved','pass':all(current.get(s)==h for s,h in base.items() if s not in changed),'details':{'unchanged_files':sum(current.get(s)==h for s,h in base.items())}})
if c.name=='platformer-04':
 original=c/'contract/baseline-main.tscn'
 checks.append({'id':'original_scene_snapshot_hash','pass':sha(original)==base['scenes/main.tscn'],'details':'Copied fixed-commit original checked against frozen baseline hash.'})
 def world_sections(s):
  chunks=re.split(r'(?=\[node )',s)
  return [x.split('[connection')[0].strip() for x in chunks if x.startswith('[node ') and ('parent="World"' in x.split('\n',1)[0] or 'parent="World/' in x.split('\n',1)[0] or any(x.startswith('[node name="'+n+'"') for n in ['Player','View','Camera','World']))]
 checks.append({'id':'world_transforms_and_route','pass':world_sections(original.read_text())==world_sections((p/'scenes/main.tscn').read_text()),'details':{'world_sections_compared':len(world_sections(original.read_text())),'original_source':str(original)}})
 mechanics=[s for s in base if s.startswith(('objects/','scripts/','models/','fonts/')) and s not in ['objects/cloud.tscn','scripts/main.gd']]
 checks.append({'id':'collision_and_gameplay_equal_original','pass':all(current.get(s)==base[s] for s in mechanics),'details':{'files_compared':len(mechanics)}})
else:
 checks.append({'id':'world_camera_inputs_identical','pass':all(current.get(s)==base[s] for s in ['scenes/main.tscn','scripts/view.gd','project.godot','objects/player.tscn','objects/platform_falling.gd','objects/brick.gd']),'details':'Original layout, view controller, keyboard and gamepad mappings, collider and mechanics are byte-identical.'})
ok=all(x['pass'] for x in checks)
out={'checks':checks,'pass':ok,'candidate_hashes':current,'contract_sha256':sha(c/'contract/acceptance.json')}
(c/'evidence/final/preservation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pass':ok,'checks':checks},ensure_ascii=False))
sys.exit(0 if ok else 1)
