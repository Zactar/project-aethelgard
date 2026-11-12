#!/usr/bin/env python3
"""
tools/seed_retrospective_memory.py
Project Aethelgard: Idempotent seeder for Institutional Memory & Post-Mortem Ledger.
"""

from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from schemas.studio_contracts import PostMortemRecord, DisciplineCompetency, DisciplineType
import sys
import json
from pathlib import Path

# Anchor workspace root relative to tools/ directory
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


HISTORICAL_INCIDENTS = [
    {
        "incident_id": "INC-20261012-LVL-01",
        "timestamp": "2026-10-12T14:22:00Z",
        "milestone_tag": "v0.2.0",
        "discipline": "Level",
        "severity": "HIGH",
        "summary": "Procedural spatial generator produced coplanar bounding box overlaps at socket transitions.",
        "root_cause": "Corridor connection sockets and target room floorplates calculated AABB bounds using raw extents without negative inset padding, resulting in coincident collision planes that trapped the player entity at entry thresholds.",
        "symptoms": [
            "Player position locked upon crossing Market Cross Square boundary",
            "Velocity vectors clamped to 0.0 by physics resolver on tick updates"
        ],
        "mitigation_applied": "Subtracted 0.15m clearance inset along connection socket axes and refactored procedural_spatial_generator.py to perform continuous separation vector verification.",
        "prevention_rule": "All procedural AABB collision bounds must incorporate a minimum 0.15m inset offset relative to the visual floorplate and socket perimeter.",
        "affected_files": [
            "services/agent_runtime/src/procedural_spatial_generator.py",
            "schemas/studio_contracts.py"
        ],
        "metadata": {"stuck_coordinates": [12.0, 0.0, -4.5]}
    },
    {
        "incident_id": "INC-20261018-CLI-02",
        "timestamp": "2026-10-18T09:41:15Z",
        "milestone_tag": "v0.3.0",
        "discipline": "Client",
        "severity": "MEDIUM",
        "summary": "NPC dialogue bubbles and floating nameplates drifted into empty space during player camera pitch changes.",
        "root_cause": "HUD billboard sprites were added as direct children of the global Three.js Scene instead of the actor's parent Object3D, and their orientation matrices were computed before the camera projection matrix updated.",
        "symptoms": [
            "NPC text tags detached from character heads and floated at horizon coordinates",
            "Console warnings: MatrixWorld needsUpdate called during active draw pass"
        ],
        "mitigation_applied": "Reparented all UI billboard anchors directly to actor root groups and moved quaternion camera alignment to the post-render update phase in web_client/index.html.",
        "prevention_rule": "Billboards and HUD text anchors must be nested under the actor transform hierarchy and update orientation post-camera-matrix computation in the render loop.",
        "affected_files": [
            "web_client/index.html"
        ],
        "metadata": {"affected_actors": ["hearthmother_elspeth", "garrett_apothecary"]}
    },
    {
        "incident_id": "INC-20261023-GMP-03",
        "timestamp": "2026-10-23T18:15:30Z",
        "milestone_tag": "v0.3.0",
        "discipline": "Gameplay",
        "severity": "HIGH",
        "summary": "Player interaction raycasts were blocked by passive environmental props and stall decor.",
        "root_cause": "The interaction subsystem executed unfiltered Scene.raycast against all meshes, allowing non-interactive collision hulls of decorative barrels and market stalls to consume raycast hits before reaching smart objects.",
        "symptoms": [
            "Unable to interact with The Common Loaf delivery counter",
            "E-key prompt failed to display despite player proximity"
        ],
        "mitigation_applied": "Introduced InteractionLayer bitmasks in studio_contracts.py and updated client raycaster to query only objects flagged with is_interactive=True.",
        "prevention_rule": "Raycasts and proximity queries must mask explicitly to InteractionLayer.INTERACTIVE and reject passive decor or static room boundary collision geometries.",
        "affected_files": [
            "schemas/studio_contracts.py",
            "web_client/index.html",
            "services/agent_runtime/src/server.py"
        ],
        "metadata": {"target_object": "loaf_counter_01"}
    },
    {
        "incident_id": "INC-20261027-SYS-04",
        "timestamp": "2026-10-27T11:05:45Z",
        "milestone_tag": "v0.4.0",
        "discipline": "Systems",
        "severity": "CRITICAL",
        "summary": "Runtime server crash on boot due to circular / uninitialized Enum dependencies in Pydantic models.",
        "root_cause": "A new status enum was declared after the model referencing it in studio_contracts.py, causing a NameError during Python module evaluation before AST compilation could complete.",
        "symptoms": [
            "Server crashed immediately during aethelgard restart",
            "NameError: name 'QuestStatus' is not defined in schemas/studio_contracts.py"
        ],
        "mitigation_applied": "Restructured studio_contracts.py so all Enum definitions strictly precede any Pydantic BaseModel definitions.",
        "prevention_rule": "All Enums and type primitives must be declared strictly at the top of the schema file prior to any Pydantic BaseModel definitions.",
        "affected_files": [
            "schemas/studio_contracts.py"
        ],
        "metadata": {"failed_symbol": "QuestStatus"}
    }
]


def seed():
    print(f"[*] Initializing Retrospective Memory for Project Aethelgard...")
    print(
        f"[*] Target Directory: {WORKSPACE_ROOT / 'build' / 'staging' / 'memory'}")

    memory = StudioRetrospectiveMemory(workspace_root=WORKSPACE_ROOT)

    # Re-seed historical records
    for raw_incident in HISTORICAL_INCIDENTS:
        record = PostMortemRecord(**raw_incident)
        memory.record_incident(record)
        print(
            f"  + Indexed [{record.severity}] {record.incident_id} ({record.discipline})")

    # Display baseline competency status
    competencies = memory.load_competencies()
    print("\n[+] Discipline Competency Baseline Established:")
    for disc, data in competencies.items():
        print(
            f"  - {disc:<12} | Regressions: {data['regressions_caused']} | Clean Streak: {data['clean_streak']}")

    # Perform sample adversarial check
    print("\n[+] Verifying Adversarial Constraint Injection:")
    sample_context = memory.generate_adversarial_context(
        discipline="Level",
        rfc_title="Expand Southern Bastion with Guard Barracks",
        proposed_diff="def generate_socket(): return AABB(bounds=[10, 0, 10])"
    )
    print(sample_context)
    print("\n[✓] Retrospective Memory System Seeded & Operational.")


if __name__ == "__main__":
    seed()
