import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from schemas.studio_contracts import (
    StudioMilestone, StudioEpic, MilestoneStatus, BiomeType, SprintGoal
)

ROADMAP_DIR = Path("build/roadmap")
ROADMAP_FILE = ROADMAP_DIR / "studio_roadmap.json"

DEFAULT_MILESTONES = [
    StudioMilestone(
        milestone_id="M1_UNDERCROFT_EXPANSION",
        version_tag="v0.2.0",
        theme="The Subterranean Smuggling Conduit",
        target_phase="PEACETIME_COMMERCE",
        status=MilestoneStatus.IN_PROGRESS,
        epics=[
            StudioEpic(
                epic_id="EPIC_M1_01",
                title="Carve Subterranean Undercroft Vaults",
                target_biome=BiomeType.SUBTERRANEAN_UNDERCROFT,
                primary_deliverable="Contiguous spatial nodes connecting aqueducts to clandestine storage",
                assigned_crews=["Level_Architect", "Client_Architect"]
            ),
            StudioEpic(
                epic_id="EPIC_M1_02",
                title="Deploy Black Market Contraband Economy",
                target_biome=BiomeType.SUBTERRANEAN_UNDERCROFT,
                primary_deliverable="Forged seals, illicit grain arbitration, and stealth buff items",
                assigned_crews=["Systems_Architect", "Gameplay_Specialist"]
            )
        ],
        release_notes=["Subterranean aqueduct expansion", "Consumable buff system with active timers"]
    ),
    StudioMilestone(
        milestone_id="M2_CATHEDRAL_INQUEST",
        version_tag="v0.3.0",
        theme="Martial Law & Theocratic Tithe Seizures",
        target_phase="MUNICIPAL_BREAD_RIOT",
        status=MilestoneStatus.PLANNING,
        epics=[
            StudioEpic(
                epic_id="EPIC_M2_01",
                title="Construct City Watch Garrison Checkpoints",
                target_biome=BiomeType.CATHEDRAL_HEIGHTS,
                primary_deliverable="Fortified watch garrison, iron barricades, and armory smart objects",
                assigned_crews=["Level_Architect", "Client_Architect"]
            ),
            StudioEpic(
                epic_id="EPIC_M2_02",
                title="Implement Granary Caloric Rationing Loop",
                target_biome=BiomeType.CATHEDRAL_HEIGHTS,
                primary_deliverable="Hardtack food queues, curfew patrols, and high-tension ambient lighting",
                assigned_crews=["Systems_Architect", "Narrative_Specialist"]
            )
        ],
        release_notes=["Martial curfew mechanics", "Cathedral district fortifications", "Emergency food rationing"]
    )
]

class StudioRoadmapEngine:
    def __init__(self):
        ROADMAP_DIR.mkdir(parents=True, exist_ok=True)
        if not ROADMAP_FILE.exists():
            self.save_roadmap(DEFAULT_MILESTONES)

    def load_roadmap(self) -> List[StudioMilestone]:
        if not ROADMAP_FILE.exists():
            return DEFAULT_MILESTONES
        raw = json.loads(ROADMAP_FILE.read_text(encoding="utf-8"))
        return [StudioMilestone.model_validate(m) for m in raw]

    def save_roadmap(self, milestones: List[StudioMilestone]):
        raw = [m.model_dump() for m in milestones]
        ROADMAP_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    def get_active_milestone(self) -> StudioMilestone:
        milestones = self.load_roadmap()
        for m in milestones:
            if m.status in (MilestoneStatus.IN_PROGRESS, MilestoneStatus.PLANNING):
                return m
        return milestones[-1]

    def advance_milestone_progress(self, deployed_rfc_titles: List[str]) -> Optional[str]:
        milestones = self.load_roadmap()
        active = None
        for m in milestones:
            if m.status == MilestoneStatus.IN_PROGRESS:
                active = m
                break

        if not active:
            return None

        for epic in active.epics:
            if not epic.is_completed:
                for title in deployed_rfc_titles:
                    words = [w.lower() for w in epic.title.split() if len(w) > 4]
                    if any(w in title.lower() for w in words):
                        epic.is_completed = True
                        break

        # Check if milestone is ready for shippable release
        all_done = all(e.is_completed for e in active.epics)
        if all_done and active.status != MilestoneStatus.SHIPPED:
            active.status = MilestoneStatus.SHIPPED
            shipped_version = active.version_tag
            self.save_roadmap(milestones)
            return shipped_version

        self.save_roadmap(milestones)
        return None
