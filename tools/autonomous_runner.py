#!/usr/bin/env python3
"""
tools/autonomous_runner.py
Project Aethelgard: Autonomous Virtual Studio Production Orchestrator (`aethelgard auto N`)
Executes the immutable 6-phase multi-agent sprint lifecycle with zero hardcoded game logic.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from schemas.studio_contracts import DeliverableStatus
from services.agent_runtime.src.blueprint_planner import BlueprintPlanner
from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
from services.agent_runtime.src.team_sync import TeamSyncEngine
from services.agent_runtime.src.autonomous_authoring import AutonomousAuthoringAgent
from services.agent_runtime.src.virtual_studio_engine import VirtualStudioEngine
from services.agent_runtime.src.codebase_engineer import CodebaseEngineerAgent
from tools.validate_webapp import audit_webapp_playability
from tools.release_packager import ReleasePackager

logger = logging.getLogger("Aethelgard.AutonomousRunner")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class AutonomousProductionOrchestrator:
    def __init__(self, workspace_root: Path = WORKSPACE_ROOT):
        self.workspace_root = Path(workspace_root)
        self.planner = BlueprintPlanner(workspace_root=self.workspace_root)
        self.roadmap_engine = StudioRoadmapEngine(workspace_root=self.workspace_root)
        self.team_sync = TeamSyncEngine(workspace_root=self.workspace_root, roadmap_engine=self.roadmap_engine)
        self.authoring_agent = AutonomousAuthoringAgent(workspace_root=self.workspace_root)
        self.studio_engine = VirtualStudioEngine(workspace_root=self.workspace_root)
        self.codebase_engineer = CodebaseEngineerAgent(workspace_root=self.workspace_root)
        self.release_packager = ReleasePackager(workspace_root=self.workspace_root)

    def run_cycle(self, cycle_index: int = 1) -> Dict[str, Any]:
        cycle_tag = f"AUTO-C{cycle_index:02d}"
        logger.info(f"=== INITIATING AUTONOMOUS SPRINT CYCLE [{cycle_tag}] ===")

        # Phase 0: GDD Ingestion Check
        self.planner.check_inbox_and_bootstrap()

        roadmap = self.roadmap_engine.load_roadmap()
        active_ver = roadmap.active_version
        milestone = next((m for m in roadmap.milestones if m.version == active_ver), None)

        if not milestone:
            logger.info("[AutonomousRunner] No active milestone found. All planned milestones complete.")
            return {"cycle": cycle_tag, "status": "COMPLETE"}

        logger.info(f"Active Roadmap Milestone Target: {active_ver} ({milestone.theme})")

        # Phase 1: Team Standup ($0.00 local alignment)
        self.team_sync.conduct_standup(cycle_id=cycle_tag)

        # Phase 2: 1-Call Batched Multi-Agent RFC Authoring
        staged_dir = self.workspace_root / "build" / "staging" / "rfcs"
        approved_dir = self.workspace_root / "build" / "rfcs" / "approved"
        existing_rfcs = list(staged_dir.glob("*.json")) + list(approved_dir.glob("*.json"))

        pending_deliverables = []
        for deliv in milestone.deliverables:
            if deliv.status == DeliverableStatus.VERIFIED:
                continue
            already_authored = False
            for rf in existing_rfcs:
                try:
                    data = json.loads(rf.read_text(encoding="utf-8"))
                    tag = data.get("milestone_tag") or data.get("target_milestone")
                    if tag == active_ver and deliv.title.lower() in data.get("title", "").lower():
                        already_authored = True
                        break
                except Exception:
                    pass
            if not already_authored:
                pending_deliverables.append(deliv)

        if pending_deliverables:
            self.authoring_agent.author_milestone_rfcs_batch(pending_deliverables, milestone=active_ver)

        # Phase 3: Review Board Quorum ($0.00 local contract check)
        review_results = self.studio_engine.evaluate_staged_rfcs()

        # Phase 4: Cohesive Milestone Plugin Synthesis & Headless VM Verification
        implemented_count = self.codebase_engineer.implement_approved_rfcs(
            review_results=review_results,
            active_version=active_ver
        )
        logger.info(f"[Phase 4: Implementation] CodebaseEngineer verified & applied {implemented_count} RFCs.")

        # Phase 5: Chaos QA Playability & Headless Runtime Audit
        webapp_valid = audit_webapp_playability()
        if not webapp_valid:
            logger.error(f"[Phase 5: Chaos QA] Playability gate FAILED for {active_ver}! Halting release promotion.")

        # Phase 6: Roadmap Audit & Release Packaging
        audit_res = self.roadmap_engine.audit_active_milestone()
        burndown_pct = audit_res.get("completion_percentage", 0.0)

        if burndown_pct >= 100.0 and webapp_valid and implemented_count > 0:
            logger.info(f"Milestone {active_ver} 100% verified by Chaos QA. Packaging release...")
            self.release_packager.package_release(active_ver)
            next_ms = self.roadmap_engine.evolve_to_next_milestone()
            if next_ms:
                logger.info(f"[✓] Studio Horizon dynamically advanced to {next_ms.version}: '{next_ms.theme}'.")

        ledger = self.codebase_engineer.gateway._load_ledger()
        cum_spend = ledger.get("total_spend_usd", 0.0)
        logger.info(
            f"=== SPRINT CYCLE [{cycle_tag}] COMPLETED: {burndown_pct}% BURNDOWN | "
            f"QA Passed: {webapp_valid} | Cumulative Ledger Spend: ${cum_spend:.4f} ==="
        )
        return {
            "cycle": cycle_tag,
            "milestone": active_ver,
            "webapp_valid": webapp_valid,
            "burndown": audit_res,
            "cumulative_spend_usd": cum_spend
        }


def main():
    parser = argparse.ArgumentParser(description="Aethelgard Autonomous Sprint Runner")
    parser.add_argument("cycles_pos", nargs="?", type=int, default=None, help="Number of sprint cycles")
    parser.add_argument("--cycles", "-c", type=int, default=1, help="Number of sprint cycles")
    args = parser.parse_args()

    num_cycles = args.cycles_pos if args.cycles_pos is not None else args.cycles
    orchestrator = AutonomousProductionOrchestrator(workspace_root=WORKSPACE_ROOT)
    for i in range(1, num_cycles + 1):
        orchestrator.run_cycle(cycle_index=i)


if __name__ == "__main__":
    main()
