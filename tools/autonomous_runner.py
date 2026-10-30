#!/usr/bin/env python3
"""
PROJECT AETHELGARD: AUTONOMOUS VIRTUAL STUDIO RUNNER
Pipes meeting goals directly into downstream sprint asset generation,
autonomous RFC authoring, codebase engineer patching, and release packaging.
"""

from tools.release_packager import package_release
from tools.engine_importer import EngineAssetIngester
from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent
from services.agent_runtime.src.team_sync import StudioCeremonyEngine
from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
from services.agent_runtime.src.optimization_engine import StudioOptimizationProfiler
from services.agent_runtime.src.codebase_engineer import CodebaseEngineerAgent
from services.agent_runtime.src.autonomous_authoring import AutonomousFeatureAuthorAgent
from schemas.studio_contracts import SprintGoal
import argparse
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


DISTRICT_ROSTER = [
    "District_MarketSquare",
    "District_OldUndercroft",
    "District_DocksCommons",
    "District_CathedralHeights"
]


class AutonomousStudioRunner:
    def __init__(self, meeting_cadence: int = 3):
        self.director = StudioDirectorManagerAgent()
        self.ingester = EngineAssetIngester()
        self.ceremony_engine = StudioCeremonyEngine(self.director.memory)
        self.author_agent = AutonomousFeatureAuthorAgent(self.director.memory)
        self.roadmap_engine = StudioRoadmapEngine()
        self.profiler = StudioOptimizationProfiler()
        self.engineer_agent = CodebaseEngineerAgent()
        self.meeting_cadence = meeting_cadence
        self.cycle_count = 0
        self.cycle_history: List[Dict[str, Any]] = []
        self.current_goals: List[SprintGoal] = []

    def run_cycle(self, cycle_index: int) -> Dict[str, Any]:
        self.cycle_count = cycle_index
        district = DISTRICT_ROSTER[(cycle_index - 1) % len(DISTRICT_ROSTER)]
        self.director.memory.world_time += 100.0

        player_stress = round(random.uniform(0.35, 0.88), 2)
        player_coords = (
            round(random.uniform(1000.0, 1800.0), 1),
            round(random.uniform(400.0, 1200.0), 1),
            0.0
        )
        sim_seed = 40000 + (cycle_index * 137)

        print("\n" + "=" * 70)
        print(
            f" >>> [CYCLE {cycle_index:02d}]: SPRINT DISPATCH ON '{district}' (Time: {self.director.memory.world_time:.1f}s) <<<")
        print("=" * 70)

        artifact = self.director.dispatch_studio_pipeline(
            district_id=district,
            player_stress=player_stress,
            player_pos=player_coords,
            seed=sim_seed,
            active_goals=self.current_goals
        )

        self.ingester.run_once()
        resolved_count = self.triage_bug_backlog()

        result = {
            "cycle": cycle_index,
            "district": district,
            "artifact_id": artifact["artifact_id"],
            "target_npc": artifact["raw_payload"]["target_npc"],
            "action": artifact["raw_payload"]["action"],
            "lore_score": artifact["lore_consistency_score"],
            "human_touch_score": artifact["human_touch_score"],
            "resolved_tickets": resolved_count
        }
        self.cycle_history.append(result)
        return result

    def triage_bug_backlog(self) -> int:
        queue = self.director.memory.bug_ticket_queue
        if not queue:
            return 0
        resolved_count = 0
        for ticket in queue:
            success, message = self.engineer_agent.inspect_and_patch_ticket(
                ticket)
            if success:
                print(
                    f"  [AUTO-CODEBASE-PATCH] {ticket.responsible_agent} resolved {ticket.ticket_id}: {message}")
                resolved_count += 1
            else:
                print(
                    f"  [AUTO-TRIAGE] {ticket.responsible_agent} reviewed {ticket.ticket_id}: {message}")

        self.director.memory.bug_ticket_queue = []

        # If patches were successfully applied, auto-commit to git
        if resolved_count > 0:
            committed = self.engineer_agent.commit_workspace_changes(
                f"apply {resolved_count} automated codebase patch(es) during cycle {self.cycle_count}"
            )
            if committed:
                print(
                    f"  [AUTO-GIT]: Committed verified code modifications to main branch.")

        return resolved_count

    def run_sprint_series(self, total_cycles: int, delay_between_cycles_sec: float = 0.2):
        start_time = time.time()
        print(
            f"\n[AUTONOMOUS STUDIO RUNNER]: Starting {total_cycles}-cycle goal-driven production run...")

        meeting = self.ceremony_engine.conduct_full_team_meeting(
            target_district=DISTRICT_ROSTER[0],
            cycle_history=[]
        )
        self.current_goals = meeting.selected_sprint_goals

        print(
            "\n[VIRTUAL DEV TEAM AUTHORING]: Drafting features from committed sprint goals...")
        self.author_agent.execute_autonomous_rfc_cycle(self.current_goals)

        shipped_ver = self.roadmap_engine.advance_milestone_progress(
            [g.primary_objective for g in self.current_goals])
        if shipped_ver:
            package_release(shipped_ver, "Shippable Milestone Expansion")

        for i in range(1, total_cycles + 1):
            self.run_cycle(i)

            if i % self.meeting_cadence == 0 and i < total_cycles:
                next_district = DISTRICT_ROSTER[i % len(DISTRICT_ROSTER)]
                meeting = self.ceremony_engine.conduct_full_team_meeting(
                    target_district=next_district,
                    cycle_history=self.cycle_history
                )
                self.current_goals = meeting.selected_sprint_goals
                print(
                    "\n[VIRTUAL DEV TEAM AUTHORING]: Drafting features from committed sprint goals...")
                self.author_agent.execute_autonomous_rfc_cycle(
                    self.current_goals)
                shipped_ver = self.roadmap_engine.advance_milestone_progress(
                    [g.primary_objective for g in self.current_goals])
                if shipped_ver:
                    package_release(
                        shipped_ver, "Shippable Milestone Expansion")

            if delay_between_cycles_sec > 0:
                time.sleep(delay_between_cycles_sec)

        elapsed = time.time() - start_time
        self.print_executive_summary(self.cycle_history, elapsed)

    def print_executive_summary(self, ledger: List[Dict[str, Any]], elapsed_sec: float):
        manifest = self.author_agent.load_manifest()
        report = self.profiler.audit_runtime_manifest(manifest)

        print("\n" + "#" * 70)
        print("          AUTONOMOUS MULTI-CYCLE SPRINT EXECUTIVE SUMMARY           ")
        print("#" * 70)
        print(f"Total Cycles Completed  : {len(ledger)}")
        print(f"Elapsed Wall Time       : {elapsed_sec:.2f} seconds")
        print(
            f"Total Assets Deployed   : {len(ledger) * 4} (Godot .tscn, Curves, Dialogues, C++ Headers)")
        print(
            f"WebGL Draw Calls Budget : {report.estimated_draw_calls} (Threshold: 120)")
        print(f"Runtime Manifest Size   : {report.payload_size_kb:.2f} KB")
        print(f"Technical Profile       : {report.triage_notes}")
        print("-" * 70)
        print(
            f"{'Cycle':<7} | {'District':<26} | {'Target NPC':<14} | {'Action':<24} | {'Soul':<5}")
        print("-" * 70)
        for entry in ledger:
            print(
                f"{entry['cycle']:<7} | "
                f"{entry['district']:<26} | "
                f"{entry['target_npc']:<14} | "
                f"{entry['action']:<24} | "
                f"{entry['human_touch_score']:<5.2f}"
            )
        print("#" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run autonomous dev team cycles.")
    parser.add_argument("--cycles", type=int, default=3,
                        help="Total cycles (default: 3)")
    parser.add_argument("--cadence", type=int, default=2,
                        help="Cycles between meetings (default: 2)")
    parser.add_argument("--delay", type=float, default=0.1,
                        help="Delay in seconds")
    args = parser.parse_args()

    runner = AutonomousStudioRunner(meeting_cadence=args.cadence)
    runner.run_sprint_series(total_cycles=args.cycles,
                             delay_between_cycles_sec=args.delay)


if __name__ == "__main__":
    main()
