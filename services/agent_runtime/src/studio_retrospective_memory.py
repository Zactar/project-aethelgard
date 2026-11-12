"""
services/agent_runtime/src/studio_retrospective_memory.py
Project Aethelgard: Inter-Project Post-Mortem & Role-Training Engine.
Conducts codebase/telemetry autopsies at the conclusion of a game project,
distills actionable Game Design & Engineering Skill Cards per discipline,
and persists them to `projects/studio_skill_cards.json` to level up the team across games.
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

from services.agent_runtime.src.llm_gateway import LLMGateway

logger = logging.getLogger("Aethelgard.Memory")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


DEFAULT_SKILL_CARDS: Dict[str, Any] = {
    "version": 1,
    "projects_completed": [],
    "global_studio_tenets": [
        "ACTION-CONSEQUENCE GAMEPLAY LOOP: Every feature must give the player an active decision, timing challenge, or spatial hazard to react to. Never substitute passive numbers or fake telemetry for gameplay.",
        "DIEGETIC VISUALS OVER HUD BOXES: Keep the playfield unobstructed. Represent status, buffs, and hazards directly on sprites, terrain, and world particles rather than adding rectangular HUD panels.",
        "COORDINATE & STATE CONTINUITY: Inspect how Milestone v0.1.0 updates player/world coordinates and health/wipeouts before writing v0.2.0+ logic. Never latch state variables with `d = d || val`.",
        "DEFENSIVE INITIALIZATION: Initialize all custom arrays and sub-objects on `StudioEngine.state` inside `init(state)` before reading or `.push()`ing in `update()`."
    ],
    "role_skill_cards": {
        "Executive_Producer": (
            "Chart milestones around interactive verbs (dodge, vault, grapple, reflect, transmute) and distinct enemy/terrain archetypes. "
            "Ban 'telemetry dashboards', 'altimeters', or passive stat counters as milestone deliverables."
        ),
        "Systems": (
            "Design tight risk-reward economies and synergetic item/upgrade modifiers that visibly alter player physics, projectiles, or hazard behavior. "
            "Use compact tuple tables to define large item catalogs in <25 lines."
        ),
        "Gameplay": (
            "Prioritize responsive controls, state-machine clarity, hit-stop/camera-shake feedback, and clear collision hitboxes. "
            "Ensure active abilities have visible on-screen effects and intuitive key bindings."
        ),
        "Level": (
            "Build dynamic spatial pacing: alternate high-intensity hazard clusters with brief recovery windows, interactive terrain features (ramps, destructibles, currents), and telegraph boss attacks clearly."
        ),
        "Client": (
            "Maintain a single, clean top HUD bar from v0.1.0. For v0.2.0+, never add new floating stat rectangles; render diegetic world effects, weather particles, sprite animations, and procedural Web Audio (filtered noise + harmonic chimes)."
        ),
        "Aesthetics": "Ban flat primitive circles/squares for characters, enemies, and props. Build multi-part articulated silhouettes with procedural animation keyframes (idle breathing, stride bob, weapon windup/follow-through, cape/robe sway) and cohesive chiaroscuro lighting/color grading.",
        "UI_UX": "Enforce strict Z-layer hierarchy: world-space tooltips must render in a post-entity pass so sprites never occlude text. De-collide floating combat numbers spatially, throttle DoT tick popups, and fold quest/alignment trackers into the top ribbon.",
        "Narrative": (
            "Deliver punchy, atmospheric flavor text inside existing draft cards and endgame run obituaries without cluttering active gameplay."
        ),
        "Codebase_Engineer": (
            "Ensure 100% compatibility with loaded milestone_*.js modules. Reuse existing state properties (`state.player`, `state.world`, `state.stats`), respect `state.paused`, and never draw overlapping UI panels."
        )
    },
    "postmortem_history": []
}


class StudioRetrospectiveMemory:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.skill_cards_file = self.workspace_root / "projects" / "studio_skill_cards.json"
        self.legacy_memory_file = self.workspace_root / "build" / "memory" / "retrospective_ledger.json"
        self.skill_cards_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.skill_cards_file.exists():
            self._save_cards(DEFAULT_SKILL_CARDS)

    def _load_cards(self) -> Dict[str, Any]:
        if self.skill_cards_file.exists():
            try:
                return json.loads(self.skill_cards_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return dict(DEFAULT_SKILL_CARDS)

    def _save_cards(self, data: Dict[str, Any]) -> None:
        self.skill_cards_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record_clean_sprint(self, discipline: str, milestone: str) -> None:
        pass

    def get_training_directive(self, role: Optional[str] = None) -> str:
        """Returns compact institutional memory (~180 tokens) for injection into LLM system prompts."""
        cards = self._load_cards()
        tenets = "\n".join(f"- {t}" for t in cards.get("global_studio_tenets", [])[:4])
        role_map = cards.get("role_skill_cards", {})
        if role and role in role_map:
            return f"STUDIO LESSONS LEARNED:\n{tenets}\nROLE MASTERY ({role}): {role_map[role]}"
        all_roles = "\n".join(f"- [{k}]: {v}" for k, v in role_map.items())
        return f"STUDIO INSTITUTIONAL MEMORY & LESSONS LEARNED:\n{tenets}\n\nDISCIPLINE SKILL CARDS:\n{all_roles}"

    def conduct_project_retrospective(self, use_llm: bool = True) -> Dict[str, Any]:
        """
        Audits the current project's milestones, code patterns, and design quality,
        then updates `projects/studio_skill_cards.json` to train the team for the next game.
        """
        active_proj_file = self.workspace_root / "projects" / "active_project.json"
        proj_title = "Unknown Project"
        if active_proj_file.exists():
            try:
                proj_title = json.loads(active_proj_file.read_text(encoding="utf-8")).get("title", proj_title)
            except Exception:
                pass

        js_dir = self.workspace_root / "web_client" / "js"
        js_files = sorted(js_dir.glob("*.js")) if js_dir.exists() else []
        code_metrics = {
            "project_title": proj_title,
            "milestone_plugins_count": len(js_files),
            "total_js_lines": sum(len(f.read_text(encoding="utf-8").splitlines()) for f in js_files),
            "hud_fillrect_calls": sum(len(re.findall(r"fillRect\(", f.read_text(encoding="utf-8"))) for f in js_files)
        }

        cards = self._load_cards()
        if not use_llm or proj_title in cards.get("projects_completed", []):
            logger.info(f"[Studio Training] Project '{proj_title}' already trained in studio_skill_cards.json ($0.00).")
            return cards
        gateway = LLMGateway(workspace_root=self.workspace_root)

        if use_llm and gateway.is_live() and js_files:
            logger.info(f"[Studio Training] Convening Post-Mortem & Role Training Council for '{proj_title}'...")
            sample_code = "\n".join(
                f"// {f.name}:\n" + "\n".join(f.read_text(encoding="utf-8").splitlines()[:35])
                for f in js_files[-3:]
            )
            sys_prompt = (
                "You are the Studio Director conducting an End-of-Project Post-Mortem & Role Training session.\n"
                "Critique the outgoing project's code & design mistakes (such as over-reliance on static HUD text boxes instead of "
                "interactive diegetic gameplay mechanics, coordinate mismatches, or state desyncs) and refine the studio's "
                "concise Role Skill Cards (<45 words per role) so the team builds vastly better games next time."
            )
            user_prompt = f"""COMPLETED PROJECT: {proj_title}
METRICS: {json.dumps(code_metrics)}
RECENT MILESTONE CODE EXCERPTS:
{sample_code[:2200]}

CURRENT SKILL CARDS:
{json.dumps(cards.get("role_skill_cards", {}), indent=2)}

Respond ONLY with a valid JSON object matching this schema:
{{
  "postmortem_summary": "2-sentence candid critique of what went well and what must improve in the next game.",
  "key_mistakes_corrected": ["Mistake 1 -> Fix", "Mistake 2 -> Fix", "Mistake 3 -> Fix"],
  "updated_role_skill_cards": {{
    "Executive_Producer": "<45 word directive>",
    "Systems": "<45 word directive>",
    "Gameplay": "<45 word directive>",
    "Level": "<45 word directive>",
    "Client": "<45 word directive>",
    "Narrative": "<45 word directive>",
    "Aesthetics": "<45 word directive>",
    "UI_UX": "<45 word directive>",
    "Codebase_Engineer": "<45 word directive>"
  }}
}}"""
            raw = gateway.complete(sys_prompt, user_prompt, temperature=0.2)
            try:
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    if isinstance(parsed.get("updated_role_skill_cards"), dict):
                        cards["role_skill_cards"].update(parsed["updated_role_skill_cards"])
                    postmortem_entry = {
                        "project": proj_title,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metrics": code_metrics,
                        "summary": parsed.get("postmortem_summary", "Completed post-mortem analysis."),
                        "mistakes_corrected": parsed.get("key_mistakes_corrected", [])
                    }
                    cards.setdefault("postmortem_history", []).append(postmortem_entry)
            except Exception as e:
                logger.warning(f"[Studio Training] Fallback to baseline skill cards: {e}")

        if proj_title not in cards.get("projects_completed", []):
            cards.setdefault("projects_completed", []).append(proj_title)
        cards["version"] = cards.get("version", 1) + 1
        self._save_cards(cards)
        logger.info(f"[✓] Persisted upgraded Studio Skill Cards (v{cards['version']}) to {self.skill_cards_file}")
        return cards
