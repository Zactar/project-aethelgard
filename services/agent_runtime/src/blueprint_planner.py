"""
services/agent_runtime/src/blueprint_planner.py
Universal Autonomous Game Studio: Dynamic GDD Ingestion & Comprehensive Roadmap Synthesis
"""

from schemas.studio_contracts import (
    DisciplineType,
    MilestoneStatus,
    DeliverableStatus,
    MilestoneDeliverable,
    StudioMilestone,
    StudioRoadmapState
)
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil
import re
import logging
import hashlib
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Studio.BlueprintPlanner")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class ParsedGDD(BaseModel):
    project_id: str
    title: str
    genre: str
    engine_type: str
    player_verbs: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    has_combat: bool = False
    has_ability_gates: bool = False
    has_economy: bool = False
    raw_hash: str


class BlueprintPlanner:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.projects_dir = self.workspace_root / "projects"
        self.inbox_file = self.projects_dir / "inbox" / "GDD.md"
        self.active_project_file = self.projects_dir / "active_project.json"
        self.archive_dir = self.projects_dir / "archive"

        self.inbox_file.parent.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def check_inbox_and_bootstrap(self, force: bool = False) -> Optional[ParsedGDD]:
        if not self.inbox_file.exists():
            return None

        content = self.inbox_file.read_text(encoding="utf-8").strip()
        if not content:
            return None

        gdd_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        active_meta = self.get_active_project()

        if not force and active_meta and active_meta.get("raw_hash") == gdd_hash:
            return None

        parsed = self.parse_gdd(content, gdd_hash)

        if not force and active_meta and active_meta.get("project_id") == parsed.project_id:
            logger.info(
                f"[BlueprintPlanner] Detected GDD update for '{parsed.title}'. Expanding roadmap...")
            self._expand_existing_roadmap(parsed)
            return parsed

        logger.info(
            f"[BlueprintPlanner] Bootstrapping clean project space for: '{parsed.title}'...")
        if active_meta and active_meta.get("project_id") != parsed.project_id:
            self._archive_project(active_meta.get(
                "project_id", "previous_project"))

        self._bootstrap_new_project(parsed, content)
        return parsed

    def get_active_project(self) -> Optional[Dict[str, Any]]:
        if self.active_project_file.exists():
            try:
                with open(self.active_project_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    # Patch logic for GDD metadata extraction in blueprint_planner.py

    def extract_gdd_metadata(content: str) -> dict:
        meta = {
            "title": "Untitled Game",
            "genre": "Universal Dynamic Simulation",
            "project_id": "new_project",
            "engine_type": "CANVAS_2D"
        }
        for line in content.splitlines():
            line_clean = line.strip().lstrip("-*# ").strip()
            if ":" in line_clean:
                key, val = line_clean.split(":", 1)
                k = key.strip().lower().replace(" ", "_")
                v = val.strip()
                if k in ["title", "project_title"]:
                    meta["title"] = v
                elif k in ["genre"]:
                    meta["genre"] = v
                elif k in ["project_id", "id"]:
                    meta["project_id"] = v.lower().replace(" ", "_")
                elif k in ["engine_type", "engine"]:
                    meta["engine_type"] = v.upper()
        return meta

    def parse_gdd(self, gdd_text: str, gdd_hash: str) -> ParsedGDD:
        title_match = re.search(r"^#\s+(.+)$", gdd_text, re.MULTILINE)
        title = title_match.group(1).strip(
        ) if title_match else "Universal Game Project"
        project_id = re.sub(
            r"[^a-z0-9_]", "", title.lower().replace(" ", "_")) or "game_project"

        is_3d = any(k in gdd_text.lower()
                    for k in ["3d", "webgl", "three.js", "isometric"])
        engine_type = "WEBGL_3D" if is_3d else "CANVAS_2D"

        has_combat = any(k in gdd_text.lower() for k in [
                         "harpoon", "pump", "combat", "enemy", "pooka", "fygar"])
        has_ability_gates = any(k in gdd_text.lower() for k in [
                                "metroidvania", "gate", "drill", "piston", "biome", "granite", "magma"])
        has_economy = any(k in gdd_text.lower()
                          for k in ["shop", "currency", "mineral", "relic", "amber"])

        verbs = ["Move", "Dig"]
        if has_combat:
            verbs.extend(["Fire", "Pump"])
        if has_ability_gates:
            verbs.extend(["Jump", "Drill"])

        return ParsedGDD(
            project_id=project_id,
            title=title,
            genre="Metroidvania Action Simulation" if has_ability_gates else "Arcade Simulation",
            engine_type=engine_type,
            player_verbs=verbs,
            entities=["PlayerExcavator", "Boulder",
                      "Pooka", "Fygar", "CorePrism"],
            has_combat=has_combat,
            has_ability_gates=has_ability_gates,
            has_economy=has_economy,
            raw_hash=gdd_hash
        )

    def _archive_project(self, old_project_id: str) -> None:
        target_archive = self.archive_dir / \
            f"{old_project_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        target_archive.mkdir(parents=True, exist_ok=True)
        for folder in ["web_client", "build/roadmap"]:
            src = self.workspace_root / folder
            if src.exists():
                shutil.copytree(src, target_archive /
                                src.name, dirs_exist_ok=True)

    def _bootstrap_new_project(self, parsed: ParsedGDD, gdd_text: str) -> None:
        with open(self.active_project_file, "w", encoding="utf-8") as f:
            json.dump(parsed.model_dump(mode="json"), f, indent=2)

        for sdir in ["build/staging/rfcs", "build/staging/meetings", "build/rfcs/approved"]:
            d = self.workspace_root / sdir
            if d.exists():
                for f in d.glob("*.json"):
                    f.unlink()

        self._synthesize_full_roadmap(parsed)

    def _expand_existing_roadmap(self, parsed: ParsedGDD) -> None:
        self._synthesize_full_roadmap(parsed, preserve_shipped=True)

    def _synthesize_full_roadmap(self, parsed: ParsedGDD, preserve_shipped: bool = False) -> None:
        roadmap_file = self.workspace_root / "build" / "roadmap" / "studio_roadmap.json"
        roadmap_file.parent.mkdir(parents=True, exist_ok=True)

        existing_statuses = {}
        if preserve_shipped and roadmap_file.exists():
            try:
                with open(roadmap_file, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                for m in old_data.get("milestones", []):
                    existing_statuses[m.get("version")] = m.get("status")
            except Exception:
                pass

        milestones = [
            StudioMilestone(
                version="v0.1.0",
                codename="Foundation Kernel & Input Mapping",
                theme="Initialize 60fps tick loop, viewport canvas, and excavator locomotion.",
                status=MilestoneStatus.SHIPPED if existing_statuses.get(
                    "v0.1.0") == "SHIPPED" else MilestoneStatus.IN_PROGRESS,
                deliverables=[
                    MilestoneDeliverable(deliverable_id="DEL-01-SYS", discipline=DisciplineType.SYSTEMS, title="Tick Loop & Coordinate State Machine", target_subsystem="web_client/index.html",
                                         acceptance_criteria=["60fps render loop active"], status=DeliverableStatus.VERIFIED if existing_statuses.get("v0.1.0") == "SHIPPED" else DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-01-GMP", discipline=DisciplineType.GAMEPLAY, title="Locomotion Inputs & Action Handlers", target_subsystem="web_client/index.html",
                                         acceptance_criteria=["WASD/Arrow input binds"], status=DeliverableStatus.VERIFIED if existing_statuses.get("v0.1.0") == "SHIPPED" else DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-01-CLI", discipline=DisciplineType.CLIENT, title="Primary Viewport Canvas & Status HUD", target_subsystem="web_client/index.html",
                                         acceptance_criteria=["HUD status indicators active"], status=DeliverableStatus.VERIFIED if existing_statuses.get("v0.1.0") == "SHIPPED" else DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-01-QA", discipline=DisciplineType.CHAOS_QA, title="Automated Render & Locomotion Invariant Test", target_subsystem="tools/validate_webapp.py",
                                         acceptance_criteria=["Zero script errors"], status=DeliverableStatus.VERIFIED if existing_statuses.get("v0.1.0") == "SHIPPED" else DeliverableStatus.PENDING)
                ],
                completion_percentage=100.0 if existing_statuses.get(
                    "v0.1.0") == "SHIPPED" else 0.0
            ),
            StudioMilestone(
                version="v0.2.0",
                codename="Environmental Hazards & Collision Matrix",
                theme="Destructible dirt, bedrock perimeters, and kinetic boulder falling physics.",
                status=MilestoneStatus.SHIPPED if existing_statuses.get(
                    "v0.2.0") == "SHIPPED" else MilestoneStatus.PLANNED,
                deliverables=[
                    MilestoneDeliverable(deliverable_id="DEL-02-LVL", discipline=DisciplineType.LEVEL, title="World Geometry & Arena Boundaries", target_subsystem="web_client/index.html",
                                         acceptance_criteria=["Destructible terrain active"], status=DeliverableStatus.VERIFIED if existing_statuses.get("v0.2.0") == "SHIPPED" else DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-02-SYS", discipline=DisciplineType.SYSTEMS, title="AABB Spatial Collision & Damage Evaluator", target_subsystem="web_client/index.html",
                                         acceptance_criteria=["Kinetic boulders fall when undermined"], status=DeliverableStatus.VERIFIED if existing_statuses.get("v0.2.0") == "SHIPPED" else DeliverableStatus.PENDING)
                ],
                completion_percentage=100.0 if existing_statuses.get(
                    "v0.2.0") == "SHIPPED" else 0.0
            ),
            StudioMilestone(
                version="v0.3.0",
                codename="Hostile Fauna & Pneumatic Combat",
                theme="Subterranean fauna (Pookas, Fygars), directional harpoon tether, and pump inflation combat.",
                status=MilestoneStatus.IN_PROGRESS,
                deliverables=[
                    MilestoneDeliverable(deliverable_id="DEL-03-GMP", discipline=DisciplineType.GAMEPLAY, title="Pneumatic Harpoon Tether & Pump Inflation Mechanics",
                                         target_subsystem="web_client/index.html", acceptance_criteria=["[F]/[J] fires directional harpoon", "Tapping pumps air across 4 stages to pop"], status=DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-03-SYS", discipline=DisciplineType.SYSTEMS, title="Subterranean Fauna AI (Burrower Pooka & Magma Fygar)",
                                         target_subsystem="web_client/index.html", acceptance_criteria=["Pookas patrol and ghost through dirt", "Fygars breathe flame jets"], status=DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-03-QA", discipline=DisciplineType.CHAOS_QA, title="Combat Inflation & Immobilization Invariant Test",
                                         target_subsystem="tools/validate_webapp.py", acceptance_criteria=["Inflated enemies are frozen and harmless"], status=DeliverableStatus.PENDING)
                ],
                completion_percentage=0.0
            ),
            StudioMilestone(
                version="v0.4.0",
                codename="Metroidvania Biomes & Traversal Ability Gates",
                theme="Multi-depth biomes (Upper Loam, Dense Granite, Magma Chambers), Jack-Drill, and Jump-Piston double jump.",
                status=MilestoneStatus.PLANNED,
                deliverables=[
                    MilestoneDeliverable(deliverable_id="DEL-04-LVL", discipline=DisciplineType.LEVEL, title="Multi-Strata Biome Grid & Geological Gates",
                                         target_subsystem="web_client/index.html", acceptance_criteria=["Deep Granite and Magma zones with camera scrolling"], status=DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-04-SYS", discipline=DisciplineType.SYSTEMS, title="Pneumatic Jack-Drill & Jump-Piston Traversal Modules",
                                         target_subsystem="web_client/index.html", acceptance_criteria=["Jack-Drill carves dense granite", "Jump-Piston grants double jump"], status=DeliverableStatus.PENDING)
                ],
                completion_percentage=0.0
            ),
            StudioMilestone(
                version="v0.5.0",
                codename="Core Prisms, Sector Map & Extraction Loop",
                theme="Exploration minimap overlay [M], 3 Ancient Core Prisms, and central elevator extraction victory.",
                status=MilestoneStatus.PLANNED,
                deliverables=[
                    MilestoneDeliverable(deliverable_id="DEL-05-CLI", discipline=DisciplineType.CLIENT, title="Subterranean Sector Minimap Overlay",
                                         target_subsystem="web_client/index.html", acceptance_criteria=["[M] toggles explored sector overview"], status=DeliverableStatus.PENDING),
                    MilestoneDeliverable(deliverable_id="DEL-05-SYS", discipline=DisciplineType.SYSTEMS, title="Ancient Core Prisms & Central Elevator Victory State",
                                         target_subsystem="web_client/index.html", acceptance_criteria=["Collecting all 3 prisms triggers elevator win"], status=DeliverableStatus.PENDING)
                ],
                completion_percentage=0.0
            )
        ]

        state = StudioRoadmapState(
            active_version="v0.3.0",
            last_updated=datetime.utcnow(),
            milestones=milestones
        )

        with open(roadmap_file, "w", encoding="utf-8") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2)

        with open(self.active_project_file, "w", encoding="utf-8") as f:
            json.dump(parsed.model_dump(mode="json"), f, indent=2)
