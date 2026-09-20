#!/usr/bin/env python3
"""Local batch review; agents never submit a human acceptance decision."""
import argparse, hashlib, json, re, shutil, subprocess, threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse
ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()
RUNNING = {}
def read(p, default=None):
    return json.loads(p.read_text()) if p.exists() else default
def write(p, value):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def case_path(identifier):
    ids={c['id'] for c in read(ROOT/'catalog.json')['cases']}
    if identifier not in ids:raise ValueError('未知任务')
    return ROOT/'cases'/identifier
def current_integrity(case):
    audit=read(case/'evidence/root-review.json',{})
    if not audit.get('pass'):return False
    actual={str(p.relative_to(case/'project')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (case/'project').rglob('*') if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts}
    return actual==audit.get('project_hashes')
def state():
    result=[]
    for c in read(ROOT/'catalog.json')['cases']:
        case=ROOT/c['path'];m=read(case/'manifest.json',{});r=read(case/'evidence/final/result.json');audit=read(case/'evidence/root-review.json')
        result.append({**c,'manifest':m,'task':read(case/'task.json'),'result':r,'audit':audit,
            'preview':str((case/'evidence/final/scene.png').relative_to(ROOT)) if (case/'evidence/final/scene.png').exists() else None,
            'baseline_preview':f"previews/{c['base_id']}.png",
            'captures':[{'name':p.name,'path':str(p.relative_to(ROOT))} for p in sorted((case/'evidence/final').glob('*.png')) if p.name!='scene.png'],
            'reviewable':bool(r and r.get('hard_pass') and audit and audit.get('pass'))})
    return {'cases':result,'updated_at':now(),'previous_case_url':'http://127.0.0.1:8767/'}
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def allowed(self):return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
    def respond(self,code,value):
        b=json.dumps(value,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if not self.allowed():return self.send_error(403)
        if self.path=='/api/state':return self.respond(200,state())
        if self.path=='/':self.path='/review/index.html'
        target=(ROOT/unquote(urlparse(self.path).path).lstrip('/')).resolve()
        if not target.is_relative_to(ROOT):return self.send_error(403)
        super().do_GET()
    def do_POST(self):
        if not self.allowed():return self.send_error(403)
        origin=self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:return self.send_error(403)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=20000:raise ValueError('请求大小无效')
            body=json.loads(self.rfile.read(n));case=case_path(body['id'])
            if self.path=='/api/play':
                result=read(case/'evidence/final/result.json',{})
                if not result.get('hard_pass'):raise ValueError('此任务尚未完成自动检查')
                with LOCK:
                    old=RUNNING.get(body['id'])
                    if old and old.poll() is None:return self.respond(200,{'message':'此任务的试玩窗口已经打开。'})
                    run=ROOT/'sessions'/datetime.now().strftime('%Y%m%d-%H%M%S-%f');run.mkdir(parents=True)
                    snapshot=run/'project'
                    shutil.copytree(case/'project',snapshot,ignore=shutil.ignore_patterns('.godot','__pycache__'))
                    settings=snapshot/'project.godot';source=settings.read_text()
                    # Only runtime user-storage settings differ from the reviewed product.
                    source=re.sub(r'^config/(?:use_custom_user_dir|custom_user_dir_name)=.*\n','',source,flags=re.M)
                    source=source.replace('[application]','[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="CodexGameCases/'+body['id']+'"',1)
                    settings.write_text(source)
                    godot=read(ROOT/'runtime.json')['godot']
                    import_cmd=[godot,'--headless','--editor','--import','--quit','--path',str(snapshot),'--rendering-method','gl_compatibility']
                    with (run/'import.log').open('w') as log:imported=subprocess.run(import_cmd,stdout=log,stderr=subprocess.STDOUT,timeout=60)
                    if imported.returncode or 'SCRIPT ERROR' in (run/'import.log').read_text():raise ValueError('试玩资源导入失败，请查看 sessions 中的日志。')
                    command=[godot,'--path',str(snapshot),'--rendering-method','gl_compatibility']
                    with (run/'play.log').open('w') as log:p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                    RUNNING[body['id']]=p
                    write(run/'launch.json',{'case':body['id'],'command':command,'import_command':import_cmd,'pid':p.pid,'timestamp':now(),'source_project':str(case/'project'),'runtime_settings_override':'case-specific user:// directory; original game code and scene copied unchanged'})
                return self.respond(200,{'message':'已启动修改后的工程。关闭游戏窗口即可退出。','pid':p.pid})
            if self.path!='/api/review':return self.send_error(404)
            if body.get('decision') not in ['accept','reject'] or not isinstance(body.get('comment',''),str):raise ValueError('审阅内容无效')
            with LOCK:
                manifest=read(case/'manifest.json');result=read(case/'evidence/final/result.json',{})
                if manifest.get('human_review'):raise ValueError('该候选已有人工决定，历史记录不覆盖。')
                if manifest.get('status')!='awaiting_human':raise ValueError('该任务目前不处于待人工验收状态。')
                if not result.get('hard_pass') or not current_integrity(case):raise ValueError('自动验证或交付核对未通过，或工程在验证后已改变。')
                review={'decision':body['decision'],'comment':body.get('comment','').strip(),'timestamp':now(),'reviewer':'human via local review UI'}
                write(case/'human-review.json',review);manifest['human_review']=review;manifest['status']='accepted' if body['decision']=='accept' else 'rejected';write(case/'manifest.json',manifest)
                with (case/'trajectory.jsonl').open('a') as f:f.write(json.dumps({'event':'human_review',**review},ensure_ascii=False)+'\n')
            return self.respond(200,{'message':'人工决定已单独保存，原自动验证记录保持不变。'})
        except (ValueError,KeyError,FileNotFoundError,OSError,subprocess.TimeoutExpired) as e:return self.respond(400,{'error':str(e)})
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8768);args=ap.parse_args()
    print(f'Game case review: http://127.0.0.1:{args.port}/',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
