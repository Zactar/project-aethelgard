"""
tools/release_packager.py
Project Aethelgard: Autonomous SemVer Release Packager
Snapshots web_client/, roadmap state, and approved RFCs into build/releases/<version>/.
"""

import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("Aethelgard.ReleasePackager")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ReleasePackager:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else WORKSPACE_ROOT
        self.releases_dir = self.workspace_root / "build" / "releases"
        self.releases_dir.mkdir(parents=True, exist_ok=True)

    def package_release(self, version: str) -> Dict[str, Any]:
        target_dir = self.releases_dir / version
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy web_client snapshot
        web_src = self.workspace_root / "web_client"
        if web_src.exists():
            shutil.copytree(web_src, target_dir / "web_client")

        # Copy roadmap snapshot
        roadmap_src = self.workspace_root / "build" / "roadmap" / "studio_roadmap.json"
        if roadmap_src.exists():
            shutil.copy2(roadmap_src, target_dir / "studio_roadmap.json")

        manifest = {
            "version": version,
            "packaged_at": datetime.utcnow().isoformat(),
            "artifacts": [str(p.relative_to(target_dir)) for p in target_dir.rglob("*") if p.is_file()]
        }
        (target_dir / "release_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info(f"[✓] Packaged release {version} to {target_dir} ({len(manifest['artifacts'])} files).")
        return manifest

    def package_milestone(self, version: str) -> Dict[str, Any]:
        return self.package_release(version)
