#!/usr/bin/env python3
"""Local human review. Engine checks and a human decision are distinct evidence."""
import json,subprocess,threading
from pathlib import Path
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import unquote,urlparse
ROOT=Path(__file__).resolve().parents[1];LOCK=threading.Lock()
def read(p):return json.loads(p.read_text())
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def allowed(self):return self.headers.get('Host') in {f'localhost:{self.server.server_port}',f'127.0.0.1:{self.server.server_port}'}
 def data(self,status,j):
  b=json.dumps(j,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if not self.allowed():return self.send_error(403)
  if self.path=='/api/run':
   m=read(ROOT/'manifest.json');checks=read(ROOT/'evidence/final/checks.json') if (ROOT/'evidence/final/checks.json').exists() else None
   return self.data(200,{'manifest':m,'checks':checks,'task':read(ROOT/'task.json'),'contract':read(ROOT/'contract/acceptance.json')})
  if self.path=='/':self.path='/review/index.html'
  target=(ROOT/unquote(urlparse(self.path).path).lstrip('/')).resolve()
  if not target.is_relative_to(ROOT):return self.send_error(403)
  super().do_GET()
 def do_POST(self):
  if not self.allowed():return self.send_error(403)
  o=self.headers.get('Origin')
  if o and o not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:return self.send_error(403)
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=20000:raise ValueError('Invalid request')
   j=json.loads(self.rfile.read(n))
   if self.path=='/api/play':
    g=read(ROOT/'runtime.json')['godot'];out=ROOT/'play_sessions'/datetime.now().strftime('%Y%m%d-%H%M%S-%f');out.mkdir(parents=True)
    cmd=[g,'--path',str(ROOT/'project'),'--rendering-method','gl_compatibility']
    with (out/'play.log').open('w') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    write(out/'launch.json',{'command':cmd,'pid':p.pid});return self.data(200,{'message':'已打开修改后的赛道。W加速，S制动/倒车，A/D转向；关闭窗口退出。','pid':p.pid})
   if self.path!='/api/review':return self.send_error(404)
   if j.get('decision') not in ['accept','reject'] or not isinstance(j.get('comment',''),str):raise ValueError('Invalid review')
   with LOCK:
    m=read(ROOT/'manifest.json')
    if m['status']!='awaiting_human' or m.get('human_review'):raise ValueError('当前没有待审阅的最终结果，或已提交决定')
    checks=read(ROOT/'evidence/final/checks.json')
    if j['decision']=='accept' and not checks.get('hard_pass'):raise ValueError('自动硬检查尚未全部通过')
    review={'decision':j['decision'],'comment':j.get('comment','').strip(),'timestamp':now(),'reviewer':'human via local review UI','candidate_sha256':m.get('final_main_sha256')}
    write(ROOT/'human-review.json',review);m['human_review']=review;m['status']='accepted' if review['decision']=='accept' else 'rejected';write(ROOT/'manifest.json',m)
    with (ROOT/'trajectory.jsonl').open('a') as f:f.write(json.dumps({'event':'human_review',**review},ensure_ascii=False)+'\n')
   return self.data(200,{'message':'你的决定已保存，自动验证证据保持原样。'})
  except (ValueError,KeyError,FileNotFoundError) as e:return self.data(400,{'error':str(e)})
if __name__=='__main__':
 print('Racing review: http://127.0.0.1:8767/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8767),Handler).serve_forever()
