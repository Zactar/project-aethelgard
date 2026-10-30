import json
from pathlib import Path

STAGING_DIR = Path("build/staging")
WEB_CLIENT_DIR = Path("web_client")

class EngineAssetIngester:
    def __init__(self):
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        WEB_CLIENT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[ENGINE INGESTER]: Listening on {STAGING_DIR.resolve()}...")

    def stage_artifact(self, artifact_path: Path):
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("auditor_approved", False):
            print(f"[INGESTER REJECTED]: Artifact {artifact_path.name} failed auditor approval.")
            return

        payload = data.get("raw_payload", {})

        # Deploy Unified Runtime Manifest directly to Web Client
        if payload.get("game_runtime_manifest"):
            target_manifest = WEB_CLIENT_DIR / "game_runtime_manifest.json"
            with open(target_manifest, "w", encoding="utf-8") as f:
                json.dump(payload["game_runtime_manifest"], f, indent=2)
            print(f"[INGESTER -> WEB CLIENT]: Deployed live game runtime manifest to {target_manifest}")

    def run_once(self):
        staged_files = list(STAGING_DIR.glob("*.json"))
        for artifact_file in staged_files:
            try:
                self.stage_artifact(artifact_file)
                artifact_file.unlink()
            except Exception as e:
                print(f"[INGESTER ERROR]: Failed staging {artifact_file.name}: {e}")

if __name__ == "__main__":
    ingester = EngineAssetIngester()
    ingester.run_once()
