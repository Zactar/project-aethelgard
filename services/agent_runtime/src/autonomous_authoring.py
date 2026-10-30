#!/usr/bin/env python3
"""
PROJECT AETHELGARD: INTEGRATED AUTONOMOUS FEATURE AUTHOR AGENT
Connects Vector Lore, Procedural Spatial Tiling, and Leontief Economy to the Review Board.
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from schemas.studio_contracts import (
    FeatureChangeRequest, GameRuntimeManifest, ItemSpec, RFCChangeType,
    RFCStatus, SpatialRoomNode, SprintGoal
)
from services.agent_runtime.src.change_request_engine import StudioReviewBoardEngine
from services.agent_runtime.src.chroma_lore_bus import ChromaLoreBus
from services.agent_runtime.src.procedural_spatial_generator import ProceduralSpatialGenerator
from services.agent_runtime.src.systemic_economy_generator import SystemicEconomyGenerator
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus

MANIFEST_PATH = Path("web_client/game_runtime_manifest.json")


class AutonomousFeatureAuthorAgent:
    """Algorithmically generates new rooms, items, and mechanics from live simulation state."""

    def __init__(self, memory_bus: StudioSharedMemoryBus):
        self.memory = memory_bus
        self.review_board = StudioReviewBoardEngine(memory_bus)
        self.lore_bus = ChromaLoreBus()
        self.spatial_gen = ProceduralSpatialGenerator(margin_buffer=80.0)
        self.economy_gen = SystemicEconomyGenerator()

    def load_manifest(self) -> GameRuntimeManifest:
        if not MANIFEST_PATH.exists():
            raise FileNotFoundError(f"Missing {MANIFEST_PATH}")
        return GameRuntimeManifest.model_validate_json(MANIFEST_PATH.read_text(encoding="utf-8"))

    def author_feature_from_goal(
        self, goal: SprintGoal, manifest: GameRuntimeManifest
    ) -> Optional[FeatureChangeRequest]:
        goal_text = goal.primary_objective.lower()
        lore_context = self.lore_bus.query_lore_context(goal_text, top_k=1)
        lore_snippet = lore_context[0] if lore_context else "Episcopal decree."
        rfc_timestamp = int(time.time() * 1000) % 1000000

        # 1. Spatial Expansion (Level Architect)
        if any(k in goal_text for k in ["undercroft", "catacomb", "vault", "garrison", "canal", "tavern", "expand", "gate"]):
            new_node = self.spatial_gen.generate_next_spatial_node(
                manifest.spatial_layout.nodes, theme_hint=goal_text)
            if new_node:
                # Link bidirectionally
                anchor_id = new_node.connected_node_ids[0]
                if anchor_id in manifest.spatial_layout.nodes:
                    if new_node.node_id not in manifest.spatial_layout.nodes[anchor_id].connected_node_ids:
                        manifest.spatial_layout.nodes[anchor_id].connected_node_ids.append(
                            new_node.node_id)

                return FeatureChangeRequest(
                    rfc_id=f"RFC-LVL-{rfc_timestamp}",
                    title=f"Construct Zone: {new_node.zone_name}",
                    description=f"Level Architect algorithmic expansion connected to {anchor_id}. Anchored to lore: {lore_snippet[:40]}",
                    submitted_by="Level_Architect",
                    change_type=RFCChangeType.NEW_ROOM_NODE,
                    payload_diff={"node": new_node.model_dump()}
                )

        # 2. Economy & Consumables (Systems Architect)
        if any(k in goal_text for k in ["smuggl", "tithe", "economy", "ration", "salve", "bread", "item", "permit", "arbitrage"]):
            item = self.economy_gen.synthesize_item(
                reserves=self.memory.commodity_reserves,
                unrest=manifest.district_unrest,
                world_time=self.memory.world_time,
                lore_snippet=lore_snippet
            )
            return FeatureChangeRequest(
                rfc_id=f"RFC-SYS-{rfc_timestamp}",
                title=f"Synthesize Item: {item.display_name}",
                description=f"Systems Architect derived item from scarcity. Base value: {item.base_value:.1f} gold.",
                submitted_by="Systems_Architect",
                change_type=RFCChangeType.NEW_ITEM,
                payload_diff={"item": item.model_dump()}
            )

        # 3. Locomotion & Physics Tuning (Gameplay Specialist)
        if any(k in goal_text for k in ["stamina", "speed", "locomotion", "physics", "recovery", "combat"]):
            new_stamina = min(160.0, manifest.mechanics.stamina_max + 10.0)
            new_recovery = min(
                24.0, manifest.mechanics.stamina_recovery_rate + 1.5)
            return FeatureChangeRequest(
                rfc_id=f"RFC-MEC-{rfc_timestamp}",
                title="Calibrate Locomotion Envelope & Recovery Envelopes",
                description=f"Gameplay Specialist tuned stamina ceiling ({new_stamina:.0f}) and recovery rate ({new_recovery:.1f}).",
                submitted_by="Gameplay_Specialist",
                change_type=RFCChangeType.ADJUST_MECHANICS,
                payload_diff={"stamina_max": new_stamina,
                              "stamina_recovery_rate": new_recovery}
            )

        return None

    def execute_autonomous_rfc_cycle(self, active_goals: List[SprintGoal]) -> List[FeatureChangeRequest]:
        manifest = self.load_manifest()
        processed: List[FeatureChangeRequest] = []

        for goal in active_goals:
            rfc = self.author_feature_from_goal(goal, manifest)
            if not rfc:
                continue

            evaluated = self.review_board.review_request(rfc, manifest)
            if evaluated.status == RFCStatus.APPROVED:
                manifest = self.review_board.apply_approved_change(
                    evaluated, manifest)
                MANIFEST_PATH.write_text(
                    manifest.model_dump_json(indent=2), encoding="utf-8")

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

            processed.append(evaluated)

        if any(r.status == RFCStatus.DEPLOYED for r in processed):
            self.broadcast_hot_reload(manifest.model_dump())

        return processed

    def broadcast_hot_reload(self, manifest_dict: dict):
        try:
            import asyncio
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
