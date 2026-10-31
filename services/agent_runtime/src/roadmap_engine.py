import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from schemas.studio_contracts import (
    BiomeType, MilestoneStatus, SprintGoal, StudioEpic, StudioMilestone
)

ROADMAP_DIR = Path("build/roadmap")
ROADMAP_FILE = ROADMAP_DIR / "studio_roadmap.json"

DEFAULT_MILESTONES = [
    StudioMilestone(
        milestone_id="M1_UNDERCROFT_EXPANSION",
        version_tag="v0.2.0",
        theme="The Subterranean Smuggling Conduit",
        target_phase="PEACETIME_COMMERCE",
        status=MilestoneStatus.SHIPPED,
        epics=[
            StudioEpic(
                epic_id="EPIC_M1_01",
                title="Carve Subterranean Undercroft Vaults",
                target_biome=BiomeType.SUBTERRANEAN_UNDERCROFT,
                primary_deliverable="Contiguous spatial nodes connecting aqueducts to clandestine storage",
                assigned_crews=["Level_Architect", "Client_Architect"],
                is_completed=True
            ),
            StudioEpic(
                epic_id="EPIC_M1_02",
                title="Deploy Black Market Contraband Economy",
                target_biome=BiomeType.SUBTERRANEAN_UNDERCROFT,
                primary_deliverable="Forged seals, illicit grain arbitration, and stealth buff items",
                assigned_crews=["Systems_Architect", "Gameplay_Specialist"],
                is_completed=True
            )
        ],
        release_notes=["Subterranean aqueduct expansion",
                       "Consumable buff system with active timers"]
    ),
    StudioMilestone(
        milestone_id="M2_CATHEDRAL_INQUEST",
        version_tag="v0.3.0",
        theme="Martial Law & Theocratic Tithe Seizures",
        target_phase="MUNICIPAL_BREAD_RIOT",
        status=MilestoneStatus.SHIPPED,
        epics=[
            StudioEpic(
                epic_id="EPIC_M2_01",
                title="Construct City Watch Garrison Checkpoints",
                target_biome=BiomeType.CATHEDRAL_HEIGHTS,
                primary_deliverable="Fortified watch garrison, iron barricades, and armory smart objects",
                assigned_crews=["Level_Architect", "Client_Architect"],
                is_completed=True
            ),
            StudioEpic(
                epic_id="EPIC_M2_02",
                title="Implement Granary Caloric Rationing Loop",
                target_biome=BiomeType.CATHEDRAL_HEIGHTS,
                primary_deliverable="Hardtack food queues, curfew patrols, and high-tension ambient lighting",
                assigned_crews=["Systems_Architect", "Narrative_Specialist"],
                is_completed=True
            )
        ],
        release_notes=["Martial curfew mechanics",
                       "Cathedral district fortifications", "Emergency food rationing"]
    ),
    StudioMilestone(
        milestone_id="M3_BREAD_RIOT_SIEGE",
        version_tag="v0.4.0",
        theme="The Bread Riot & Siege of the High Seat",
        target_phase="MUNICIPAL_BREAD_RIOT",
        status=MilestoneStatus.IN_PROGRESS,
        epics=[
            StudioEpic(
                epic_id="EPIC_M3_01",
                title="Erect Riot Barricades & Fortified Thoroughfares",
                target_biome=BiomeType.CIVIC_MARKET,
                primary_deliverable="Obstacle barricades, splintered timber carts, and high-unrest crimson lighting",
                assigned_crews=["Level_Architect", "Client_Architect"],
                is_completed=False
            ),
            StudioEpic(
                epic_id="EPIC_M3_02",
                title="Infiltrate Arch-Prelate Malakor's Inner Sanctum",
                target_biome=BiomeType.CATHEDRAL_HEIGHTS,
                primary_deliverable="Sanctum keycard puzzle, episcopal decree ledger, and high-tier stealth items",
                assigned_crews=["Systems_Architect", "Narrative_Specialist"],
                is_completed=False
            )
        ],
        release_notes=["Bread riot escalation phase",
                       "Dynamic barrier props", "Sanctum infiltration storyline"]
    ),
    StudioMilestone(
        milestone_id="M4_GRAND_SLUICE_CONCLAVE",
        version_tag="v0.5.0",
        theme="The Episcopal Conclave & Grand Sluice Network",
        target_phase="POST_RIOT_MARTIAL_RATIONING",
        status=MilestoneStatus.PLANNING,
        epics=[
            StudioEpic(
                epic_id="EPIC_M4_01",
                title="Commission Grand Subterranean Sluice Mechanism",
                target_biome=BiomeType.SUBTERRANEAN_UNDERCROFT,
                primary_deliverable="Multi-valve aqueduct drainage network and deep waterway traversal",
                assigned_crews=["Level_Architect", "Gameplay_Specialist"],
                is_completed=False
            ),
            StudioEpic(
                epic_id="EPIC_M4_02",
                title="Enforce Guild Trade Arbitration & Debt Debt Collateral",
                target_biome=BiomeType.LOW_DOCKS,
                primary_deliverable="Live commodity price bidding and dynamic loan debt liquidation",
                assigned_crews=["Systems_Architect", "Chaos_Commander"],
                is_completed=False
            )
        ],
        release_notes=["Grand sluice network",
                       "Commodity arbitrage market", "Full narrative conclusion"]
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
            if m.status == MilestoneStatus.IN_PROGRESS:
                return m
        for m in milestones:
            if m.status == MilestoneStatus.PLANNING:
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
            for m in milestones:
                if m.status == MilestoneStatus.PLANNING:
                    m.status = MilestoneStatus.IN_PROGRESS
                    active = m
                    break

        if not active:
            return None

        manifest_path = Path("web_client/game_runtime_manifest.json")
        manifest_data = {}
        if manifest_path.exists():
            try:
                manifest_data = json.loads(
                    manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        existing_nodes = list(manifest_data.get(
            "spatial_layout", {}).get("nodes", {}).keys())
        existing_items = list(manifest_data.get("items", {}).keys())

        # Strict Verification: Epic completes ONLY if matching physical nodes, items, or RFCs exist
        for epic in active.epics:
            if not epic.is_completed:
                epic_words = epic.title.lower()

                # 1. Undercroft / Vault verification
                if "vault" in epic_words or "aqueduct" in epic_words:
                    if any("AQUEDUCT" in n or "VAULT" in n or "UNDERCROFT" in n for n in existing_nodes):
                        epic.is_completed = True

                # 2. Black Market Economy verification
                elif "contraband" in epic_words or "black market" in epic_words:
                    if any("contraband" in i or "permit" in i for i in existing_items):
                        epic.is_completed = True

                # 3. Garrison Checkpoints / Barricades verification
                elif "checkpoint" in epic_words or "garrison" in epic_words or "barricade" in epic_words:
                    has_node = any(
                        "GARRISON" in n or "BASTION" in n or "BARRICADE" in n for n in existing_nodes)
                    has_rfc = any("garrison" in t.lower(
                    ) or "barricade" in t.lower() for t in deployed_rfc_titles)
                    if has_node or has_rfc:
                        epic.is_completed = True

                # 4. Caloric Rationing / Grain verification
                elif "ration" in epic_words or "caloric" in epic_words:
                    has_item = any(
                        "ration" in i or "flour" in i or "hard tack" in i for i in existing_items)
                    has_rfc = any("ration" in t.lower() or "bread" in t.lower()
                                  for t in deployed_rfc_titles)
                    if has_item or has_rfc:
                        epic.is_completed = True

                # 5. Sanctum Infiltration verification
                elif "sanctum" in epic_words or "malakor" in epic_words:
                    has_node = any(
                        "SANCTUM" in n or "CATHEDRAL" in n for n in existing_nodes)
                    has_rfc = any("sanctum" in t.lower()
                                  for t in deployed_rfc_titles)
                    if has_node or has_rfc:
                        epic.is_completed = True

        # Complete milestone only when all epics are strictly satisfied
        all_done = all(e.is_completed for e in active.epics)
        if all_done and active.status != MilestoneStatus.SHIPPED:
            active.status = MilestoneStatus.SHIPPED
            shipped_version = active.version_tag

            # Promote next milestone
            for m in milestones:
                if m.status == MilestoneStatus.PLANNING:
                    m.status = MilestoneStatus.IN_PROGRESS
                    break

            self.save_roadmap(milestones)
            return shipped_version

        self.save_roadmap(milestones)
        return None
