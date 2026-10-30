#!/usr/bin/env python3
"""
PROJECT AETHELGARD: AUTOMATED RELEASE PACKAGER & CHANGELOG GENERATOR
Archives shippable manifest releases, verifies playtest baselines, and compiles release notes.
"""

from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
from services.agent_runtime.src.optimization_engine import StudioOptimizationProfiler
from schemas.studio_contracts import GameRuntimeManifest
import json
from pathlib import Path
import sys
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


RELEASES_DIR = ROOT_DIR / "build" / "releases"
CHANGELOG_PATH = ROOT_DIR / "CHANGELOG.md"
MANIFEST_PATH = ROOT_DIR / "web_client" / "game_runtime_manifest.json"


def package_release(version_tag: str, release_title: str) -> Path:
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = RELEASES_DIR / version_tag
    target_dir.mkdir(parents=True, exist_ok=True)

    if not MANIFEST_PATH.exists():
        print(f"[ERROR]: {MANIFEST_PATH} not found.")
        return target_dir

    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest = GameRuntimeManifest.model_validate(manifest_data)

    profiler = StudioOptimizationProfiler()
    report = profiler.audit_runtime_manifest(manifest)

    # 1. Snapshot manifest
    snapshot_file = target_dir / "game_runtime_manifest.json"
    snapshot_file.write_text(json.dumps(
        manifest_data, indent=2), encoding="utf-8")

    # 2. Compile release notes
    items_list = ", ".join(
        [item.display_name for item in manifest.items.values()]) if manifest.items else "None"
    quests_list = ", ".join(
        [q.title for q in manifest.active_quests]) if manifest.active_quests else "None"
    npcs_list = ", ".join(
        [npc.name for npc in manifest.npcs.values()]) if manifest.npcs else "None"
    date_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

    release_md = f"""# Project Aethelgard - Release {version_tag}
**Title:** {release_title}
**Date:** {date_str}
**Simulation Phase:** `{manifest.simulation_phase}` | **District Unrest:** `{manifest.district_unrest:.2f}`

## Technical Performance Profile
- **Spatial Zones:** {report.total_nodes}
- **Procedural Props:** {report.total_props}
- **Estimated WebGL Draw Calls:** {report.estimated_draw_calls}
- **Runtime Manifest Size:** {report.payload_size_kb} KB
- **Profiler Verdict:** {report.triage_notes}

## Shippable Features & World Assets
- **Items Catalog:** {items_list}
- **Active Quests:** {quests_list}
- **NPC Roster:** {npcs_list}

---
*Packaged autonomously by Project Aethelgard Studio Production Loop.*
"""
    (target_dir / "RELEASE_NOTES.md").write_text(release_md, encoding="utf-8")

    # 3. Prepend to CHANGELOG.md cleanly
    existing_changelog = CHANGELOG_PATH.read_text(
        encoding="utf-8") if CHANGELOG_PATH.exists() else ""
    separator = chr(10) * 2
    CHANGELOG_PATH.write_text(
        f"{release_md}{separator}{existing_changelog}", encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"  [RELEASE PACKAGED]: {version_tag} - '{release_title}'")
    print(f"  Archive Location  : {target_dir}")
    print(f"  Changelog Updated : {CHANGELOG_PATH}")
    print("=" * 70 + "\n")
    return target_dir


if __name__ == "__main__":
    roadmap_engine = StudioRoadmapEngine()
    active = roadmap_engine.get_active_milestone()
    package_release(active.version_tag, active.theme)
