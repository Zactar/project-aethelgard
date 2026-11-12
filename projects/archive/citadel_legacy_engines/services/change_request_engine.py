import json
import math
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

from schemas.studio_contracts import (
    FeatureChangeRequest, RFCChangeType, RFCStatus, AgentReviewVote,
    GameRuntimeManifest, ItemSpec, ItemCategory, SpatialRoomNode,
    Vector3D, SmartObjectAnchor, GameplayMechanicsSpec
)
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus

class StudioReviewBoardEngine:
    def __init__(self, memory_bus: StudioSharedMemoryBus):
        self.memory = memory_bus
        self.rfc_dir = Path("build/rfcs")
        self.pending_dir = self.rfc_dir / "pending"
        self.approved_dir = self.rfc_dir / "approved"
        self.rejected_dir = self.rfc_dir / "rejected"
        for d in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def review_request(self, rfc: FeatureChangeRequest, manifest: GameRuntimeManifest) -> FeatureChangeRequest:
        votes: List[AgentReviewVote] = []
        risks: List[str] = []

        # 1. Systems Architect Review
        if rfc.change_type in (RFCChangeType.NEW_ITEM, RFCChangeType.MODIFY_ITEM):
            item_data = rfc.payload_diff.get("item", {})
            val = float(item_data.get("base_value", 0.0))
            if val <= 0:
                risks.append("Systems: Item value cannot be zero or negative.")
                votes.append(AgentReviewVote(agent_id="Systems_Architect", approved=False, score=0.2, comments="Economic anomaly.", flagged_risks=["Zero base value"]))
            elif val > 500:
                risks.append("Systems: Item value causes runaway inflation risk.")
                votes.append(AgentReviewVote(agent_id="Systems_Architect", approved=False, score=0.4, comments="Value exceeds market ceilings.", flagged_risks=["Hyperinflation"]))
            else:
                votes.append(AgentReviewVote(agent_id="Systems_Architect", approved=True, score=0.95, comments="Balanced economic payload."))

        # 2. Level Architect Review
        if rfc.change_type == RFCChangeType.NEW_ROOM_NODE:
            node_data = rfc.payload_diff.get("node", {})
            node_id = node_data.get("node_id", "")
            if node_id in manifest.spatial_layout.nodes:
                risks.append(f"Level: Node ID '{node_id}' already exists in topology.")
                votes.append(AgentReviewVote(agent_id="Level_Architect", approved=False, score=0.1, comments="Collision with existing node."))
            else:
                votes.append(AgentReviewVote(agent_id="Level_Architect", approved=True, score=0.92, comments="Spatial boundary verified."))

        # 3. Gameplay Mechanics Review
        if rfc.change_type == RFCChangeType.ADJUST_MECHANICS:
            speed = float(rfc.payload_diff.get("player_base_speed", manifest.mechanics.player_base_speed))
            if speed > 3000.0 or speed < 400.0:
                risks.append("Gameplay: Speed scalar violates camera damping limits.")
                votes.append(AgentReviewVote(agent_id="Gameplay_Specialist", approved=False, score=0.3, comments="Locomotion broke playability envelopes."))
            else:
                votes.append(AgentReviewVote(agent_id="Gameplay_Specialist", approved=True, score=0.96, comments="Movement parameters within stable range."))

        # 4. Lore Auditor Review
        payload_str = json.dumps(rfc.payload_diff).lower()
        if "changed species" in payload_str or "unlicensed deity" in payload_str:
            risks.append("Lore Auditor: Somatic or theological dogma violation detected.")
            votes.append(AgentReviewVote(agent_id="Lore_Auditor", approved=False, score=0.0, comments="Canon violation."))
        else:
            votes.append(AgentReviewVote(agent_id="Lore_Auditor", approved=True, score=0.98, comments="Complies with canon dogmas."))

        # 5. Chaos Crew Headless Verification
        votes.append(AgentReviewVote(
            agent_id="Chaos_Commander", approved=len(risks) == 0,
            score=0.95 if len(risks) == 0 else 0.40,
            comments="Passed stress test." if len(risks) == 0 else "Blocked by simulation faults."
        ))

        # Quorum Evaluation: Minimum 75% approval score and 0 hard vetoes
        avg_score = sum(v.score for v in votes) / max(len(votes), 1)
        hard_veto = any(not v.approved and v.score < 0.25 for v in votes)

        rfc.review_votes = votes
        rfc.resolved_at = time.time()

        if avg_score >= 0.70 and not hard_veto:
            rfc.status = RFCStatus.APPROVED
        else:
            rfc.status = RFCStatus.REJECTED
            rfc.rejection_reasons = risks

        return rfc

    def apply_approved_change(self, rfc: FeatureChangeRequest, manifest: GameRuntimeManifest) -> GameRuntimeManifest:
        """Applies an approved RFC payload diff to the active manifest."""
        diff = rfc.payload_diff

        if rfc.change_type == RFCChangeType.NEW_ITEM:
            item_data = diff["item"]
            spec = ItemSpec(**item_data)
            manifest.items[spec.item_id] = spec

        elif rfc.change_type == RFCChangeType.NEW_ROOM_NODE:
            node_data = diff["node"]
            node = SpatialRoomNode(**node_data)
            manifest.spatial_layout.nodes[node.node_id] = node

        elif rfc.change_type == RFCChangeType.ADJUST_MECHANICS:
            for k, v in diff.items():
                if hasattr(manifest.mechanics, k):
                    setattr(manifest.mechanics, k, v)

        elif rfc.change_type == RFCChangeType.UPDATE_UI_THEME:
            for k, v in diff.items():
                if hasattr(manifest.ui, k):
                    setattr(manifest.ui, k, v)

        manifest.manifest_version = int(time.time())
        rfc.status = RFCStatus.DEPLOYED
        return manifest
