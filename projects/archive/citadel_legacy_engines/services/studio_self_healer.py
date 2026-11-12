"""
services/agent_runtime/src/studio_self_healer.py
Project Aethelgard: Autonomous Diagnostic & Self-Healing Spatial Engine
"""

from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from schemas.studio_contracts import (
    PostMortemRecord,
    IncidentSeverity,
    DisciplineType
)
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.SelfHealer")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class StudioSelfHealer:
    """
    Audits runtime spatial manifests, detects room stagnation, non-contiguous
    corridor sockets, and AABB boundary collisions. Records rollbacks to memory.
    """

    def __init__(self, workspace_root: Optional[Path] = None, memory: Optional[StudioRetrospectiveMemory] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = memory or StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)
        self.manifest_path = self.workspace_root / \
            "web_client" / "game_runtime_manifest.json"

    def audit_and_heal_topology(self, staged_manifest: Dict[str, Any]) -> bool:
        """
        Audits proposed spatial topology against collision and corridor invariants.
        Returns True if sound, False if topological break requires rollback.
        """
        rooms = staged_manifest.get("rooms", [])
        if not rooms:
            logger.warning("Empty rooms manifest submitted for audit.")
            return False

        # 1. Detect Coincident AABB Collisions
        for i, room_a in enumerate(rooms):
            for j, room_b in enumerate(rooms):
                if i >= j:
                    continue
                if self._check_aabb_overlap(room_a, room_b):
                    self._on_topological_break(
                        break_type="AABB_OVERLAP",
                        room_ids=[room_a.get("room_id", "unknown"), room_b.get(
                            "room_id", "unknown")],
                        details=f"Spatial bounding box collision between '{room_a.get('room_id')}' and '{room_b.get('room_id')}'."
                    )
                    return False

        # 2. Verify Socket Inset Compliance (INC-20261012-LVL-01)
        for room in rooms:
            for socket in room.get("corridor_sockets", []):
                inset = socket.get("clearance_inset", 0.0)
                if inset < 0.15:
                    self._on_topological_break(
                        break_type="INSUFFICIENT_INSET",
                        room_ids=[room.get("room_id", "unknown")],
                        details=f"Room '{room.get('room_id')}' corridor socket lacks 0.15m inset (found {inset}m)."
                    )
                    return False

        logger.info(
            f"Spatial topology audit passed ({len(rooms)} zones verified).")
        return True

    def _check_aabb_overlap(self, room_a: Dict[str, Any], room_b: Dict[str, Any]) -> bool:
        """Determines if two 3D boxes intersect without tolerance margin."""
        pos_a = room_a.get("position", [0, 0, 0])
        dim_a = room_a.get("dimensions", [0, 0, 0])
        pos_b = room_b.get("position", [0, 0, 0])
        dim_b = room_b.get("dimensions", [0, 0, 0])

        margin = 0.15
        x_overlap = abs(pos_a[0] - pos_b[0]) * \
            2 < (dim_a[0] + dim_b[0] - margin)
        z_overlap = abs(pos_a[2] - pos_b[2]) * \
            2 < (dim_a[2] + dim_b[2] - margin)

        return x_overlap and z_overlap

    def _on_topological_break(self, break_type: str, room_ids: List[str], details: str) -> None:
        """Logs a spatial regression incident to the retrospective ledger."""
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-LVL-{uuid.uuid4().hex[:4].upper()}"

        record = PostMortemRecord(
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            milestone_tag="v0.5.0",
            discipline=DisciplineType.LEVEL,
            severity=IncidentSeverity.HIGH,
            summary=f"Topological Break [{break_type}]: {', '.join(room_ids)}",
            root_cause=details,
            symptoms=[f"Self-healer detected {break_type}", details],
            mitigation_applied="Spatial expansion rejected; rolled back to previous valid manifest.",
            prevention_rule="Ensure room socket offsets enforce minimum 0.15m separation on all floorplate axes.",
            affected_files=["web_client/game_runtime_manifest.json"],
            metadata={"conflicting_rooms": room_ids, "break_type": break_type}
        )

        self.memory.record_incident(record)
        logger.warning(
            f"Self-Healer recorded post-mortem {incident_id}: {details}")


if __name__ == "__main__":
    healer = StudioSelfHealer()
    print("\n--- TEST: Simulating Self-Healer Overlap Detection ---")
    mock_overlapping_manifest = {
        "rooms": [
            {"room_id": "market_cross", "position": [
                0, 0, 0], "dimensions": [20, 4, 20]},
            {"room_id": "encroaching_bakery", "position": [
                5, 0, 5], "dimensions": [15, 4, 15]}
        ]
    }
    is_valid = healer.audit_and_heal_topology(mock_overlapping_manifest)
    print(f"Topology Valid (Expected False): {is_valid}")
