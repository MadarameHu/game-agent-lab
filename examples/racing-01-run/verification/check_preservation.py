"""Check preserved gameplay and all main-scene text outside GridMap cell data."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 expected=json.loads((ROOT/'contract/protected-files.json').read_text());project=ROOT/'project'
 changed=[name for name,h in expected.items() if not (project/name).is_file() or sha(project/name)!=h]
 before=(ROOT/'evidence/baseline/main.tscn').read_text();after=(project/'scenes/main.tscn').read_text()
 pattern=r'(\[node name="GridMap"[^\n]*\][\s\S]*?)data = \{[\s\S]*?\n\}'
 def strip(s):
  out,n=re.subn(pattern,lambda m:m.group(1)+'data = {LAYOUT}',s,count=1)
  if n!=1:raise ValueError('Cannot locate GridMap serialized data')
  return out
 outside_same=strip(before)==strip(after)
 return {'id':'protected_gameplay','pass':not changed and outside_same,'details':{'protected_file_count':len(expected),'changed_files':changed,'outside_gridmap_unchanged':outside_same,'main_changed':before!=after,'main_sha256':sha(project/'scenes/main.tscn'),'baseline_sha256':sha(ROOT/'evidence/baseline/main.tscn')}}
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
