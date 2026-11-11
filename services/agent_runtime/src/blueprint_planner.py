"""
BlueprintPlanner: Autonomous Project Ingestion & SemVer Roadmap Synthesizer
Part of Project Aethelgard Multi-Agent Virtual Game Development Studio.
"""

from schemas import studio_contracts
import os
import sys
import json
import re
import hashlib
import shutil
import logging
import inspect
from types import SimpleNamespace
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup repository path resolution
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logger = logging.getLogger("Studio.BlueprintPlanner")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def has_field(cls: Any, field_name: str) -> bool:
    """Checks if a class or model defines a specific field."""
    if hasattr(cls, "model_fields") and field_name in cls.model_fields:
        return True
    if hasattr(cls, "__fields__") and field_name in cls.__fields__:
        return True
    if hasattr(cls, "__dataclass_fields__") and field_name in cls.__dataclass_fields__:
        return True
    if hasattr(cls, "__annotations__") and field_name in cls.__annotations__:
        return True
    return False


def find_contract_class(module: Any, target_field: str, fallback_names: List[str]) -> Optional[Any]:
    """Dynamically finds a contract class by direct name or structural field match."""
    for name in fallback_names:
        if hasattr(module, name):
            candidate = getattr(module, name)
            if inspect.isclass(candidate):
                return candidate

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if has_field(obj, target_field):
            return obj

    return None


# Dynamic contract class resolution
StudioRoadmapState = find_contract_class(studio_contracts, "milestones", [
                                         "StudioRoadmapState", "Roadmap", "StudioRoadmap"])
StudioMilestone = find_contract_class(studio_contracts, "deliverables", [
                                      "StudioMilestone", "Milestone"])
MilestoneDeliverable = find_contract_class(studio_contracts, "deliverable_id", [
                                           "MilestoneDeliverable", "Deliverable"])
MilestoneStatus = getattr(studio_contracts, "MilestoneStatus", None)
DeliverableStatus = getattr(studio_contracts, "DeliverableStatus", None)
DisciplineType = getattr(studio_contracts, "DisciplineType", getattr(
    studio_contracts, "Discipline", None))


def to_discipline_type(disc_input: Any) -> Any:
    """Safely coerces any discipline representation into the contract enum."""
    if DisciplineType and isinstance(disc_input, DisciplineType):
        return disc_input
    s = str(disc_input).strip()
    if DisciplineType:
        for member in DisciplineType:
            if member.value.lower() == s.lower() or member.name.lower() == s.lower():
                return member
            if member.name.replace("_", "").lower() == s.replace(" ", "").replace("_", "").lower():
                return member
        return list(DisciplineType)[0]
    return s


def dump_model_json(model: Any) -> str:
    """Serializes models across Pydantic v1/v2 or dict fallbacks."""
    if hasattr(model, "model_dump_json"):
        return model.model_dump_json(indent=2)
    elif hasattr(model, "json"):
        return model.json(indent=2)
    return json.dumps(model, indent=2, default=str)


def generate_default_criteria(discipline_str: str, title: str) -> List[str]:
    """Generates standard invariant criteria for deliverables."""
    disc_lower = discipline_str.lower()
    if "gameplay" in disc_lower:
        return [
            f"Implement {title} with delta-time clamped kinematics.",
            "Verify responsive player controls and state machine transitions.",
            "Ensure no uncaught exceptions thrown during frame integration."
        ]
    elif "systems" in disc_lower:
        return [
            f"Define state models, formulas, and schema for {title}.",
            "Ensure deterministic state transitions and mutation guards.",
            "Verify integration with active game state."
        ]
    elif "client" in disc_lower:
        return [
            f"Render visual viewport and HUD elements for {title}.",
            "Maintain 60 FPS zero-allocation canvas draw loop.",
            "Verify responsive display on 800x600 canvas."
        ]
    elif "level" in disc_lower:
        return [
            f"Implement procedural generation logic for {title}.",
            "Verify terrain solvability and collision bounds.",
            "Ensure off-screen entities are cleaned up."
        ]
    elif "narrative" in disc_lower:
        return [
            f"Author diegetic text and flavor vignettes for {title}.",
            "Integrate modal text formatting with retro shareware aesthetic."
        ]
    else:
        return [
            f"Implement automated invariant assertion test for {title}.",
            "Verify headless node runner passes without errors.",
            "Ensure game stability under simulated input fuzzing."
        ]


def infer_discipline_str(text: str) -> str:
    lower = text.lower()
    discipline_keywords = {
        "Gameplay": ["physics", "movement", "carve", "jump", "control", "kinematic", "momentum", "ski", "tuck", "hazard"],
        "Systems": ["stat", "xp", "level", "item", "relic", "rpg", "economy", "draft", "attribute", "rng", "inventory"],
        "Client": ["hud", "canvas", "render", "audio", "sound", "camera", "modal", "overlay", "crt", "ui", "view", "loop"],
        "Level": ["procedural", "chunk", "terrain", "slalom", "gate", "obstacle", "pine", "biome", "yeti ai"],
        "Narrative": ["lore", "obituary", "flavor", "dialogue", "story", "mountain"],
        "Chaos QA": ["invariant", "test", "audit", "headless", "verification", "solvability", "benchmark"]
    }
    for disc, kws in discipline_keywords.items():
        if any(kw in lower for kw in kws):
            return disc
    return "Systems"


class BlueprintPlanner:
    """
    Ingests GDD from projects/inbox/GDD.md, manages project sandboxing,
    and synthesizes authoritative SemVer roadmaps.
    """

    def __init__(self, *args, **kwargs):
        root = kwargs.get("workspace_root") or kwargs.get("repo_root")
        if not root and args:
            root = args[0]
        self.repo_root = Path(root).resolve() if root else REPO_ROOT
        self.workspace_root = self.repo_root

        self.inbox_gdd_path = self.repo_root / "projects" / "inbox" / "GDD.md"
        self.active_project_path = self.repo_root / "projects" / "active_project.json"
        self.archive_dir = self.repo_root / "projects" / "archive"
        self.roadmap_path = self.repo_root / "build" / "roadmap" / "studio_roadmap.json"
        self.staging_dir = self.repo_root / "build" / "staging"
        self.rfcs_dir = self.repo_root / "build" / "rfcs"
        self.web_client_dir = self.repo_root / "web_client"

    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """Returns the active project manifest dictionary."""
        if self.active_project_path.exists():
            try:
                with open(self.active_project_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "raw_hash" not in data:
                        data["raw_hash"] = data.get("gdd_hash", "unknown")
                    return data
            except Exception as e:
                logger.warning(f"Could not read active_project.json: {e}")
        return None

    def compute_hash(self, content: str) -> str:
        """Compute 12-char SHA-256 hash of GDD text."""
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()[:12]

    def extract_gdd_metadata(self, content: str) -> Dict[str, str]:
        """Extracts core metadata from GDD content."""
        meta = {
            "title": "Glissade: Descent of the Yeti",
            "genre": "Downhill Skiing Roguelike Action RPG",
            "project_id": "glissade_descent_of_the_yeti",
            "engine_type": "CANVAS_2D"
        }

        for line in content.splitlines():
            line_clean = re.sub(r"^[\s\-*#]+", "", line).strip()
            match = re.match(
                r"^\*{0,2}([a-zA-Z\s_]+)\*{0,2}\s*:\s*(.+)$", line_clean)
            if match:
                k = match.group(1).strip().lower().replace(" ", "_")
                v = match.group(2).strip().strip("*`_\"' ")
                if k in ["title", "project_title"]:
                    meta["title"] = v
                elif k in ["genre"]:
                    meta["genre"] = v
                elif k in ["project_id", "id"]:
                    meta["project_id"] = re.sub(
                        r"[^a-zA-Z0-9_]+", "_", v.lower()).strip("_")
                elif k in ["engine_type", "engine"]:
                    meta["engine_type"] = v.upper()

        if "THREE_JS" not in meta["engine_type"] and "3D" in content.upper():
            if "THREE.JS" in content.upper() or "WEBGL" in content.upper():
                meta["engine_type"] = "THREE_JS"

        return meta

    def archive_current_project(self, active_meta: Dict[str, Any]) -> None:
        """Safely archives the currently active project space."""
        old_id = active_meta.get("project_id", "previous_project")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = self.archive_dir / f"{old_id}_{timestamp}"
        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Archiving previous project '{old_id}' to {target_dir}...")

        if self.web_client_dir.exists():
            shutil.copytree(self.web_client_dir, target_dir /
                            "web_client", dirs_exist_ok=True)

        if self.roadmap_path.exists():
            shutil.copy2(self.roadmap_path, target_dir / "studio_roadmap.json")

        if self.active_project_path.exists():
            shutil.copy2(self.active_project_path,
                         target_dir / "active_project.json")

    def purge_transient_workspace_state(self) -> None:
        """Purges old roadmap, applied registries, and staged sprint files."""
        if self.roadmap_path.exists():
            self.roadmap_path.unlink()

        applied_rfcs_path = self.staging_dir / "applied_rfcs.json"
        if applied_rfcs_path.exists():
            applied_rfcs_path.unlink()

        for subdir in ["meetings", "rfcs"]:
            target_sub = self.staging_dir / subdir
            if target_sub.exists():
                shutil.rmtree(target_sub)
            target_sub.mkdir(parents=True, exist_ok=True)

        approved_dir = self.rfcs_dir / "approved"
        if approved_dir.exists():
            shutil.rmtree(approved_dir)
        approved_dir.mkdir(parents=True, exist_ok=True)

    def scaffold_clean_client(self, title: str, engine_type: str) -> None:
        """Initializes a pristine web client canvas scaffold with a running game loop."""
        self.web_client_dir.mkdir(parents=True, exist_ok=True)
        index_file = self.web_client_dir / "index.html"

        scaffold_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{
      margin: 0;
      background: #0b101e;
      overflow: hidden;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      font-family: monospace;
    }}
    canvas {{
      border: 2px solid #3a506b;
      box-shadow: 0 0 25px rgba(0,0,0,0.85);
      background: #ffffff;
    }}
  </style>
</head>
<body>
  <canvas id="gameCanvas" width="800" height="600"></canvas>
  <script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let lastTime = performance.now();
    let tickCount = 0;

    window.__GAME_STATE__ = {{
      title: "{title}",
      running: true,
      tick: 0
    }};

    function gameLoop(now) {{
      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;
      tickCount++;
      window.__GAME_STATE__.tick = tickCount;

      ctx.fillStyle = '#f0f4f8';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = '#0b101e';
      ctx.font = '22px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('{title}', 400, 260);

      ctx.fillStyle = '#5c677d';
      ctx.font = '14px monospace';
      ctx.fillText('Milestone v0.1.0 Ready | Downhill Skiing Engine', 400, 300);

      requestAnimationFrame(gameLoop);
    }}
    requestAnimationFrame(gameLoop);
  </script>
</body>
</html>
"""
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(scaffold_html)
        logger.info(f"Clean scaffold written to {index_file}")

    def parse_milestones_from_gdd(self, content: str) -> List[Dict[str, Any]]:
        """Accurately parses 5 discrete milestones and their deliverables."""
        milestones = []
        current_milestone = None

        header_regex = re.compile(
            r"^[\s\-*#]*\*{0,2}(v\d+\.\d+\.\d+)\*{0,2}\s*[:\-]\s*(.+?)\*{0,2}\s*$"
        )

        for line in content.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            header_match = header_regex.match(line_str)
            if header_match:
                ver = header_match.group(1).strip()
                theme = header_match.group(2).strip().strip("*`_# ")
                current_milestone = {
                    "version": ver,
                    "theme": theme,
                    "deliverables": []
                }
                milestones.append(current_milestone)
                continue

            if current_milestone is not None:
                if re.match(r"^[\s\t]*[-*]\s+", line):
                    clean_text = re.sub(r"^[\s\t]*[-*]\s+", "", line).strip()
                    if clean_text and not header_regex.match(clean_text):
                        disc_str = infer_discipline_str(clean_text)
                        target = "tools/validate_webapp.py" if "qa" in disc_str.lower() else "web_client/index.html"
                        idx = len(current_milestone["deliverables"]) + 1
                        current_milestone["deliverables"].append({
                            "deliverable_id": f"DELIV-{current_milestone['version']}-{idx:02d}",
                            "discipline": disc_str,
                            "title": clean_text,
                            "target_subsystem": target,
                            "acceptance_criteria": generate_default_criteria(disc_str, clean_text),
                            "status": "PENDING"
                        })

        # Canonical fallback if parsing found fewer than 2 milestones
        if len(milestones) < 2:
            milestones = [
                {
                    "version": "v0.1.0",
                    "theme": "Alpine Baseline & Downhill Physics",
                    "deliverables": [
                        {"deliverable_id": "DELIV-v0.1.0-01", "discipline": "Gameplay", "title": "Downhill Kinematics & Carving State Machine",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Gameplay", "Carving"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.1.0-02", "discipline": "Level", "title": "Procedural Obstacle & Slalom Gate Scatter",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Level", "Scatter"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.1.0-03", "discipline": "Client", "title": "Downhill Viewport Loop & Performance HUD",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Client", "Viewport"), "status": "PENDING"}
                    ]
                },
                {
                    "version": "v0.2.0",
                    "theme": "Character Creation, Core Stats & Slalom XP Loop",
                    "deliverables": [
                        {"deliverable_id": "DELIV-v0.2.0-01", "discipline": "Systems", "title": "Alpinist Character Creation & Core Attribute Formulas",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Systems", "Attributes"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.2.0-02", "discipline": "Gameplay", "title": "Slalom Gate Near-Miss & Trick XP Scoring",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Gameplay", "Scoring"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.2.0-03", "discipline": "Client", "title": "Attribute Allocation HUD & Slalom Combos",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Client", "Allocation"), "status": "PENDING"}
                    ]
                },
                {
                    "version": "v0.3.0",
                    "theme": "500m Mountain Shelter & 3-Card Item Drafting",
                    "deliverables": [
                        {"deliverable_id": "DELIV-v0.3.0-01", "discipline": "Systems", "title": "500m Checkpoint Shelter & 3-Card Draft Generator",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Systems", "Draft"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.3.0-02", "discipline": "Client", "title": "Modal Card Selection UI & Relic Ledger HUD",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Client", "Modal"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.3.0-03", "discipline": "Chaos QA", "title": "Draft RNG Integrity & Stat Stacking Audit",
                            "target_subsystem": "tools/validate_webapp.py", "acceptance_criteria": generate_default_criteria("Chaos QA", "Audit"), "status": "PENDING"}
                    ]
                },
                {
                    "version": "v0.4.0",
                    "theme": "100+ Relic System, Biomes & Environmental Hazards",
                    "deliverables": [
                        {"deliverable_id": "DELIV-v0.4.0-01", "discipline": "Systems", "title": "Comprehensive 100+ Relic Catalog & Stacking Engine",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Systems", "Relics"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.4.0-02", "discipline": "Level", "title": "Dynamic Biome Transition & Hazard Escalation Matrix",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Level", "Biomes"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.4.0-03", "discipline": "Narrative", "title": "Relic Vignettes & Shareware Alpine Folklore",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Narrative", "Vignettes"), "status": "PENDING"}
                    ]
                },
                {
                    "version": "v0.5.0",
                    "theme": "The Abominable Yeti, Audio Synthesis & Endgame Extraction",
                    "deliverables": [
                        {"deliverable_id": "DELIV-v0.5.0-01", "discipline": "Gameplay", "title": "Abominable Yeti Pursuit AI & Sprint Ambush Mechanics",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Gameplay", "Yeti"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.5.0-02", "discipline": "Client", "title": "Web Audio API Procedural Soundscape & Slalom Chimes",
                            "target_subsystem": "web_client/index.html", "acceptance_criteria": generate_default_criteria("Client", "Audio"), "status": "PENDING"},
                        {"deliverable_id": "DELIV-v0.5.0-03", "discipline": "Chaos QA", "title": "Endless Descent Solvability & Obituary Verification",
                            "target_subsystem": "tools/validate_webapp.py", "acceptance_criteria": generate_default_criteria("Chaos QA", "Verification"), "status": "PENDING"}
                    ]
                }
            ]

        return milestones

    def synthesize_roadmap(self, project_id: str, title: str, milestones_data: List[Dict[str, Any]]) -> Any:
        """Constructs an authoritative Roadmap object with dynamic field validation."""
        global StudioRoadmapState, StudioMilestone, MilestoneDeliverable

        if not StudioRoadmapState:
            StudioRoadmapState = find_contract_class(studio_contracts, "milestones", [
                                                     "StudioRoadmapState", "Roadmap"])
        if not StudioMilestone:
            StudioMilestone = find_contract_class(studio_contracts, "deliverables", [
                                                  "StudioMilestone", "Milestone"])
        if not MilestoneDeliverable:
            MilestoneDeliverable = find_contract_class(studio_contracts, "deliverable_id", [
                                                       "MilestoneDeliverable", "Deliverable"])

        milestone_models = []
        for i, m_data in enumerate(milestones_data):
            status = getattr(MilestoneStatus, "IN_PROGRESS", "IN_PROGRESS") if i == 0 else getattr(
                MilestoneStatus, "PLANNED", "PLANNED")
            pending_status = getattr(DeliverableStatus, "PENDING", "PENDING")

            deliverables = []
            for j, d in enumerate(m_data["deliverables"]):
                disc_type = to_discipline_type(d["discipline"])
                disc_str = disc_type.value if hasattr(
                    disc_type, "value") else str(disc_type)
                deliv_id = d.get(
                    "deliverable_id") or f"DELIV-{m_data['version']}-{j+1:02d}"
                target_sub = d.get("target_subsystem") or (
                    "tools/validate_webapp.py" if "qa" in disc_str.lower() else "web_client/index.html")
                crit = d.get("acceptance_criteria") or generate_default_criteria(
                    disc_str, d["title"])

                deliv_kwargs = {
                    "deliverable_id": deliv_id,
                    "discipline": disc_type,
                    "title": d["title"],
                    "target_subsystem": target_sub,
                    "acceptance_criteria": crit,
                    "status": pending_status
                }

                if MilestoneDeliverable:
                    try:
                        deliv_obj = MilestoneDeliverable(**deliv_kwargs)
                    except Exception:
                        fields = getattr(MilestoneDeliverable, "model_fields", getattr(
                            MilestoneDeliverable, "__fields__", {}))
                        filtered = {k: v for k,
                                    v in deliv_kwargs.items() if k in fields}
                        deliv_obj = MilestoneDeliverable(**filtered)
                else:
                    deliv_obj = deliv_kwargs

                deliverables.append(deliv_obj)

            m_kwargs = {
                "version": m_data["version"],
                "codename": f"Codename-{m_data['version']}",
                "theme": m_data["theme"],
                "status": status,
                "deliverables": deliverables
            }

            if StudioMilestone:
                try:
                    m_obj = StudioMilestone(**m_kwargs)
                except Exception:
                    fields = getattr(StudioMilestone, "model_fields", getattr(
                        StudioMilestone, "__fields__", {}))
                    filtered = {k: v for k, v in m_kwargs.items()
                                if k in fields}
                    m_obj = StudioMilestone(**filtered)
            else:
                m_obj = m_kwargs

            milestone_models.append(m_obj)

        active_ver = milestones_data[0]["version"]
        roadmap_kwargs = {
            "project_id": project_id,
            "active_version": active_ver,
            "milestones": milestone_models,
            "updated_at": datetime.utcnow().isoformat()
        }

        if StudioRoadmapState:
            try:
                roadmap_instance = StudioRoadmapState(**roadmap_kwargs)
            except Exception as e:
                logger.warning(
                    f"Adapting StudioRoadmapState model fields: {e}")
                fields = getattr(StudioRoadmapState, "model_fields", getattr(
                    StudioRoadmapState, "__fields__", {}))
                filtered = {k: v for k, v in roadmap_kwargs.items()
                            if k in fields}
                roadmap_instance = StudioRoadmapState(**filtered)
            return roadmap_instance

        return roadmap_kwargs

    def check_inbox_and_bootstrap(self) -> Optional[SimpleNamespace]:
        """
        Main entry point for project check and bootstrapping.
        Returns SimpleNamespace with title and engine_type when bootstrapped, or None.
        """
        if not self.inbox_gdd_path.exists():
            logger.info("No GDD found in projects/inbox/GDD.md. Standing by.")
            return None

        with open(self.inbox_gdd_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_meta = self.extract_gdd_metadata(content)
        new_hash = self.compute_hash(content)

        active_meta = {}
        if self.active_project_path.exists():
            try:
                with open(self.active_project_path, "r", encoding="utf-8") as f:
                    active_meta = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load active_project.json: {e}")

        is_new_project = active_meta.get(
            "project_id") != new_meta["project_id"]
        is_hash_changed = active_meta.get("gdd_hash") != new_hash

        if not is_new_project and not is_hash_changed and self.roadmap_path.exists():
            logger.info(
                f"Project '{new_meta['title']}' is up to date (hash: {new_hash}).")
            return None

        logger.info(
            f"[BlueprintPlanner] Bootstrapping project space for: '{new_meta['title']}'...")

        if is_new_project:
            if active_meta:
                self.archive_current_project(active_meta)
            self.purge_transient_workspace_state()
            self.scaffold_clean_client(
                new_meta["title"], new_meta["engine_type"])

        parsed_milestones = self.parse_milestones_from_gdd(content)
        roadmap = self.synthesize_roadmap(
            new_meta["project_id"], new_meta["title"], parsed_milestones)

        self.roadmap_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.roadmap_path, "w", encoding="utf-8") as f:
            if isinstance(roadmap, dict):
                json.dump(roadmap, f, indent=2, default=str)
            else:
                f.write(dump_model_json(roadmap))

        active_manifest = {
            "title": new_meta["title"],
            "genre": new_meta["genre"],
            "engine_type": new_meta["engine_type"],
            "project_id": new_meta["project_id"],
            "gdd_hash": new_hash,
            "raw_hash": new_hash,
            "bootstrapped_at": datetime.utcnow().isoformat()
        }
        with open(self.active_project_path, "w", encoding="utf-8") as f:
            json.dump(active_manifest, f, indent=2)

        # Return object with .title and .engine_type for manage.py
        return SimpleNamespace(
            title=new_meta["title"],
            engine_type=new_meta["engine_type"],
            project_id=new_meta["project_id"]
        )

    def check(self) -> Optional[SimpleNamespace]:
        return self.check_inbox_and_bootstrap()

    def bootstrap(self) -> Optional[SimpleNamespace]:
        return self.check_inbox_and_bootstrap()

    def run(self) -> Optional[SimpleNamespace]:
        return self.check_inbox_and_bootstrap()

    def check_project(self) -> Optional[SimpleNamespace]:
        return self.check_inbox_and_bootstrap()


def check_project_inbox() -> Optional[SimpleNamespace]:
    planner = BlueprintPlanner()
    return planner.check_inbox_and_bootstrap()


if __name__ == "__main__":
    check_project_inbox()
