#!/usr/bin/env python3
"""Local input catalogue; launching a scene never executes a task query."""
import argparse, json, subprocess
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
from inputs import ROOT, command
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def allowed(self):return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
    def do_GET(self):
        if not self.allowed():return self.send_error(403)
        target=(ROOT/unquote(urlparse(self.path).path).lstrip('/')).resolve()
        if not target.is_relative_to(ROOT):return self.send_error(403)
        super().do_GET()
    def do_POST(self):
        if not self.allowed():return self.send_error(403)
        origin=self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:return self.send_error(403)
        if self.path!='/api/play':return self.send_error(404)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<4096:raise ValueError('Invalid body')
            req=json.loads(self.rfile.read(n));cmd=command(req['task_id'])
            out=ROOT/'sessions'/datetime.now().strftime('%Y%m%d-%H%M%S-%f');out.mkdir(parents=True)
            with (out/'play.log').open('w') as f:proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            (out/'launch.json').write_text(json.dumps({'task_id':req['task_id'],'command':cmd,'pid':proc.pid},indent=2))
            data=json.dumps({'ok':True,'message':'初始场景已启动；尚未执行任务需求。关闭游戏窗口可退出。','pid':proc.pid}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        except (ValueError,KeyError,FileNotFoundError) as e:
            self.send_error(400,str(e))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);a=p.parse_args()
    print(f'Input catalogue: http://127.0.0.1:{a.port}/',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
