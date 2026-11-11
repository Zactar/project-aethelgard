"""
services/agent_runtime/src/team_sync.py
Project Aethelgard: Standup Ceremony with Contextual Lore Vector Brainstorming
"""

from services.agent_runtime.src.chroma_lore_bus import ChromaLoreBus
from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from schemas.studio_contracts import DisciplineType
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.TeamSync")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class TeamSyncEngine:
    """
    Coordinates virtual studio standups:
    - Analyzes retrospective memory and clean streaks.
    - Queries ChromaLoreBus dynamically based on active district tension.
    - Synthesizes lore-grounded feature proposals for incoming sprints.
    """

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
        self.meetings_dir = self.workspace_root / "build" / "staging" / "meetings"
        self.meetings_dir.mkdir(parents=True, exist_ok=True)

    def conduct_standup(
        self,
        sprint_cycle_tag: str = "W1800",
        milestone_tag: Optional[str] = None,
        active_unrest_theme: str = "district commodity scarcity and curfew patrol"
    ) -> Dict[str, Any]:
        """
        Executes an autonomous standup ceremony grounded in retrospective memory,
        active roadmap versioning, and dynamic canon retrieval.
        """
        if not milestone_tag:
            from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
            milestone_tag = StudioRoadmapEngine(
                workspace_root=self.workspace_root).load_roadmap().active_version

        logger.info(
            f"Convening sprint standup ceremony [{sprint_cycle_tag}] for {milestone_tag}...")

        competencies = self.memory.load_competencies()
        recent_incidents = self.memory.load_ledger()[-5:]

        # 1. Query ChromaLoreBus for contextual narrative tension
        canon_matches = self.lore_bus.query_canon(
            query_text=active_unrest_theme, n_results=3)
        lore_context_summary = " ".join([m["text"] for m in canon_matches])

        # 2. Generate discipline briefs combining memory constraints and emergent lore
        discipline_briefs = {}
        for discipline in DisciplineType:
            disc_name = discipline.value
            comp = competencies.get(disc_name, {})
            streak = comp.get("clean_streak", 0)
            regressions = comp.get("regressions_caused", 0)
            friction_notes = comp.get("active_friction_notes", [])

            # Dynamic proposal grounded in retrieved lore
            proposal = self._generate_lore_grounded_proposal(
                discipline, canon_matches)

            discipline_briefs[disc_name] = {
                "reliability_streak": streak,
                "lifetime_regressions": regressions,
                "status": "CAUTION" if friction_notes else "HEALTHY",
                "active_constraints": friction_notes[-2:] if friction_notes else ["Clear to proceed with planned backlog."],
                "contextual_proposal": proposal
            }

        minutes = {
            "standup_id": f"SYNC-{sprint_cycle_tag}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "milestone_tag": milestone_tag,
            "attendees": [d.value for d in DisciplineType],
            "unrest_focus": active_unrest_theme,
            "retrieved_canon_nodes": [m.get("id", m.get("passage_id", f"NODE-{idx}")) for idx, m in enumerate(canon_matches)],
            "discipline_briefs": discipline_briefs,
            "recent_incidents_reviewed": [
                f"[{r['severity']}] {r['incident_id']} ({r['discipline']}): {r['summary']}"
                for r in recent_incidents
            ],
            "action_items": [
                "Prioritize proposals addressing active district unrest.",
                "Chaos QA and Systems Architect hold strict veto enforcement over WebGL and schema bounds."
            ]
        }

        meeting_file = self.meetings_dir / f"SYNC-{sprint_cycle_tag}.json"
        with open(meeting_file, "w", encoding="utf-8") as f:
            json.dump(minutes, f, indent=2)

        logger.info(f"Standup minutes persisted to {meeting_file}")
        return minutes

    def _generate_lore_grounded_proposal(self, discipline: DisciplineType, canon_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesizes role-specific feature objectives derived from canon matches."""
        lead_canon = canon_matches[0] if canon_matches else {
            "text": "Citadel guards maintain checkpoints.",
            "metadata": {"district": "Market Cross Square"}
        }
        district = lead_canon.get("metadata", {}).get("district", "Citadel")

        if discipline == DisciplineType.LEVEL:
            return {
                "objective": f"Expand {district} with subterranean bypass corridors",
                "subsystem": "procedural_spatial_generator.py",
                "design_constraint": "Maintain 0.15m socket clearance on all connection seams"
            }
        elif discipline == DisciplineType.GAMEPLAY:
            return {
                "objective": f"Implement curfew line-of-sight detection and bribe mechanics in {district}",
                "subsystem": "server.py",
                "design_constraint": "Mask interaction queries to InteractionLayer.INTERACTIVE"
            }
        elif discipline == DisciplineType.NARRATIVE:
            return {
                "objective": f"Author dialogue branching for contraband couriers under the {district} curfew",
                "subsystem": "schemas/studio_contracts.py",
                "design_constraint": "Strict low-fantasy vernacular; reject anachronisms"
            }
        elif discipline == DisciplineType.CLIENT:
            return {
                "objective": f"Add instanced lantern light cones for curfew watchmen in {district}",
                "subsystem": "web_client/index.html",
                "design_constraint": "Total additional draw calls <= 15; child to actor hierarchy"
            }
        elif discipline == DisciplineType.SYSTEMS:
            return {
                "objective": "Expand dynamic commodity price bidding on hearth grain",
                "subsystem": "services/agent_runtime/src/systemic_economy_generator.py",
                "design_constraint": "All newly declared state enums must precede models"
            }
        else:  # CHAOS_QA
            return {
                "objective": "Construct stress test verifying zero player entrapment across newly paved corridors",
                "subsystem": "tools/manage.py",
                "design_constraint": "Enforce hard vetoes on WebGL budget and spatial overlap"
            }


if __name__ == "__main__":
    sync = TeamSyncEngine()
    notes = sync.conduct_standup(
        "W1900", "v0.5.0", active_unrest_theme="aqueduct smuggling and curfew evasion")
    print("\n--- DYNAMIC LORE-DRIVEN STANDUP MINUTES ---")
    print(f"Standup ID: {notes['standup_id']}")
    print(f"Unrest Focus: {notes['unrest_focus']}")
    print(f"Canon Nodes Ingested: {notes['retrieved_canon_nodes']}")
    print("\nDiscipline Objectives:")
    for disc, data in notes["discipline_briefs"].items():
        prop = data["contextual_proposal"]
        print(f" - [{disc}] {prop['objective']}")
        print(f"     Constraint: {prop['design_constraint']}")
