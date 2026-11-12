"""
services/agent_runtime/src/roadmap_engine.py
Project Aethelgard: Autonomous Roadmap & Dynamic Horizon Evolution Engine.
Tracks deliverable burndown, enforces applied-RFC verification, and dynamically
charts new SemVer milestones (v0.6.0+) via LLM when pre-scripted milestones ship.
"""

import sys
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

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
from services.agent_runtime.src.llm_gateway import LLMGateway
from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory

logger = logging.getLogger("Aethelgard.Roadmap")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class StudioRoadmapEngine:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.roadmap_dir = self.workspace_root / "build" / "roadmap"
        self.roadmap_dir.mkdir(parents=True, exist_ok=True)
        self.roadmap_file = self.roadmap_dir / "studio_roadmap.json"

    def load_roadmap(self) -> StudioRoadmapState:
        if self.roadmap_file.exists():
            try:
                data = json.loads(self.roadmap_file.read_text(encoding="utf-8"))
                return StudioRoadmapState(**data)
            except Exception as e:
                logger.warning(f"Failed to parse studio_roadmap.json: {e}")
        return StudioRoadmapState(active_version="v0.1.0", milestones=[])

    def save_roadmap(self, state: StudioRoadmapState) -> None:
        state.last_updated = datetime.utcnow()
        self.roadmap_file.write_text(
            json.dumps(state.model_dump(mode="json"), indent=2),
            encoding="utf-8"
        )

    def audit_active_milestone(self) -> Dict[str, Any]:
        state = self.load_roadmap()
        milestone = next(
            (m for m in state.milestones if m.version == state.active_version and m.status != MilestoneStatus.SHIPPED),
            None
        )
        if not milestone:
            milestone = next((m for m in reversed(state.milestones) if m.version == state.active_version), None)

        if not milestone:
            return {
                "version": state.active_version,
                "codename": "Unscheduled",
                "status": "INITIALIZING",
                "verified_deliverables": "0/0",
                "completion_percentage": 0.0,
                "deliverables": []
            }

        applied_rfcs_file = self.workspace_root / "build" / "staging" / "applied_rfcs.json"
        applied_rfc_ids = []
        if applied_rfcs_file.exists():
            try:
                applied_rfc_ids = json.loads(applied_rfcs_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        approved_dir = self.workspace_root / "build" / "rfcs" / "approved"
        approved_rfcs = list(approved_dir.glob("*.json")) if approved_dir.exists() else []
        verified_count = 0
        total_count = len(milestone.deliverables)

        for deliv in milestone.deliverables:
            deliv_verified = False
            for rfc_file in approved_rfcs:
                try:
                    data = json.loads(rfc_file.read_text(encoding="utf-8"))
                    rfc_id = data.get("rfc_id", rfc_file.stem)
                    if rfc_id not in applied_rfc_ids:
                        continue
                    title_matches = (
                        deliv.title.lower() in data.get("title", "").lower()
                        or data.get("title", "").lower() in deliv.title.lower()
                    )
                    if title_matches:
                        deliv.status = DeliverableStatus.VERIFIED
                        deliv.verified_artifact = rfc_file.name
                        deliv_verified = True
                        break
                except Exception:
                    pass

            if deliv_verified:
                verified_count += 1
            else:
                deliv.status = DeliverableStatus.PENDING

        milestone.completion_percentage = round((verified_count / total_count) * 100, 1) if total_count > 0 else 0.0
        if milestone.completion_percentage >= 100.0:
            milestone.status = MilestoneStatus.VALIDATING
        elif milestone.status != MilestoneStatus.SHIPPED:
            milestone.status = MilestoneStatus.IN_PROGRESS

        self.save_roadmap(state)
        return {
            "version": milestone.version,
            "codename": milestone.codename,
            "theme": milestone.theme,
            "status": milestone.status.value if hasattr(milestone.status, "value") else str(milestone.status),
            "verified_deliverables": f"{verified_count}/{total_count}",
            "completion_percentage": milestone.completion_percentage,
            "deliverables": [d.model_dump(mode="json") for d in milestone.deliverables]
        }

    def _increment_semver(self, version: str) -> str:
        match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", str(version))
        if not match:
            return "v0.6.0"
        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return f"v{major}.{minor + 1}.{patch}"

    def _synthesize_dynamic_milestone(self, next_ver: str, shipped_milestones: List[StudioMilestone]) -> StudioMilestone:
        """
        Uses LLMGateway (1 compact JSON call) to autonomously chart the next post-launch
        milestone when all pre-scripted GDD milestones have shipped.
        """
        gdd_path = self.workspace_root / "projects" / "inbox" / "GDD.md"
        gdd_text = gdd_path.read_text(encoding="utf-8")[:1800] if gdd_path.exists() else "2D Action Roguelike Game."
        shipped_summary = [f"{m.version}: {m.theme}" for m in shipped_milestones]

        gateway = LLMGateway(workspace_root=self.workspace_root)
        theme = f"Autonomous Expansion {next_ver}: Endless Mastery & Boss Mutations"
        codename = f"Horizon-{next_ver}"
        raw_deliverables = [
            {"discipline": "Systems", "title": "Prestige ascension multiplier and dynamic difficulty scaling ledger."},
            {"discipline": "Gameplay", "title": "Elite hazard combos, adrenaline burst mechanic, and score streak overdrive."},
            {"discipline": "Client", "title": "Dynamic weather particle shaders and post-run telemetry breakdown."}
        ]

        if gateway.is_live():
            exec_card = StudioRetrospectiveMemory(workspace_root=self.workspace_root).get_training_directive("Executive_Producer")
            sys_prompt = exec_card + "\n\n" + (
                "You are the Autonomous Executive Producer of a virtual game studio.\n"
                "All initial GDD milestones have shipped. GAME DESIGN MANDATE: NEVER propose new HUD stat boxes, telemetry panels, or text counters. Propose ONLY diegetic, interactive in-world gameplay mechanics (new enemy hazards, interactive terrain structures, visual particle effects, or active player movement abilities). Design the next post-launch expansion milestone "
                f"({next_ver}) with 3 concrete, additive features that deepen replayability without breaking prior modules."
            )
            user_prompt = f"""GAME DESIGN DOCUMENT EXCERPT:
{gdd_text}

ALREADY SHIPPED MILESTONES:
{json.dumps(shipped_summary, indent=2)}

Respond ONLY with a valid JSON object matching this schema:
{{
  "codename": "Operation <Name>",
  "theme": "<Concise Milestone Theme Title>",
  "deliverables": [
    {{"discipline": "Systems", "title": "<Deliverable 1 description>"}},
    {{"discipline": "Gameplay", "title": "<Deliverable 2 description>"}},
    {{"discipline": "Client", "title": "<Deliverable 3 description>"}}
  ]
}}"""
            raw = gateway.complete(sys_prompt, user_prompt, temperature=0.2)
            try:
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    codename = parsed.get("codename") or codename
                    theme = parsed.get("theme") or theme
                    if isinstance(parsed.get("deliverables"), list) and len(parsed["deliverables"]) >= 2:
                        raw_deliverables = parsed["deliverables"][:4]
            except Exception as e:
                logger.warning(f"[Dynamic Horizon] Fallback used for {next_ver}: {e}")

        deliv_objs = []
        for idx, d in enumerate(raw_deliverables, start=1):
            disc_str = d.get("discipline", "Systems")
            disc_enum = DisciplineType.SYSTEMS
            for member in DisciplineType:
                if member.value.lower() == str(disc_str).lower():
                    disc_enum = member
                    break
            deliv_objs.append(
                DeliverableItem(
                    deliverable_id=f"DELIV-{next_ver.upper().replace('.', '_')}-{idx:02d}",
                    discipline=disc_enum,
                    title=d.get("title", f"Expansion Feature {idx}"),
                    target_subsystem="web_client/index.html",
                    status=DeliverableStatus.PENDING
                )
            )

        logger.info(f"[Dynamic Horizon Planner] Charted new autonomous milestone {next_ver}: '{theme}'")
        return StudioMilestone(
            version=next_ver,
            codename=codename,
            theme=theme,
            status=MilestoneStatus.IN_PROGRESS,
            completion_percentage=0.0,
            deliverables=deliv_objs
        )

    def evolve_to_next_milestone(self) -> Optional[StudioMilestone]:
        state = self.load_roadmap()
        current = next(
            (m for m in state.milestones if m.version == state.active_version and m.status != MilestoneStatus.SHIPPED),
            None
        )
        if current:
            current.status = MilestoneStatus.SHIPPED
            current.completed_at = datetime.utcnow()
            logger.info(f"Archived milestone {current.version} ({current.codename}) as SHIPPED.")

        # Find next planned milestone in roadmap
        next_ms = next((m for m in state.milestones if m.status == MilestoneStatus.PLANNED), None)
        if next_ms:
            next_ms.status = MilestoneStatus.IN_PROGRESS
            state.active_version = next_ms.version
            self.save_roadmap(state)
            logger.info(f"[AUTONOMOUS ROADMAP EVOLUTION] Advanced to {next_ms.version}: '{next_ms.theme}'")
            return next_ms

        # All pre-scripted milestones are SHIPPED -> Dynamically chart the next SemVer milestone!
        next_ver = self._increment_semver(state.active_version)
        dyn_ms = self._synthesize_dynamic_milestone(next_ver, state.milestones)
        state.milestones.append(dyn_ms)
        state.active_version = dyn_ms.version
        self.save_roadmap(state)
        logger.info(f"[AUTONOMOUS ROADMAP EVOLUTION] Dynamically charted & activated {dyn_ms.version}: '{dyn_ms.theme}'")
        return dyn_ms
