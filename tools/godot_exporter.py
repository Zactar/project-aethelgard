#!/usr/bin/env python3
"""
tools/godot_exporter.py
Project Aethelgard: Godot 4 Scene Tree (.tscn) Dual-Exporter
"""

import logging
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.GodotExporter")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class Godot4Exporter:
    def __init__(self, workspace_root: Path = WORKSPACE_ROOT):
        self.workspace_root = workspace_root
        self.manifest_path = self.workspace_root / \
            "web_client" / "game_runtime_manifest.json"
        self.output_dir = self.workspace_root / "godot_project" / "scenes" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_scenes(self) -> bool:
        """Parses runtime manifest and generates native Godot 4 .tscn files."""
        if not self.manifest_path.exists():
            logger.error(
                f"Cannot export: {self.manifest_path} does not exist.")
            return False

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            rooms = manifest.get("rooms", [])
            for room in rooms:
                room_id = room.get("room_id", "unnamed_room")
                pos = room.get("position", [0, 0, 0])
                dims = room.get("dimensions", [10, 4, 10])

                tscn_content = f"""[gd_scene format=3]

[node name="{room_id}" type="Node3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {pos[0]}, {pos[1]}, {pos[2]})

[node name="Floorplate" type="CSGBox3D" parent="."]
size = Vector3({dims[0]}, 0.4, {dims[2]})
use_collision = true
"""
                scene_file = self.output_dir / f"District_{room_id}.tscn"
                scene_file.write_text(tscn_content, encoding="utf-8")

            logger.info(
                f"[✓] Godot 4 Exporter generated {len(rooms)} scenes at {self.output_dir}")
            return True
        except Exception as e:
            logger.error(f"Godot export failed: {e}")
            return False


if __name__ == "__main__":
    exporter = Godot4Exporter()
    success = exporter.export_scenes()
    sys.exit(0 if success else 1)
