#!/usr/bin/env python3
"""
PROJECT AETHELGARD: AUTONOMOUS STUDIO SELF-HEALING & HEALTH ENGINE
Monitors studio production output, identifies architectural stagnation,
and executes self-corrective repairs on layouts, schemas, and assets.
"""

from tools.godot_exporter import export_manifest_to_godot
from services.agent_runtime.src.procedural_spatial_generator import ProceduralSpatialGenerator
from schemas.studio_contracts import GameRuntimeManifest
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


logger = logging.getLogger("StudioSelfHealer")
MANIFEST_PATH = ROOT_DIR / "web_client" / "game_runtime_manifest.json"


class StudioSelfHealer:
    """Diagnoses and repairs production bottlenecks autonomously."""

    def __init__(self):
        self.spatial_gen = ProceduralSpatialGenerator(margin_buffer=120.0)

    def audit_and_repair_studio_health(self) -> Dict[str, Any]:
        """Runs a complete diagnostic across game assets and executes required course-corrections."""
        report = {
            "spatial_nodes_added": 0,
            "corridors_repaired": False,
            "quest_sync_repaired": False,
            "status": "HEALTHY"
        }

        if not MANIFEST_PATH.exists():
            return report

        try:
            manifest_data = json.loads(
                MANIFEST_PATH.read_text(encoding="utf-8"))
            manifest = GameRuntimeManifest.model_validate(manifest_data)
        except Exception as e:
            logger.error(f"Self-healer failed to read manifest: {e}")
            return report

        nodes = manifest.spatial_layout.nodes
        modified = False

        # Diagnostic 1: Stagnant Spatial Expansion (Citadel must scale to 7+ rooms)
        if len(nodes) < 7:
            logger.info(
                f"Self-Healer detected spatial stagnation ({len(nodes)}/7 rooms). Carving contiguous expansions...")
            for expansion_theme in ["Garrison Bastion Checkpoint", "Cathedral Undercroft Ossuary", "Canal Cargo Concourse"]:
                if len(nodes) >= 7:
                    break
                new_node = self.spatial_gen.generate_next_spatial_node(
                    nodes, theme_hint=expansion_theme)
                if new_node:
                    anchor_id = new_node.connected_node_ids[0]
                    if anchor_id in nodes and new_node.node_id not in nodes[anchor_id].connected_node_ids:
                        nodes[anchor_id].connected_node_ids.append(
                            new_node.node_id)
                    nodes[new_node.node_id] = new_node
                    report["spatial_nodes_added"] += 1
                    modified = True

        # Diagnostic 2: Bidirectional Corridor Integrity
        for node_id, node in list(nodes.items()):
            for target_id in node.connected_node_ids:
                if target_id in nodes:
                    if node_id not in nodes[target_id].connected_node_ids:
                        nodes[target_id].connected_node_ids.append(node_id)
                        report["corridors_repaired"] = True
                        modified = True

        if modified:
            MANIFEST_PATH.write_text(
                manifest.model_dump_json(indent=2), encoding="utf-8")
            export_manifest_to_godot(manifest)
            report["status"] = "REPAIRED"
            logger.info(
                f"Self-Healer repaired studio state: +{report['spatial_nodes_added']} room(s) carved and synced.")

        return report
