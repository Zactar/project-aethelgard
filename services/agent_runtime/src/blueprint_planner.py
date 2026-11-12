"""
services/agent_runtime/src/blueprint_planner.py
Project Aethelgard: 100% Game-Agnostic GDD Parser, Project Archiver & Roadmap Bootstrapper.
Zero hardcoded game titles or deliverables.
"""

import re
import sys
import json
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

from schemas.studio_contracts import (
    StudioRoadmapState,
    StudioMilestone,
    DeliverableItem,
    DisciplineType,
    MilestoneStatus,
    DeliverableStatus
)

logger = logging.getLogger("Studio.BlueprintPlanner")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class BlueprintPlanner:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.projects_dir = self.workspace_root / "projects"
        self.inbox_gdd = self.projects_dir / "inbox" / "GDD.md"
        self.active_project_file = self.projects_dir / "active_project.json"
        self.archive_dir = self.projects_dir / "archive"
        self.web_client_dir = self.workspace_root / "web_client"
        self.roadmap_file = self.workspace_root / "build" / "roadmap" / "studio_roadmap.json"

        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.roadmap_file.parent.mkdir(parents=True, exist_ok=True)

    def compute_gdd_hash(self, content: str) -> str:
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:12]

    def extract_metadata(self, content: str) -> Dict[str, str]:
        title = "Untitled Studio Project"
        # Match first H1 heading (# Title)
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            raw_title = h1_match.group(1).strip()
            raw_title = re.sub(r"^(?:Game Design Document\s*(?:\(GDD\))?\s*:|GDD\s*:?)\s*", "", raw_title, flags=re.IGNORECASE)
            title = raw_title.strip(" *\"#")

        genre = "2D Arcade Action"
        g_match = re.search(r"\*\*Genre:?\*\*:?\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if g_match:
            genre = g_match.group(1).strip()

        engine_type = "CANVAS_2D"
        e_match = re.search(r"\*\*Engine(?:\s+Type)?:?\*\*:?\s*([A-Z0-9_]+)", content, re.MULTILINE | re.IGNORECASE)
        if e_match:
            engine_type = e_match.group(1).strip().upper()

        project_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return {
            "title": title,
            "genre": genre,
            "engine_type": engine_type,
            "project_id": project_id,
            "gdd_hash": self.compute_gdd_hash(content), "hash": self.compute_gdd_hash(content)
        }

    def _resolve_discipline(self, raw_disc: str) -> DisciplineType:
        s = raw_disc.strip().lower()
        if any(k in s for k in ("aesthetic", "graphic", "animat", "art", "shader", "vfx")):
            return DisciplineType.AESTHETICS
        if any(k in s for k in ("ui", "ux", "hud", "ergonom", "interface", "menu")):
            return DisciplineType.UI_UX
        for member in DisciplineType:
            if member.value.lower() in s or member.name.lower() in s:
                return member
        return DisciplineType.SYSTEMS

    def parse_milestones_from_gdd(self, content: str) -> List[StudioMilestone]:
        """
        Parses all `### Milestone vX.Y.Z: Theme` sections and bulleted deliverables
        from GDD.md regardless of colon/bracket punctuation style.
        """
        milestones: List[StudioMilestone] = []
        pattern = re.compile(
            r"^#{2,4}\s*Milestone\s+(v?\d+\.\d+\.\d+)\s*[:\-–]?\s*(.*)$",
            re.MULTILINE | re.IGNORECASE
        )
        matches = list(pattern.finditer(content))

        for idx, m in enumerate(matches):
            ver = m.group(1).strip()
            if not ver.startswith("v"):
                ver = "v" + ver
            theme = m.group(2).strip() or f"Milestone {ver}"
            start_pos = m.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            section_body = content[start_pos:end_pos]

            deliverables: List[DeliverableItem] = []
            # Match bullets like: - **[Client]** Description OR - [Systems]: Description
            bullet_re = re.compile(
                r"^\s*[\-\*]\s*(?:\*\*)?\[([A-Za-z_\s]+)\](?:\*\*)?\s*:?(?:\*\*)?\s*(.+)$",
                re.MULTILINE
            )
            for b_idx, bm in enumerate(bullet_re.finditer(section_body), start=1):
                disc = self._resolve_discipline(bm.group(1))
                deliv_title = bm.group(2).strip()
                deliverables.append(
                    DeliverableItem(
                        deliverable_id=f"DELIV-{ver.upper().replace('.', '_')}-{b_idx:02d}",
                        discipline=disc,
                        title=deliv_title,
                        target_subsystem="web_client/index.html",
                        status=DeliverableStatus.PENDING
                    )
                )

            if deliverables:
                milestones.append(
                    StudioMilestone(
                        version=ver,
                        codename=f"Codename-{ver}",
                        theme=theme,
                        status=MilestoneStatus.IN_PROGRESS if len(milestones) == 0 else MilestoneStatus.PLANNED,
                        completion_percentage=0.0,
                        deliverables=deliverables
                    )
                )

        if not milestones:
            # Universal fallback if GDD has no Milestone headings
            milestones.append(
                StudioMilestone(
                    version="v0.1.0",
                    codename="Codename-v0.1.0",
                    theme="Core Engine Loop, Player Controls & Primary Mechanics",
                    status=MilestoneStatus.IN_PROGRESS,
                    completion_percentage=0.0,
                    deliverables=[
                        DeliverableItem(deliverable_id="DELIV-V0_1_0-01", discipline=DisciplineType.CLIENT, title="Core 800x600 Canvas Renderer, Background & Top Status Ribbon"),
                        DeliverableItem(deliverable_id="DELIV-V0_1_0-02", discipline=DisciplineType.GAMEPLAY, title="Primary Player Controller, Movement Physics & Action Mechanics"),
                        DeliverableItem(deliverable_id="DELIV-V0_1_0-03", discipline=DisciplineType.SYSTEMS, title="Core World Entity Spawner, Collision Detection & Scoring Loop")
                    ]
                )
            )
        return milestones

    def archive_previous_project(self, prev_meta: Dict[str, Any]) -> Optional[Path]:
        prev_id = prev_meta.get("project_id", "previous_project")
        try:
            from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
            StudioRetrospectiveMemory(workspace_root=self.workspace_root).conduct_project_retrospective(use_llm=True)
        except Exception as e:
            logger.warning(f"[BlueprintPlanner] Pre-archive retrospective skipped: {e}")

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest = self.archive_dir / f"{prev_id}_{ts}"
        dest.mkdir(parents=True, exist_ok=True)

        if self.web_client_dir.exists():
            shutil.copytree(self.web_client_dir, dest / "web_client", dirs_exist_ok=True)
        if self.roadmap_file.exists():
            shutil.copy2(self.roadmap_file, dest / "studio_roadmap.json")
        releases_dir = self.workspace_root / "build" / "releases"
        if releases_dir.exists():
            shutil.copytree(releases_dir, dest / "releases", dirs_exist_ok=True)
            shutil.rmtree(releases_dir)
            releases_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[BlueprintPlanner] Archived outgoing project '{prev_meta.get('title')}' to {dest}")
        return dest

    def scaffold_clean_client(self, title: str, engine_type: str) -> None:
        """Resets web_client/ from index_template.html and purges prior project RFCs & JS plugins."""
        self.web_client_dir.mkdir(parents=True, exist_ok=True)
        js_dir = self.web_client_dir / "js"
        if js_dir.exists():
            shutil.rmtree(js_dir)
        js_dir.mkdir(parents=True, exist_ok=True)

        for stale_dir in [
            self.workspace_root / "build" / "staging" / "rfcs",
            self.workspace_root / "build" / "rfcs" / "approved",
            self.workspace_root / "build" / "staging" / "meetings"
        ]:
            if stale_dir.exists():
                for f in stale_dir.glob("*.json"):
                    f.unlink()

        applied_file = self.workspace_root / "build" / "staging" / "applied_rfcs.json"
        if applied_file.exists():
            applied_file.unlink()

        template_file = self.web_client_dir / "index_template.html"
        index_file = self.web_client_dir / "index.html"
        if template_file.exists():
            html = template_file.read_text(encoding="utf-8")
            html = html.replace("<title>Aethelgard Universal Game Runtime</title>", f"<title>{title}</title>")
            index_file.write_text(html, encoding="utf-8")
            logger.info(f"[BlueprintPlanner] Cloned clean microkernel template for '{title}'.")

    def check_inbox_and_bootstrap(self, force: bool = False) -> Dict[str, Any]:
        if not self.inbox_gdd.exists():
            return {"bootstrapped": False, "reason": "No GDD.md in projects/inbox/"}

        content = self.inbox_gdd.read_text(encoding="utf-8")
        new_meta = self.extract_metadata(content)

        if self.active_project_file.exists() and not force:
            try:
                cur_meta = json.loads(self.active_project_file.read_text(encoding="utf-8"))
                if cur_meta.get("gdd_hash") == new_meta["gdd_hash"] and cur_meta.get("project_id") == new_meta["project_id"]:
                    logger.info(f"Project '{new_meta['title']}' is up to date (hash: {new_meta['gdd_hash']}).")
                    return {"bootstrapped": False, "meta": cur_meta}
                else:
                    self.archive_previous_project(cur_meta)
            except Exception:
                pass

        logger.info(f"[BlueprintPlanner] Bootstrapping NEW project space for: '{new_meta['title']}'...")
        self.scaffold_clean_client(new_meta["title"], new_meta["engine_type"])

        milestones = self.parse_milestones_from_gdd(content)
        roadmap_state = StudioRoadmapState(
            active_version=milestones[0].version,
            milestones=milestones
        )
        self.roadmap_file.write_text(
            json.dumps(roadmap_state.model_dump(mode="json"), indent=2),
            encoding="utf-8"
        )

        new_meta["bootstrapped_at"] = datetime.utcnow().isoformat()
        self.active_project_file.write_text(json.dumps(new_meta, indent=2), encoding="utf-8")
        return {"bootstrapped": True, "meta": new_meta, "milestones_count": len(milestones)}

    def get_active_project(self) -> Dict[str, Any]:
        if self.active_project_file.exists():
            try:
                return json.loads(self.active_project_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        if self.inbox_gdd.exists():
            return self.extract_metadata(self.inbox_gdd.read_text(encoding="utf-8"))
        return {"title": "None", "genre": "None", "engine_type": "CANVAS_2D", "project_id": "none", "gdd_hash": "none"}
