"""
PROJECT AETHELGARD: VIRTUAL STUDIO TEAM SYNC & BRAINSTORMING ENGINE
Automates team meetings, retrospectives, collaborative ideation, and goal synthesis.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import random
import time
from typing import Dict, List, Any, Tuple

from schemas.studio_contracts import (
    IdeaDiscipline, BrainstormIdea, SprintGoal, SprintMeetingMinutes, BugSeverity
)
from services.agent_runtime.src.virtual_studio_engine import StudioSharedMemoryBus


class StudioCeremonyEngine:
    def __init__(self, memory_bus: StudioSharedMemoryBus):
        self.memory = memory_bus

    # ==========================================================================
    # PHASE 1: RETROSPECTIVE & CONSOLIDATION
    # ==========================================================================
    def run_sprint_retrospective(self, cycle_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reviews systemic metrics, Leontief reserves, and unresolved bugs."""
        unresolved_bugs = [b for b in self.memory.bug_ticket_queue]
        total_p0 = sum(1 for b in unresolved_bugs if b.severity == BugSeverity.P0_CRITICAL)
        total_p1 = sum(1 for b in unresolved_bugs if b.severity == BugSeverity.P1_HIGH)

        retro = {
            "completed_sprint_cycles": len(cycle_history),
            "current_district_unrest": round(self.memory.active_district_unrest, 3),
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
        return retro

    # ==========================================================================
    # PHASE 2: COLLABORATIVE BRAINSTORMING
    # ==========================================================================
    def conduct_brainstorming_session(self) -> List[BrainstormIdea]:
        """Gathers creative proposals from specialized agent personas."""
        proposals: List[BrainstormIdea] = []

        # 1. Systems Architect Pitch (Metabolic Mechanics)
        proposals.append(BrainstormIdea(
            idea_id="IDEA-SYS-01",
            proposing_agent="Systems_Architect",
            discipline=IdeaDiscipline.SYSTEMS_DESIGN,
            title="Drought-Induced Grain Arbitrage & Black Market Mills",
            pitch=(
                "Introduce a regional harvest drought curve. When flour stockpiles drop below 30 units, "
                "bakers begin purchasing illicit milled grain from the Old Undercroft at a 2.5x price markup."
            ),
            technical_feasibility_score=0.95,
            systemic_emergence_score=0.90,
            estimated_complexity="LOW"
        ))

        # 2. Level Architect Pitch (Spatial Emergence)
        proposals.append(BrainstormIdea(
            idea_id="IDEA-LVL-01",
            proposing_agent="Level_Architect",
            discipline=IdeaDiscipline.LEVEL_ARCHITECTURE,
            title="Vertical Aqueduct Catacombs with Dynamic Sluice Gates",
            pitch=(
                "Carve contiguous vertical water-drainage corridors beneath Market Square linking directly "
                "to Docks Commons. Sluice gate Smart Objects can be sealed to dry out escape routes or opened to flood them."
            ),
            technical_feasibility_score=0.88,
            systemic_emergence_score=0.92,
            estimated_complexity="MEDIUM"
        ))

        # 3. Lyric Pitch (Aesthetic & Cultural Subversion)
        proposals.append(BrainstormIdea(
            idea_id="IDEA-STY-01",
            proposing_agent="Lyric_StyleGuide",
            discipline=IdeaDiscipline.AESTHETIC_STYLE,
            title="Soot-Etched Protest Murals & Street Lamp Decal Shifts",
            pitch=(
                "When district tension exceeds 0.65, dynamically swap clean cathedral banners for "
                "hand-drawn chalk graffiti and smoldering tallow torches. Give the working-class alleyways "
                "a rhythmic, defiant visual pulse."
            ),
            technical_feasibility_score=0.92,
            systemic_emergence_score=0.85,
            estimated_complexity="LOW"
        ))

        # 4. Chaos Commander Pitch (Adversarial Balance Gauntlet)
        proposals.append(BrainstormIdea(
            idea_id="IDEA-QA-01",
            proposing_agent="Chaos_Commander",
            discipline=IdeaDiscipline.QA_COMBAT_BALANCE,
            title="Stamina Exhaustion Penalty on Melee Roll Spamming",
            pitch=(
                "Min-Maxer bots are abusing zero-cost roll cancels. We need an exponential stamina recovery "
                "curve that induces a 1.2s stagger when rolling at zero stamina."
            ),
            technical_feasibility_score=0.98,
            systemic_emergence_score=0.78,
            estimated_complexity="LOW"
        ))

        return proposals

    # ==========================================================================
    # PHASE 3: SPRINT PLANNING & GOAL SELECTION
    # ==========================================================================
    def compile_sprint_goals(
        self, retro: Dict[str, Any], ideas: List[BrainstormIdea], target_district: str
    ) -> Tuple[List[SprintGoal], str]:
        """Studio Director synthesizes top proposals into committed sprint goals."""
        # Filter high feasibility and emergence ideas
        selected_ideas = [i for i in ideas if i.technical_feasibility_score >= 0.85 and i.systemic_emergence_score >= 0.80]
        
        goals: List[SprintGoal] = []
        for idx, idea in enumerate(selected_ideas, start=1):
            goals.append(SprintGoal(
                goal_id=f"GOAL-S{int(self.memory.world_time // 100)}-{idx:02d}",
                target_district=target_district,
                primary_objective=idea.title,
                driving_ideas=[idea.idea_id],
                assigned_crews=[idea.proposing_agent, "Studio_Director"],
                success_criteria=f"Empirically verified in {target_district} via headless Gauntlet pass.",
                is_completed=False
            ))

        director_notes = (
            f"Sprint goals locked for {target_district}. Backlog cleared of critical faults. "
            f"Prioritizing systemic feedback loops over static prop dressing. All teams cleared to build."
        )
        return goals, director_notes

    def conduct_full_team_meeting(
        self, target_district: str, cycle_history: List[Dict[str, Any]]
    ) -> SprintMeetingMinutes:
        print("\n" + "=" * 70)
        print(f" [STUDIO ALL-HANDS]: SPRINT STANDUP & BRAINSTORMING CEREMONY ")
        print(f" Target District: {target_district} | World Time: {self.memory.world_time:.1f}s")
        print("=" * 70)

        # 1. Retrospective
        retro = self.run_sprint_retrospective(cycle_history)
        print(f"1. Retrospective Status : {retro['retrospective_consensus']}")
        print(f"   Unresolved Bugs      : {retro['backlog_health']['total_unresolved_bugs']} (P0: {retro['backlog_health']['p0_blockers']})")
        print(f"   Commodity Reserves   : {retro['commodity_reserves']}")

        # 2. Brainstorming
        print("\n2. Cross-Crew Brainstorming Pitches:")
        ideas = self.conduct_brainstorming_session()
        for idea in ideas:
            print(f"   • [{idea.discipline.value}] {idea.proposing_agent}: \"{idea.title}\"")
            print(f"     Pitch: {idea.pitch}")
            print(f"     Feasibility: {idea.technical_feasibility_score:.2f} | Emergence: {idea.systemic_emergence_score:.2f}")

        # 3. Goal Selection
        goals, notes = self.compile_sprint_goals(retro, ideas, target_district)
        print(f"\n3. Committed Sprint Goals for Upcoming Production Run:")
        for g in goals:
            print(f"   ▶ [{g.goal_id}] {g.primary_objective} (Assigned: {', '.join(g.assigned_crews)})")

        meeting_minutes = SprintMeetingMinutes(
            meeting_id=f"SYNC-W{int(self.memory.world_time)}",
            world_time_marker=self.memory.world_time,
            retrospective_summary=retro,
            brainstorm_proposals=ideas,
            selected_sprint_goals=goals,
            director_closing_notes=notes
        )

        # Persist minutes to build/staging/
        out_dir = Path("build/staging/meetings")
        out_dir.mkdir(parents=True, exist_ok=True)
        minutes_path = out_dir / f"{meeting_minutes.meeting_id}.json"
        with open(minutes_path, "w", encoding="utf-8") as f:
            f.write(meeting_minutes.model_dump_json(indent=2))

        print(f"\n[STUDIO DIRECTOR]: Meeting minutes archived to {minutes_path}\n" + "=" * 70 + "\n")
        return meeting_minutes
