#!/usr/bin/env python3
"""
PROJECT AETHELGARD: DYNAMIC SPRINT CEREMONY & BRAINSTORMING ENGINE
Synthesizes evolving sprint proposals based on active milestone epics, district biomes, and unrest levels.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import random
import time
from typing import Any, Dict, List, Tuple

from schemas.studio_contracts import (
    BrainstormIdea, BugSeverity, IdeaDiscipline, MilestoneStatus,
    SprintGoal, SprintMeetingMinutes
)
from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus

# Dynamic proposal generators per discipline
IDEA_BANKS = {
    IdeaDiscipline.SYSTEMS_DESIGN: [
        ("Black Market Commodity Arbitrage", "Establish dynamic price fluctuations for smuggled flour and medicinal tinctures."),
        ("Cathedral Tithe Inspection Protocols", "Enforce 35% grain seizures at city gates with contraband confiscation risk."),
        ("Emergency Caloric Bread Rationing", "Distribute hardtack ration coupons to de-escalate municipal riot unrest."),
        ("Guild Loan Sharking & Debt Collateral", "Allow artisans to pledge shop hearths as collateral for black market capital.")
    ],
    IdeaDiscipline.LEVEL_ARCHITECTURE: [
        ("Subterranean Drainage Conduits & Sluice Gates", "Carve canal passages connecting the low docks to hidden distillery vaults."),
        ("City Watch Garrison & Armory Checkpoints", "Erect fortified iron gates and weapon racks along the Market Cross perimeter."),
        ("Cathedral Undercroft Ossuary & Catacombs", "Excavate stone crypts beneath the basilica for covert guild rendezvous."),
        ("Hearthside Taproom & Common Lodgings", "Construct multi-tier wooden common house with peat hearths and ale casks.")
    ],
    IdeaDiscipline.NARRATIVE_LORE: [
        ("Inquisitor Vael's Heresy Inquest", "Deploy cathedral investigators interrogating apothecaries about forbidden herbs."),
        ("Dockmaster Orlov's Waterway Manifests", "Introduce corrupt dockmaster willing to falsify canal shipping registers."),
        ("Watch Captain Vane's Curfew Decrees", "Station municipal patrol commanders leveling spears at unauthorized gatherings."),
        ("Smuggler Kaelen's Undercroft Network", "Establish rogue guild contact offering forged tithe stamps for silver.")
    ],
    IdeaDiscipline.GAMEPLAY_MECHANICS: [
        ("Stealth Damping & Guard Line-of-Sight", "Calibrate player movement noise and shadow concealment inside clandestine zones."),
        ("Locomotion Dash & Stamina Bursts", "Tune high-velocity sprint bursts and rapid recovery envelopes during combat spikes."),
        ("Lockpicking & Sluice Crank Interaction Envelopes", "Implement mechanical timing checks for opening secured storage chests."),
        ("Tonic Buff Degradation Curves", "Add decaying visual aura shaders and tapering speed boosts for consumed elixirs.")
    ],
    IdeaDiscipline.AESTHETIC_STYLE: [
        ("Volumetric Fog & Smoky Hearth Blooms", "Deploy flickering point lanterns and ambient peat smoke shaders across alleys."),
        ("Riot Barricade Props & Broken Carts", "Dress streets with splintered grain crates, burning barrels, and protest banners."),
        ("Cathedral Stained Glass Radiance", "Cast dynamic kaleidoscopic light beams onto polished stone sanctuary floors."),
        ("Subterranean Water Reflection Shaders", "Simulate specular water ripples and dripping sluice conduits in low canals.")
    ],
    IdeaDiscipline.QA_COMBAT_BALANCE: [
        ("Monte Carlo Economic Arbitrage Stress Test", "Simulate 500 barter transactions to detect infinite gold duplication loops."),
        ("Topological Navmesh Reachability Audit", "Deploy automated pathfinder bots traversing all connected rooms and doors."),
        ("Smart Object Collision & Facing Yaw Validation", "Ensure all interaction anchors have 360-degree clear approach radius."),
        ("Consumable Buff Stacking Exploit Audit", "Stress test concurrent elixir ingestion to prevent unbounded velocity multiplication.")
    ]
}


class StudioCeremonyEngine:
    """Orchestrates cross-crew retrospectives, brainstorming sessions, and goal commitment."""

    def __init__(self, memory_bus: StudioSharedMemoryBus):
        self.memory = memory_bus
        self.roadmap_engine = StudioRoadmapEngine()

    def run_sprint_retrospective(self, cycle_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        unresolved_bugs = [b for b in self.memory.bug_ticket_queue]
        total_p0 = sum(1 for b in unresolved_bugs if b.severity == BugSeverity.P0_CRITICAL)
        total_p1 = sum(1 for b in unresolved_bugs if b.severity == BugSeverity.P1_HIGH)

        return {
            "completed_sprint_cycles": len(cycle_history),
            "current_district_unrest": round(self.memory.active_district_unrest, 3),
            "active_phase": self.memory.active_phase,
            "commodity_reserves": self.memory.commodity_reserves,
            "backlog_health": {
                "total_unresolved_bugs": len(unresolved_bugs),
                "p0_blockers": total_p0,
                "p1_exploits": total_p1
            },
            "retrospective_consensus": (
                "STABLE_PRODUCTION" if total_p0 == 0 else "HALT_FOR_HOTFIX"
            )
        }

    def conduct_brainstorming_session(self) -> List[BrainstormIdea]:
        active_milestone = self.roadmap_engine.get_active_milestone()
        proposals: List[BrainstormIdea] = []
        crew_roster = [
            ("Systems_Architect", IdeaDiscipline.SYSTEMS_DESIGN),
            ("Level_Architect", IdeaDiscipline.LEVEL_ARCHITECTURE),
            ("Narrative_Specialist", IdeaDiscipline.NARRATIVE_LORE),
            ("Gameplay_Specialist", IdeaDiscipline.GAMEPLAY_MECHANICS),
            ("Client_Architect", IdeaDiscipline.AESTHETIC_STYLE),
            ("Chaos_Commander", IdeaDiscipline.QA_COMBAT_BALANCE)
        ]

        # Rotate proposals based on world time and simulation phase
        random.seed(int(self.memory.world_time) + int(self.memory.active_district_unrest * 100))

        for agent_name, discipline in crew_roster:
            bank = IDEA_BANKS[discipline]
            title, pitch = random.choice(bank)
            feasibility = round(random.uniform(0.88, 0.98), 2)
            emergence = round(random.uniform(0.82, 0.96), 2)
            prop_id = f"IDEA-{discipline.value[:3]}-{int(self.memory.world_time % 1000):03d}"

            proposals.append(BrainstormIdea(
                idea_id=prop_id,
                proposing_agent=agent_name,
                discipline=discipline,
                title=title,
                pitch=f"[{active_milestone.version_tag} - {active_milestone.theme}]: {pitch}",
                technical_feasibility_score=feasibility,
                systemic_emergence_score=emergence
            ))

        return proposals

    def compile_sprint_goals(
        self, retro: Dict[str, Any], ideas: List[BrainstormIdea], target_district: str
    ) -> Tuple[List[SprintGoal], str]:
        # Filter top emergent ideas
        sorted_ideas = sorted(ideas, key=lambda x: (x.technical_feasibility_score + x.systemic_emergence_score), reverse=True)
        selected = sorted_ideas[:4]

        goals: List[SprintGoal] = []
        for idx, idea in enumerate(selected, start=1):
            goals.append(SprintGoal(
                goal_id=f"GOAL-W{int(self.memory.world_time // 100)}-{idx:02d}",
                target_district=target_district,
                primary_objective=idea.title,
                driving_ideas=[idea.idea_id],
                assigned_crews=[idea.proposing_agent, "Studio_Director"],
                success_criteria=f"Verified in {target_district} across engine and web client.",
                is_completed=False
            ))

        active_milestone = self.roadmap_engine.get_active_milestone()
        director_notes = (
            f"Sprint goals committed for {target_district} under {active_milestone.version_tag} ({active_milestone.theme}). "
            f"Phase: {self.memory.active_phase} | Unrest: {self.memory.active_district_unrest:.2f}. All crews cleared to build."
        )
        return goals, director_notes

    def conduct_full_team_meeting(
        self, target_district: str, cycle_history: List[Dict[str, Any]]
    ) -> SprintMeetingMinutes:
        print("\n" + "=" * 70)
        print(" [STUDIO ALL-HANDS]: DYNAMIC SPRINT STANDUP & MILESTONE BURNDOWN ")
        print(f" Phase: {self.memory.active_phase} | District: {target_district} | Time: {self.memory.world_time:.1f}s")
        print("=" * 70)

        retro = self.run_sprint_retrospective(cycle_history)
        print(f"1. Retrospective Status : {retro['retrospective_consensus']}")
        print(f"   Commodity Reserves   : {retro['commodity_reserves']}")
        print(f"   Unresolved Bugs      : {retro['backlog_health']['total_unresolved_bugs']}")

        print("\n2. Cross-Crew Brainstorming Proposals:")
        ideas = self.conduct_brainstorming_session()
        for idea in ideas:
            print(f"   * [{idea.discipline.value}] {idea.proposing_agent}: '{idea.title}'")

        goals, notes = self.compile_sprint_goals(retro, ideas, target_district)
        print("\n3. Committed Sprint Goals:")
        for g in goals:
            print(f"   > [{g.goal_id}] {g.primary_objective}")

        meeting_minutes = SprintMeetingMinutes(
            meeting_id=f"SYNC-W{int(self.memory.world_time)}",
            world_time_marker=self.memory.world_time,
            retrospective_summary=retro,
            brainstorm_proposals=ideas,
            selected_sprint_goals=goals,
            director_closing_notes=notes
        )

        out_dir = Path("build/staging/meetings")
        out_dir.mkdir(parents=True, exist_ok=True)
        minutes_path = out_dir / f"{meeting_minutes.meeting_id}.json"
        with open(minutes_path, "w", encoding="utf-8") as f:
            f.write(meeting_minutes.model_dump_json(indent=2))

        print(f"\n[STUDIO DIRECTOR]: Minutes archived to {minutes_path}\n" + "=" * 70 + "\n")
        return meeting_minutes