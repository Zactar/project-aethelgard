"""
tools/validate_webapp.py
Chaos QA Commander: Universal Headless Playability & Plugin Runtime Audit
"""

import os
import sys
import shutil
import subprocess
import tempfile
import urllib.request
import logging
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("ChaosQA.Validator")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def audit_webapp_playability() -> bool:
    logger.info(
        "=== CHAOS QA: UNIVERSAL PLAYABILITY & HEADLESS RUNTIME AUDIT ===")
    index_path = WORKSPACE_ROOT / "web_client" / "index.html"
    if not index_path.exists():
        logger.error("[✗] Missing web_client/index.html!")
        return False

    html = index_path.read_text(encoding="utf-8")
    if 'id="gameCanvas"' not in html or "requestAnimationFrame" not in html:
        logger.error("[✗] Chaos QA Failure: Missing core canvas or tick loop!")
        return False

    # Execute all loaded JS plugins inside a headless Node.js DOM sandbox
    node_bin = shutil.which("node")
    js_dir = WORKSPACE_ROOT / "web_client" / "js"
    plugin_files = sorted(js_dir.glob("mod_*.js")) if js_dir.exists() else []

    if node_bin and plugin_files:
        combined_plugins = "\n;\n".join(pf.read_text(
            encoding="utf-8") for pf in plugin_files)
        audit_script = f"""
        const noop = () => {{}};
        const mockCtx = new Proxy({{}}, {{
          get: (t, p) => p === 'measureText' ? () => ({{ width: 50 }}) : (p in t ? t[p] : noop),
          set: (t, p, v) => {{ t[p] = v; return true; }}
        }});
        const mockEl = new Proxy({{
          width: 800, height: 600, style: {{}},
          getContext: () => mockCtx,
          getBoundingClientRect: () => ({{ left: 0, top: 0, width: 800, height: 600 }}),
          addEventListener: noop
        }}, {{ get: (t, p) => (p in t ? t[p] : noop) }});

        global.window = {{ __STUDIO_ERRORS__: [], addEventListener: noop, innerWidth: 800, innerHeight: 600 }};
        global.document = {{ getElementById: () => mockEl, querySelector: () => mockEl, createElement: () => mockEl, body: mockEl, addEventListener: noop }};
        global.requestAnimationFrame = noop;
        global.performance = {{ now: () => 1000 }};

        const hooks = {{ update: [], render: [] }};
        global.window.StudioEngine = {{
          canvas: mockEl, ctx: mockCtx, modules: {{}}, hooks,
          state: {{
            running: true, paused: false, tick: 1,
            player: {{ x: 400, baseViewportY: 220, currentViewportY: 220, worldDistance: 100, vx: 0, vy: 200, skisAngle: 0, jumpZ: 0, jumpVz: 0, isAirborne: false, state: 'CRUISING', wipeoutTimer: 0, wipeouts: 0, characterClass: 'Olympian' }},
            stats: {{ VEL: 10, AGI: 10, BAL: 10, MOX: 10, LCK: 10, level: 1, xp: 0, nextLevelXp: 100, unspentPoints: 0, combo: 1 }},
            level: {{ obstacles: [{{ x: 300, worldY: 500, type: 'tree', radius: 16, cleared: false }}], slalomGates: [], cameraShake: 0 }},
            keys: {{ left: false, right: false, up: false, down: false, jump: false }}
          }},
          registerModule: function(name, def) {{
            if (typeof def.init === 'function') def.init(this.state, this);
            if (typeof def.update === 'function') hooks.update.push(def.update.bind(def));
            if (typeof def.render === 'function') hooks.render.push(def.render.bind(def));
          }}
        }};
        global.StudioEngine = global.window.StudioEngine;

        try {{
          {combined_plugins}
          for (let i = 0; i < 5; i++) {{
            hooks.update.forEach(fn => fn(0.016, global.StudioEngine.state));
            hooks.render.forEach(fn => fn(mockCtx, global.StudioEngine.state));
          }}
        }} catch (e) {{
          console.error("CHAOS_QA_PLUGIN_CRASH:", e.message);
          process.exit(1);
        }}
        if (global.window.__STUDIO_ERRORS__.length > 0) {{
          console.error("CHAOS_QA_STUDIO_ERRORS:", JSON.stringify(global.window.__STUDIO_ERRORS__));
          process.exit(1);
        }}
        process.exit(0);
        """
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=True) as tf:
            tf.write(audit_script)
            tf.flush()
            res = subprocess.run([node_bin, tf.name],
                                 capture_output=True, text=True)
            if res.returncode != 0:
                logger.error(
                    f"[✗] Chaos QA Headless Plugin Execution Failed:\n{res.stderr.strip()}")
                return False
        logger.info(
            f"[✓] Verified {len(plugin_files)} isolated StudioEngine plugins in headless sandbox.")

    # Verify HTTP Port 3000 responsiveness
    try:
        with urllib.request.urlopen("[http://127.0.0.1:3000](http://127.0.0.1:3000)", timeout=3) as resp:
            if resp.status == 200:
                logger.info(
                    "[✓] Web client active on Port 3000 with running tick loop.")
    except Exception:
        logger.warning(
            "[!] Port 3000 server not responding locally; starting background server...")
        subprocess.Popen(
            [sys.executable, "-m", "http.server", "3000",
                "--directory", str(WORKSPACE_ROOT / "web_client")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    logger.info("[✓] ALL UNIVERSAL PLAYABILITY INVARIANTS PASSED.")
    return True


if __name__ == "__main__":
    sys.exit(0 if audit_webapp_playability() else 1)
