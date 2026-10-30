#!/usr/bin/env python3
"""
PROJECT AETHELGARD: AUTONOMOUS VIRTUAL STUDIO RUNNER (WITH TEAM CEREMONIES)
Executes multi-cycle autonomous planning, periodic team meetings, QA, and asset ingestion.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import argparse
import time
import random
from typing import List, Dict, Any

from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent
from services.agent_runtime.src.team_sync import StudioCeremonyEngine
from tools.engine_importer import EngineAssetIngester

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
        self.meeting_cadence = meeting_cadence
        self.cycle_count = 0
        self.cycle_history: List[Dict[str, Any]] = []

    def run_cycle(self, cycle_index: int) -> Dict[str, Any]:
        self.cycle_count = cycle_index
        district = DISTRICT_ROSTER[(cycle_index - 1) % len(DISTRICT_ROSTER)]
        self.director.memory.world_time += 100.0

        # Simulate dynamic economic shifts & player telemetry
        player_stress = round(random.uniform(0.35, 0.88), 2)
        player_coords = (
            round(random.uniform(1000.0, 1800.0), 1),
            round(random.uniform(400.0, 1200.0), 1),
            0.0
        )
        sim_seed = 40000 + (cycle_index * 137)

        print("\n" + "=" * 70)
        print(f" >>> [CYCLE {cycle_index:02d}]: SPRINT DISPATCH ON '{district}' (World Time: {self.director.memory.world_time:.1f}s) <<<")
        print("=" * 70)

        # 1. Pipeline Execution
        artifact = self.director.dispatch_studio_pipeline(
            district_id=district,
            player_stress=player_stress,
            player_pos=player_coords,
            seed=sim_seed
        )

        # 2. Ingest Assets into Engine Folders
        self.ingester.run_once()

        # 3. Bug Triage
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
            print(f"  [AUTO-TRIAGE] {ticket.responsible_agent} patched ticket '{ticket.ticket_id}': {ticket.title}")
            resolved_count += 1
        self.director.memory.bug_ticket_queue = []
        return resolved_count

    def run_sprint_series(self, total_cycles: int, delay_between_cycles_sec: float = 0.2):
        start_time = time.time()
        print(f"\n[AUTONOMOUS STUDIO RUNNER]: Commencing {total_cycles}-cycle milestone run...")

        # Initial Kickoff Meeting before Cycle 1
        self.ceremony_engine.conduct_full_team_meeting(
            target_district=DISTRICT_ROSTER[0],
            cycle_history=[]
        )

        for i in range(1, total_cycles + 1):
            self.run_cycle(i)

            # Convene periodic team meetings based on cadence
            if i % self.meeting_cadence == 0 and i < total_cycles:
                next_district = DISTRICT_ROSTER[i % len(DISTRICT_ROSTER)]
                self.ceremony_engine.conduct_full_team_meeting(
                    target_district=next_district,
                    cycle_history=self.cycle_history
                )

            if delay_between_cycles_sec > 0:
                time.sleep(delay_between_cycles_sec)

        elapsed = time.time() - start_time
        self.print_executive_summary(self.cycle_history, elapsed)

    def print_executive_summary(self, ledger: List[Dict[str, Any]], elapsed_sec: float):
        print("\n" + "#" * 70)
        print("          AUTONOMOUS MULTI-CYCLE SPRINT EXECUTIVE SUMMARY           ")
        print("#" * 70)
        print(f"Total Cycles Completed : {len(ledger)}")
        print(f"Elapsed Wall Time      : {elapsed_sec:.2f} seconds")
        print(f"Total Assets Deployed  : {len(ledger) * 4} (Curves, PCG Layouts, Dialogues, C++ Headers)")
        print("-" * 70)
        print(f"{'Cycle':<7} | {'District':<26} | {'Target NPC':<14} | {'Action':<22} | {'Soul':<5}")
        print("-" * 70)
        for entry in ledger:
            print(
                f"{entry['cycle']:<7} | "
                f"{entry['district']:<26} | "
                f"{entry['target_npc']:<14} | "
                f"{entry['action']:<22} | "
                f"{entry['human_touch_score']:<5.2f}"
            )
        print("#" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run autonomous dev team cycles with team ceremonies.")
    parser.add_argument("--cycles", type=int, default=6, help="Total cycles to run (default: 6)")
    parser.add_argument("--cadence", type=int, default=3, help="Cycles between team sync meetings (default: 3)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay in seconds between cycles")
    args = parser.parse_args()

    runner = AutonomousStudioRunner(meeting_cadence=args.cadence)
    runner.run_sprint_series(total_cycles=args.cycles, delay_between_cycles_sec=args.delay)
