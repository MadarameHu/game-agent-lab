#!/usr/bin/env python3
"""Run a real model -> scene -> Godot verification loop. No human auto-approval."""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pipeline.model_client import ModelClient
from pipeline.runtime import load_runtime
from review.server import ReviewStore

def now():
    return datetime.now(timezone.utc).isoformat()

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

def append(path, event):
    with path.open("a") as stream:
        stream.write(json.dumps({"timestamp": now(), **event}, ensure_ascii=False) + "\n")

def parse_action(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("moves"), list) or not data["moves"]:
        raise ValueError("Model must return an object with a nonempty moves array")
    return data

def apply_action(scene, action, require_all=False):
    candidate = copy.deepcopy(scene)
    by_id = {o["id"]: o for o in candidate["objects"]}
    seen = set()
    for move in action["moves"]:
        oid = move.get("id")
        if oid not in by_id or oid in seen:
            raise ValueError("Unknown or repeated object ID")
        p = move.get("position")
        if (not isinstance(p, list) or len(p) != 3 or
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in p)
            or p[1] != 0 or any(abs(v) > 20 for v in p)):
            raise ValueError("Position must be finite [x,0,z] in bounded world coordinates")
        by_id[oid]["position"] = p
        seen.add(oid)
    if require_all and seen != set(by_id):
        raise ValueError("Initial generation must place all six catalogue objects")
    # Only positions are accepted. Room, goal, dimensions and IDs cannot be changed by the model.
    return candidate

def prompt(scene, checks, mode):
    system = """You are a spatial layout assistant editing a small executable 3D warehouse scene.
Return ONLY a JSON object: {"moves":[{"id":"crate_03","position":[x,0,z]}],"reason":"short explanation"}.
Do not emit code or markdown. You may only move existing objects; do not resize, delete, add or rotate them.
Coordinates are meters; X east/west, Z north/south, Y vertical. position Y is bottom and must remain zero.
Room inner rectangle: X [-6,6], Z [-5,5]. Player center starts at [-4,0,0] and must WALK to [4,0,0].
Use the object's entire box dimensions for boundaries and overlaps. Leave at least 0.8m wide continuous paths
for a radius .30m capsule. Keep start/goal clear. Avoid placing crates on top of each other.
The engine, not you, determines success. A smaller change is preferable when repairing.
"""
    payload = {"operation": mode, "brief": scene["brief"], "scene": scene}
    if checks is None:
        payload["instruction"] = "Generate a fresh arrangement: return a position for ALL SIX objects. Catalogue positions are placeholders. Keep a clear central east-west corridor. Arrange storage along the room perimeter with space between boxes."
    else:
        payload["engine_feedback"] = checks
        payload["instruction"] = "Repair the actual failed engine checks. Return only the objects you need to move; keep every other object unchanged."
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]

def verify(runtime, scene, folder, headless=False):
    write(folder / "scene.json", scene)
    command = [runtime["godot"]]
    if headless:
        command.append("--headless")
    command += ["--path", str(ROOT / "engine"), "--", "--spec", str(folder / "scene.json"), "--out", str(folder)]
    started = time.time()
    proc = subprocess.run(command, text=True, capture_output=True, timeout=100)
    (folder / "engine.log").write_text(proc.stdout + "\n" + proc.stderr)
    write(folder / "execution.json", {"command": command, "exit_code": proc.returncode, "elapsed_seconds": time.time()-started,
            "scene_sha256": hashlib.sha256((folder / "scene.json").read_bytes()).hexdigest()})
    if proc.returncode != 0:
        raise RuntimeError("Godot process failed; see engine.log and execution.json")
    if not (folder / "checks.json").exists():
        raise RuntimeError("Godot did not produce checks.json; see engine.log")
    result = json.loads((folder / "checks.json").read_text())
    if not isinstance(result.get("hard_pass"), bool):
        raise RuntimeError("Malformed engine report")
    return result

def run(args):
    runtime = load_runtime(ROOT)
    if not runtime["godot"]:
        raise ValueError("Set GODOT_BIN or run launch.py configure before generating a scene")
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S-") + args.mode
    if not all(c.isalnum() or c in "-_." for c in run_id) or run_id in (".", ".."):
        raise ValueError("Invalid run ID")
    directory = ROOT / "runs" / run_id
    if directory.exists():
        raise ValueError("Run already exists; use a new ID to preserve evidence")
    directory.mkdir(parents=True)
    trace = directory / "trajectory.jsonl"
    scene = json.loads((ROOT / "fixtures" / "blocked-room.json").read_text())
    if args.mode == "generate":
        # Values are explicitly placeholders, not an accepted scene nor a hidden repair.
        for o in scene["objects"]:
            o["position"] = [0, 0, 0]
    client = ModelClient()
    health = client.health()
    write(directory / "model-health.json", health)
    manifest = {"run_id": run_id, "brief": scene["brief"], "created_at": now(), "mode": args.mode,
                "model": {**health.get("model", {}), "deployment": "Transformers via configured SSH service", "health": health},
                "model_call_count": 0, "status": "running", "candidates": [], "final_candidate_id": None, "human_review": None,
                "implementation": "Independent public-component implementation; not original paper reproduction"}
    write(directory / "manifest.json", manifest)
    write(ROOT / "runs" / "latest.json", {"run_id": run_id})
    append(trace, {"type": "run_started", "mode": args.mode, "brief": scene["brief"], "human_review": None})

    def record_candidate(cid, origin, scene, model_response=None):
        folder = directory / "candidates" / cid
        checks = verify(runtime, scene, folder, args.headless)
        entry = {"id": cid, "origin": origin, "spec": f"candidates/{cid}/scene.json", "checks": f"candidates/{cid}/checks.json",
                 "screenshot": f"candidates/{cid}/scene.png" if (folder / "scene.png").exists() else None}
        if model_response:
            entry["model_response"] = model_response
        manifest["candidates"].append(entry)
        manifest["final_candidate_id"] = cid
        write(directory / "manifest.json", manifest)
        append(trace, {"type": "engine_verification", "candidate_id": cid, "origin": origin,
                       "hard_pass": checks["hard_pass"], "engine_reward": checks["engine_reward"], "checks_path": entry["checks"],
                       "scene_sha256": hashlib.sha256((folder / "scene.json").read_bytes()).hexdigest()})
        print(json.dumps({"candidate": cid, "origin": origin, "hard_pass": checks["hard_pass"], "engine_reward": checks["engine_reward"]}), flush=True)
        return checks

    try:
        checks = record_candidate("000-blocked-fixture", "fixture", scene) if args.mode == "repair" else None
        for attempt in range(1, args.max_calls+1):
            cid = f"{attempt:03d}-model"
            request = {"messages": prompt(scene, checks, args.mode), "max_new_tokens": 2048, "temperature": 0,
                       "request_id": f"{run_id}-{cid}"}
            write(directory / f"requests/{cid}.json", request)
            append(trace, {"type": "model_request", "candidate_id": cid, "request_path": f"requests/{cid}.json"})
            response = client.generate(**request)
            manifest["model_call_count"] += 1
            write(directory / f"responses/{cid}.json", response)
            append(trace, {"type": "model_response", "candidate_id": cid, "response_path": f"responses/{cid}.json", "usage": response.get("usage")})
            write(directory / "manifest.json", manifest)
            if response.get("finish_reason") == "length":
                raise ValueError("Model output was truncated; saved response is not a valid candidate")
            action = parse_action(response["raw_text"])
            updated = apply_action(scene, action, require_all=args.mode == "generate" and attempt == 1)
            write(directory / f"actions/{cid}.json", action)
            append(trace, {"type": "scene_edit", "candidate_id": cid, "moves": action["moves"], "model_reason": action.get("reason"),
                           "previous_candidate_id": manifest["final_candidate_id"]})
            scene = updated
            checks = record_candidate(cid, "model", scene, f"responses/{cid}.json")
            if checks["hard_pass"]:
                break
        manifest["status"] = "awaiting_human"
        manifest["completed_at"] = now()
        write(directory / "manifest.json", manifest)
        ReviewStore(ROOT).exports(directory, manifest)
        append(trace, {"type": "awaiting_human_review", "candidate_id": manifest["final_candidate_id"],
                       "engine_pass": checks["hard_pass"], "human_accept": None, "combined_reward": None})
        print(json.dumps({"run": run_id, "engine_pass": checks["hard_pass"], "model_calls": manifest["model_call_count"], "human_review": "pending"}), flush=True)
        return 0 if checks["hard_pass"] else 2
    except Exception as exc:
        manifest["status"] = "error"
        manifest["error"] = str(exc)
        write(directory / "manifest.json", manifest)
        append(trace, {"type": "run_error", "error": str(exc)})
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["repair", "generate"], default="repair")
    parser.add_argument("--run-id")
    parser.add_argument("--max-calls", type=int, default=3)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_calls <= 5:
        parser.error("max-calls must be 1..5")
    raise SystemExit(run(args))
