#!/usr/bin/env python3
"""Local read-only evidence viewer with isolated play copies and human-only decisions.

racing-01 predates complete project audit hashes: its recorded main, 48 protected
files, checker, driver and contract are checked, then a persistent full-project
fingerprint protects subsequent demo sessions. This is not a retroactive audit.
"""
import argparse
import copy
import difflib
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
TEXT_LIMIT = 500_000


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else default


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def hashes(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '.godot' not in p.parts and '__pycache__' not in p.parts}


def fingerprint(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or '\x00' in relative:
        raise ValueError('文件路径无效')
    value = Path(relative)
    if value.is_absolute() or '..' in value.parts:
        raise ValueError('不允许访问登记目录以外的路径')
    target = (root / value).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('不允许通过链接访问登记目录以外的文件')
    return target


class Demo:
    def __init__(self, root=HERE, roots=None):
        self.root = Path(root)
        outputs = self.root.parent
        self.roots = roots or {'batch': outputs / 'game-cases-v1', 'racing01': outputs / 'racing-01-run', 'inputs': outputs / 'game-inputs-v1', 'prd': outputs / 'game-trajectory-prd'}
        self.lock = threading.RLock()
        self.sessions = {}
        self.active = {}
        self.initial = read(self.root / 'data.json', {'cases': []})
        self.cases = {c['id']: c for c in self.initial['cases']}
        baseline_path = self.root / 'integrity-baseline.json'
        self.baseline = read(baseline_path, {})
        changed = False
        for identifier in self.cases:
            if identifier not in self.baseline:
                case = self.case_dir(identifier)
                self.baseline[identifier] = {'project': hashes(case / 'project'), 'verification': hashes(case / 'verification'),
                    'contract': digest(case / 'contract/acceptance.json'), 'evidence': hashes(case / 'evidence'), 'created_at': now(),
                    'note': 'Demo 首次启动时的文件指纹；不等于历史验证。'}
                changed = True
            elif 'evidence' not in self.baseline[identifier]:
                self.baseline[identifier]['evidence'] = hashes(self.case_dir(identifier) / 'evidence')
                changed = True
        if changed:
            atomic_write(baseline_path, self.baseline)

    def case_dir(self, identifier):
        if identifier not in self.cases:
            raise ValueError('未知任务')
        return self.roots['racing01'] if identifier == 'racing-01' else safe_path(self.roots['batch'] / 'cases', identifier)

    def integrity(self, identifier):
        case = self.case_dir(identifier)
        current = hashes(case / 'project')
        contract = digest(case / 'contract/acceptance.json')
        base = self.baseline[identifier]
        issues = []
        notes = []
        if current != base['project'] or hashes(case / 'verification') != base['verification'] or contract != base['contract']:
            issues.append('工程、检查器或验收契约相对 Demo 初次记录已改变。')
        if hashes(case / 'evidence') != base.get('evidence'):
            issues.append('验证证据相对 Demo 初次记录已改变。')
        if identifier == 'racing-01':
            r = read(case / 'evidence/final-verification-v2/result.json', {})
            protected = read(case / 'contract/protected-files.json', {})
            preserved = read(case / 'evidence/final/preservation.json', {})
            audit_ok = bool(r.get('checks') and all(v is True for v in r['checks'].values()) and preserved.get('pass'))
            recorded = {**protected, 'scenes/main.tscn': r.get('source_main_sha256')}
            if not recorded or any(current.get(p) != h for p, h in recorded.items()):
                issues.append('最终场景或受保护资源与原始验证记录不一致。')
            for name, key in [('drive_lap.gd', 'driver_sha256'), ('check_racing.py', 'checker_sha256')]:
                if digest(case / 'verification' / name) != r.get(key):
                    issues.append('赛车原始检查器与验证记录不一致。')
            recorded_contract = r.get('contract_sha256')
            notes.append('racing-01 已核对最终场景、48 个受保护文件、检查器、驾驶脚本及契约；完整工程指纹从本 Demo 首次启动起绑定，原记录没有完整工程历史审计。')
        else:
            r = read(case / 'evidence/final/result.json', {})
            audit = read(case / 'evidence/root-review.json', {})
            audit_ok = bool(audit.get('pass') and r.get('hard_pass') and r.get('checks') and all(c.get('pass') is True for c in r['checks']))
            if not audit.get('project_hashes'):
                audit_ok = False
            elif current != audit['project_hashes']:
                issues.append('当前工程与交叉核验时保存的完整工程指纹不一致。')
            for path, expected in r.get('verification_hashes', {}).items():
                if digest(safe_path(case, path)) != expected:
                    issues.append('检查器与最终验证记录不一致。')
            recorded_contract = r.get('contract_sha256')
        if not recorded_contract or recorded_contract != contract:
            issues.append('契约与最终验证记录不一致。')
        status = 'changed' if issues else ('verified' if audit_ok else 'unknown')
        return {'integrity': status, 'integrity_notes': notes + issues, 'candidate_hash': fingerprint(current), 'contract_hash': contract,
                'playable': status == 'verified', 'reviewable': status == 'verified' and bool(self.cases[identifier].get('hard_pass'))}

    def reviews(self, identifier):
        case = self.case_dir(identifier)
        manifest = read(case / 'manifest.json', {})
        original = manifest.get('human_review') or read(case / 'human-review.json') or self.cases[identifier].get('review')
        local = read(self.root / 'reviews' / (identifier + '.json'))
        return original, local

    def state(self):
        cases = []
        for identifier, source in self.cases.items():
            c = copy.deepcopy(source)
            c.update(self.integrity(identifier))
            original, local = self.reviews(identifier)
            c['review'] = original or local
            c['review_source'] = 'original' if original else ('demo' if local else None)
            c['review_binding_valid'] = (local.get('candidate_hash') == c['candidate_hash'] and local.get('contract_hash') == c['contract_hash']) if local and not original else None
            c['reviewable'] = c['reviewable'] and c['review'] is None
            if original:
                c['integrity_notes'].append('已有原页面人工决定，保留原记录；未记录完整指纹的旧决定不补造绑定。')
            cases.append(c)
        return {'cases': cases, 'updated_at': now()}

    def bound(self, body):
        identifier = body.get('id')
        info = self.integrity(identifier)
        if info['integrity'] != 'verified':
            raise ValueError('当前工程或验证记录未通过完整性核对，暂不能执行此操作。')
        if body.get('candidate_hash') != info['candidate_hash'] or body.get('contract_hash') != info['contract_hash']:
            raise ValueError('页面中的候选版本已过期，请刷新后重试。')
        return identifier, info

    def review(self, body):
        with self.lock:
            identifier, info = self.bound(body)
            if not info['reviewable']:
                raise ValueError('自动验证未通过，不能提交人工验收。')
            if any(self.reviews(identifier)):
                raise ValueError('此任务已有人工决定，历史记录不能覆盖。')
            if body.get('decision') not in {'accept', 'reject'}:
                raise ValueError('人工决定无效')
            comment = body.get('comment', '')
            if not isinstance(comment, str) or len(comment) > 6000:
                raise ValueError('审阅说明无效或超过 6000 字')
            if body['decision'] == 'reject' and not comment.strip():
                raise ValueError('退回修改时请填写原因。')
            items = body.get('item_reviews', {})
            if not isinstance(items, (dict, list)) or len(json.dumps(items)) > 12000:
                raise ValueError('逐项审阅内容无效')
            value = {k: body[k] for k in ('id', 'candidate_hash', 'contract_hash', 'decision')}
            value.update(comment=comment.strip(), item_reviews=items, timestamp=now(), reviewer='human via local demo UI')
            target = self.root / 'reviews' / (identifier + '.json')
            target.parent.mkdir(exist_ok=True)
            with target.open('x', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            return {'message': '人工决定已保存，并绑定当前工程和契约；原始验证记录保持不变。', 'review': value}

    def diff(self, identifier, path):
        case = self.case_dir(identifier)
        source = read(case / 'source.json', {})
        base_id = source.get('base_id') or self.cases[identifier]['category']
        if base_id not in {'racing', 'platformer', 'city-builder'}:
            raise ValueError('基础工程未登记')
        before = safe_path(self.roots['inputs'] / 'bases' / base_id / 'project', path)
        after = safe_path(case / 'project', path)
        if not before.is_file() and not after.is_file():
            raise FileNotFoundError('文件不存在')
        for p in (before, after):
            if p.is_file() and p.stat().st_size > TEXT_LIMIT:
                raise ValueError('此文件超过 500 KB，请查看原文件。')
        try:
            old = before.read_text() if before.is_file() else ''
            new = after.read_text() if after.is_file() else ''
            if '\x00' in old + new:
                raise UnicodeError()
        except UnicodeError:
            raise ValueError('此文件为二进制素材，不能生成文本差异。')
        diff = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='初始/' + path, tofile='最终/' + path))
        return {'path': path, 'before_available': before.is_file(), 'diff': diff, 'content': new, 'notes': ['对比原始基础工程与最终候选；不代表完整的模型逐轮输出。']}

    def play(self, body):
        with self.lock:
            identifier, info = self.bound(body)
            old = self.active.get(identifier)
            if old and self.sessions[old]['status'] in {'preparing', 'importing', 'running'}:
                return self.play_status(old)
            sid = uuid.uuid4().hex
            entry = {'session_id': sid, 'id': identifier, 'status': 'preparing', 'message': '正在准备独立试玩副本。', 'log_url': '/sessions/' + sid + '/launch.json'}
            self.sessions[sid] = entry
            self.active[identifier] = sid
            threading.Thread(target=self.launch, args=(sid, identifier, info), daemon=True).start()
            return dict(entry)

    def play_status(self, sid):
        with self.lock:
            if sid not in self.sessions:
                raise ValueError('试玩会话不存在')
            return dict(self.sessions[sid])

    def launch(self, sid, identifier, info):
        run = self.root / 'sessions' / sid
        run.mkdir(parents=True)
        entry = self.sessions[sid]
        def update(status, message, log=None):
            with self.lock:
                entry.update(status=status, message=message)
                if log:
                    entry['log_url'] = '/sessions/' + sid + '/' + log
                atomic_write(run / 'status.json', entry)
        try:
            case = self.case_dir(identifier)
            snapshot = run / 'project'
            shutil.copytree(case / 'project', snapshot, ignore=shutil.ignore_patterns('.godot', '__pycache__'))
            if fingerprint(hashes(snapshot)) != info['candidate_hash']:
                raise ValueError('复制过程中原工程发生变化，已中止启动。')
            settings = snapshot / 'project.godot'
            source = settings.read_text()
            source = re.sub(r'^config/(?:use_custom_user_dir|custom_user_dir_name)=.*\n', '', source, flags=re.M)
            if '[application]' not in source:
                raise ValueError('工程缺少 application 配置')
            source = source.replace('[application]', '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="CodexTrajectoryDemo/' + identifier + '"', 1)
            settings.write_text(source)
            runtime_root = self.roots['racing01'] if identifier == 'racing-01' else self.roots['batch']
            configured = os.environ.get('GODOT_BIN') or read(runtime_root / 'runtime.json', {}).get('godot')
            godot = (shutil.which(configured) or configured) if configured else (shutil.which('godot') or shutil.which('godot4'))
            if not godot or not Path(godot).is_file():
                raise ValueError('未找到 Godot。请设置 GODOT_BIN 或将 godot / godot4 加入 PATH。')
            command = [godot, '--path', str(snapshot), '--rendering-method', 'gl_compatibility']
            import_cmd = command + ['--headless', '--editor', '--import', '--quit']
            atomic_write(run / 'launch.json', {'id': identifier, 'candidate_hash': info['candidate_hash'], 'contract_hash': info['contract_hash'], 'timestamp': now(), 'import_command': import_cmd, 'command': command, 'runtime_override': 'Only isolated user:// settings; source remains read-only.'})
            update('importing', '正在导入试玩资源，通常需要几秒。', 'import.log')
            with (run / 'import.log').open('w') as log:
                result = subprocess.run(import_cmd, stdout=log, stderr=subprocess.STDOUT, timeout=90)
            logtext = (run / 'import.log').read_text(errors='replace')
            if result.returncode or 'SCRIPT ERROR' in logtext:
                raise ValueError('Godot 导入失败，请查看日志。')
            with (run / 'play.log').open('w') as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            update('running', '游戏窗口已启动，关闭游戏窗口即可退出。', 'play.log')
            code = process.wait()
            if code or 'SCRIPT ERROR' in (run / 'play.log').read_text(errors='replace'):
                update('failed', '游戏运行时报告错误，请查看日志。')
            else:
                update('closed', '试玩窗口已关闭。')
        except Exception as e:
            update('failed', str(e))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    @property
    def app(self):
        return self.server.app

    def origin_ok(self):
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        return self.headers.get('Host') in allowed and (not self.headers.get('Origin') or self.headers['Origin'] in {'http://' + h for h in allowed})

    def json(self, status, value):
        payload = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def file(self, path):
        if not path.is_file():
            raise FileNotFoundError('文件不存在')
        content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if path.suffix in {'.gd', '.tscn', '.tres', '.godot', '.jsonl', '.log', '.md', '.py', '.gdshader', '.uid'}:
            content_type = 'text/plain; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(path.stat().st_size))
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        with path.open('rb') as f:
            shutil.copyfileobj(f, self.wfile)

    def do_GET(self):
        if not self.origin_ok():
            return self.json(403, {'error': '只允许本机页面访问'})
        try:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            q = parse_qs(parsed.query)
            if path == '/api/state':
                return self.json(200, self.app.state())
            if path == '/api/diff':
                return self.json(200, self.app.diff(q.get('id', [''])[0], q.get('path', [''])[0]))
            if path == '/api/play-status':
                return self.json(200, self.app.play_status(q.get('session_id', [''])[0]))
            if path.startswith('/files/'):
                parts = path.split('/', 3)
                if len(parts) != 4 or parts[2] not in self.app.roots:
                    raise ValueError('文件来源未登记')
                return self.file(safe_path(self.app.roots[parts[2]], parts[3]))
            if path.startswith('/sessions/'):
                parts = path.strip('/').split('/')
                if len(parts) != 3 or not re.fullmatch('[a-f0-9]{32}', parts[1]) or parts[2] not in {'launch.json', 'import.log', 'play.log', 'status.json'}:
                    raise ValueError('试玩日志路径无效')
                return self.file(safe_path(self.app.root, path.lstrip('/')))
            if path.startswith('/api/'):
                return self.json(404, {'error': '接口不存在'})
            return self.file(safe_path(self.app.root / 'web', 'index.html' if path == '/' else path.lstrip('/')))
        except FileNotFoundError as e:
            self.json(404, {'error': str(e)})
        except (ValueError, KeyError, OSError) as e:
            self.json(400, {'error': str(e)})

    def do_POST(self):
        if not self.origin_ok():
            return self.json(403, {'error': '只允许本机页面访问'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 24000:
                raise ValueError('请求体大小无效')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('请求体必须为对象')
            if self.path == '/api/review':
                return self.json(200, self.app.review(body))
            if self.path == '/api/play':
                return self.json(200, self.app.play(body))
            return self.json(404, {'error': '接口不存在'})
        except (ValueError, KeyError, OSError) as e:
            self.json(400, {'error': str(e)})


def create_server(app, port=8769):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.app = app
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8769)
    args = parser.parse_args()
    app = Demo()
    print(f'Trajectory demo: http://127.0.0.1:{args.port}/ ({len(app.cases)} cases)', flush=True)
    create_server(app, args.port).serve_forever()
