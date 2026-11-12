#!/usr/bin/env python3
"""
tools/evolve_milestone.py
Project Aethelgard: Autonomous Milestone Evolution Utility
"""

from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine, VersionBumpType
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


def main():
    engine = StudioRoadmapEngine(workspace_root=WORKSPACE_ROOT)

    # Evolve to next SemVer milestone autonomously
    next_ms = engine.evolve_to_next_milestone(bump_type=VersionBumpType.MINOR)
    print(f"\n[✓] Autonomous Roadmap Evolution Complete:")
    print(f"    Version:  {next_ms.version}")
    print(f"    Codename: {next_ms.codename}")
    print(f"    Theme:    {next_ms.theme}")

    audit = engine.audit_active_milestone()
    print(f"\n[+] Active Milestone Backlog:")
    print(
        f"    Burndown: {audit['completion_percentage']}% ({audit['verified_deliverables']})")
    for d in audit['deliverables']:
        status_sym = "[✓]" if d['status'] == "VERIFIED" else "[ ]"
        print(f"    {status_sym} [{d['discipline']:<10}] {d['title']}")


if __name__ == "__main__":
    main()
