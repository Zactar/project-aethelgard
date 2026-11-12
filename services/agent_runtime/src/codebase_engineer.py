"""
services/agent_runtime/src/codebase_engineer.py
Universal Multi-Agent Studio: Cohesive Milestone Plugin Engineer
Features:
- Cohesive 1-call per-milestone plugin synthesis (web_client/js/milestone_<ver>.js)
- Flat-token cross-milestone state & interface digest
- Node.js vm.runInContext headless sandbox with 1-pass closed-loop self-healing
"""

import os
import sys
import json
import logging
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
from services.agent_runtime.src.llm_gateway import LLMGateway

logger = logging.getLogger("Studio.CodebaseEngineer")
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


MICROKERNEL_CONTRACT = """
- AESTHETICS, GRAPHICS & ARTICULATED ANIMATION MANDATE: NEVER render characters, monsters, or shrines as plain circles or rectangles! Every entity must be drawn as a multi-part articulated dark-fantasy silhouette with procedural animation (`Math.sin(t * 8)` stride bob, breathing torso scale, held weapon/shield orientation, and glowing eyes/runes).
- UI/UX ERGONOMICS & Z-ORDER MANDATE: NEVER draw world entities over item/lore tooltips—defer all tooltips to `state.world.activeTooltip` rendered in the final Z-pass! De-collide floating combat texts spatially and throttle periodic ground DoT popups (`>= 0.7s` cooldown) so text never stacks into an illegible smudge.
- CONTEXT-AWARE SCREEN SHAKE & STEADY HUD LAW: Apply cameraShake translations ONLY inside `ctx.save()...ctx.restore()` around world-space playfield rendering. Always call `ctx.setTransform(1,0,0,1,0,0)` before drawing the top status ribbon (`y: 0..36`) so UI text never shakes or clips past `x = 800`.
- INTERACTIVE CHARACTER CUSTOMIZATION LAW: When building RPG Character Creation modals, include interactive customization (live `[R]` stat dice re-rolling, point allocation, background pacts, and weapon loadout toggles) rather than a static selector.
- ESCALATING WAVE SEQUENCING & BOSS PACING LAW (MANDATORY):
  Never spawn endgame bosses (`v0.5.0`) or all elite enemy types (`v0.4.0`) immediately on Wave 1!
  - Wave 1 (`state.world.wave === 1`): Foundational core hazards only (`v0.1.0`) so the player masters controls.
  - Wave 2–4 (`state.world.wave >= 2`): Gradually introduce environmental anomalies, hunter squadrons, and mid-run upgrade drafts.
  - Wave 5+ (`state.world.wave >= 5`): Gate boss encounters strictly behind `state.world.wave >= 5` with a warning telegraph!
- SINGLE-OWNER CONTROL MUTATION LAW:
  Only Milestone `v0.1.0` may apply continuous movement/rotation physics (`keys.up`, `keys.left`, `keys.right`, `keys.down`), and only Milestone `v0.2.0` may bind `[SHIFT/E]` (`keys.action`) specials. Later milestones (`v0.3.0+`) MUST NOT add competing velocity impulses (`player.vx += ...`) to movement or fire keys!

- CANONICAL STUDIO KEYBOARD & CONTROL SCHEME STANDARD (MANDATORY):
  Never invent obscure keys or conflicting key bindings across milestones! Every module MUST adhere to this unified control map on `state.keys`:
  1. `state.keys.left` / `state.keys.right` (`ArrowLeft`/`ArrowRight` or `A`/`D`): Steering / Angular Rotation / Menu Card Cycle.
  2. `state.keys.up` (`ArrowUp` or `W`): Forward Thrust / Primary Acceleration.
  3. `state.keys.down` (`ArrowDown` or `S`): Retro-Brake / Inertial Dampener / Crouch.
  4. `state.keys.jump` (`Space`): Primary Weapon Fire (continuous while held) AND Menu Confirm / Replay Reset when a modal is open.
  5. `state.keys.action` (`Shift` or `E`): Unified Special Ability / Dash-Parry Trigger. If multiple milestones add active abilities, trigger them together harmoniously on `state.keys.action` rather than binding new keys!
  6. `state.keys.digit1`..`digit4` (`1`..`4`): Instant Card / Upgrade / Pilot Selection in modals.
  7. MENU SCENE ISOLATION: Always begin `update(dt, state)` and `render(ctx, state)` in combat/hazard/boss modules (`v0.3.0+`) with `if (state.paused) return;` (unless that module is currently rendering the active modal) so enemies, bosses, and projectiles NEVER move or draw over Character Select, Upgrade Draft, or Game Over screens!

- HUD NUMBER FORMATTING & WARM SFX DSP: Always format HUD scores as integers (`Math.floor(state.score)`) and multipliers to at most 1 decimal place (`combo.toFixed(1)`). Keep laser/combat SFX warm and punchy by keeping oscillator frequencies below `650Hz` with low gain (`<= 0.06`) so SFX never sound shrill.
UNIVERSAL GAME DESIGN, KINETIC JUICE & AUDIO DSP CHARTER:
- DIEGETIC WORLD MECHANICS OVER UI TEXT: Never add static text/number boxes to represent new features. Every feature must manifest visually and interactively inside the 2D playfield (animated sprites, terrain hazards, collectibles, boss attacks, weather particles, or active player abilities).
- COORDINATE SPACE CONSISTENCY: Inspect loaded modules before spawning entities. Match the base module's coordinate system (e.g., if the player stays near a fixed screen Y while world objects scroll upward, spawn new world objects in that exact scrolling screen-space).
- KINETIC GAME FEEL ("JUICE"): Use smooth velocity damping, particle bursts on collisions/pickups, floating score/status popups (`state.world.floatingTexts`), and brief `state.world.cameraShake` impulses on heavy impacts.
- GENRE-ADAPTIVE SPATIAL GRID, POINTER & KEYBOARD ERGONOMICS:
  1. Dual Input Support (Mouse Pointer + Keyboard): For grid, board, or tactical arena games, ALWAYS support BOTH mouse hover/click (`state.pointer.x`, `state.pointer.y`, `state.pointer.clicked` or `POINTER_DOWN` event) AND keyboard cursor navigation (`WASD`/`Arrow` keys to move the active cell highlight + `Space`/`Enter` to confirm).
  2. Crisp State Transitions & Turn Arbitration: In turn-based or round-based games, maintain an explicit state machine (`PLAYER_TURN`, `AI_THINKING`, `ROUND_OVER`) with a brief `0.35s` visual delay before the AI places its move so the player can read the board state clearly.
  3. Tactile Geometric "Juice": Animate newly placed symbols with scale/alpha interpolation (`0.0 -> 1.0`), emit radial particle sparks on placement, draw a glowing vector beam across winning alignments, and allow instant `[SPACE]` or click rematch when a round ends.
- PROCEDURAL WEB AUDIO DSP: For continuous movement/wind/engine/water sounds, synthesize a Web Audio API white-noise buffer routed through a `BiquadFilterNode` (bandpass/lowpass) modulated by speed; use harmonic `sine`/`triangle` arpeggios for positive feedback chimes.

UNIVERSAL STUDIOENGINE MICROKERNEL CONTRACT (800x600 Canvas):
Register one cohesive module using:
window.StudioEngine.registerModule("Milestone_vX_Y_Z", {
  init: function(state, engine) { /* initialize state properties */ },
  update: function(dt, state, engine) { /* dt in seconds; update physics & logic */ },
  render: function(ctx, state, engine) { /* draw to 800x600 ctx */ }
});

SHARED BLACKBOARD (`state` / `window.StudioEngine.state`):
- state.running (bool), state.paused (bool), state.tick (int), state.dt (float), state.score (int)
- state.player: { x: 400, y: 220, vx: 0, vy: 0, width: 24, height: 32, angle: 0, z: 0, vz: 0, isAirborne: false, state: 'IDLE', health: 3, maxHealth: 3, wipeouts: 0, cooldown: 0 }
- state.stats: { level: 1, xp: 0, nextLevelXp: 100, unspentPoints: 0, combo: 1, attributes: { VEL: 10, AGI: 10, BAL: 10, MOX: 10, LCK: 10 }, characterClass: null }
- state.inventory: { items: [], relics: [], currency: 0, pendingDraft: null }
- state.world (alias state.level): { distance: 0, speed: 0, cameraX: 0, cameraY: 0, cameraShake: 0, biome: 'DEFAULT', entities: [], obstacles: [], gates: [], particles: [] }
- state.keys: { up, down, left, right, jump, action, map, digit1, digit2, digit3, digit4 }
- state.pointer: { x, y, clicked }
- Events: engine.on("EVENT_NAME", (payload, state) => {}) and engine.emit("EVENT_NAME", payload)

CRITICAL RULES & HUD SPATIAL ZONES:
1. Keep code concise (<120 lines), modular, and 100% self-contained. For large item/relic/entity databases (e.g. 50-100+ items), NEVER write verbose multi-line objects per item; use compact tuple arrays or combinatorial prefix+base generators to synthesize 100+ items in <25 lines.
2. STRICT HUD DOCKING CONTRACT & Z-ORDER RULES (Never overlap prior milestone HUD bars!):
   - Always call `ctx.save()`, set `ctx.textAlign = 'left'`, and call `ctx.restore()` in `render()`.
   - Top Bar `y: 0..42` is RESERVED for v0.1.0 (Speed, Distance, Health).
   - Top-Left Dock `x: 12..250, y: 46..86` is RESERVED for v0.2.0 (Class, Level, XP Bar).
   - Bottom-Left Dock `x: 12..345, y: 536..588` is RESERVED for v0.3.0 (Equipped Gear & Active Gadget).
   - Top-Right Dock `x: 580..788, y: 46..106` is RESERVED for v0.4.0 (Biome, Grip, Relics).
   - Bottom-Right Dock `x: 520..788, y: 536..588` is RESERVED for v0.5.0 (Yeti Proximity Radar, Audio Status, High Score).
   - GAME DESIGN LAW FOR v0.6.0+: All 4 HUD corners are 100% FULL. DO NOT draw any new HUD rectangles or telemetry panels! Render all v0.6.0+ features diegetically in world space on the slope (sprites, ramps, bosses, particles, projectiles).
   - NEVER open a modal if `state.paused === true` is already locked by another milestone.
   - Top Bar `y: 0..42` is RESERVED for v0.1.0 (Speed, Distance, Health/Wipeouts).
   - Sub-Top Left `x: 16..320, y: 48..84` is RESERVED for v0.2.0 (Class, Level, XP Bar, Combo).
   - Sub-Top Right `x: 520..784, y: 48..110` is RESERVED for v0.3.0+ (Equipped Relics, Active Cooldown, Shelter Distance).
   - Modal Overlays (Class Select, Level-Up, 500m Shelter Draft) must set `state.paused = true` while open and unpause (`state.paused = false`) upon selection.
3. Always initialize any custom arrays/objects on `state` inside `init(state)` before reading them in `update` or `render`.
4. Output ONLY valid, raw JavaScript code. No markdown fences, no prose.
"""


class CodebaseEngineerAgent:
    def __init__(self, workspace_root: Optional[Path] = None, memory: Optional[StudioRetrospectiveMemory] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = memory or StudioRetrospectiveMemory(workspace_root=self.workspace_root)
        self.node_bin = shutil.which("node")
        self.applied_rfcs_file = self.workspace_root / "build" / "staging" / "applied_rfcs.json"
        self.applied_rfcs_file.parent.mkdir(parents=True, exist_ok=True)
        self.gateway = LLMGateway(workspace_root=self.workspace_root)

    def _get_applied_rfcs(self) -> List[str]:
        if self.applied_rfcs_file.exists():
            try:
                return json.loads(self.applied_rfcs_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _mark_rfcs_applied(self, rfc_ids: List[str]) -> None:
        applied = self._get_applied_rfcs()
        for rfc_id in rfc_ids:
            if rfc_id not in applied:
                applied.append(rfc_id)
        self.applied_rfcs_file.write_text(json.dumps(applied, indent=2), encoding="utf-8")

    def _extract_v1_blackboard_schema(self) -> str:
        """
        Scans milestone_v0_1_0.js to extract state.player, state.world, AND nested
        sub-object properties (like state.world.lattice.*) so v0.2.0+ plugins never guess wrong names.
        """
        v1_file = self.workspace_root / "web_client" / "js" / "milestone_v0_1_0.js"
        if not v1_file.exists():
            return "Foundational v0.1.0 milestone: establish clean properties on state.player and state.world."
        code = v1_file.read_text(encoding="utf-8")
        p_props = sorted(list(set(re.findall(r"(?:state\.player|st\.player|\bp)\.([a-zA-Z0-9_]+)", code))))
        w_props = sorted(list(set(re.findall(r"(?:state\.world|st\.world|\bw)\.([a-zA-Z0-9_]+)", code))))
        lat_props = sorted(list(set(re.findall(r"(?:lattice|\blat)\.([a-zA-Z0-9_]+)", code))))
        nested_line = f"- state.world.lattice properties in v0.1.0: {lat_props}\n" if lat_props else ""
        return (
            "LOCKED v0.1.0 BLACKBOARD SCHEMA (YOU MUST REUSE THESE EXACT PROPERTY NAMES):\n"
            f"- state.player properties in v0.1.0: {p_props}\n"
            f"- state.world properties in v0.1.0: {w_props}\n"
            f"{nested_line}"
            "- Shared Engine Array Aliases: `state.world.lasers === state.world.bullets === state.world.projectiles` "
            "and `state.world.asteroids === state.world.rocks === state.world.obstacles`."
        )

    def _extract_prior_modules_summary(self) -> str:
        """
        Builds a token-bounded context of existing milestone plugins:
        Includes v0.1.0 base code + compact interface digests of subsequent milestones.
        """
        js_dir = self.workspace_root / "web_client" / "js"
        if not js_dir.exists():
            return "No prior milestone modules registered yet (Foundational v0.1.0 milestone)."
        files = sorted(js_dir.glob("*.js"))
        if not files:
            return "No prior milestone modules registered yet."

        summaries = []
        for idx, f in enumerate(files):
            content = f.read_text(encoding="utf-8")
            if idx == 0 or idx == len(files) - 1:
                # Include source for base v0.1.0 and the immediately preceding milestone
                summaries.append(f"// --- LOADED MODULE: {f.name} ---\n{content[:2500]}")
            else:
                mods = re.findall(r'registerModule\(\s*["\']([^"\']+)["\']', content)
                events = list(set(re.findall(r'engine\.(?:on|emit)\(\s*["\']([^"\']+)["\']', content)))
                props = sorted(list(set(re.findall(r'state\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?', content))))[:20]
                summaries.append(f"// --- DIGEST OF {f.name}: Modules={mods}, Events={events}, StateProps={props} ---")
        return "\n\n".join(summaries)

    def implement_approved_rfcs(
        self,
        review_results: Optional[List[Any]] = None,
        active_version: Optional[str] = None
    ) -> int:
        approved_dir = self.workspace_root / "build" / "rfcs" / "approved"
        if not approved_dir.exists():
            return 0

        applied_rfcs = self._get_applied_rfcs()
        pending_rfc_data: List[Dict[str, Any]] = []
        already_applied_count = 0

        for f in sorted(approved_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                tag = data.get("milestone_tag") or data.get("target_milestone") or data.get("milestone_target")
                if active_version and tag != active_version:
                    continue
                rfc_id = data.get("rfc_id", f.stem)
                if rfc_id in applied_rfcs:
                    already_applied_count += 1
                    continue
                pending_rfc_data.append(data)
            except Exception as e:
                logger.warning(f"Could not read approved RFC {f.name}: {e}")

        if not pending_rfc_data:
            return already_applied_count

        milestone_ver = active_version or pending_rfc_data[0].get("milestone_tag", "v0.1.0")
        rfc_ids = [r.get("rfc_id", "RFC") for r in pending_rfc_data]

        logger.info(
            f"[CodebaseEngineer] Batch-synthesizing {len(pending_rfc_data)} approved RFCs for Milestone {milestone_ver} in 1 cohesive LLM call..."
        )

        if self._synthesize_cohesive_milestone_plugin(milestone_ver, pending_rfc_data):
            self._mark_rfcs_applied(rfc_ids)
            self._git_commit("web_client/", f"auto(studio): implement Milestone {milestone_ver} ({len(rfc_ids)} RFCs)")
            return already_applied_count + len(pending_rfc_data)

        return already_applied_count

    def _sanitize_code(self, raw_text: str) -> str:
        text = raw_text.strip()
        match = re.search(r"```(?:javascript|js)?\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        # Automatically guard dotted `.push(` calls against undefined arrays
        text = re.sub(
            r"(?<![a-zA-Z0-9_$\.\(\)])([a-zA-Z_$][a-zA-Z0-9_$]*(?:\.[a-zA-Z_$][a-zA-Z0-9_$]*)+)\.push\(",
            lambda m: f"({m.group(1)} || ({m.group(1)} = [])).push(",
            text
        )
        return text

    def _verify_full_stack_in_sandbox(self, candidate_file: Path, candidate_code: str) -> Tuple[bool, str]:
        """
        Executes the actual web_client/index.html microkernel + all prior plugins + candidate_code
        and asserts 0 uncaught exceptions AND 0 isolated faults in window.__STUDIO_ERRORS__.
        """
        from tools.validate_webapp import run_headless_microkernel_audit
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as cand_tf:
            cand_tf.write(candidate_code)
            cand_path = cand_tf.name
        try:
            passed, msg = run_headless_microkernel_audit(extra_plugin_path=cand_path)
            if not passed:
                logger.warning(f"[SandboxGuard] Candidate failed real-microkernel audit:\n{msg}")
            return passed, msg
        finally:
            if os.path.exists(cand_path):
                os.unlink(cand_path)

    def _synthesize_cohesive_milestone_plugin(self, milestone_ver: str, rfcs: List[Dict[str, Any]]) -> bool:
        js_dir = self.workspace_root / "web_client" / "js"
        js_dir.mkdir(parents=True, exist_ok=True)
        safe_ver = re.sub(r"[^a-zA-Z0-9_]", "_", milestone_ver)
        plugin_filename = f"milestone_{safe_ver}.js"
        plugin_path = js_dir / plugin_filename

        prior_summary = self._extract_v1_blackboard_schema() + "\n\n" + self._extract_prior_modules_summary()
        gdd_path = self.workspace_root / "projects" / "inbox" / "GDD.md"
        gdd_excerpt = gdd_path.read_text(encoding="utf-8")[:1500] if gdd_path.exists() else ""

        specs_block = []
        for r in rfcs:
            disc = r.get("discipline", "Systems")
            title = r.get("title", "")
            spec = r.get("technical_specification") or r.get("payload_diff", {}).get("technical_specification", "")
            specs_block.append(f"### [{disc}] {title}\n{spec}")
        combined_specs = "\n\n".join(specs_block)

        eng_card = self.memory.get_training_directive("Codebase_Engineer") if hasattr(self.memory, "get_training_directive") else ""
        system_prompt = (
            eng_card + "\n\nYou are the Lead Systems & Gameplay Integration Architect in an autonomous game studio.\n"
            "Synthesize a single, concise, cohesive, bug-free JavaScript plugin file implementing all deliverables for the active milestone.\n"
            + MICROKERNEL_CONTRACT
        )

        user_prompt = f"""ACTIVE MILESTONE: {milestone_ver}

GAME OVERVIEW EXCERPT:
{gdd_excerpt}

EXISTING WORKSPACE MODULES (ALREADY LOADED):
{prior_summary}

DELIVERABLE SPECIFICATIONS TO IMPLEMENT IN THIS MILESTONE:
{combined_specs}

Write the complete JavaScript code for `web_client/js/{plugin_filename}` using `window.StudioEngine.registerModule(...)`."""

        js_code = self._sanitize_code(self.gateway.complete(system_prompt, user_prompt, temperature=0.1))
        if not js_code or "registerModule" not in js_code:
            logger.error(f"[CodebaseEngineer] Invalid or truncated module code returned for {milestone_ver}.")
            return False

        passed, err_trace = self._verify_full_stack_in_sandbox(plugin_path, js_code)
        if not passed:
            logger.info(f"[Self-Healer] Attempting 1-pass autonomous repair for {plugin_filename}...")
            repair_prompt = (
                f"Your previous JavaScript module for {milestone_ver} threw this error in the headless Node VM sandbox:\n"
                f"{err_trace}\n\n"
                f"BROKEN CODE:\n{js_code}\n\n"
                "Fix the bug and output ONLY the corrected, complete raw JavaScript module."
            )
            js_code = self._sanitize_code(self.gateway.complete(system_prompt, repair_prompt, temperature=0.1))
            passed, err_trace = self._verify_full_stack_in_sandbox(plugin_path, js_code)
            if not passed:
                logger.error(f"[CodebaseEngineer] Self-healing failed for {plugin_filename}. Aborting commit.")
                return False

        header = f"// Cohesive Milestone Plugin: {milestone_ver}\n"
        plugin_path.write_text(header + js_code + "\n", encoding="utf-8")
        logger.info(f"[CodebaseEngineer] Verified & wrote cohesive milestone plugin: web_client/js/{plugin_filename}")

        index_path = self.workspace_root / "web_client" / "index.html"
        if index_path.exists():
            html = index_path.read_text(encoding="utf-8")
            script_tag = f'  <script src="js/{plugin_filename}"></script>'
            if script_tag not in html and "</body>" in html:
                html = html.replace("</body>", f"{script_tag}\n</body>")
                index_path.write_text(html, encoding="utf-8")
                logger.info(f"[CodebaseEngineer] Attached {plugin_filename} to web_client/index.html")

        return True

    def _git_commit(self, relative_path: str, message: str) -> None:
        try:
            subprocess.run(["git", "add", relative_path], cwd=self.workspace_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.workspace_root, check=True, capture_output=True)
            logger.info(f"[Git] Committed: {message}")
        except subprocess.CalledProcessError:
            pass
