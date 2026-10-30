#!/usr/bin/env python3
"""
PROJECT AETHELGARD: GENERATIVE AUTONOMOUS AUTHORING ENGINE
Enables virtual dev team agents to algorithmically generate rooms, items, mechanics, and quests.
"""

import asyncio
import json
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from schemas.studio_contracts import (
    FeatureChangeRequest, GameRuntimeManifest, ItemCategory, ItemSpec,
    ObjectiveStatus, ProceduralPropSpec, PropPrimitiveType, QuestObjective,
    RFCChangeType, RFCStatus, SmartObjectAnchor, SpatialRoomNode, SprintGoal,
    SystemicQuest, Vector3D
)
from services.agent_runtime.src.change_request_engine import StudioReviewBoardEngine
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus

MANIFEST_PATH = Path("web_client/game_runtime_manifest.json")


class AutonomousFeatureAuthorAgent:
    """Translates sprint standup goals into algorithmic RFC diffs across Level, Systems, and Narrative."""

    def __init__(self, memory_bus: StudioSharedMemoryBus):
        self.memory = memory_bus
        self.review_board = StudioReviewBoardEngine(memory_bus)

    def load_manifest(self) -> GameRuntimeManifest:
        if not MANIFEST_PATH.exists():
            raise FileNotFoundError(
                f"Runtime manifest missing at {MANIFEST_PATH}")
        return GameRuntimeManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))

    # ==========================================================================
    # 1. PROCEDURAL SPATIAL EXPANDER (Level Architect)
    # ==========================================================================
    def generate_spatial_expansion(
        self, goal: SprintGoal, manifest: GameRuntimeManifest
    ) -> Optional[FeatureChangeRequest]:
        nodes = manifest.spatial_layout.nodes
        goal_text = goal.primary_objective.lower()

        # Potential district expansions catalogue
        expansion_templates = [
            {
                "node_id": "NODE_UNDERCROFT_VAULT",
                "zone_name": "Old Undercroft Vaults",
                "function": "CLANDESTINE_STORAGE",
                "anchor_to": "NODE_AQUEDUCT_CATACOMBS",
                "offset": (1400.0, 0.0, 0.0),
                "dims": (1200.0, 1000.0, 350.0),
                "smart_object": ("SO_SMUGGLER_CACHE", "SmartObject.Container.SmugglerCache"),
                "keywords": ["undercroft", "vault", "catacomb", "smuggl", "storage"]
            },
            {
                "node_id": "NODE_WATCH_GARRISON",
                "zone_name": "City Watch Garrison",
                "function": "MILITARY_CHECKPOINT",
                "anchor_to": "NODE_PLAZA",
                "offset": (-2100.0, 0.0, 0.0),
                "dims": (1200.0, 1200.0, 400.0),
                "smart_object": ("SO_WEAPON_RACK", "SmartObject.Armory.WeaponRack"),
                "keywords": ["barricade", "curfew", "garrison", "watch", "guard", "checkpoint"]
            },
            {
                "node_id": "NODE_DOCKS_CANAL",
                "zone_name": "Lower Docks Canal",
                "function": "TRANSIT_WATERWAY",
                "anchor_to": "NODE_AQUEDUCT_CATACOMBS",
                "offset": (0.0, 1400.0, 50.0),
                "dims": (1400.0, 1000.0, 300.0),
                "smart_object": ("SO_CARGO_CRANE", "SmartObject.Mechanism.CargoCrane"),
                "keywords": ["dock", "canal", "water", "sluice", "aqueduct", "drainage"]
            },
            {
                "node_id": "NODE_HEARTH_TAVERN",
                "zone_name": "The Hearthside Taproom",
                "function": "CIVIC_GATHERING",
                "anchor_to": "NODE_BAKERY",
                "offset": (-1300.0, 0.0, 0.0),
                "dims": (1100.0, 1000.0, 350.0),
                "smart_object": ("SO_BREW_CASK", "SmartObject.Craft.AleCask"),
                "keywords": ["tavern", "inn", "ale", "bread", "comfort", "repose"]
            }
        ]

        for tmpl in expansion_templates:
            target_id = tmpl["node_id"]
            if target_id in nodes:
                continue

            anchor_id = tmpl["anchor_to"]
            if anchor_id not in nodes:
                continue

            matches_intent = any(k in goal_text for k in tmpl["keywords"])
            if matches_intent:
                anchor = nodes[anchor_id]
                dx, dy, dz = tmpl["offset"]
                w, d, h = tmpl["dims"]
                cx = anchor.center_location.x + dx
                cy = anchor.center_location.y + dy
                cz = anchor.center_location.z + dz

                so_anchor_id, so_tag = tmpl["smart_object"]
                new_node = SpatialRoomNode(
                    node_id=target_id,
                    zone_name=tmpl["zone_name"],
                    function=tmpl["function"],
                    bounds_min=Vector3D(x=cx - (w / 2), y=cy - (d / 2), z=cz),
                    bounds_max=Vector3D(
                        x=cx + (w / 2), y=cy + (d / 2), z=cz + h),
                    center_location=Vector3D(x=cx, y=cy, z=cz),
                    connected_node_ids=[anchor_id],
                    smart_objects=[
                        SmartObjectAnchor(
                            anchor_id=so_anchor_id,
                            smart_object_tag=so_tag,
                            relative_position=Vector3D(x=cx, y=cy, z=cz),
                            interaction_facing_yaw=0.0
                        )
                    ]
                )

                return FeatureChangeRequest(
                    rfc_id=f"RFC-LVL-{int(time.time())}-{target_id}",
                    title=f"Construct Zone: {tmpl['zone_name']}",
                    description=f"Level Architect authored contiguous zone expansion linked to {anchor.zone_name}.",
                    submitted_by="Level_Architect",
                    change_type=RFCChangeType.NEW_ROOM_NODE,
                    payload_diff={"node": new_node.model_dump()}
                )

        return None

    # ==========================================================================
    # 2. SYSTEMIC ITEM & RECIPE SYNTHESIZER (Systems Architect)
    # ==========================================================================
    def generate_systemic_item(
        self, goal: SprintGoal, manifest: GameRuntimeManifest
    ) -> Optional[FeatureChangeRequest]:
        goal_text = goal.primary_objective.lower()
        unrest = manifest.district_unrest
        existing_keys = set(manifest.items.keys())

        item_templates = [
            {
                "item_id": "item_forged_permit",
                "display_name": "Forged Tithe Permit",
                "category": ItemCategory.CONTRABAND,
                "base_value": round(28.0 + (unrest * 15.0), 1),
                "description": "Counterfeit church wax seal granting access through locked curfew gates.",
                "icon_symbol": "📜",
                "effects": {"stealth_bonus": 0.40, "duration_sec": 20.0},
                "keywords": ["smuggl", "tithe", "permit", "evasion", "arbitrage"]
            },
            {
                "item_id": "item_smoke_phial",
                "display_name": "Phosphor Smoke Phial",
                "category": ItemCategory.CONSUMABLE,
                "base_value": 22.0,
                "description": "Herbal combustive powder that blankets sightlines and increases sprint speed.",
                "icon_symbol": "💨",
                "effects": {"speed_boost": 0.30, "duration_sec": 14.0},
                "keywords": ["smoke", "escape", "torch", "brazier", "grime"]
            },
            {
                "item_id": "item_salted_jerky",
                "display_name": "Cured Dock Jerky",
                "category": ItemCategory.CONSUMABLE,
                "base_value": 14.0,
                "description": "Chewy sea-salted protein ration. Instantly recovers 50 stamina.",
                "icon_symbol": "🥩",
                "effects": {"stamina_restore": 50.0},
                "keywords": ["ration", "curfew", "food", "harvest", "drought", "stamina"]
            }
        ]

        for tmpl in item_templates:
            if tmpl["item_id"] in existing_keys:
                continue

            if any(k in goal_text for k in tmpl["keywords"]):
                spec = ItemSpec(
                    item_id=tmpl["item_id"],
                    display_name=tmpl["display_name"],
                    category=tmpl["category"],
                    base_value=tmpl["base_value"],
                    description=tmpl["description"],
                    icon_symbol=tmpl["icon_symbol"],
                    effects=tmpl["effects"]
                )
                return FeatureChangeRequest(
                    rfc_id=f"RFC-SYS-{int(time.time())}-{spec.item_id}",
                    title=f"Synthesize Item: {spec.display_name}",
                    description=f"Systems Architect authored item calibrated to current unrest ({unrest:.2f}).",
                    submitted_by="Systems_Architect",
                    change_type=RFCChangeType.NEW_ITEM,
                    payload_diff={"item": spec.model_dump()}
                )

        return None

    # ==========================================================================
    # 3. GAMEPLAY MECHANICS CALIBRATOR (Gameplay Specialist)
    # ==========================================================================
    def generate_mechanics_tuning(
        self, goal: SprintGoal, manifest: GameRuntimeManifest
    ) -> Optional[FeatureChangeRequest]:
        goal_text = goal.primary_objective.lower()
        if any(k in goal_text for k in ["stamina", "exhaustion", "sprint", "speed", "roll"]):
            curr_max = manifest.mechanics.stamina_max
            target_max = min(150.0, curr_max + 10.0)
            target_recovery = min(
                22.0, manifest.mechanics.stamina_recovery_rate + 2.0)

            return FeatureChangeRequest(
                rfc_id=f"RFC-MEC-{int(time.time())}",
                title="Calibrate Locomotion & Stamina Recovery Envelope",
                description=f"Gameplay Specialist tuned stamina ceiling ({target_max:.0f}) and recovery ({target_recovery:.1f}).",
                submitted_by="Gameplay_Specialist",
                change_type=RFCChangeType.ADJUST_MECHANICS,
                payload_diff={
                    "stamina_max": target_max,
                    "stamina_recovery_rate": target_recovery
                }
            )
        return None

    # ==========================================================================
    # MASTER AUTHORING CYCLE
    # ==========================================================================
    def execute_autonomous_rfc_cycle(self, active_goals: List[SprintGoal]) -> List[FeatureChangeRequest]:
        manifest = self.load_manifest()
        processed: List[FeatureChangeRequest] = []

        for goal in active_goals:
            # 1. Level Architect Draft
            rfc_lvl = self.generate_spatial_expansion(goal, manifest)
            if rfc_lvl:
                manifest = self._evaluate_and_deploy(rfc_lvl, manifest)
                processed.append(rfc_lvl)

            # 2. Systems Architect Draft
            rfc_sys = self.generate_systemic_item(goal, manifest)
            if rfc_sys:
                manifest = self._evaluate_and_deploy(rfc_sys, manifest)
                processed.append(rfc_sys)

            # 3. Gameplay Mechanics Draft
            rfc_mec = self.generate_mechanics_tuning(goal, manifest)
            if rfc_mec:
                manifest = self._evaluate_and_deploy(rfc_mec, manifest)
                processed.append(rfc_mec)

        if any(r.status == RFCStatus.DEPLOYED for r in processed):
            self.broadcast_hot_reload(manifest.model_dump())

        return processed

    def _evaluate_and_deploy(
        self, rfc: FeatureChangeRequest, manifest: GameRuntimeManifest
    ) -> GameRuntimeManifest:
        evaluated = self.review_board.review_request(rfc, manifest)
        if evaluated.status == RFCStatus.APPROVED:
            manifest = self.review_board.apply_approved_change(
                evaluated, manifest)
            MANIFEST_PATH.write_text(
                manifest.model_dump_json(indent=2), encoding="utf-8")

            # Archive approved change
            out_path = self.review_board.approved_dir / \
                f"{evaluated.rfc_id}.json"
            out_path.write_text(evaluated.model_dump_json(
                indent=2), encoding="utf-8")
            print(
                f"  [AUTO-DEPLOYED]: {evaluated.title} ({evaluated.change_type.value})")
        else:
            out_path = self.review_board.rejected_dir / \
                f"{evaluated.rfc_id}.json"
            out_path.write_text(evaluated.model_dump_json(
                indent=2), encoding="utf-8")
            print(
                f"  [AUTO-REJECTED]: {evaluated.title} - Blocked by review board")
        return manifest

    def broadcast_hot_reload(self, manifest_dict: dict):
        try:
            import websockets

            async def _notify():
                async with websockets.connect("ws://127.0.0.1:8765") as ws:
                    await ws.send(json.dumps({
                        "type": "HOT_RELOAD_TRIGGER",
                        "manifest": manifest_dict
                    }))

            asyncio.run(_notify())
            print(
                "  [LIVE BROADCAST]: Manifest update pushed to connected browser sessions.")
        except Exception:
            pass
