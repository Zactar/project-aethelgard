import json
from pathlib import Path

STAGING_DIR = Path("build/staging")
UE5_CONTENT_DIR = Path("unreal/ProjectAethelgard/Content")
UE5_SOURCE_DIR = Path("unreal/ProjectAethelgard/Source/ProjectAethelgard")
WEB_CLIENT_DIR = Path("web_client")

class EngineAssetIngester:
    def __init__(self):
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        (UE5_CONTENT_DIR / "Balance/Hotfixes").mkdir(parents=True, exist_ok=True)
        (UE5_CONTENT_DIR / "Levels/PCG_Layouts").mkdir(parents=True, exist_ok=True)
        (UE5_CONTENT_DIR / "Dialogue").mkdir(parents=True, exist_ok=True)
        (UE5_SOURCE_DIR / "Private").mkdir(parents=True, exist_ok=True)
        WEB_CLIENT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[ENGINE INGESTER]: Listening on {STAGING_DIR.resolve()}...")

    def stage_artifact(self, artifact_path: Path):
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("auditor_approved", False):
            print(f"[INGESTER REJECTED]: Artifact {artifact_path.name} failed auditor approval.")
            return

        payload = data.get("raw_payload", {})

        if payload.get("client_manifest"):
            target_manifest = WEB_CLIENT_DIR / "district_manifest.json"
            with open(target_manifest, "w", encoding="utf-8") as f:
                json.dump(payload["client_manifest"], f, indent=2)
            print(f"[INGESTER -> WEB CLIENT]: Deployed dynamic prop manifest to {target_manifest}")

        if payload.get("hotfix_csv"):
            target_csv = UE5_CONTENT_DIR / "Balance/Hotfixes/DT_CombatScalars_Hotfixed.csv"
            with open(target_csv, "w", encoding="utf-8") as f:
                f.write(payload["hotfix_csv"])
            print(f"[INGESTER -> UE5 BALANCE]: Deployed hotfix CSV to {target_csv}")

        if payload.get("spatial_layout"):
            target_layout = UE5_CONTENT_DIR / f"Levels/PCG_Layouts/{artifact_path.stem}_Layout.json"
            with open(target_layout, "w", encoding="utf-8") as f:
                json.dump(payload["spatial_layout"], f, indent=2)
            print(f"[INGESTER -> UE5 PCG]: Deployed spatial layout to {target_layout}")

        if payload.get("dialogue"):
            target_dlg = UE5_CONTENT_DIR / f"Dialogue/{artifact_path.stem}_Dialogue.json"
            with open(target_dlg, "w", encoding="utf-8") as f:
                json.dump(payload["dialogue"], f, indent=2)
            print(f"[INGESTER -> UE5 DIALOGUE]: Deployed dialogue asset to {target_dlg}")

        if payload.get("cpp_scaffold"):
            target_cpp = UE5_SOURCE_DIR / f"Private/{artifact_path.stem}_Task.h"
            with open(target_cpp, "w", encoding="utf-8") as f:
                f.write(payload["cpp_scaffold"])
            print(f"[INGESTER -> UE5 C++]: Deployed C++ StateTree task scaffold to {target_cpp}")

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
