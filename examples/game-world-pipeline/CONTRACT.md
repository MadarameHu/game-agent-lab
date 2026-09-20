# Runnable world-development pipeline contract

This is an independent implementation of the paper's workflow using public components, not a reproduction of its model or scores.

## Scene JSON v1

`schema_version: 1`, `brief: string`, `room: {width:12,depth:10,height:3}`, `player: {position:[-4,0,0],radius:0.3,height:1.6}`, `goal: {position:[4,0,0],radius:0.65}`, `objects: [{id:string,asset:"crate"|"barrel"|"shelf",position:[x,0,z],size:[width,height,depth],rotation_y:0}]`.

Positions are ground-based: object y is its bottom, not its center. Keep room, player, goal fixed. At least six objects must remain, with stable IDs. In v1 use axis-aligned boxes, rotation_y=0. Asset visuals are scaled to the exact collision box, with source/license recorded. Real engine collision shapes determine clearance, not image similarity.

## Engine interface

Godot project under `engine/`. CLI: GODOT --path ENGINE -- --spec ABS_SCENE_JSON --out ABS_RESULT_DIR [--play]. No `--play` means verification and screenshot then quit. Verification must work headless (skip screenshot only in actual headless mode) and with a normal native display (save scene.png). No model involvement in check computation.

`checks.json`: {schema_version:1, engine:{name,version}, checks:[{id,pass,weight,details}], hard_pass:boolean, engine_reward:number, repair_hints:[string], rollout:{reached_goal:boolean,steps:number,path:[[x,y,z]], ...}}.

Checks and weights: scene_load .10, bounds .15, no_overlap .20, route_exists .25, rollout_reaches_goal .30. All are hard gates. Include minimum-object-count in scene_load validation. Use actual Godot Physics queries for agent clearance/occupancy and a real CharacterBody3D physics rollout following the derived path. Explicitly document probe/grid resolution and overlap tolerance. Do not claim a NavMesh test if using grid BFS. Required actor radius .30; actual reach condition distance<=goal.radius. No aesthetic/"human" proxy scores.

`scene.png` shows the submitted scene from a clear overview. `--play` permits human WASD movement, R reset, Esc quit, goal success display; do not auto-run the agent in play mode. Model edits must stay confined to scene JSON.

## Runs / review interface

Each run: `runs/<run_id>/manifest.json`, `trajectory.jsonl`, `candidates/<candidate_id>/scene.json`, `checks.json`, `scene.png`, model request/response records. `runs/latest.json` is {run_id:string}.

Manifest: {run_id, brief, model:{name,...}, status:"running"|"awaiting_human"|"accepted"|"rejected", candidates:[{id,origin:"fixture"|"model",spec,checks,screenshot}], final_candidate_id, human_review:null|{decision,comment,timestamp}}. Candidate file paths are relative to run directory.

Review server under `review/` uses standard-library Python and local HTML/JS. Bind localhost. Read latest manifest; show before/after images, checker outcomes, exact model provenance, trajectory and input/output JSON. Human Accept is enabled only if final checks hard_pass=true. POST review appends a review event, saves review.json, updates manifest and generates human-reviewed exports. No acceptance is assumed before the user presses a button. Rejected candidates and failed checks remain in the trace.

Training export: supervised accepted model action conditioned on the authentic request messages, with final scene retained as result_scene for audit (sft.jsonl); transition records with engine_reward and human_review (rl_transitions.jsonl), where combined_reward is null until human decision exists; accepted final reward uses hard gate*(.65*human_accept+.35*engine_reward). Explain that no training update is performed in the smoke run.

## Ownership

- Model agent: DSW isolated model runner, local `pipeline/model_client.py`, model deployment notes/config (no secrets). Use the explicitly configured GPU only, recheck before loading; never touch other tasks.
- Engine agent: `engine/` only; report required asset interface. Root supplies runtime and licensed assets.
- Review agent: `review/` only. Root supplies manifest and runtime config. Runtime config path at project root `runtime.json`: {godot,project_root,model:{...}}.
- Root: orchestration, assets, runtime installation, fixtures, runs, README, integration and acceptance evidence.

## Minimum actual evidence

Use a clearly labeled blocked-room fixture for repair evaluation, never present a fixture as model-generated failure. Perform actual open-model inference to edit it; engine verifies each candidate independently. Also produce a model-generated candidate from the brief if feasible. At least one failed engine check, one real model repair, a passing final rollout, screenshot, playable scene, and pending human-review UI. Cap smoke inference at five calls; persist every attempt. No fake engine labels or hidden method bonuses.
