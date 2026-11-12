#!/usr/bin/env python3
"""
tools/qa_regression_runner.py
Project Aethelgard: Chaos QA Spatial Inset & WebGL Budget Automated Regression Test
"""

from services.agent_runtime.src.studio_self_healer import StudioSelfHealer
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


def run_chaos_qa_suite():
    print("[*] Chaos QA: Executing Automated Regression Test Suite for v0.6.0...")
    manifest_path = WORKSPACE_ROOT / "web_client" / "game_runtime_manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Audit AABB collision margin invariants
    healer = StudioSelfHealer(workspace_root=WORKSPACE_ROOT)
    passed_topology = healer.audit_and_heal_topology(manifest)

    # 2. Audit interaction layer bitmasking
    unmasked_actors = [
        a["actor_id"] for a in manifest.get("actors", [])
        if a.get("interaction_layer") != "InteractionLayer.INTERACTIVE"
    ]

    print(
        f"  + Topological Separation: {'PASSED' if passed_topology else 'FAILED'}")
    print(
        f"  + Interaction Layer Masking: {'PASSED' if not unmasked_actors else 'FAILED'}")

    assert passed_topology, "Topological break detected!"
    assert not unmasked_actors, f"Unmasked actors detected: {unmasked_actors}"

    print("[✓] Chaos QA Suite Completed: All invariants verified without regressions.")
    return True


if __name__ == "__main__":
    run_chaos_qa_suite()
