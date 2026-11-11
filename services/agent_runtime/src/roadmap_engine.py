"""
services/agent_runtime/src/roadmap_engine.py
Project Aethelgard Studio: Universal Roadmap & Milestone Burndown Engine
"""

from services.agent_runtime.src.chroma_lore_bus import ChromaLoreBus
from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from schemas.studio_contracts import (
    MilestoneStatus,
    DeliverableStatus,
    StudioMilestone,
    StudioRoadmapState
)
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.Roadmap")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class StudioRoadmapEngine:
    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        memory: Optional[StudioRetrospectiveMemory] = None,
        lore_bus: Optional[ChromaLoreBus] = None
    ):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = memory or StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)
        self.lore_bus = lore_bus or ChromaLoreBus(
            workspace_root=self.workspace_root)
        self.roadmap_dir = self.workspace_root / "build" / "roadmap"
        self.roadmap_dir.mkdir(parents=True, exist_ok=True)
        self.roadmap_file = self.roadmap_dir / "studio_roadmap.json"

    def load_roadmap(self) -> StudioRoadmapState:
        if not self.roadmap_file.exists():
            return StudioRoadmapState(active_version="v0.1.0", milestones=[])
        try:
            with open(self.roadmap_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # Defensive normalizer: backfill missing required Pydantic fields
            if "milestones" in raw_data and isinstance(raw_data["milestones"], list):
                for idx, m in enumerate(raw_data["milestones"]):
                    if not m.get("theme"):
                        m["theme"] = m.get(
                            "codename") or f"Milestone {m.get('version', idx)} Theme"
                    if "deliverables" not in m or not isinstance(m["deliverables"], list):
                        m["deliverables"] = []
                    if "completion_percentage" not in m:
                        m["completion_percentage"] = 100.0 if m.get(
                            "status") == "SHIPPED" else 0.0
                    if m.get("status") in ("PENDING", None):
                        m["status"] = "IN_PROGRESS" if idx == 0 else "PLANNED"

            return StudioRoadmapState(**raw_data)
        except Exception as e:
            logger.error(f"Error deserializing roadmap state: {e}")
            return StudioRoadmapState(active_version="v0.1.0", milestones=[])

    def save_roadmap(self, state: StudioRoadmapState) -> None:
        state.last_updated = datetime.utcnow()
        with open(self.roadmap_file, "w", encoding="utf-8") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2)

    def evolve_to_next_milestone(self, forced_next_version: Optional[str] = None) -> Optional[StudioMilestone]:
        """Advances to the next scheduled milestone in the active project roadmap."""
        state = self.load_roadmap()
        current = next(
            (m for m in state.milestones if m.version == state.active_version), None)

        if current:
            current.status = MilestoneStatus.SHIPPED
            current.completed_at = datetime.utcnow()
            logger.info(
                f"Archived milestone {current.version} ({current.codename}) as SHIPPED.")

        # Look for the next planned milestone in the project
        next_ms = None
        if forced_next_version:
            next_ms = next(
                (m for m in state.milestones if m.version == forced_next_version), None)
        else:
            for m in state.milestones:
                if m.status not in (MilestoneStatus.SHIPPED, MilestoneStatus.IN_PROGRESS):
                    next_ms = m
                    break

        if next_ms:
            next_ms.status = MilestoneStatus.IN_PROGRESS
            state.active_version = next_ms.version
            self.save_roadmap(state)
            logger.info(
                f"[AUTONOMOUS ROADMAP EVOLUTION] Advanced to {next_ms.version}: '{next_ms.codename}'")
            return next_ms

        logger.info(
            "[AUTONOMOUS ROADMAP] All planned project milestones completed!")
        self.save_roadmap(state)
        return current

    def audit_active_milestone(self) -> Dict[str, Any]:
        state = self.load_roadmap()
        milestone = next((m for m in state.milestones if m.version ==
                         state.active_version and m.status != MilestoneStatus.SHIPPED), None)
        if not milestone:
            milestone = next((m for m in reversed(state.milestones)
                             if m.version == state.active_version), None)

        if not milestone:
            return {
                "version": state.active_version,
                "codename": "Unscheduled Milestone",
                "status": "INITIALIZING",
                "verified_deliverables": "0/0",
                "completion_percentage": 0.0,
                "deliverables": []
            }

        approved_rfcs = list(
            (self.workspace_root / "build" / "rfcs" / "approved").glob("*.json"))
        verified_count = 0
        total_count = len(milestone.deliverables)

        for deliv in milestone.deliverables:
            disc_val = deliv.discipline.value if hasattr(
                deliv.discipline, "value") else str(deliv.discipline)
            deliv_verified = False

            for rfc_file in approved_rfcs:
                try:
                    with open(rfc_file, "r", encoding="utf-8") as f:
                        rfc_data = json.load(f)
                    if (
                        rfc_data.get("milestone_tag") == milestone.version and
                        (rfc_data.get("target_deliverable_id") == deliv.deliverable_id or
                         (rfc_data.get("discipline") == disc_val and deliv.title in rfc_data.get("title", "")))
                    ):
                        deliv.status = DeliverableStatus.VERIFIED
                        deliv.verified_artifact = rfc_file.name
                        deliv_verified = True
                        break
                except Exception:
                    pass

            if deliv_verified:
                verified_count += 1
            else:
                deliv.status = DeliverableStatus.PENDING

        milestone.completion_percentage = round(
            (verified_count / total_count) * 100, 1) if total_count > 0 else 0.0

        if milestone.completion_percentage >= 100.0:
            milestone.status = MilestoneStatus.VALIDATING
        elif milestone.status != MilestoneStatus.SHIPPED:
            milestone.status = MilestoneStatus.IN_PROGRESS

        self.save_roadmap(state)

        return {
            "version": milestone.version,
            "codename": milestone.codename,
            "status": milestone.status if isinstance(milestone.status, str) else milestone.status.value,
            "verified_deliverables": f"{verified_count}/{total_count}",
            "completion_percentage": milestone.completion_percentage,
            "deliverables": [d.model_dump(mode="json") for d in milestone.deliverables]
        }
