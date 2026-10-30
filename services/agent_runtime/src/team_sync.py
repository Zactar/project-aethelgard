"""
PROJECT AETHELGARD: CONTEXT-REACTIVE TEAM SYNC & IDEATION ENGINE
Generates dynamic brainstorming proposals conditioned on active world state and simulation phase.
"""

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
        """Pitches proposals tailored directly to the active phase."""
        phase = self.memory.active_phase
        proposals: List[BrainstormIdea] = []

        if phase == "MUNICIPAL_BREAD_RIOT" or self.memory.commodity_reserves.get("Flour", 0) <= 35.0:
            # Crisis proposals
            proposals.append(BrainstormIdea(
                idea_id="IDEA-SYS-CRISIS-01",
                proposing_agent="Systems_Architect",
                discipline=IdeaDiscipline.SYSTEMS_DESIGN,
                title="Curfew Bread Rations & Emergency Granary Depots",
                pitch="Institute caloric rationing. Church guards issue 1 hardtack loaf per citizen per day.",
                technical_feasibility_score=0.96,
                systemic_emergence_score=0.91,
                estimated_complexity="LOW"
            ))
            proposals.append(BrainstormIdea(
                idea_id="IDEA-LVL-CRISIS-01",
                proposing_agent="Level_Architect",
                discipline=IdeaDiscipline.LEVEL_ARCHITECTURE,
                title="Iron Barricades & Checkpoint Portcullis Gates",
                pitch="Seal main plaza thoroughfares with wooden barricades; funnel NPC flow through fortified checkpoints.",
                technical_feasibility_score=0.92,
                systemic_emergence_score=0.88,
                estimated_complexity="MEDIUM"
            ))
            proposals.append(BrainstormIdea(
                idea_id="IDEA-STY-CRISIS-01",
                proposing_agent="Lyric_StyleGuide",
                discipline=IdeaDiscipline.AESTHETIC_STYLE,
                title="Clandestine Night-Chalk Runes & Smoldering Braziers",
                pitch="Replace street torches with heavy iron braziers emitting thick acrid smoke and defiant guild sigils.",
                technical_feasibility_score=0.94,
                systemic_emergence_score=0.86,
                estimated_complexity="LOW"
            ))
        else:
            # Peacetime / Expansion proposals
            proposals.append(BrainstormIdea(
                idea_id="IDEA-SYS-PEACE-01",
                proposing_agent="Systems_Architect",
                discipline=IdeaDiscipline.SYSTEMS_DESIGN,
                title="Artisan Guild Smuggling Ring & Tithe Evasion",
                pitch="Artisans establish hidden gold reserves behind shop hearths to bypass the 35% Malakor tithe.",
                technical_feasibility_score=0.94,
                systemic_emergence_score=0.89,
                estimated_complexity="LOW"
            ))
            proposals.append(BrainstormIdea(
                idea_id="IDEA-LVL-PEACE-01",
                proposing_agent="Level_Architect",
                discipline=IdeaDiscipline.LEVEL_ARCHITECTURE,
                title="Vertical Aqueduct Catacombs with Dynamic Sluice Gates",
                pitch="Carve subterranean aqueduct conduits connecting the market square to the dock canals.",
                technical_feasibility_score=0.90,
                systemic_emergence_score=0.93,
                estimated_complexity="MEDIUM"
            ))
            proposals.append(BrainstormIdea(
                idea_id="IDEA-STY-PEACE-01",
                proposing_agent="Lyric_StyleGuide",
                discipline=IdeaDiscipline.AESTHETIC_STYLE,
                title="Soot-Etched Protest Murals & Street Lamp Decal Shifts",
                pitch="Dynamic visual grunge: warm tallow lantern blooms contrasted against stark theocratic stone.",
                technical_feasibility_score=0.95,
                systemic_emergence_score=0.84,
                estimated_complexity="LOW"
            ))

        proposals.append(BrainstormIdea(
            idea_id="IDEA-QA-01",
            proposing_agent="Chaos_Commander",
            discipline=IdeaDiscipline.QA_COMBAT_BALANCE,
            title="Stamina Exhaustion Penalty on Melee Roll Spamming",
            pitch="Introduce a 1.2s stagger penalty when dodging at zero stamina to dismantle infinite iframe loops.",
            technical_feasibility_score=0.98,
            systemic_emergence_score=0.79,
            estimated_complexity="LOW"
        ))

        return proposals

    def compile_sprint_goals(
        self, retro: Dict[str, Any], ideas: List[BrainstormIdea], target_district: str
    ) -> Tuple[List[SprintGoal], str]:
        selected_ideas = [i for i in ideas if i.technical_feasibility_score >= 0.88 and i.systemic_emergence_score >= 0.80]
        goals: List[SprintGoal] = []
        for idx, idea in enumerate(selected_ideas, start=1):
            goals.append(SprintGoal(
                goal_id=f"GOAL-W{int(self.memory.world_time // 100)}-{idx:02d}",
                target_district=target_district,
                primary_objective=idea.title,
                driving_ideas=[idea.idea_id],
                assigned_crews=[idea.proposing_agent, "Studio_Director"],
                success_criteria=f"Verified in {target_district} under phase {self.memory.active_phase}.",
                is_completed=False
            ))

        director_notes = (
            f"Goals aligned for {target_district} in phase {self.memory.active_phase}. "
            f"Active proposals: {len(goals)}. All crews authorized to construct."
        )
        return goals, director_notes

    def conduct_full_team_meeting(
        self, target_district: str, cycle_history: List[Dict[str, Any]]
    ) -> SprintMeetingMinutes:
        print("\n" + "=" * 70)
        print(f" [STUDIO ALL-HANDS]: SPRINT STANDUP & BRAINSTORMING CEREMONY ")
        print(f" Phase: {self.memory.active_phase} | District: {target_district} | Time: {self.memory.world_time:.1f}s")
        print("=" * 70)

        retro = self.run_sprint_retrospective(cycle_history)
        print(f"1. Retrospective Status : {retro['retrospective_consensus']}")
        print(f"   Commodity Reserves   : {retro['commodity_reserves']}")
        print(f"   Unresolved Bugs      : {retro['backlog_health']['total_unresolved_bugs']}")

        print("\n2. Context-Reactive Brainstorming Proposals:")
        ideas = self.conduct_brainstorming_session()
        for idea in ideas:
            print(f"   • [{idea.discipline.value}] {idea.proposing_agent}: \"{idea.title}\"")

        goals, notes = self.compile_sprint_goals(retro, ideas, target_district)
        print(f"\n3. Committed Sprint Goals for Upcoming Production Run:")
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
