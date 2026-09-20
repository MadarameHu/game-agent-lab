from pathlib import Path
import json, hashlib, sys
c=Path(__file__).resolve().parents[1]
r=json.loads((c/'evidence/final/result.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[]
for name,h in r['candidate_hashes'].items():
 p=c/'project'/name
 if not p.is_file() or sha(p)!=h:errors.append('candidate changed: '+name)
for name,h in r['verification_hashes'].items():
 p=c/name
 if not p.is_file() or sha(p)!=h:errors.append('checker changed: '+name)
if sha(c/'contract/acceptance.json')!=r['contract_sha256']:errors.append('contract changed')
actual={str(p.relative_to(c/'project')) for p in (c/'project').rglob('*') if p.is_file() and '.godot' not in p.parts}
if actual!=set(r['candidate_hashes']):errors.append('candidate file set changed')
if not r['hard_pass'] or any(not x['pass'] for x in r['checks']):errors.append('hard checks failed')
print(json.dumps({'valid':not errors,'errors':errors}))
sys.exit(1 if errors else 0)
