"""Deterministically replace only the GridMap cell serialization.

This is the coding agent's layout generator, not the acceptance verifier.
Tile IDs/orthogonal indices come from the independent inspection metadata.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent
SCENE = ROOT / "outputs/racing-01-run/project/scenes/main.tscn"
CONTRACT = ROOT / "outputs/racing-01-run/contract/acceptance.json"
METADATA = ROOT / "work/racing-01/validator/tile_metadata.json"
PATTERN = re.compile(r'(?m)^data = \{\n"cells": PackedInt32Array\([^\n]*\)\n\}')

# Ordered forward travel from the preserved spawn tile (+Z initially).
ROUTE = [(0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (0, 3),
         (-1, 3), (-2, 3), (-3, 3), (-3, 2), (-3, 1),
         (-3, 0), (-3, -1), (-3, -2), (-2, -2), (-1, -2),
         (0, -2), (0, -1)]
FOREST = [(-4, -4), (-3, -4), (-2, -4), (0, -4), (1, -4),
          (-4, -3), (-4, 0), (-4, 2)]
TENTS = [(2, 0)]
CORNER_ORIENTATIONS = {
    frozenset([(-1, 0), (0, 1)]): 0,
    frozenset([(1, 0), (0, -1)]): 10,
    frozenset([(0, 1), (1, 0)]): 16,
    frozenset([(0, -1), (-1, 0)]): 22,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    before = SCENE.read_text()
    matches = list(PATTERN.finditer(before))
    assert len(matches) == 1, "Expected one narrowly scoped GridMap data block"
    original = WORK / "main.before.tscn"
    if not original.exists():
        original.write_text(before)
    baseline = original.read_text()
    assert PATTERN.sub("<GRIDMAP_DATA>", before) == PATTERN.sub("<GRIDMAP_DATA>", baseline)
    assert json.loads(CONTRACT.read_text())["frozen_before_candidate_edit"] is True
    metadata = json.loads(METADATA.read_text())
    names = {t["id"]: t["name"] for t in metadata["tiles"]}
    assert names[3] == "track-corner" and names[4] == "track-finish" and names[6] == "track-straight"
    assert len(ROUTE) == len(set(ROUTE))
    cells = {(x, z): (0, 0) for z in range(-4, 4) for x in range(-4, 4)}
    road_records = []
    for index, point in enumerate(ROUTE):
        prev = ROUTE[index-1]
        nxt = ROUTE[(index+1) % len(ROUTE)]
        ports = frozenset([(prev[0]-point[0], prev[1]-point[1]),
                           (nxt[0]-point[0], nxt[1]-point[1])])
        assert all(abs(x)+abs(z) == 1 for x,z in ports)
        if ports == frozenset([(0, -1), (0, 1)]):
            item, orientation = (4 if point == (0, 0) else 6), 0
        elif ports == frozenset([(-1, 0), (1, 0)]):
            item, orientation = 6, 16
        else:
            item, orientation = 3, CORNER_ORIENTATIONS[ports]
        cells[point] = (item, orientation)
        road_records.append({"cell": [point[0], 0, point[1]], "item": item,
                             "orientation": orientation, "ports": sorted(ports)})
    for index, point in enumerate(FOREST):
        assert point not in ROUTE
        cells[point] = (1, [0, 10, 16, 22][index % 4])
    for point in TENTS:
        assert point not in ROUTE and point not in FOREST
        cells[point] = (2, 0)
    # Godot GridMap storage is packed x/y, packed z, item | (orthogonal_index << 16).
    # All cells here deliberately use y=0 and no alternate transform.
    packed = []
    for (x,z), (item,orientation) in sorted(cells.items(), key=lambda kv: (kv[0][1],kv[0][0])):
        packed.extend([x & 0xffff, z & 0xffff, item | (orientation << 16)])
    replacement = 'data = {\n"cells": PackedInt32Array(' + ', '.join(map(str,packed)) + ')\n}'
    after = PATTERN.sub(lambda _: replacement, before)
    assert PATTERN.sub("<GRIDMAP_DATA>", before) == PATTERN.sub("<GRIDMAP_DATA>", after)
    SCENE.write_text(after)
    decision = {
        "task_id": "racing-01", "candidate": "layout-v1", "author_role": "coding agent",
        "acceptance_claim": "Pending independent validation and human visual review",
        "contract_sha256": sha(CONTRACT.read_bytes()), "tile_metadata_sha256": sha(METADATA.read_bytes()),
        "main_scene_before_sha256": sha(baseline.encode()), "main_scene_after_sha256": sha(after.encode()),
        "outside_grid_data_unchanged": True, "modified_project_paths": ["scenes/main.tscn"],
        "mesh_library_modified": False,
        "road_cells": road_records, "road_count": len(ROUTE), "total_cells": len(cells),
        "forest_cells": [[x,0,z] for x,z in FOREST], "tent_cells": [[x,0,z] for x,z in TENTS],
        "design": {
            "spawn": "Preserved (3.5,0,5), +Z; finish tile remains at cell(0,0)",
            "continuous_straight": [[-3,0,z] for z in [2,1,0,-1]],
            "left_then_right": [[0,0,2],[1,0,2]],
            "physical_ground": "Original 60m x 60m collider and GridMap transform unchanged",
            "tile_world_pitch_m": 9.99*0.75,
            "decoration": "Tents east/outside; forest concentrated west/north; original parked-truck nodes unchanged",
            "visual_bounds": "Inspector mesh AABBs: forest/tents XZ approximately [-5,5], scale .75; no decoration occupies a road cell; next native review must assess foliage/camera occlusion",
        },
    }
    (WORK / "decision.json").write_text(json.dumps(decision, indent=2)+"\n")
    (WORK / "candidate-data.json").write_text(json.dumps({"cells":[{"x":x,"y":0,"z":z,"item":i,"orientation":o} for (x,z),(i,o) in sorted(cells.items())]},indent=2)+"\n")
    print(json.dumps({"scene":str(SCENE),"road_count":len(ROUTE),"total_cells":len(cells),"after_sha256":decision["main_scene_after_sha256"],"validation":"pending"},indent=2))


if __name__ == "__main__":
    main()
