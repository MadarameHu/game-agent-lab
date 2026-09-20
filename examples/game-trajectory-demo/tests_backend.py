#!/usr/bin/env python3
"""Backend tests use isolated artificial files only; never accept a genuine case."""
import http.client
import importlib.util
import json
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('trajectory_server', HERE / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
WORK = HERE.parents[1] / 'work/game-trajectory-demo/backend'


class BackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = WORK / ('tests-' + uuid.uuid4().hex)
        cls.root = cls.fixture / 'demo'
        cls.roots = {k: cls.fixture / k for k in ['batch', 'racing01', 'inputs', 'prd']}
        cls.case = cls.roots['batch'] / 'cases/platformer-test'
        for p in [cls.root / 'web', cls.case / 'project/scripts', cls.case / 'verification', cls.case / 'contract', cls.case / 'evidence/final', cls.roots['inputs'] / 'bases/platformer/project/scripts']:
            p.mkdir(parents=True, exist_ok=True)
        (cls.root / 'web/index.html').write_text('demo')
        cls.roots['prd'].mkdir()
        (cls.roots['prd'] / 'PRD.md').write_text('# Fixture PRD')
        (cls.case / 'project/project.godot').write_text('[application]\nconfig/name="fixture"\n')
        (cls.case / 'project/scripts/player.gd').write_text('extends Node\n# final\n')
        (cls.roots['inputs'] / 'bases/platformer/project/scripts/player.gd').write_text('extends Node\n# initial\n')
        (cls.case / 'verification/test.gd').write_text('# fixture checker')
        server.atomic_write(cls.case / 'source.json', {'base_id': 'platformer'})
        server.atomic_write(cls.case / 'contract/acceptance.json', {'criteria': ['fixture']})
        contract = server.digest(cls.case / 'contract/acceptance.json')
        server.atomic_write(cls.case / 'evidence/final/result.json', {'hard_pass': True, 'checks': [{'pass': True}], 'contract_sha256': contract})
        server.atomic_write(cls.case / 'evidence/root-review.json', {'pass': True, 'project_hashes': server.hashes(cls.case / 'project')})
        server.atomic_write(cls.case / 'manifest.json', {'human_review': None})
        server.atomic_write(cls.root / 'data.json', {'cases': [{'id': 'platformer-test', 'category': 'platformer', 'hard_pass': True, 'review': None}]})
        cls.app = server.Demo(cls.root, cls.roots)
        cls.httpd = server.create_server(cls.app, 0)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def request(self, path, body=None, headers=None):
        con = http.client.HTTPConnection('127.0.0.1', self.httpd.server_port)
        h = {'Content-Type': 'application/json'}
        h.update(headers or {})
        con.request('POST' if body is not None else 'GET', path, json.dumps(body) if body is not None else None, h)
        response = con.getresponse()
        raw = response.read()
        result = (response.status, json.loads(raw) if response.getheader('Content-Type', '').startswith('application/json') else raw)
        con.close()
        return result

    def binding(self):
        c = self.app.state()['cases'][0]
        return {k: c[k] for k in ['id', 'candidate_hash', 'contract_hash']}

    def test_01_state_and_diff(self):
        status, body = self.request('/api/state')
        self.assertEqual(status, 200)
        self.assertEqual(body['cases'][0]['integrity'], 'verified')
        self.assertIsNone(body['cases'][0]['review'])
        status, body = self.request('/api/diff?id=platformer-test&path=scripts/player.gd')
        self.assertEqual(status, 200)
        self.assertIn('-# initial', body['diff'])
        self.assertIn('+# final', body['diff'])
        self.assertTrue(body['before_available'])

    def test_02_path_and_host_protection(self):
        for path in ['/files/batch/../demo/data.json', '/files/batch/%2e%2e/demo/data.json', '/api/diff?id=platformer-test&path=../../source.json', '/files/unregistered/foo', '/sessions/arbitrary/project/project.godot']:
            self.assertEqual(self.request(path)[0], 400, path)
        self.assertEqual(self.request('/', headers={'Host': 'attacker.test'})[0], 403)
        self.assertEqual(self.request('/api/review', {}, {'Origin': 'https://attacker.test'})[0], 403)
        (self.roots['batch'] / 'escape').symlink_to(self.root / 'data.json')
        self.assertEqual(self.request('/files/batch/escape')[0], 400)
        self.assertEqual(self.request('/files/batch/cases/platformer-test/project/scripts/player.gd')[0], 200)
        self.assertEqual(self.request('/files/prd/PRD.md')[0], 200)
        self.assertEqual(self.request('/api/diff?id=unknown&path=scripts/player.gd')[0], 400)

    def test_03_stale_candidate_and_mutation(self):
        binding = self.binding()
        bad = {**binding, 'candidate_hash': 'old', 'decision': 'accept'}
        self.assertEqual(self.request('/api/review', bad)[0], 400)
        p = self.case / 'project/scripts/player.gd'
        content = p.read_text()
        p.write_text(content + '# changed\n')
        try:
            self.assertEqual(self.app.state()['cases'][0]['integrity'], 'changed')
            self.assertEqual(self.request('/api/play', binding)[0], 400)
            self.assertEqual(self.request('/api/review', {**binding, 'decision': 'accept'})[0], 400)
            restarted = server.Demo(self.root, self.roots)
            self.assertEqual(restarted.state()['cases'][0]['integrity'], 'changed')
        finally:
            p.write_text(content)
        p = self.case / 'verification/test.gd'
        content = p.read_text()
        p.write_text('changed checker')
        try:
            self.assertEqual(self.app.state()['cases'][0]['integrity'], 'changed')
        finally:
            p.write_text(content)
        e = self.case / 'evidence/final/result.json'
        old = e.read_text()
        e.write_text(old + '\n')
        try:
            self.assertEqual(self.app.state()['cases'][0]['integrity'], 'changed')
        finally:
            e.write_text(old)
        p = self.case / 'contract/acceptance.json'
        content = p.read_text()
        p.write_text('{}')
        try:
            self.assertEqual(self.app.state()['cases'][0]['integrity'], 'changed')
        finally:
            p.write_text(content)

    def test_04_async_isolated_launch(self):
        executable = self.fixture / 'fake_godot.py'
        executable.write_text('#!' + sys.executable + '\nimport sys,time\nprint("fixture executable",flush=True)\ntime.sleep(.25)\n')
        executable.chmod(0o755)
        server.atomic_write(self.roots['batch'] / 'runtime.json', {'godot': str(executable)})
        initial = server.hashes(self.case / 'project')
        status, response = self.request('/api/play', self.binding())
        self.assertEqual(status, 200)
        sid = response['session_id']
        self.assertIn(response['status'], ['preparing', 'importing'])
        duplicate = self.request('/api/play', self.binding())[1]
        self.assertEqual(duplicate['session_id'], sid)
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            status, current = self.request('/api/play-status?session_id=' + sid)
            if current['status'] in ['closed', 'failed']:
                break
            time.sleep(.05)
        self.assertEqual(current['status'], 'closed', current)
        self.assertEqual(initial, server.hashes(self.case / 'project'))
        product = self.root / 'sessions' / sid / 'project'
        self.assertIn('CodexTrajectoryDemo/platformer-test', (product / 'project.godot').read_text())
        self.assertEqual((product / 'scripts/player.gd').read_text(), (self.case / 'project/scripts/player.gd').read_text())
        self.assertEqual(self.request(current['log_url'])[0], 200)
        self.assertEqual(self.request('/api/play-status?session_id=missing')[0], 400)

    def test_05_original_review_preserved(self):
        old = {'decision': 'reject', 'comment': 'original fixture decision'}
        server.atomic_write(self.case / 'manifest.json', {'human_review': old})
        try:
            state = self.app.state()['cases'][0]
            self.assertEqual(state['review'], old)
            self.assertEqual(state['review_source'], 'original')
            self.assertFalse(state['reviewable'])
            self.assertEqual(self.request('/api/review', {**self.binding(), 'decision': 'accept'})[0], 400)
        finally:
            server.atomic_write(self.case / 'manifest.json', {'human_review': None})

    def test_06_fixture_review_is_immutable(self):
        binding = self.binding()
        self.assertEqual(self.request('/api/review', {**binding, 'decision': 'reject', 'comment': ''})[0], 400)
        status, body = self.request('/api/review', {**binding, 'decision': 'accept', 'comment': 'Test fixture only; not a real human result'})
        self.assertEqual(status, 200)
        self.assertEqual(body['review']['candidate_hash'], binding['candidate_hash'])
        self.assertEqual(self.request('/api/review', {**binding, 'decision': 'reject', 'comment': 'overwrite'})[0], 400)
        self.assertIsNone(server.read(self.case / 'manifest.json')['human_review'])
        state = self.app.state()['cases'][0]
        self.assertEqual(state['review_source'], 'demo')
        self.assertTrue(state['review_binding_valid'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
