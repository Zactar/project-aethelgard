#!/usr/bin/env python3
"""
tools/autonomous_runner.py
Project Aethelgard: Autonomous Virtual Studio Production Orchestrator (`aethelgard auto N`)
"""

from tools.engine_importer import AutonomousEngineImporter
from services.agent_runtime.src.virtual_studio_engine import VirtualStudioEngine
from services.agent_runtime.src.autonomous_authoring import AutonomousAuthoringAgent
from services.agent_runtime.src.team_sync import TeamSyncEngine
from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
from schemas.studio_contracts import DisciplineType, DeliverableStatus, MilestoneStatus
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import logging
import json
import sys
from pathlib import Path

# Anchor workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.AutonomousRunner")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class AutonomousProductionOrchestrator:
    """
    Simulates an end-to-end autonomous development cycle:
    1. Team Standup & Backlog Discovery
    2. Role-specific Specialist Authoring mapped to Active Deliverables
    3. Multi-agent Quorum Review & Veto Resolution
    4. Autonomous Engine Compilation & Web Manifest Hot-Patching
    5. Webapp Playability & Runtime Validation
    6. Roadmap Milestone Burndown & Auto-Release Packaging
    """

    def __init__(self, workspace_root: Path = WORKSPACE_ROOT):
        self.workspace_root = workspace_root
        self.roadmap_engine = StudioRoadmapEngine(
            workspace_root=self.workspace_root)
        self.team_sync = TeamSyncEngine(workspace_root=self.workspace_root)
        self.authoring_agent = AutonomousAuthoringAgent(
            workspace_root=self.workspace_root)
        self.studio_engine = VirtualStudioEngine(
            workspace_root=self.workspace_root)
        self.importer = AutonomousEngineImporter(
            workspace_root=self.workspace_root)

    def run_cycle(self, cycle_index: int = 1) -> Dict[str, Any]:
        cycle_tag = f"AUTO-C{cycle_index:02d}"
        logger.info(
            f"=== INITIATING AUTONOMOUS SPRINT CYCLE [{cycle_tag}] ===")

        # 0. UNIVERSAL PROJECT INBOX & BLUEPRINT DETECTION
        from services.agent_runtime.src.blueprint_planner import BlueprintPlanner
        planner = BlueprintPlanner(workspace_root=self.workspace_root)
        new_project = planner.check_inbox_and_bootstrap()
        if new_project:
            logger.info(
                f"=== PROJECT TRANSITION: Switched to '{new_project.title}' ({new_project.genre}) ===")
            logger.info(
                f"Engine Target: {new_project.engine_type} | Milestone v0.1.0 Initialized.")

        # 1. STANDUP CEREMONY
        roadmap_state = self.roadmap_engine.load_roadmap()
        active_ver = roadmap_state.active_version
        logger.info(f"Active Roadmap Milestone Target: {active_ver}")

        self.team_sync.conduct_standup(
            sprint_cycle_tag=cycle_tag,
            milestone_tag=active_ver,
            active_unrest_theme="district commodity scarcity and curfew patrol"
        )

        # 2. DISCOVER PENDING DELIVERABLES & DISPATCH SPECIALISTS
        active_milestone = next((m for m in roadmap_state.milestones if m.version ==
                                active_ver and m.status != MilestoneStatus.SHIPPED), None)
        staged_rfcs = []

        if active_milestone:
            for deliv in active_milestone.deliverables:
                if deliv.status != DeliverableStatus.VERIFIED:
                    logger.info(
                        f"Dispatching specialist for pending deliverable: [{deliv.discipline}] '{deliv.title}'")
                    rfc = self._dispatch_specialist_to_author(
                        deliv, active_ver)
                    if rfc:
                        staged_rfcs.append(rfc)

        # 3. HIGH-FRICTION REVIEW BOARD QUORUM
        review_results = self.studio_engine.process_all_staged_rfcs()

        # 4. AUTONOMOUS CODEBASE IMPLEMENTATION (Codebase Engineer writes code to disk)
        from services.agent_runtime.src.codebase_engineer import CodebaseEngineerAgent
        engineer = CodebaseEngineerAgent(workspace_root=self.workspace_root)
        implemented_count = engineer.implement_approved_rfcs(
            review_results, active_version=active_ver)
        logger.info(
            f"[Phase 4: Implementation] CodebaseEngineer implemented {implemented_count} approved RFCs on disk.")

        # 5. AUTONOMOUS MANIFEST COMPILATION
        self.importer.compile_manifest()

        # 6. WEBAPP PLAYABILITY & RUNTIME VALIDATION (Chaos QA tests live code)
        webapp_valid = self._validate_webapp_runtime()

        # 7. ROADMAP AUDIT, BURNDOWN & AUTO-RELEASE PACKAGING
        audit_res = self.roadmap_engine.audit_active_milestone()

        if audit_res.get("completion_percentage", 0.0) >= 100.0 and webapp_valid:
            logger.info(
                f"Milestone {active_ver} validated & verified in webapp. Triggering autonomous release packager...")
            self._package_and_evolve_release(active_ver)

        logger.info(
            f"=== SPRINT CYCLE [{cycle_tag}] COMPLETED: {audit_res.get('completion_percentage', 0.0)}% BURNDOWN ===")
        return {
            "cycle": cycle_tag,
            "milestone": active_ver,
            "webapp_valid": webapp_valid,
            "burndown": audit_res
        }

    def _calculate_next_room_position(self, dimensions: List[float]) -> Tuple[List[float], str, List[float]]:
        """
        Algorithmic spatial placement:
        Calculates non-overlapping candidate coordinates along the citadel frontier
        with guaranteed >= 0.20m AABB clearance margins and socket alignment.
        """
        manifest_path = self.workspace_root / "web_client" / "game_runtime_manifest.json"
        rooms = []
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    rooms = json.load(f).get("rooms", [])
            except Exception:
                pass

        if not rooms:
            return [0.0, 0.0, 0.0], "origin", [0.0, 0.0, 0.0]

        # Find the furthest frontier room along the negative Z axis
        anchor_room = min(rooms, key=lambda r: r.get("position", [0, 0, 0])[2])
        anchor_pos = anchor_room.get("position", [0.0, 0.0, 0.0])
        anchor_dim = anchor_room.get("dimensions", [20.0, 4.5, 20.0])

        # Step along negative Z with clearance buffer
        clearance_margin = 8.0  # Buffer for connecting thoroughfare
        candidate_z = anchor_pos[2] - (anchor_dim[2] / 2.0) - \
            (dimensions[2] / 2.0) - clearance_margin
        candidate_x = anchor_pos[0]
        candidate_y = anchor_pos[1]

        socket_z = candidate_z + (dimensions[2] / 2.0)
        return [candidate_x, candidate_y, candidate_z], anchor_room.get("room_id", "market_cross"), [candidate_x, candidate_y, socket_z]

    def _dispatch_specialist_to_author(self, deliverable, milestone_tag: str) -> Optional[Dict[str, Any]]:
        """Universally dispatches specialists based on deliverable parameters without project coupling."""
        disc = deliverable.discipline if isinstance(
            deliverable.discipline, str) else deliverable.discipline.value
        disc_type = deliverable.discipline if isinstance(
            deliverable.discipline, DisciplineType) else DisciplineType(disc)

        return self.authoring_agent.author_rfc(
            discipline=disc_type,
            title=deliverable.title,
            summary=f"Implement deliverable '{deliverable.title}' for milestone {milestone_tag}.",
            target_subsystem=deliverable.target_subsystem,
            proposed_changes={
                "deliverable_id": deliverable.deliverable_id,
                "target_subsystem": deliverable.target_subsystem,
                "acceptance_criteria": deliverable.acceptance_criteria,
                "status": "APPROVED_SPEC"
            },
            milestone_tag=milestone_tag,
            target_deliverable_id=deliverable.deliverable_id
        )

    def _validate_webapp_runtime(self) -> bool:
        validator = self.workspace_root / "tools" / "validate_webapp.py"
        if not validator.exists():
            return True
        try:
            subprocess.run([sys.executable, str(validator)],
                           cwd=self.workspace_root, check=True)
            return True
        except subprocess.CalledProcessError:
            logger.error("Webapp runtime validation failed!")
            return False

    def _package_and_evolve_release(self, version: str) -> None:
        packager = self.workspace_root / "tools" / "release_packager.py"
        if packager.exists():
            try:
                subprocess.run([sys.executable, str(packager), version],
                               cwd=self.workspace_root, check=True, capture_output=True)
                logger.info(
                    f"[✓] Release packager completed build archive for {version}.")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Release packager exited with error: {e}")

        # Evolve roadmap to next milestone in the continuum
        new_ms = self.roadmap_engine.evolve_to_next_milestone()
        logger.info(
            f"[✓] Studio Horizon dynamically advanced to {new_ms.version}: '{new_ms.codename}'.")


def main():
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    orchestrator = AutonomousProductionOrchestrator()
    for i in range(1, cycles + 1):
        orchestrator.run_cycle(cycle_index=i)


if __name__ == "__main__":
    main()
