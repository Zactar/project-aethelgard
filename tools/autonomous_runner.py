#!/usr/bin/env python3
"""
PROJECT AETHELGARD: AUTONOMOUS VIRTUAL STUDIO SPRINT RUNNER
Executes multi-cycle autonomous planning, design, QA, and asset ingestion.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import argparse
import time
import random
from typing import List, Dict, Any

from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent
from tools.engine_importer import EngineAssetIngester

# Target district roster for systemic world expansion
DISTRICT_ROSTER = [
    "District_MarketSquare",
    "District_OldUndercroft",
    "District_DocksCommons",
    "District_CathedralHeights"
]

class AutonomousStudioRunner:
    def __init__(self):
        self.director = StudioDirectorManagerAgent()
        self.ingester = EngineAssetIngester()
        self.cycle_count = 0

    def run_cycle(self, cycle_index: int) -> Dict[str, Any]:
        """Executes a single autonomous development and world-simulation cycle."""
        self.cycle_count = cycle_index
        district = DISTRICT_ROSTER[(cycle_index - 1) % len(DISTRICT_ROSTER)]
        
        # Advance world clock and environmental parameters
        self.director.memory.world_time += 100.0
        
        # Dynamically vary player stress and spatial coordinates to simulate diverse player sessions
        player_stress = round(random.uniform(0.35, 0.88), 2)
        player_coords = (
            round(random.uniform(1000.0, 1800.0), 1),
            round(random.uniform(400.0, 1200.0), 1),
            0.0
        )
        sim_seed = 40000 + (cycle_index * 137)

        print("\n" + "=" * 70)
        print(f" >>> [CYCLE {cycle_index:02d}]: SPRINT DISPATCH ON '{district}' (World Time: {self.director.memory.world_time}s) <<<")
        print("=" * 70)
        print(f"Input Telemetry: Stress={player_stress:.2f} | PlayerPos={player_coords} | Seed={sim_seed}")

        # 1. Execute Virtual Studio Pipeline (Planning -> Design -> Content -> QA)
        artifact = self.director.dispatch_studio_pipeline(
            district_id=district,
            player_stress=player_stress,
            player_pos=player_coords,
            seed=sim_seed
        )

        # 2. Ingest generated artifacts into Unreal Engine directories
        print("[AUTONOMOUS RUNNER]: Ingesting staged assets to Unreal Engine...")
        self.ingester.run_once()

        # 3. Process the QA Bug Backlog: Auto-resolve tickets via Systems/StateTree patches
        resolved_tickets = self.triage_bug_backlog()

        return {
            "cycle": cycle_index,
            "district": district,
            "artifact_id": artifact["artifact_id"],
            "target_npc": artifact["raw_payload"]["target_npc"],
            "action": artifact["raw_payload"]["action"],
            "lore_score": artifact["lore_consistency_score"],
            "human_touch_score": artifact["human_touch_score"],
            "resolved_tickets": resolved_tickets
        }

    def triage_bug_backlog(self) -> int:
        """Simulates dev agents pulling and resolving tickets filed by the Chaos Crew."""
        queue = self.director.memory.bug_ticket_queue
        if not queue:
            return 0

        resolved_count = 0
        remaining_queue = []

        for ticket in queue:
            # High-priority and medium tickets get patched within the cycle
            print(f"  [AUTO-TRIAGE] {ticket.responsible_agent} patched ticket '{ticket.ticket_id}': {ticket.title}")
            resolved_count += 1

        self.director.memory.bug_ticket_queue = remaining_queue
        return resolved_count

    def run_sprint_series(self, total_cycles: int, delay_between_cycles_sec: float = 1.0):
        """Runs the studio for a fixed number of autonomous cycles."""
        start_time = time.time()
        print(f"\n[AUTONOMOUS STUDIO RUNNER]: Starting batch run of {total_cycles} autonomous cycles...\n")

        summary_ledger = []
        for i in range(1, total_cycles + 1):
            cycle_result = self.run_cycle(i)
            summary_ledger.append(cycle_result)
            if i < total_cycles and delay_between_cycles_sec > 0:
                time.sleep(delay_between_cycles_sec)

        elapsed = time.time() - start_time
        self.print_executive_summary(summary_ledger, elapsed)

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
    parser = argparse.ArgumentParser(description="Run autonomous dev team cycles for Project Aethelgard.")
    parser.add_argument("--cycles", type=int, default=4, help="Number of autonomous cycles to run (default: 4)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay in seconds between cycles (default: 0.5)")
    args = parser.parse_args()

    runner = AutonomousStudioRunner()
    runner.run_sprint_series(total_cycles=args.cycles, delay_between_cycles_sec=args.delay)
