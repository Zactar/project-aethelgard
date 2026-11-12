// Cohesive Milestone Plugin: v0.6.0
window.StudioEngine.registerModule("Milestone_v0_6_0", {
  init(st, eng) {
    const w = st.world = st.world || {};
    st.stats = st.stats || {};
    st.inventory = st.inventory || { relics: [] };
    w.activeTelemetry = [];
    w.ghostTrajectory = JSON.parse(localStorage.getItem("glissade_ghost_traj") || "[]");
    w.heatModifiers = w.heatModifiers || ["black_ice", "whiteout"];
    w.shelterVisited = false;
    this.sampleTimer = 0;
    this.prevVx = 0;
    this.gForce = 1.0;
    this.deltaT = 0;
    this.lastChalDist = -1;
  },
  update(dt, st, eng) {
    if (!st.running) return;
    const p = st.player || {}, w = st.world || {}, s = st.stats;
    const heatDefs = { black_ice: 2, whiteout: 3, twin_yetis: 4 };
    const H = (w.heatModifiers || []).reduce((acc, m) => acc + (heatDefs[m] || 1), 0);
    s.heatLevel = H;
    s.xpMultiplier = Math.pow(1.18, H);
    s.luckBonus = 0.04 * H;
    if (w.heatModifiers.includes("twin_yetis")) w.yetiCount = 2;
    if (w.heatModifiers.includes("whiteout")) w.visibilityRadius = 240;

    const d = w.distance || p.y || 0;
    const chalDist = Math.floor(d / 500) * 500;
    if (chalDist > 0 && chalDist !== this.lastChalDist && d % 500 < 25 && p.state !== "CHALET") {
      this.lastChalDist = chalDist;
      p.state = "CHALET";
      st.paused = true;
    }

    if (p.state === "CHALET") {
      const k = st.keys || {}, inv = st.inventory;
      if (k.digit1) {
        const counts = {};
        inv.relics.forEach(r => { counts[r.id] = (counts[r.id] || 0) + 1; });
        const dupId = Object.keys(counts).find(id => counts[id] >= 2);
        if (dupId) {
          const idxs = [];
          inv.relics.forEach((r, i) => { if (r.id === dupId && idxs.length < 2) idxs.push(i); });
          const base = inv.relics[idxs[0]];
          inv.relics.splice(idxs[1], 1);
          inv.relics.splice(idxs[0], 1);
          (inv.relics || (inv.relics = [])).push({ id: base.id + "_mythic", name: "Mythic " + (base.name || dupId), tier: (base.tier || 1) + 1 });
          s.transmutationsPerformed = (s.transmutationsPerformed || 0) + 1;
        }
      }
      if (k.digit2) {
        const maxH = p.maxHealth || p.maxHp || 3;
        const curH = p.health || p.hp || 3;
        const nextH = Math.max(1, curH - Math.ceil(0.25 * maxH));
        if (p.health !== undefined) p.health = nextH; else p.hp = nextH;
        (inv.relics || (inv.relics = [])).push({ id: "blood_curse_" + Date.now(), name: "Blood Charm", cursed: true, vyMod: 0.4, turnMod: -0.3 });
        s.transmutationsPerformed = (s.transmutationsPerformed || 0) + 1;
      }
      if (k.digit3 || k.jump || k.action) {
        p.state = 0x01;
        st.paused = false;
      }
      return;
    }

    if (st.paused) return;
    this.sampleTimer++;
    if (this.sampleTimer % 6 === 0) {
      (w.activeTelemetry || (w.activeTelemetry = [])).push({ x: p.x, y: p.y, vx: p.vx, vy: p.vy, t: (st.tick || 0) * dt });
      if (w.activeTelemetry.length > 1200) w.activeTelemetry.shift();
      if (!w.ghostTrajectory.length && d > 1000) {
        localStorage.setItem("glissade_ghost_traj", JSON.stringify(w.activeTelemetry));
      }
    }

    const curT = (st.tick || 0) * dt;
    const ghostSample = w.ghostTrajectory.find(pt => Math.abs(pt.y - p.y) < 24);
    if (ghostSample) this.deltaT = curT - ghostSample.t;
    this.gForce = 1.0 + Math.abs((p.vx - this.prevVx) / Math.max(0.001, dt)) / 980;
    this.prevVx = p.vx || 0;
  },
  render(ctx, st) {
    ctx.save();
    ctx.textAlign = "left";
    const w = st.world || {}, p = st.player || {}, camY = w.camY || w.cameraY || 0;
    if (w.ghostTrajectory && w.ghostTrajectory.length) {
      const gPt = w.ghostTrajectory.find(pt => Math.abs(pt.y - p.y) < 300);
      if (gPt) {
        ctx.save();
        ctx.globalCompositeOperation = "screen";
        ctx.fillStyle = "#00f3ff";
        ctx.globalAlpha = 0.45;
        const gx = gPt.x - (w.camX || 400) + 400, gy = gPt.y - camY + 220;
        ctx.beginPath(); ctx.arc(gx, gy, 12, 0, 6.28); ctx.fill();
        ctx.fillRect(gx - 4, gy + 10, 8, 14);
        ctx.restore();
      }
    }
    // Sub-Top Right reserved dock (x: 520..784, y: 48..110)
    ctx.fillStyle = "#0a1a0f";
    ctx.fillRect(520, 52, 260, 52);
    ctx.strokeStyle = "#00ff66";
    ctx.lineWidth = 1;
    ctx.strokeRect(520, 52, 260, 52);
    ctx.fillStyle = "#00ff66";
    ctx.font = "9px monospace";
    ctx.fillText(`CRT LIVE TELEMETRY // HEAT: H${st.stats?.heatLevel || 0}`, 526, 64);
    ctx.fillText(`SPLIT Δt : ${(this.deltaT >= 0 ? "+" : "") + this.deltaT.toFixed(2)}s | Vy: ${(p.vy || 0).toFixed(0)}`, 526, 78);
    ctx.fillText(`LATERAL G: ${this.gForce.toFixed(2)}G | XP: ${(st.stats?.xpMultiplier || 1).toFixed(2)}x`, 526, 92);

    if (p.state === "CHALET") {
      ctx.fillStyle = "rgba(10, 14, 24, 0.92)";
      ctx.fillRect(150, 120, 500, 340);
      ctx.strokeStyle = "#e8b836";
      ctx.lineWidth = 2;
      ctx.strokeRect(150, 120, 500, 340);
      ctx.fillStyle = "#fff";
      ctx.font = "14px monospace";
      ctx.fillText("--- CHALET FORGE & TRANSMUTATION ---", 240, 155);
      ctx.font = "11px monospace";
      ctx.fillStyle = "#00f3ff";
      ctx.fillText("[1] Relic Fusion: Combine 2 Duplicates into Mythic", 180, 210);
      ctx.fillStyle = "#ff4444";
      ctx.fillText("[2] Transmute Blood: Sacrifice 25% HP for Cursed Alpine Charm", 180, 250);
      ctx.fillStyle = "#55ff55";
      ctx.fillText("[3 / JUMP / ACTION] Exit Chalet & Resume Descent", 180, 290);
      ctx.fillStyle = "#888";
      ctx.fillText(`Relics: ${(st.inventory?.relics || []).length} | HP: ${p.health || p.hp || 3}`, 180, 340);
    }
    ctx.restore();
  }
});
