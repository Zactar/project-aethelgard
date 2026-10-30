#!/usr/bin/env python3
"""
PROJECT AETHELGARD: ENGINE-AGNOSTIC ASSET INGESTER
Directs staged artifacts into the Three.js web client and Godot 4 scene representations.
"""

from tools.godot_exporter import export_manifest_to_godot
from schemas.studio_contracts import GameRuntimeManifest
from pathlib import Path
import json
import shutil
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


STAGING_DIR = ROOT_DIR / "build" / "staging"
WEB_DIR = ROOT_DIR / "web_client"


class EngineAssetIngester:
    def __init__(self):
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        WEB_DIR.mkdir(parents=True, exist_ok=True)

    def run_once(self) -> int:
        staged_files = list(STAGING_DIR.glob("*.json"))
        processed_count = 0

        for f in staged_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                payload = data.get("raw_payload", {})
                runtime_manifest = payload.get("game_runtime_manifest")

                if runtime_manifest:
                    # 1. Update web client target
                    target_file = WEB_DIR / "game_runtime_manifest.json"
                    target_file.write_text(json.dumps(
                        runtime_manifest, indent=2), encoding="utf-8")

                    # 2. Export Godot 4 compatibility scene
                    manifest_obj = GameRuntimeManifest.model_validate(
                        runtime_manifest)
                    export_manifest_to_godot(manifest_obj)

                    processed_count += 1
                f.unlink()
            except Exception as e:
                print(f"  [INGESTER WARNING] Error processing {f.name}: {e}")

        return processed_count


if __name__ == "__main__":
    ingester = EngineAssetIngester()
    count = ingester.run_once()
    print(f"[INGESTER]: Processed {count} staged studio artifact(s).")
