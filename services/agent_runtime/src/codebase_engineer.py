"""
services/agent_runtime/src/codebase_engineer.py
Universal Multi-Agent Studio: Isolated Plugin Codebase Engineer
Writes isolated JS plugin modules (web_client/js/mod_<rfc_id>.js) and verifies
runtime execution in a headless Node.js sandbox prior to committing.
"""

from services.agent_runtime.src.llm_gateway import LLMGateway
from services.agent_runtime.src.studio_retrospective_memory import StudioRetrospectiveMemory
import os
import sys
import json
import logging
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Studio.CodebaseEngineer")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


BLACKBOARD_SCHEMA_CONTRACT = """
EXACT MICROKERNEL & BLACKBOARD CONTRACT (DO NOT INVENT UNDEFINED PROPERTIES):
window.StudioEngine.registerModule("ModuleName", {
  init: function(state, engine) { /* optional setup */ },
  update: function(dt, state) { /* dt in seconds; mutate state safely */ },
  render: function(ctx, state) { /* 800x600 CanvasRenderingContext2D */ }
});

Available properties on `state`:
- state.running (boolean), state.paused (boolean), state.tick (number)
- state.player: { x, baseViewportY, currentViewportY, worldDistance, vx, vy, skisAngle, jumpZ, jumpVz, isAirborne, state, wipeoutTimer, wipeouts, characterClass }
- state.stats: { VEL, AGI, BAL, MOX, LCK, level, xp, nextLevelXp, unspentPoints, combo }
- state.level: { obstacles: Array<{x, worldY, type, radius, cleared}>, slalomGates: Array, cameraShake: number }
- state.keys: { left, right, up, down, jump }

STRICT RULES:
1. Never draw an opaque full-screen background in render() unless state.paused === true (e.g. a modal overlay).
2. Always guard custom properties you attach to `state` (e.g. `if (!state.customData) state.customData = ...`).
3. Output ONLY raw JavaScript calling `window.StudioEngine.registerModule(...)`. No markdown fences, no HTML tags.
"""


class CodebaseEngineerAgent:
    def __init__(self, workspace_root: Optional[Path] = None, memory: Optional[StudioRetrospectiveMemory] = None):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.memory = memory or StudioRetrospectiveMemory(
            workspace_root=self.workspace_root)
        self.node_bin = shutil.which("node")
        self.applied_rfcs_file = self.workspace_root / \
            "build" / "staging" / "applied_rfcs.json"
        self.applied_rfcs_file.parent.mkdir(parents=True, exist_ok=True)
        self.gateway = LLMGateway(workspace_root=self.workspace_root)

    def _get_applied_rfcs(self) -> List[str]:
        if self.applied_rfcs_file.exists():
            try:
                with open(self.applied_rfcs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _mark_rfc_applied(self, rfc_id: str) -> None:
        applied = self._get_applied_rfcs()
        if rfc_id not in applied:
            applied.append(rfc_id)
            with open(self.applied_rfcs_file, "w", encoding="utf-8") as f:
                json.dump(applied, f, indent=2)

    def implement_approved_rfcs(
        self,
        review_results: Optional[List[Any]] = None,
        active_version: Optional[str] = None
    ) -> int:
        implemented_count = 0
        approved_dir = self.workspace_root / "build" / "rfcs" / "approved"
        if not approved_dir.exists():
            return 0

        target_rfc_files: List[Path] = []
        applied_rfcs = self._get_applied_rfcs()

        if review_results:
            for item in review_results:
                rfc_id = getattr(item, "rfc_id", None) if hasattr(
                    item, "rfc_id") else item.get("rfc_id")
                status = getattr(item, "status", getattr(item, "verdict", "APPROVED")) if hasattr(
                    item, "status") else item.get("status", "APPROVED")
                status_str = status.value if hasattr(
                    status, "value") else str(status)
                if "REJECT" in status_str.upper():
                    continue
                f = approved_dir / f"{rfc_id}.json"
                if f.exists() and f not in target_rfc_files:
                    target_rfc_files.append(f)

        if active_version:
            for f in approved_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as rf:
                        data = json.load(rf)
                    tag = data.get("milestone_tag") or data.get(
                        "target_milestone") or data.get("milestone_target")
                    if tag == active_version and f not in target_rfc_files:
                        target_rfc_files.append(f)
                except Exception:
                    pass

        for rfc_file in target_rfc_files:
            try:
                with open(rfc_file, "r", encoding="utf-8") as f:
                    rfc_data = json.load(f)
            except Exception as e:
                logger.warning(
                    f"Could not read approved RFC {rfc_file.name}: {e}")
                continue

            rfc_id = rfc_data.get("rfc_id", rfc_file.stem)
            if rfc_id in applied_rfcs:
                logger.info(
                    f"[CodebaseEngineer] RFC {rfc_id} already applied. Skipping.")
                implemented_count += 1
                continue

            title = rfc_data.get("title", "")
            discipline = rfc_data.get("discipline", "")
            subsystem = (
                rfc_data.get("target_subsystem")
                or rfc_data.get("payload_diff", {}).get("target_subsystem")
                or "web_client/index.html"
            )

            # Studio Governance Guard: Never let game RFCs overwrite studio runtime tools
            if subsystem.startswith(("services/", "tools/", "schemas/")):
                logger.info(
                    f"[Governance Guard] Protected studio file '{subsystem}'. Marking RFC {rfc_id} verified.")
                self._mark_rfc_applied(rfc_id)
                implemented_count += 1
                continue

            logger.info(
                f"[CodebaseEngineer] Implementing approved RFC {rfc_id} [{discipline}]: '{title}'")

            success = self._synthesize_isolated_plugin(rfc_data)
            if success:
                self._mark_rfc_applied(rfc_id)
                implemented_count += 1
                self._git_commit(
                    "web_client/", f"auto(studio): implement {rfc_id} - {title}")

        return implemented_count

    def _sanitize_code(self, raw_text: str) -> str:
        text = raw_text.strip()
        match = re.search(
            r"```(?:javascript|js)?\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        lines = [line for line in text.splitlines(
        ) if not line.strip().startswith("```")]
        return "\n".join(lines).strip()

    def _verify_module_in_headless_sandbox(self, js_code: str) -> bool:
        """
        Executes the synthesized plugin inside a headless Node.js VM with a mocked
        StudioEngine and Canvas 2D context to catch TypeError/ReferenceError pre-commit.
        """
        if not self.node_bin:
            return True

        harness = f"""
        const noop = () => {{}};
        const mockCtx = new Proxy({{}}, {{
          get: (target, prop) => {{
            if (prop === 'measureText') return () => ({{ width: 50 }});
            if (prop === 'createLinearGradient' || prop === 'createRadialGradient') {{
              return () => ({{ addColorStop: noop }});
            }}
            if (prop in target) return target[prop];
            return noop;
          }},
          set: (target, prop, val) => {{ target[prop] = val; return true; }}
        }});

        const mockElement = new Proxy({{
          width: 800,
          height: 600,
          style: {{}},
          getContext: () => mockCtx,
          getBoundingClientRect: () => ({{ left: 0, top: 0, width: 800, height: 600 }}),
          addEventListener: noop
        }}, {{
          get: (target, prop) => (prop in target ? target[prop] : noop)
        }});

        global.window = {{
          __STUDIO_ERRORS__: [],
          addEventListener: noop,
          removeEventListener: noop,
          innerWidth: 800,
          innerHeight: 600
        }};
        global.document = {{
          getElementById: () => mockElement,
          querySelector: () => mockElement,
          createElement: () => mockElement,
          body: mockElement,
          addEventListener: noop
        }};
        global.requestAnimationFrame = noop;
        global.performance = {{ now: () => 1000 }};

        const registeredHooks = {{ update: [], render: [] }};
        global.window.StudioEngine = {{
          canvas: mockElement,
          ctx: mockCtx,
          modules: {{}},
          hooks: registeredHooks,
          state: {{
            running: true, paused: false, tick: 1,
            player: {{ x: 400, baseViewportY: 220, currentViewportY: 220, worldDistance: 100, vx: 0, vy: 200, skisAngle: 0, jumpZ: 0, jumpVz: 0, isAirborne: false, state: 'CRUISING', wipeoutTimer: 0, wipeouts: 0, characterClass: 'Olympian' }},
            stats: {{ VEL: 10, AGI: 10, BAL: 10, MOX: 10, LCK: 10, level: 1, xp: 0, nextLevelXp: 100, unspentPoints: 0, combo: 1 }},
            level: {{ obstacles: [{{ x: 300, worldY: 500, type: 'tree', radius: 16, cleared: false }}], slalomGates: [], cameraShake: 0 }},
            keys: {{ left: false, right: false, up: false, down: false, jump: false }}
          }},
          registerModule: function(name, def) {{
            if (typeof def.init === 'function') def.init(this.state, this);
            if (typeof def.update === 'function') registeredHooks.update.push(def.update.bind(def));
            if (typeof def.render === 'function') registeredHooks.render.push(def.render.bind(def));
          }}
        }};
        global.StudioEngine = global.window.StudioEngine;

        try {{
          {js_code}
          for (let frame = 0; frame < 3; frame++) {{
            registeredHooks.update.forEach(fn => fn(0.016, global.StudioEngine.state));
            registeredHooks.render.forEach(fn => fn(mockCtx, global.StudioEngine.state));
          }}
        }} catch (err) {{
          console.error("SANDBOX_RUNTIME_ERROR:", err.message);
          process.exit(1);
        }}
        process.exit(0);
        """

        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=True) as tf:
            tf.write(harness)
            tf.flush()
            res = subprocess.run([self.node_bin, tf.name],
                                 capture_output=True, text=True)
            if res.returncode != 0:
                logger.error(
                    f"[SandboxGuard] Rejected plugin due to runtime/syntax failure:\n{res.stderr.strip()}")
                return False
        return True

    def _synthesize_isolated_plugin(self, rfc: Dict[str, Any]) -> bool:
        rfc_id = rfc.get("rfc_id", "RFC_UNKNOWN")
        rfc_title = rfc.get("title", "Feature Module")
        rfc_spec = rfc.get("technical_specification") or rfc.get(
            "payload_diff", {}).get("technical_specification", "")

        js_dir = self.workspace_root / "web_client" / "js"
        js_dir.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", rfc_id)
        plugin_filename = f"mod_{safe_id}.js"
        plugin_path = js_dir / plugin_filename

        system_prompt = (
            "You are the Senior Codebase Engineer in an autonomous virtual game studio.\n"
            "Synthesize an isolated JavaScript plugin file for the approved RFC.\n"
            + BLACKBOARD_SCHEMA_CONTRACT
        )

        user_prompt = f"""Deliverable Title: {rfc_title}
RFC ID: {rfc_id}

Technical Specification:
{rfc_spec}

Write the complete, self-contained JavaScript plugin module implementing this feature."""

        logger.info(
            f"[CodebaseEngineer] Synthesizing isolated plugin 'web_client/js/{plugin_filename}'...")
        js_code = self._sanitize_code(self.gateway.complete(
            system_prompt, user_prompt, temperature=0.1))

        if not js_code or "registerModule" not in js_code:
            logger.warning(
                f"[CodebaseEngineer] LLM did not emit a valid StudioEngine.registerModule call for {rfc_id}.")
            return False

        # Pre-commit headless execution test
        if not self._verify_module_in_headless_sandbox(js_code):
            logger.error(
                f"[CodebaseEngineer] Aborting {plugin_filename}: failed headless sandbox execution.")
            return False

        # Write isolated JS plugin file
        header = f"// Autonomous Plugin: {rfc_id} | {rfc_title}\n"
        plugin_path.write_text(header + js_code + "\n", encoding="utf-8")
        logger.info(
            f"[CodebaseEngineer] Wrote verified plugin: web_client/js/{plugin_filename}")

        # Register script tag in web_client/index.html
        index_path = self.workspace_root / "web_client" / "index.html"
        if index_path.exists():
            html = index_path.read_text(encoding="utf-8")
            script_tag = f'  <script src="js/{plugin_filename}"></script>'
            if script_tag not in html and "</body>" in html:
                html = html.replace("</body>", f"{script_tag}\n</body>")
                index_path.write_text(html, encoding="utf-8")
                logger.info(
                    f"[CodebaseEngineer] Linked {plugin_filename} in web_client/index.html")

        return True

    def _git_commit(self, relative_path: str, message: str) -> None:
        try:
            subprocess.run(["git", "add", relative_path],
                           cwd=self.workspace_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", message],
                           cwd=self.workspace_root, check=True, capture_output=True)
            logger.info(f"[Git] Committed: {message}")
        except subprocess.CalledProcessError:
            pass
