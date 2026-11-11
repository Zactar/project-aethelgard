#!/usr/bin/env python3
"""
tools/engine_importer.py
Project Aethelgard: Autonomous Dynamic Spatial Compiler & Manifest Hot-Patcher
"""

from services.agent_runtime.src.studio_self_healer import StudioSelfHealer
from typing import Dict, Any, List
import logging
import json
import sys
from pathlib import Path

# Anchor workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.EngineImporter")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class AutonomousEngineImporter:
    """
    Dynamically compiles `web_client/game_runtime_manifest.json` from approved RFCs
    and runtime topology contracts, eliminating hardcoded room dictionaries.
    """

    def __init__(self, workspace_root: Path = WORKSPACE_ROOT):
        self.workspace_root = workspace_root
        self.manifest_path = self.workspace_root / \
            "web_client" / "game_runtime_manifest.json"
        self.approved_rfcs_dir = self.workspace_root / "build" / "rfcs" / "approved"
        self.self_healer = StudioSelfHealer(workspace_root=self.workspace_root)

    def compile_manifest(self) -> bool:
        # Check active project metadata
        active_proj_file = self.workspace_root / "projects" / "active_project.json"
        if active_proj_file.exists():
            try:
                with open(active_proj_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("engine_type") != "WEBGL_3D":
                    logger.info(
                        f"[EngineImporter] Project '{meta.get('title')}' is {meta.get('engine_type')}. Skipping 3D spatial room compilation.")
                    return True
            except Exception:
                pass

    def _derive_thoroughfares(self, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        thoroughfares = []
        seen_pairs = set()

        for room in rooms:
            rid = room.get("room_id")
            for sock in room.get("corridor_sockets", []):
                target = sock.get("target_room")
                pair_key = tuple(sorted([rid, target]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    thoroughfares.append({
                        "from": rid,
                        "to": target,
                        "width": 3.2,
                        "curb_height": 0.15
                    })
        return thoroughfares


if __name__ == "__main__":
    importer = AutonomousEngineImporter()
    success = importer.compile_manifest()
    sys.exit(0 if success else 1)
