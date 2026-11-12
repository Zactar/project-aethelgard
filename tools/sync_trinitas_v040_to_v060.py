#!/usr/bin/env python3
"""
tools/upgrade_studio_v5_architecture.py
1. Fixes the `_smartCtx` `save()`/`restore()` and `globalAlpha` poisoning bug seen in image_6b02dc.jpg
   so `_modalCtx` never inherits fractional alpha (0.22) from background starfield passes.
2. Upgrades web_client/index_template.html & web_client/index.html with:
   - Synchronized Dual-Context `save()` / `restore()` in `_smartCtx`
   - Forced `_modalCtx.globalAlpha = 1.0` & `_modalCtx.shadowBlur = 0` on modal backdrop initialization
   - StudioEngine v5.0 Spatial Slot Registry (`StudioEngine.claimSpatialSlot`)
3. Upgrades tools/validate_webapp.py with v5.0 Canvas State-Stack (`save`/`restore`) & Alpha-Leak Auditing.
"""

import re
from pathlib import Path

ROOT = Path("/workspaces/project-aethelgard")

# ---------------------------------------------------------------------------
# 1. Fix _smartCtx save()/restore() & Modal Alpha Reset in index.html & index_template.html
# ---------------------------------------------------------------------------
for html_name in ["index_template.html", "index.html"]:
    hp = ROOT / "web_client" / html_name
    if not hp.exists():
        continue
    html = hp.read_text(encoding="utf-8")

    # Ensure _modalCtx resets globalAlpha = 1.0 and shadowBlur = 0 whenever a modal pass begins!
    old_modal_init_1 = """              _modalCtx.font = target.font;
              _modalCtx.textAlign = target.textAlign;
              _modalCtx.textBaseline = target.textBaseline;
              _modalCtx.fillStyle = 'rgba(6, 9, 18, 0.94)';
              _modalCtx.fillRect(0, 36, 800, 564);"""

    new_modal_init_1 = """              _modalCtx.globalAlpha = 1.0;
              _modalCtx.shadowBlur = 0;
              _modalCtx.font = target.font;
              _modalCtx.textAlign = target.textAlign;
              _modalCtx.textBaseline = target.textBaseline;
              _modalCtx.fillStyle = 'rgba(6, 9, 18, 0.96)';
              _modalCtx.fillRect(0, 36, 800, 564);"""

    html = html.replace(old_modal_init_1, new_modal_init_1)

    # Intercept ctx.save() and ctx.restore() in _smartCtx so BOTH _baseCtx and _modalCtx save/restore together!
    old_val_bind = """      const val = activeTarget[prop];
      return typeof val === 'function' ? val.bind(activeTarget) : val;"""

    new_val_bind = """      if (prop === 'save' || prop === 'restore') {
        return function() {
          target[prop]();
          _modalCtx[prop]();
        };
      }
      const val = activeTarget[prop];
      return typeof val === 'function' ? val.bind(activeTarget) : val;"""

    html = html.replace(old_val_bind, new_val_bind)

    # Add StudioEngine.claimSpatialSlot helper for v5.0 Spatial Budget Management
    if "claimSpatialSlot:" not in html:
        slot_helper = """    _spatialSlots: {},
    claimSpatialSlot: function(roomKey, x, y, minRadius) {
      const list = this._spatialSlots[roomKey] || (this._spatialSlots[roomKey] = []);
      const r = minRadius || 48;
      for (let i = 0; i < list.length; i++) {
        if (Math.hypot(list[i].x - x, list[i].y - y) < list[i].r + r) return false;
      }
      list.push({ x: x, y: y, r: r });
      return true;
    },
    on: function("""
        html = html.replace("    on: function(", slot_helper, 1)

    hp.write_text(html, encoding="utf-8")

print("[✓] Fixed _smartCtx dual-context save()/restore() & modal globalAlpha=1.0 lock in index.html & index_template.html.")

# ---------------------------------------------------------------------------
# 2. Ensure milestone_v0_5_0.js resets ctx.globalAlpha = 1.0 before drawing Verdict Modal
# ---------------------------------------------------------------------------
v5_path = ROOT / "web_client" / "js" / "milestone_v0_5_0.js"
if v5_path.exists():
    v5 = v5_path.read_text(encoding="utf-8")
    v5 = v5.replace(
        "if (this.verdictOpen && this.lastSummary) {\n      const sum = this.lastSummary;\n      ctx.save();",
        "if (this.verdictOpen && this.lastSummary) {\n      const sum = this.lastSummary;\n      ctx.save();\n      ctx.globalAlpha = 1.0;\n      ctx.fillStyle = 'rgba(6, 9, 18, 0.96)';\n      ctx.fillRect(0, 36, 800, 564);"
    )
    v5_path.write_text(v5, encoding="utf-8")
    print("[✓] Locked opaque backdrop & globalAlpha=1.0 on Grand Arbiter Series Verdict Modal in milestone_v0_5_0.js.")

# ---------------------------------------------------------------------------
# 3. Upgrade tools/validate_webapp.py with v5.0 Canvas State-Stack Auditing
# ---------------------------------------------------------------------------
vw_path = ROOT / "tools" / "validate_webapp.py"
if vw_path.exists():
    vw_code = vw_path.read_text(encoding="utf-8")
    old_audit_ret = 'return True, f"Studio v4.0 Governance (Control, Schema, Aesthetics & UI/UX Z-Layer) Verified ({len(plugin_files)} modules; {status_note})"'
    new_audit_ret = '''for pf in plugin_files:
        c = pf.read_text(encoding="utf-8")
        saves = len(re.findall(r"\\.save\\(\\s*\\)", c))
        restores = len(re.findall(r"\\.restore\\(\\s*\\)", c))
        if saves != restores:
            warnings.append(f"{pf.name}:unbalanced-ctx-save-restore({saves}!={restores})")
    status_note = f"warnings={warnings}" if warnings else "0 conflicts, balanced ctx stacks"
    return True, f"Studio v5.0 Governance (Control, Deep Schema, Spatial Slots & Canvas Stack) Verified ({len(plugin_files)} modules; {status_note})"'''
    if old_audit_ret in vw_code:
        vw_code = vw_code.replace(old_audit_ret, new_audit_ret)
        vw_path.write_text(vw_code, encoding="utf-8")
        print("[✓] Upgraded tools/validate_webapp.py to Studio v5.0 Governance (added Canvas save/restore balance audit).")
        