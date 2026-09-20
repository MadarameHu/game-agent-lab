# Godot warehouse verifier

Independent executable implementation of the paper's proposed workflow, not its original Unity checker, assets, model, or benchmark scores.

The fixed 12 × 10 × 3 m room contains an actual `StaticBody3D` floor/walls and one `BoxShape3D` per object. The visual room has low boundary rails to keep the overview readable, while the colliding walls are 3 m high. Object positions are bottom centers; player position is the capsule's bottom. Optional CC0 Kenney GLB meshes are normalized by their combined AABB to each declared collision box. All collision checks use the boxes, including when a barrel/shelf visual has internal empty space. Visual details never add rewards.

First import optional resources (required after copying fresh GLB/textures):

```sh
GODOT --headless --editor --import --path ENGINE --quit
```

Verify with a screenshot on a native display:

```sh
GODOT --path ENGINE -- --spec ABS_SCENE_JSON --out ABS_RESULT_DIR
```

Add `--headless` before `--path` for the same physics verification without screenshots. Add `--play` after the scene arguments to play manually: WASD/arrows move along ground axes, R resets, Esc closes. Play mode never runs the agent or assumes human acceptance. The engine's acceptance badge is explicitly engine validation, not a human review.

In play mode, a short movement-key press is buffered for 0.12 seconds so a tap between physics frames remains visible. Held keys retain continuous movement, and R clears the buffer. Verification rollouts do not use this input buffer.

## Checks

All five checks are hard gates. `engine_reward` is the sum of passed check weights; `hard_pass` is true only when every check passes. The outer pipeline must use the hard gate for combined training reward.

| Check | Weight | Implementation |
|---|---:|---|
| scene_load | .10 | Typed JSON structure, at least 6 unique objects, finite dimensions, fixed room/player/goal, supported axis-aligned shapes |
| bounds | .15 | Exact declared collider extents versus room inner bounds, 1 mm numeric tolerance |
| no_overlap | .20 | Actual `PhysicsDirectSpaceState3D.intersect_shape` for each box, excluding itself; each probe is 4 mm smaller in total extent, allowing touching faces |
| route_exists | .25 | 0.25 m grid with actual capsule shape queries, radius .30 + .02 m clearance; 4-neighbor BFS |
| rollout_reaches_goal | .30 | Real `CharacterBody3D.move_and_slide`, gravity, 60 Hz, following BFS waypoints at up to 3.5 m/s; goal distance ≤ .65 m |

The rollout is limited to 2,400 physics steps and aborts after 120 stagnant steps. `checks.json` records settings, failures, asset source mode, trajectory samples, and repair hints. Native verification also writes `scene.png`.

## Limits

This is ground-plane walking around static, axis-aligned boxes. It is not a NavMesh test, physics stability simulation, an aesthetic scorer, or a test of a general world model. The finite grid can conservatively miss narrow valid routes, and endpoint occupancy can admit a candidate segment that a real rollout then rejects. Barrel/shelf collisions deliberately remain full boxes matching the JSON specification. Objects in v1 have no rotation and must fit inside the 3 m height.

`tests/manual-open-fixture.json` is a **hand-edited engine sanity fixture**, not a model-generated repair. The root pipeline saves real model candidates separately under `runs/`.
