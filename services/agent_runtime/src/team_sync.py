"""
services/agent_runtime/src/team_sync.py
Project Aethelgard: Multi-Agent Sprint Standup & Blackboard Alignment Engine
"""

from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.TeamSync")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class TeamSyncEngine:
    """
    Convenes the 6 specialized agent disciplines at the start of a sprint cycle,
    inspects pending deliverables on the active milestone, and persists standup minutes.
    """

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        roadmap_engine: Optional[StudioRoadmapEngine] = None,
        memory: Optional[StudioRetrospectiveMemory] = None
    ):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.roadmap_engine = roadmap_engine or StudioRoadmapEngine(
            workspace_root=self.workspace_root)
        self.memory = memory or StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)
        self.meetings_dir = self.workspace_root / "build" / "staging" / "meetings"
        self.meetings_dir.mkdir(parents=True, exist_ok=True)

    def run_standup(self, cycle_id: str = "AUTO-C01", *args, **kwargs) -> Dict[str, Any]:
        state = self.roadmap_engine.load_roadmap()
        active_ver = state.active_version
        logger.info(
            f"Convening sprint standup ceremony [{cycle_id}] for {active_ver}...")

        milestone = next(
            (m for m in state.milestones if m.version == active_ver), None)
        deliverables_summary = []
        if milestone:
            for d in milestone.deliverables:
                disc = d.discipline.value if hasattr(
                    d.discipline, "value") else str(d.discipline)
                stat = d.status.value if hasattr(
                    d.status, "value") else str(d.status)
                deliverables_summary.append({
                    "deliverable_id": d.deliverable_id,
                    "discipline": disc,
                    "title": d.title,
                    "target_subsystem": d.target_subsystem,
                    "status": stat
                })

        minutes = {
            "meeting_id": f"SYNC-{cycle_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "active_milestone": active_ver,
            "theme": milestone.theme if milestone else "Core Architecture",
            "deliverables_in_scope": deliverables_summary,
            "blackboard_contract": "window.StudioEngine.state (player, stats, inventory, world, keys, pointer)"
        }

        out_file = self.meetings_dir / f"SYNC-{cycle_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(minutes, f, indent=2)

        logger.info(f"Standup minutes persisted to {out_file}")
        return minutes

    # Alias for runner compatibility
    def convene_standup(self, cycle_id: str = "AUTO-C01", *args, **kwargs) -> Dict[str, Any]:
        return self.run_standup(cycle_id=cycle_id, *args, **kwargs)

    def conduct_standup(self, cycle_id: str = "AUTO-C01", *args, **kwargs):
        return self.run_standup(cycle_id=cycle_id, *args, **kwargs)
