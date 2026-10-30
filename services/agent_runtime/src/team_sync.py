import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import time
from typing import Dict, List, Any, Tuple

from schemas.studio_contracts import (
    IdeaDiscipline, BrainstormIdea, SprintGoal, SprintMeetingMinutes, BugSeverity
)
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus

class StudioCeremonyEngine:
    def __init__(self, memory_bus: StudioSharedMemoryBus):
        self.memory = memory_bus

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
        phase = self.memory.active_phase
        proposals: List[BrainstormIdea] = []

        if phase == "MUNICIPAL_BREAD_RIOT":
            proposals.append(BrainstormIdea(
                idea_id="IDEA-SYS-01", proposing_agent="Systems_Architect",
                discipline=IdeaDiscipline.SYSTEMS_DESIGN,
                title="Curfew Bread Rations & Emergency Granary Depots",
                pitch="Institute caloric rationing. Church guards issue 1 hardtack loaf per citizen per day.",
                technical_feasibility_score=0.96, systemic_emergence_score=0.91
            ))
        else:
            proposals.append(BrainstormIdea(
                idea_id="IDEA-SYS-01", proposing_agent="Systems_Architect",
                discipline=IdeaDiscipline.SYSTEMS_DESIGN,
                title="Artisan Guild Smuggling Ring & Tithe Evasion",
                pitch="Artisans establish hidden gold reserves behind shop hearths to bypass the 35% Malakor tithe.",
                technical_feasibility_score=0.94, systemic_emergence_score=0.89
            ))

        proposals.append(BrainstormIdea(
            idea_id="IDEA-LVL-01", proposing_agent="Level_Architect",
            discipline=IdeaDiscipline.LEVEL_ARCHITECTURE,
            title="Vertical Aqueduct Catacombs with Dynamic Sluice Gates",
            pitch="Carve subterranean aqueduct conduits connecting the market square to the dock canals.",
            technical_feasibility_score=0.90, systemic_emergence_score=0.93
        ))

        proposals.append(BrainstormIdea(
            idea_id="IDEA-CLI-01", proposing_agent="Client_Architect",
            discipline=IdeaDiscipline.AESTHETIC_STYLE,
            title="Volumetric Torchlight Blooms & Interactive Workstation Shaders",
            pitch="Deploy dynamic point lantern flickering and emissive pulses on active smart object meshes.",
            technical_feasibility_score=0.95, systemic_emergence_score=0.87
        ))

        proposals.append(BrainstormIdea(
            idea_id="IDEA-QA-01", proposing_agent="Chaos_Commander",
            discipline=IdeaDiscipline.QA_COMBAT_BALANCE,
            title="Automated Client Headless Navigation & Boundary Stress Test",
            pitch="Deploy automated bots traversing all topological nodes to catch out-of-bounds clipping.",
            technical_feasibility_score=0.98, systemic_emergence_score=0.82
        ))

        return proposals

    def compile_sprint_goals(
        self, retro: Dict[str, Any], ideas: List[BrainstormIdea], target_district: str
    ) -> Tuple[List[SprintGoal], str]:
        selected = [i for i in ideas if i.technical_feasibility_score >= 0.88 and i.systemic_emergence_score >= 0.80]
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

        director_notes = (
            f"Goals aligned for {target_district} under phase {self.memory.active_phase}. "
            f"Client and server pipelines synchronized. All crews cleared to build."
        )
        return goals, director_notes

    def conduct_full_team_meeting(
        self, target_district: str, cycle_history: List[Dict[str, Any]]
    ) -> SprintMeetingMinutes:
        print("\n" + "=" * 70)
        print(" [STUDIO ALL-HANDS]: SPRINT STANDUP & BRAINSTORMING CEREMONY ")
        print(f" Phase: {self.memory.active_phase} | District: {target_district} | Time: {self.memory.world_time:.1f}s")
        print("=" * 70)

        retro = self.run_sprint_retrospective(cycle_history)
        print(f"1. Retrospective Status : {retro['retrospective_consensus']}")
        print(f"   Commodity Reserves   : {retro['commodity_reserves']}")
        print(f"   Unresolved Bugs      : {retro['backlog_health']['total_unresolved_bugs']}")

        print("\n2. Cross-Crew Brainstorming Proposals:")
        ideas = self.conduct_brainstorming_session()
        for idea in ideas:
            print(f"   • [{idea.discipline.value}] {idea.proposing_agent}: '{idea.title}'")

        goals, notes = self.compile_sprint_goals(retro, ideas, target_district)
        print("\n3. Committed Sprint Goals:")
        for g in goals:
            print(f"   ▶ [{g.goal_id}] {g.primary_objective}")

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
