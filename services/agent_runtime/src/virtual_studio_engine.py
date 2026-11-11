"""
services/agent_runtime/src/virtual_studio_engine.py
Project Aethelgard: High-Friction Review Board Quorum & Multi-Agent Studio Engine
"""

from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from schemas.studio_contracts import (
    DisciplineType,
    ReviewVote,
    DisciplineBallot,
    ReviewQuorumResult,
    PostMortemRecord,
    IncidentSeverity
)
from datetime import datetime
from typing import List, Dict, Any, Optional
import shutil
import logging
import json
import sys
from pathlib import Path

# Workspace root injection strictly precedes internal package imports
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.StudioEngine")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class HighFrictionReviewBoard:
    """
    Adversarial multi-discipline review quorum that evaluates staged RFCs.
    Enforces hard vetoes, WebGL draw-call budgets, spatial invariants, and memory rules.
    """

    def __init__(self, workspace_root: Optional[Path] = None, memory: Optional[StudioRetrospectiveMemory] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = memory or StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)

        self.staging_dir = self.workspace_root / "build" / "staging" / "rfcs"
        self.approved_dir = self.workspace_root / "build" / "rfcs" / "approved"
        self.rejected_dir = self.workspace_root / "build" / "rfcs" / "rejected"

        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_rfc(self, rfc_payload: Dict[str, Any]) -> ReviewQuorumResult:
        """
        Convenes all discipline specialists to vote on a staged RFC.
        """
        rfc_id = rfc_payload.get("rfc_id", "UNKNOWN_RFC")
        title = rfc_payload.get("title", "")
        author_discipline = rfc_payload.get("discipline", "")
        changes = rfc_payload.get("proposed_changes", {})
        preflight_passed = rfc_payload.get(
            "validation_verdict", {}).get("passes_preflight", True)

        ballots: List[DisciplineBallot] = []

        # 1. Chaos QA Commander Ballot (Adversarial Stress Test)
        ballots.append(self._audit_chaos_qa(rfc_payload, preflight_passed))

        # 2. Systems Architect Ballot (AST, Schema Integrity, Pydantic Order)
        ballots.append(self._audit_systems(changes))

        # 3. Client Architect Ballot (WebGL Budgets, Hierarchy, Materials)
        ballots.append(self._audit_client(changes))

        # 4. Level Architect Ballot (AABB Spacing, Sockets, Inset)
        ballots.append(self._audit_level(changes))

        # 5. Gameplay Specialist Ballot (Raycasting, Economy, Pacing)
        ballots.append(self._audit_gameplay(changes))

        # 6. Narrative Specialist Ballot (Canon Consistency & Tone)
        ballots.append(self._audit_narrative(rfc_payload))

        # Tally Quorum
        approvals = sum(1 for b in ballots if b.vote == ReviewVote.APPROVE)
        rejections = sum(1 for b in ballots if b.vote in (
            ReviewVote.REJECT, ReviewVote.REQUEST_CHANGES))
        vetoes = sum(1 for b in ballots if b.veto)

        # Quorum threshold: At least 4 approvals and strictly 0 vetoes
        quorum_passed = (approvals >= 4) and (vetoes == 0)
        status = "APPROVED" if quorum_passed else "REJECTED"

        directives = []
        for b in ballots:
            if b.friction_points:
                directives.extend(
                    [f"[{b.reviewer}] {fp}" for fp in b.friction_points])

        summary = (
            f"Review Board Quorum {'PASSED' if quorum_passed else 'FAILED'}: "
            f"{approvals}/{len(ballots)} approvals, {rejections} rejections, {vetoes} vetoes."
        )

        result = ReviewQuorumResult(
            rfc_id=rfc_id,
            status=status,
            quorum_reached=quorum_passed,
            total_votes=len(ballots),
            approvals=approvals,
            rejections=rejections,
            vetoes_cast=vetoes,
            ballots=ballots,
            synthesis_summary=summary,
            actionable_directives=directives
        )

        self._process_verdict(rfc_id, rfc_payload, result, author_discipline)
        return result

    def _audit_chaos_qa(self, rfc_payload: Dict[str, Any], preflight_passed: bool) -> DisciplineBallot:
        friction = []
        if not preflight_passed:
            reasons = rfc_payload.get(
                "validation_verdict", {}).get("reasons", [])
            friction.extend(reasons)
            return DisciplineBallot(
                reviewer=DisciplineType.CHAOS_QA,
                vote=ReviewVote.REJECT,
                critique="Pre-flight validation failed. Proposal directly repeats recorded studio regressions.",
                friction_points=friction,
                veto=True
            )

        return DisciplineBallot(
            reviewer=DisciplineType.CHAOS_QA,
            vote=ReviewVote.APPROVE,
            critique="Passed historical regression screening. Negative constraints validated.",
            friction_points=[]
        )

    def _audit_systems(self, changes: Dict[str, Any]) -> DisciplineBallot:
        payload_str = json.dumps(changes).lower()
        if "schema_patch" in changes:
            code = changes["schema_patch"]
            if "(basemodel)" in code.lower() and "(str, enum)" in code.lower():
                if code.find("(BaseModel)") < code.find("(str, Enum)"):
                    return DisciplineBallot(
                        reviewer=DisciplineType.SYSTEMS,
                        vote=ReviewVote.REJECT,
                        critique="Topological breakdown: BaseModel declared before Enum in schema definition.",
                        friction_points=[
                            "Violation of INC-20261027-SYS-04: Enums must strictly precede models."],
                        veto=True
                    )

        return DisciplineBallot(
            reviewer=DisciplineType.SYSTEMS,
            vote=ReviewVote.APPROVE,
            critique="Schema and bytecode evaluation constraints satisfied.",
            friction_points=[]
        )

    def _audit_client(self, changes: Dict[str, Any]) -> DisciplineBallot:
        draw_calls = changes.get("estimated_draw_calls", 10)
        triangles = changes.get("estimated_triangles", 5000)
        parent_hierarchy = changes.get("parent_hierarchy", "").lower()

        friction = []
        is_hard_breach = False

        if draw_calls > 120:
            friction.append(
                f"Exceeds WebGL budget: {draw_calls} draw calls requested (hard ceiling: 120).")
            is_hard_breach = True
        if triangles > 150000:
            friction.append(
                f"Exceeds WebGL budget: {triangles} triangles requested (hard ceiling: 150k).")
            is_hard_breach = True
        if "scene" in parent_hierarchy and "actor" not in parent_hierarchy:
            friction.append(
                "Violation of INC-20261018-CLI-02: Billboard attached directly to global Scene.")
            is_hard_breach = True

        if friction:
            return DisciplineBallot(
                reviewer=DisciplineType.CLIENT,
                vote=ReviewVote.REJECT,
                critique="WebGL client runtime performance or hierarchy invariants breached.",
                friction_points=friction,
                veto=is_hard_breach  # Hard budget breaches trigger a non-negotiable veto
            )

        return DisciplineBallot(
            reviewer=DisciplineType.CLIENT,
            vote=ReviewVote.APPROVE,
            critique="Complies with WebGL budget and scene-graph transform hierarchy.",
            friction_points=[]
        )

        return DisciplineBallot(
            reviewer=DisciplineType.CLIENT,
            vote=ReviewVote.APPROVE,
            critique="Complies with WebGL budget and scene-graph transform hierarchy.",
            friction_points=[]
        )

    def _audit_level(self, changes: Dict[str, Any]) -> DisciplineBallot:
        inset = changes.get("inset_offset", 0.20)
        friction = []
        if "floorplate_dimensions" in changes and inset < 0.15:
            friction.append(
                f"Boundary inset {inset}m is below minimum 0.15m margin.")

        if friction:
            return DisciplineBallot(
                reviewer=DisciplineType.LEVEL,
                vote=ReviewVote.REJECT,
                critique="Insufficient clearance margin risks player entrapment at transition seams.",
                friction_points=friction,
                veto=True
            )

        return DisciplineBallot(
            reviewer=DisciplineType.LEVEL,
            vote=ReviewVote.APPROVE,
            critique="AABB dimensions and socket clearance margins conform to spatial contracts.",
            friction_points=[]
        )

    def _audit_gameplay(self, changes: Dict[str, Any]) -> DisciplineBallot:
        layer_mask = changes.get("layer_mask", "")
        payload_str = json.dumps(changes).lower()

        friction = []
        if ("raycast" in payload_str or "interaction" in payload_str) and "interactionlayer.interactive" not in layer_mask.lower():
            friction.append(
                "Interaction query missing InteractionLayer.INTERACTIVE bitmask.")

        if friction:
            return DisciplineBallot(
                reviewer=DisciplineType.GAMEPLAY,
                vote=ReviewVote.REQUEST_CHANGES,
                critique="Unmasked raycasts risk proximity interception by static environmental hulls.",
                friction_points=friction,
                veto=False
            )

        return DisciplineBallot(
            reviewer=DisciplineType.GAMEPLAY,
            vote=ReviewVote.APPROVE,
            critique="Interaction masks and gameplay mechanics validated.",
            friction_points=[]
        )

    def _audit_narrative(self, rfc_payload: Dict[str, Any]) -> DisciplineBallot:
        summary = rfc_payload.get("summary", "").lower()
        title = rfc_payload.get("title", "").lower()

        forbidden_anachronisms = ["cyber", "neon",
                                  "laser", "spaceship", "submachine"]
        detected = [
            word for word in forbidden_anachronisms if word in summary or word in title]

        if detected:
            return DisciplineBallot(
                reviewer=DisciplineType.NARRATIVE,
                vote=ReviewVote.REJECT,
                critique=f"Canon dissonance detected: Anachronistic terms {detected} in medieval low-fantasy setting.",
                friction_points=[
                    f"Remove anachronistic terms: {', '.join(detected)}"],
                veto=False
            )

        return DisciplineBallot(
            reviewer=DisciplineType.NARRATIVE,
            vote=ReviewVote.APPROVE,
            critique="Thematic lore consistency maintained.",
            friction_points=[]
        )

    def _process_verdict(
        self,
        rfc_id: str,
        rfc_payload: Dict[str, Any],
        verdict: ReviewQuorumResult,
        author_discipline: str
    ) -> None:
        """
        Transitions the RFC file between staging and approved/rejected directories,
        updating discipline competency tallies accordingly.
        """
        source_file = self.staging_dir / f"{rfc_id}.json"
        enriched_payload = {
            **rfc_payload,
            "review_verdict": verdict.model_dump(mode="json")
        }

        if verdict.quorum_reached:
            dest_file = self.approved_dir / f"{rfc_id}.json"
            with open(dest_file, "w", encoding="utf-8") as f:
                json.dump(enriched_payload, f, indent=2)
            if source_file.exists():
                source_file.unlink()

            # Increment clean streak and accepted RFC count
            disc_enum = next(
                (d for d in DisciplineType if d.value == author_discipline), None)
            if disc_enum:
                self.memory.record_successful_sprint(disc_enum)
            logger.info(f"[QUORUM APPROVED] RFC {rfc_id} moved to {dest_file}")
        else:
            dest_file = self.rejected_dir / f"{rfc_id}.json"
            with open(dest_file, "w", encoding="utf-8") as f:
                json.dump(enriched_payload, f, indent=2)
            if source_file.exists():
                source_file.unlink()
            logger.warning(
                f"[QUORUM REJECTED] RFC {rfc_id} moved to {dest_file}")


class VirtualStudioEngine:
    """
    Main director orchestrating autonomous production cycles, standups,
    RFC processing, and milestone progress.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)
        self.review_board = HighFrictionReviewBoard(
            workspace_root=self.workspace_root, memory=self.memory)

    def process_all_staged_rfcs(self) -> List[ReviewQuorumResult]:
        """Audits all RFC files currently sitting in build/staging/rfcs/."""
        staged_files = list(
            (self.workspace_root / "build" / "staging" / "rfcs").glob("*.json"))
        results = []

        if not staged_files:
            logger.info("No staged RFCs to review.")
            return results

        logger.info(
            f"Convening Review Board for {len(staged_files)} staged RFCs...")
        for rfc_file in staged_files:
            try:
                with open(rfc_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                result = self.review_board.evaluate_rfc(payload)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate RFC {rfc_file.name}: {e}")

        return results


if __name__ == "__main__":
    engine = VirtualStudioEngine()
    results = engine.process_all_staged_rfcs()
    print(
        f"\n--- REVIEW BOARD HARNESS COMPLETED ({len(results)} RFCs processed) ---")
    for res in results:
        print(f"RFC: {res.rfc_id} | Status: {res.status} | Approvals: {res.approvals}/{res.total_votes} | Vetoes: {res.vetoes_cast}")
        if res.actionable_directives:
            for directive in res.actionable_directives:
                print(f"  * {directive}")
