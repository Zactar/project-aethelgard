#!/usr/bin/env python3
"""
tools/rfc_pipeline.py
Project Aethelgard: End-to-end RFC Authoring, Review Quorum, and Staging Pipeline
"""

from schemas.studio_contracts import DisciplineType
from services.agent_runtime.src.autonomous_authoring import AutonomousAuthoringAgent
from services.agent_runtime.src.virtual_studio_engine import VirtualStudioEngine
import argparse
import sys
from pathlib import Path

# Anchor workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


def run_pipeline():
    parser = argparse.ArgumentParser(
        description="Aethelgard RFC Review Pipeline")
    parser.add_argument("action", choices=[
                        "review", "simulate", "status"], default="review", nargs="?")
    args = parser.parse_args()

    engine = VirtualStudioEngine(workspace_root=WORKSPACE_ROOT)

    if args.action == "review":
        print("[*] Processing all staged RFCs through High-Friction Review Board...")
        results = engine.process_all_staged_rfcs()
        print(f"\n[✓] Evaluation completed. Processed: {len(results)} RFCs.")

    elif args.action == "simulate":
        print("[*] Simulating authoring and review cycle...")
        author = AutonomousAuthoringAgent(workspace_root=WORKSPACE_ROOT)

        # 1. Author non-compliant RFC
        print("  -> Authoring non-compliant proposal (draw calls > 120)...")
        author.author_rfc(
            discipline=DisciplineType.CLIENT,
            title="Add Volumetric Dynamic Torches",
            summary="Adds 50 point lights with individual shadow maps across the citadel square.",
            target_subsystem="web_client/index.html",
            proposed_changes={
                "light_count": 50,
                "estimated_draw_calls": 240,  # Breaches 120 draw-call cap
                "parent_hierarchy": "ActorTransformGroup"
            }
        )

        # 2. Author compliant RFC
        print("  -> Authoring compliant proposal (optimized instancing)...")
        author.author_rfc(
            discipline=DisciplineType.CLIENT,
            title="Instanced Cobblestone Kerbs",
            summary="Consolidates market curb meshes into a single instanced mesh buffer.",
            target_subsystem="web_client/index.html",
            proposed_changes={
                "estimated_draw_calls": 2,
                "estimated_triangles": 12000,
                "parent_hierarchy": "ActorTransformGroup"
            }
        )

        # 3. Convene review quorum
        print("\n[*] Convening Review Board Quorum...")
        results = engine.process_all_staged_rfcs()
        print("\n--- QUORUM VERDICTS ---")
        for res in results:
            print(
                f"[{res.status}] {res.rfc_id}: Approvals {res.approvals}/{res.total_votes} | Vetoes: {res.vetoes_cast}")
            for d in res.actionable_directives:
                print(f"    - {d}")

    elif args.action == "status":
        staged = list((WORKSPACE_ROOT / "build" /
                      "staging" / "rfcs").glob("*.json"))
        approved = list((WORKSPACE_ROOT / "build" /
                        "rfcs" / "approved").glob("*.json"))
        rejected = list((WORKSPACE_ROOT / "build" /
                        "rfcs" / "rejected").glob("*.json"))

        print("\n[Project Aethelgard RFC Registry Status]")
        print("=" * 60)
        print(f" - Staged for Review: {len(staged)}")
        print(f" - Approved:          {len(approved)}")
        print(f" - Rejected:          {len(rejected)}")
        print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
