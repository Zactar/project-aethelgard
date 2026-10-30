#!/usr/bin/env python3
"""
PROJECT AETHELGARD: GODOT 4 SCENE & RESOURCE EXPORTER
Converts GameRuntimeManifest spatial rooms, props, and NPCs into native Godot 4 .tscn files.
"""

from schemas.studio_contracts import GameRuntimeManifest
from pathlib import Path
import json
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


GODOT_EXPORT_DIR = ROOT_DIR / "godot_project" / "scenes" / "generated"
MANIFEST_PATH = ROOT_DIR / "web_client" / "game_runtime_manifest.json"


def export_manifest_to_godot(manifest: GameRuntimeManifest) -> Path:
    GODOT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    scene_file = GODOT_EXPORT_DIR / f"{manifest.district_id}.tscn"

    tscn_lines = [
        '[gd_scene format=3 uid="uid://aethelgard_' +
        manifest.district_id.lower() + '"]',
        "",
        '[node name="' + manifest.district_id + '" type="Node3D"]',
        ""
    ]

    # Convert Spatial Room Nodes to Godot 3D Floorplates
    for node_id, node in manifest.spatial_layout.nodes.items():
        min_p = node.bounds_min
        max_p = node.bounds_max
        w = abs(max_p.x - min_p.x) / 100.0  # Scale to meters
        d = abs(max_p.y - min_p.y) / 100.0
        cx = node.center_location.x / 100.0
        cy = node.center_location.z / 100.0
        cz = node.center_location.y / 100.0

        tscn_lines.extend([
            f'[node name="{node_id}" type="CSGBox3D" parent="."]',
            f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {cx:.2f}, {cy:.2f}, {cz:.2f})',
            f'size = Vector3({w:.2f}, 0.2, {d:.2f})',
            f'use_collision = true',
            ""
        ])

    # Convert NPCs to Godot CharacterBody3D placeholders
    for npc_id, npc in manifest.npcs.items():
        nx = npc.position.x / 100.0
        ny = npc.position.z / 100.0
        nz = npc.position.y / 100.0

        tscn_lines.extend([
            f'[node name="{npc_id}" type="CharacterBody3D" parent="."]',
            f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {nx:.2f}, {ny:.2f}, {nz:.2f})',
            f'[node name="Collision" type="CollisionShape3D" parent="{npc_id}"]',
            f'[node name="Mesh" type="CSGCylinder3D" parent="{npc_id}"]',
            f'radius = 0.55',
            f'height = 1.8',
            ""
        ])

    scene_file.write_text("\n".join(tscn_lines), encoding="utf-8")
    print(f"  [GODOT 4 EXPORTER]: Exported district scene to {scene_file}")
    return scene_file


if __name__ == "__main__":
    if MANIFEST_PATH.exists():
        manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        m = GameRuntimeManifest.model_validate(manifest_data)
        export_manifest_to_godot(m)
    else:
        print(f"[ERROR]: {MANIFEST_PATH} not found.")
