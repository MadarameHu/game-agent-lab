import json,hashlib,re
from pathlib import Path
c=Path(__file__).resolve().parents[1]
b=json.loads((c/'contract/baseline-hashes.json').read_text())
allowed=set(json.loads((c/'task.json').read_text())['editable_paths'])
errors=[]
for name,h in b.items():
 if name in allowed:continue
 p=c/'project'/name
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append(name)
base=c.parents[2]/'game-inputs-v1/bases/racing/project/scenes/main.tscn'
a=(c/'project/scenes/main.tscn').read_text();z=base.read_text()
def grid(s):
 return re.search(r'\[node name="GridMap".*?(?=\n\[node|\Z)',s,re.S).group()
if grid(a)!=grid(z):errors.append('GridMap block changed')
result={'id':'preservation','pass':not errors,'summary':'All baseline files outside allowed paths identical; original GridMap block identical.','details':{'errors':errors,'baseline_files':len(b)}}
(c/'evidence/final/preservation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
raise SystemExit(0 if not errors else 1)
