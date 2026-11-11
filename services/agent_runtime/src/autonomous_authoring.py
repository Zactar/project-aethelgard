"""
services/agent_runtime/src/autonomous_authoring.py
Project Aethelgard: Autonomous RFC Authoring Agent with Retrospective Memory Grounding
"""

from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from schemas.studio_contracts import DisciplineType, IncidentSeverity
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.Authoring")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class AutonomousAuthoringAgent:
    """
    Synthesizes and stages architectural, topological, gameplay, and narrative RFCs.
    Queries StudioRetrospectiveMemory before authoring to ground proposals in past
    post-mortems, preventing cyclical regressions.
    """

    def __init__(self, workspace_root: Optional[Path] = None, memory: Optional[StudioRetrospectiveMemory] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = memory or StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)
        self.rfcs_staging_dir = self.workspace_root / "build" / "staging" / "rfcs"
        self.rfcs_staging_dir.mkdir(parents=True, exist_ok=True)

    def author_rfc(
        self,
        discipline: DisciplineType,
        title: str,
        summary: str,
        target_subsystem: str,
        proposed_changes: Dict[str, Any],
        milestone_tag: Optional[str] = None,
        target_deliverable_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Drafts a structured Request for Comments (RFC), embedding negative constraints
        and executing pre-flight compliance checks. Dynamically resolves active milestone version.
        """
        # Resolve active milestone dynamically if not provided
        if not milestone_tag:
            from services.agent_runtime.src.roadmap_engine import StudioRoadmapEngine
            milestone_tag = StudioRoadmapEngine(
                workspace_root=self.workspace_root).load_roadmap().active_version

        disc_val = discipline.value if isinstance(
            discipline, DisciplineType) else discipline
        logger.info(
            f"Authoring RFC under discipline '{disc_val}': '{title}' (Milestone: {milestone_tag})")

        query_context = f"{title} {summary} {target_subsystem} {json.dumps(proposed_changes)}"
        active_friction_rules = self.memory.query_friction_rules(
            discipline=disc_val,
            context_query=query_context,
            limit=4
        )
        adversarial_context = self.memory.generate_adversarial_context(
            discipline=disc_val,
            rfc_title=title,
            proposed_diff=json.dumps(proposed_changes)
        )

        rfc_id = f"RFC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        compliance_audit = self._audit_against_historical_rules(
            discipline=disc_val,
            proposed_changes=proposed_changes,
            friction_rules=active_friction_rules
        )

        # In author_rfc():
        from services.agent_runtime.src.studio_knowledge_base import StudioKnowledgeBase
        kb = StudioKnowledgeBase(workspace_root=self.workspace_root)
        role_curriculum = kb.get_role_training_context(disc_val)

        rfc_payload = {
            "rfc_id": rfc_id,
            "title": title,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "milestone_tag": milestone_tag,
            "target_deliverable_id": target_deliverable_id,
            "discipline": disc_val,
            "target_subsystem": target_subsystem,
            "status": "STAGED_FOR_REVIEW",
            "summary": summary,
            "pedagogical_grounding": role_curriculum[:240] + "...",
            "proposed_changes": proposed_changes,
            "retrospective_memory": {
                "injected_friction_rules": active_friction_rules,
                "adversarial_prompt_context": adversarial_context,
                "pre_flight_audit": compliance_audit
            },
            "validation_verdict": {
                "passes_preflight": compliance_audit["passed"],
                "reasons": compliance_audit["reasons"]
            }
        }

        staged_file = self.rfcs_staging_dir / f"{rfc_id}.json"
        with open(staged_file, "w", encoding="utf-8") as f:
            json.dump(rfc_payload, f, indent=2)

        logger.info(
            f"Staged RFC '{rfc_id}' written to {staged_file} [Pre-flight Passed: {compliance_audit['passed']}]")
        return rfc_payload

    def _audit_against_historical_rules(
        self,
        discipline: str,
        proposed_changes: Dict[str, Any],
        friction_rules: List[str]
    ) -> Dict[str, Any]:
        """Static heuristic checks enforcing historical post-mortem rules."""
        violations = []
        payload_str = json.dumps(proposed_changes).lower()

        # Rule 1: Level Spatial Inset Padding (INC-20261012-LVL-01)
        if discipline in (DisciplineType.LEVEL.value, "Level"):
            if any(k in payload_str for k in ("bounds", "floorplate", "socket", "new_room")):
                inset_offset = proposed_changes.get("inset_offset")
                if inset_offset is None and "new_room" in proposed_changes:
                    inset_offset = proposed_changes["new_room"].get(
                        "inset_offset")
                if inset_offset is None:
                    inset_offset = 0.0

                if inset_offset < 0.15:
                    violations.append(
                        f"Violation of INC-20261012-LVL-01: Boundary lacks 0.15m clearance inset (found {inset_offset}m)."
                    )

        # Rule 2: Client Billboard Hierarchy (INC-20261018-CLI-02)
        if discipline in (DisciplineType.CLIENT.value, "Client"):
            if any(k in payload_str for k in ("billboard", "nameplate", "hud")):
                parent_target = proposed_changes.get(
                    "parent_hierarchy", "").lower()
                if "scene" in parent_target and "actor" not in parent_target:
                    violations.append(
                        "Violation of INC-20261018-CLI-02: Billboard attached directly to global Scene.")

        # Rule 3: Gameplay Raycast Layer Masking (INC-20261023-GMP-03)
        if discipline in (DisciplineType.GAMEPLAY.value, "Gameplay"):
            if "raycast" in payload_str or "interaction" in payload_str:
                layer_mask = (
                    proposed_changes.get("layer_mask") or
                    proposed_changes.get("interaction_layer") or
                    ""
                )
                if "interactionlayer.interactive" not in str(layer_mask).lower():
                    violations.append(
                        "Violation of INC-20261023-GMP-03: Interaction query lacks InteractionLayer.INTERACTIVE.")

        # Rule 4: Systems Topological Schema Declaration (INC-20261027-SYS-04)
        if discipline in (DisciplineType.SYSTEMS.value, "Systems"):
            if "schema_patch" in proposed_changes:
                patch_code = proposed_changes.get("schema_patch", "")
                if "class " in patch_code and "(str, Enum)" in patch_code and "(BaseModel)" in patch_code:
                    first_model = patch_code.find("(BaseModel)")
                    first_enum = patch_code.find("(str, Enum)")
                    if first_model < first_enum and first_model != -1:
                        violations.append(
                            "Violation of INC-20261027-SYS-04: BaseModel declared prior to Enum.")

        return {
            "passed": len(violations) == 0,
            "violations_detected": len(violations),
            "reasons": violations if violations else ["All historical friction constraints satisfied."]
        }
