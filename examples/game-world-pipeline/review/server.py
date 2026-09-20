#!/usr/bin/env python3
"""Local, human-operated review of immutable engine verification evidence."""
from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from pipeline.runtime import load_runtime
LOCK = threading.Lock()
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def within(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("必须使用运行目录内的相对路径")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("路径超出运行目录")
    return path


class ReviewStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.runs = self.root / "runs"

    def run(self, run_id=None):
        run_id = run_id or read_json(self.runs / "latest.json")["run_id"]
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            raise ValueError("无效 run_id")
        directory = within(self.runs, run_id)
        manifest = read_json(directory / "manifest.json")
        if manifest.get("run_id") != run_id:
            raise ValueError("run_id 与 manifest 不一致")
        return directory, manifest

    def final(self, directory, manifest):
        candidates = manifest.get("candidates", [])
        candidate = next((c for c in candidates if c["id"] == manifest.get("final_candidate_id")), None)
        if candidate is None:
            raise ValueError("最终候选尚未生成")
        checks = read_json(within(directory, candidate["checks"]))
        return candidate, checks

    def list_runs(self):
        rows = []
        if not self.runs.exists():
            return rows
        for directory in sorted(self.runs.iterdir()):
            if not directory.is_dir() or not RUN_ID.fullmatch(directory.name):
                continue
            try:
                _, manifest = self.run(directory.name)
            except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError):
                continue
            mode = manifest.get("mode")
            if mode not in ("generate", "repair"):
                mode = "repair" if any(c.get("origin") == "fixture" for c in manifest.get("candidates", [])) else "generate"
            rows.append({"run_id": manifest["run_id"], "mode": mode,
                         "display_label": "从需求生成" if mode == "generate" else "从失败场景修复",
                         "status": manifest.get("status"), "model_call_count": manifest.get("model_call_count")})
        return rows

    @staticmethod
    def passes(checks):
        required = {"scene_load", "bounds", "no_overlap", "route_exists", "rollout_reaches_goal"}
        entries = checks.get("checks", [])
        return (checks.get("hard_pass") is True and required.issubset({c.get("id") for c in entries})
                and all(c.get("pass") is True for c in entries))

    def view(self, run_id=None):
        directory, manifest = self.run(run_id)
        candidates = []
        for candidate in manifest.get("candidates", []):
            item = dict(candidate)
            for key in ("spec", "checks"):
                try:
                    item[key + "_data"] = read_json(within(directory, item[key]))
                except (FileNotFoundError, KeyError, json.JSONDecodeError):
                    item[key + "_data"] = None
            candidates.append(item)
        trajectory = []
        trace = directory / "trajectory.jsonl"
        if trace.exists():
            for line in trace.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        trajectory.append(json.loads(line))
                    except json.JSONDecodeError:
                        trajectory.append({"unparsed_line": line})
        # Only JSON/text files already in this run are exposed, never runtime config or arbitrary paths.
        artifacts = []
        for p in sorted(directory.rglob("*")):
            if p.is_file() and p.resolve().is_relative_to(directory.resolve()) and p.suffix in (".json", ".jsonl", ".txt", ".log"):
                if p.stat().st_size <= 2_000_000:
                    artifacts.append({"path": str(p.relative_to(directory)), "text": p.read_text(encoding="utf-8", errors="replace")})
        final = next((c for c in candidates if c["id"] == manifest.get("final_candidate_id")), {})
        can_accept = manifest.get("status") == "awaiting_human" and self.passes(final.get("checks_data") or {})
        return {"manifest": manifest, "candidates": candidates, "trajectory": trajectory,
                "artifacts": artifacts, "can_accept": can_accept}

    def exports(self, directory, manifest):
        review = manifest.get("human_review")
        sft, transitions = [], []
        candidates = manifest.get("candidates", [])
        for index, candidate in enumerate(candidates):
            if candidate.get("origin") != "model":
                continue
            checks = read_json(within(directory, candidate["checks"]))
            scene = read_json(within(directory, candidate["spec"]))
            is_final = candidate["id"] == manifest.get("final_candidate_id")
            candidate_review = review if is_final else None
            combined = None
            if candidate_review is not None:
                human_accept = int(candidate_review["decision"] == "accept")
                combined = int(self.passes(checks)) * (0.65 * human_accept + 0.35 * float(checks["engine_reward"]))
            prior = candidates[index - 1] if index else None
            previous_scene = read_json(within(directory, prior["spec"])) if prior else None
            previous_checks = read_json(within(directory, prior["checks"])) if prior else None
            action_path = within(directory, candidate.get("action") or f"actions/{candidate['id']}.json")
            action = read_json(action_path) if action_path.is_file() else None
            request_path = within(directory, candidate.get("model_request") or f"requests/{candidate['id']}.json")
            request = read_json(request_path) if request_path.is_file() else {}
            messages = request.get("messages")
            response_path = within(directory, candidate.get("model_response") or f"responses/{candidate['id']}.json")
            response = read_json(response_path) if response_path.is_file() else {}
            output = action if action is not None else response.get("raw_text")
            transitions.append({"schema_version": 1, "run_id": manifest["run_id"], "candidate_id": candidate["id"],
                "origin": "model", "model": manifest.get("model"), "brief": manifest.get("brief"),
                "previous_candidate_id": prior["id"] if prior else None,
                "previous_origin": prior.get("origin") if prior else None,
                "previous_scene": previous_scene, "previous_checks": previous_checks, "action": action,
                "scene": scene, "checks": checks, "engine_reward": checks.get("engine_reward"),
                "human_review": candidate_review, "combined_reward": combined})
            if (is_final and review and review["decision"] == "accept" and self.passes(checks)
                    and isinstance(messages, list) and messages and output is not None):
                sft.append({"schema_version": 1, "run_id": manifest["run_id"], "candidate_id": candidate["id"],
                    "origin": "model", "model": manifest.get("model"), "input": {"messages": messages},
                    "output": output, "result_scene": scene,
                    "context": {"brief": manifest.get("brief"), "previous_scene": previous_scene,
                                "previous_checks": previous_checks, "previous_origin": prior.get("origin") if prior else None},
                    "human_review": review})
        for name, rows in (("sft.jsonl", sft), ("rl_transitions.jsonl", transitions)):
            (directory / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    def review(self, run_id, decision, comment):
        if decision not in ("accept", "reject") or not isinstance(comment, str) or len(comment) > 10000:
            raise ValueError("审核决定或评论无效")
        with LOCK:
            directory, manifest = self.run(run_id)
            if manifest.get("status") != "awaiting_human" or manifest.get("human_review"):
                raise ValueError("此运行未等待审核，或已经审核")
            candidate, checks = self.final(directory, manifest)
            if decision == "accept" and not self.passes(checks):
                raise ValueError("最终候选未通过全部真实引擎硬检查，不能接受")
            review = {"decision": decision, "comment": comment.strip(), "timestamp": now()}
            manifest["human_review"] = review
            manifest["status"] = "accepted" if decision == "accept" else "rejected"
            write_json(directory / "review.json", review)
            with (directory / "trajectory.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"type": "human_review", "run_id": run_id, "candidate_id": candidate["id"], **review}, ensure_ascii=False) + "\n")
            write_json(directory / "manifest.json", manifest)
            self.exports(directory, manifest)
            return review

    def play(self, run_id):
        with LOCK:
            directory, manifest = self.run(run_id)
            candidate, checks = self.final(directory, manifest)
            runtime = load_runtime(self.root)
            if not runtime["godot"]:
                raise ValueError("请设置 GODOT_BIN，或运行 launch.py configure --godot PATH")
            project = Path(runtime["project_root"]).resolve()
            # project_root may name the pipeline root or its engine project.
            engine = project if (project / "project.godot").is_file() else project / "engine"
            if not (engine / "project.godot").is_file():
                raise ValueError("runtime.json 的 Godot 项目路径无效")
            out = directory / "play_sessions" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            out.mkdir(parents=True)
            command = [runtime["godot"], "--path", str(engine), "--", "--spec", str(within(directory, candidate["spec"])), "--out", str(out), "--play"]
            with (out / "play.log").open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            return {"pid": process.pid, "output": str(out.relative_to(directory)), "message": "Godot 试玩已启动；WASD 移动，R 重置，Esc 退出。"}


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, content_type="application/json; charset=utf-8"):
            payload = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, (dict, list)) else data
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            try:
                if self.headers.get("Host", "") not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
                    return self.send(403, {"error": "仅允许 localhost 访问"})
                url = urlparse(self.path)
                if url.path == "/api/run":
                    return self.send(200, store.view(parse_qs(url.query).get("run_id", [None])[0]))
                if url.path == "/api/runs":
                    return self.send(200, store.list_runs())
                if url.path.startswith("/run-file/"):
                    parts = unquote(url.path).split("/", 3)
                    if len(parts) != 4:
                        raise ValueError("无效文件路径")
                    directory, _ = store.run(parts[2])
                    path = within(directory, parts[3])
                    if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".json", ".jsonl", ".txt", ".log"):
                        raise ValueError("不允许读取此类型")
                    return self.send(200, path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream")
                filename = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}.get(url.path)
                if filename:
                    return self.send(200, (HERE / filename).read_bytes(), mimetypes.guess_type(filename)[0] + "; charset=utf-8")
                self.send(404, {"error": "未找到"})
            except FileNotFoundError:
                self.send(404, {"error": "运行或文件尚未生成"})
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                self.send(400, {"error": str(e)})

        def do_POST(self):
            try:
                # JSON content type prevents cross-origin form submission; Origin/Host defend local DNS rebinding.
                host = self.headers.get("Host", "")
                allowed_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
                if host not in allowed_hosts or self.headers.get("Origin", "http://" + host) != "http://" + host:
                    return self.send(403, {"error": "仅允许本机同源请求"})
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("必须提交 JSON")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 20000:
                    raise ValueError("请求长度无效")
                data = json.loads(self.rfile.read(length))
                if self.path == "/api/review":
                    return self.send(200, store.review(data["run_id"], data["decision"], data.get("comment", "")))
                if self.path == "/api/play":
                    return self.send(200, store.play(data["run_id"]))
                self.send(404, {"error": "未找到"})
            except (ValueError, KeyError, FileNotFoundError, OSError) as e:
                self.send(400, {"error": str(e)})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=HERE.parent)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(ReviewStore(args.root)))
    print(f"Review: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
