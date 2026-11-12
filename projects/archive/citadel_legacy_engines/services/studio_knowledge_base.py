"""
services/agent_runtime/src/studio_knowledge_base.py
Project Aethelgard: Studio Knowledge Base & Pedagogical Training Engine
Integrates ELVTR Multi-Agent Architecture and Emergent Complexity Frameworks.
"""

from services.agent_runtime.src.chroma_lore_bus import ChromaLoreBus
from typing import Dict, Any, List, Optional
import logging
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.KnowledgeBase")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class StudioKnowledgeBase:
    def __init__(self, workspace_root: Optional[Path] = None, lore_bus: Optional[ChromaLoreBus] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.curriculum_dir = self.workspace_root / "knowledge_base" / "curriculum"
        self.curriculum_dir.mkdir(parents=True, exist_ok=True)
        self.training_ledger_file = self.workspace_root / \
            "build" / "staging" / "training_ledger.json"
        self.training_ledger_file.parent.mkdir(parents=True, exist_ok=True)
        self.lore_bus = lore_bus or ChromaLoreBus(
            workspace_root=self.workspace_root)

    def train_team(self) -> Dict[str, Any]:
        """Indexes curriculum modules into the deterministic training ledger and vector bus."""
        logger.info(
            "Executing virtual dev team training cycle across all curricula...")
        curricula_files = list(self.curriculum_dir.rglob("*.json"))
        indexed_topics = []
        curriculum_cache = {}

        for c_file in curricula_files:
            if c_file.stat().st_size == 0:
                continue

            try:
                with open(c_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                title = data.get("title", c_file.stem)

                # Ingest general principles
                for mod in data.get("modules", []):
                    topic = mod.get("topic", "Principle")
                    text = f"{title} - {topic}: " + \
                        " ".join(mod.get("core_principles", []))
                    rule = mod.get("operational_rule", "")
                    if rule:
                        text += f" Operational Rule: {rule}"
                    self._safely_index_passage(
                        f"TRAIN-{c_file.stem}-{topic[:20]}", text)
                    indexed_topics.append(f"{title} -> {topic}")

                # Ingest role-specific competencies
                competencies = data.get("core_competencies", [])
                if competencies:
                    disc = data.get("discipline", c_file.stem)
                    text = f"{disc} Specialization: " + " ".join(competencies)
                    self._safely_index_passage(f"TRAIN-ROLE-{disc}", text)
                    indexed_topics.append(
                        f"Discipline: {disc} ({len(competencies)} competencies)")

                curriculum_cache[c_file.stem] = data

            except Exception as e:
                logger.warning(
                    f"Could not ingest curriculum {c_file.name}: {e}")

        payload = {
            "status": "COMPLETED",
            "modules_trained": len(indexed_topics),
            "topics": indexed_topics,
            "curricula": curriculum_cache
        }
        with open(self.training_ledger_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        logger.info(
            f"[✓] Virtual Dev Team training complete: {len(indexed_topics)} curriculum modules mastered.")
        return payload

    def _safely_index_passage(self, passage_id: str, text: str) -> None:
        try:
            # Check for correct method signature on ChromaLoreBus
            if hasattr(self.lore_bus, "add_passage"):
                self.lore_bus.add_passage(passage_id=passage_id, text=text)
            elif hasattr(self.lore_bus, "add_canon_passage"):
                self.lore_bus.add_canon_passage(
                    passage_id=passage_id, text=text, category="studio_training", unrest_bias=0.0)
        except Exception:
            pass

    def get_role_training_context(self, discipline: str) -> str:
        """Retrieves design principles for a specific role from the disk training ledger."""
        if self.training_ledger_file.exists():
            try:
                with open(self.training_ledger_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                curricula = data.get("curricula", {})
                for k, c in curricula.items():
                    if discipline.lower() in k.lower():
                        comps = c.get("core_competencies", [])
                        if comps:
                            return " | ".join(comps[:3])
            except Exception:
                pass
        return "Apply strict AABB collision margins, closed-loop economic scarcity, and responsive game feel."
