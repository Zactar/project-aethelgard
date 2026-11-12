// Cohesive Milestone Plugin: v0.4.0
window.StudioEngine.registerModule("Milestone_v0_4_0", {
  init(st, eng) {
    const w = st.world = st.world || {};
    w.entities = w.entities || [];
    w.currentBiome = "Alpine Resort";
    w.paletteLerp = 0;
    w.blizzardAlpha = 0;
    w.nextGenY = 800;
    w.yetiAggro = 0;
    st.inventory = st.inventory || { items: [], relics: [], currency: 0 };
    st.inventory.equippedRelics = st.inventory.equippedRelics || [];
    st.inventory.activeDraft = null;
    const p = st.player = st.player || {};
    p.topSpeedMul = 1.0; p.accelMul = 1.0; p.carveGrip = 1.0; p.staminaRegen = 1.0;
    p.isAirborne = p.isAirborne || false;

    // Combinatorial 100+ Relic Catalog Synthesizer
    const P = ["Frost", "Apex", "Gore", "Gale", "Obsidian", "Phantom", "Rune", "Cursed", "Blizz", "Vortex"],
          B = ["Edge", "Ski", "Binding", "Visor", "Core", "Boots", "Wax", "Charm", "Pole", "Cloak", "Talon"],
          R = ["Common", "Rare", "Epic", "Cursed"];
    st.inventory.relicCatalog = [];
    for (let i = 0; i < 110; i++) {
      const pfx = P[i % P.length], base = B[Math.floor(i / P.length) % B.length],
            rar = i % 20 === 19 ? "Cursed" : (i % 7 === 0 ? "Epic" : (i % 3 === 0 ? "Rare" : "Common")),
            s = rar === "Cursed" ? 1.6 : (rar === "Epic" ? 1.3 : (rar === "Rare" ? 1.15 : 1.05)),
            g = rar === "Cursed" ? 0.5 : (rar === "Epic" ? 1.2 : 1.05);
      (st.inventory.relicCatalog || (st.inventory.relicCatalog = [])).push({
        id: `r_${i}`, name: `${pfx} ${base} +${i}`, rarity: rar,
        desc: rar === "Cursed" ? "+60% Spd, -50% Grip, +Yeti" : `+${Math.round((s-1)*100)}% Spd, +${Math.round((g-1)*100)}% Grip`,
        apply: (pl, stt) => { pl.topSpeedMul *= s; pl.carveGrip *= g; if (rar === "Cursed") (stt.world.yetiAggro = (stt.world.yetiAggro || 0) + 0.2); }
      });
    }
  },
  applyRelic(st, relic) {
    (st.inventory.equippedRelics || (st.inventory.equippedRelics = [])).push(relic);
    relic.apply(st.player, st);
    st.inventory.activeDraft = null;
    st.paused = false;
  },
  update(dt, st, eng) {
    if (!st.running) return;
    const w = st.world, p = st.player, d = w.distance || 0;
    const biomes = [{ n: "Alpine Resort", e: 1500, col: [240, 245, 255] }, { n: "Black Diamond Pines", e: 3500, col: [200, 220, 230] }, { n: "Glacial Crevasse", e: 6000, col: [170, 210, 240] }, { n: "Yeti Tundra", e: Infinity, col: [140, 160, 190] }];
    let curIdx = biomes.findIndex(b => d < b.e);
    if (curIdx === -1) curIdx = 3;
    w.currentBiome = biomes[curIdx].n;
    const curB = biomes[curIdx], prevEnd = curIdx > 0 ? biomes[curIdx - 1].e : 0;
    w.paletteLerp = Math.min(1, Math.max(0, (d - prevEnd) / 200));

    // Environmental Hazards & Blizzards
    const isBlizz = curIdx >= 2;
    w.blizzardAlpha = isBlizz ? Math.min(0.7, (d - 3500) / 2500) : 0;
    if (w.blizzardAlpha > 0) p.vx = (p.vx || 0) + Math.sin(st.tick * 0.05) * 40 * w.blizzardAlpha * dt;

    // 500m Refuge Checkpoint Draft Trigger
    const check500 = Math.floor(d / 350);
    if (check500 > (w.lastCheck500 || 0)) {
      w.lastCheck500 = check500;
      const cat = st.inventory.relicCatalog;
      st.inventory.activeDraft = [cat[Math.floor(Math.random()*cat.length)], cat[Math.floor(Math.random()*cat.length)], cat[Math.floor(Math.random()*cat.length)]];
      st.paused = true;
    }
    if (st.paused) {
      if (st.keys?.digit1 && st.inventory.activeDraft) this.applyRelic(st, st.inventory.activeDraft[0]);
      if (st.keys?.digit2 && st.inventory.activeDraft) this.applyRelic(st, st.inventory.activeDraft[1]);
      if (st.keys?.digit3 && st.inventory.activeDraft) this.applyRelic(st, st.inventory.activeDraft[2]);
      return;
    }

    // Procedural Hazard & Slice Generator
    const targetY = (p.y || 0) + 800;
    while (w.nextGenY < targetY) {
      w.nextGenY += 80 + Math.random() * 80;
      const roll = Math.random(), gateW = curIdx >= 1 ? 70 : 140;
      if (roll < 0.25) (w.entities || (w.entities = [])).push({ type: "ice", x: 60 + Math.random() * 680, y: w.nextGenY, w: 90, h: 40 });
      else if (roll < 0.45 && curIdx >= 2) (w.entities || (w.entities = [])).push({ type: "chasm", x: 40 + Math.random() * 700, y: w.nextGenY, w: 120, h: 32 });
      else if (roll < 0.70) (w.entities || (w.entities = [])).push({ type: "gate", x: 80 + Math.random() * (640 - gateW), y: w.nextGenY, w: gateW, h: 16, passed: false });
    }

    // Entity Interaction & Hazard Kinematics
    let onIce = false;
    p.isAirborne = (p.z || 0) > 0;
    w.entities = w.entities.filter(e => {
      if (e.y < (p.y || 0) - 400) return false;
      const hit = Math.abs(p.x - (e.x + e.w / 2)) < (e.w / 2 + 12) && Math.abs(p.y - (e.y + e.h / 2)) < (e.h / 2 + 14);
      if (hit) {
        if (e.type === "ice") { onIce = true; p.vx = (p.vx || 0) * 0.995; }
        else if (e.type === "chasm" && (!p.isAirborne || (p.z || 0) < 1.0)) {
          p.state = 0x08; p.wipeoutTimer = 2.0; p.vy = 0; p.vx = 0; if (st.stats) st.stats.balance = Math.max(1, (st.stats.balance || 10) - 2);
        } else if (e.type === "gate" && !e.passed) { e.passed = true; if (st.stats) st.stats.xp = (st.stats.xp || 0) + 35; }
      }
      return true;
    });
    p.carveGrip = onIce ? 0.15 : (p.baseCarveGrip || 1.0);
  },
  render(ctx, st, eng) {
    const w = st.world, p = st.player, camY = (p?.y || 0) - 200;
    // Render Slice Entities
    (w.entities || []).forEach(e => {
      const ey = e.y - camY;
      if (ey < -50 || ey > 650) return;
      if (e.type === "ice") { ctx.fillStyle = "rgba(180, 230, 255, 0.65)"; ctx.fillRect(e.x, ey, e.w, e.h); }
      else if (e.type === "chasm") { ctx.fillStyle = "#0f1522"; ctx.fillRect(e.x, ey, e.w, e.h); }
      else if (e.type === "gate") {
        ctx.fillStyle = e.passed ? "#55ff55" : "#ff3333";
        ctx.fillRect(e.x, ey, 6, e.h); ctx.fillRect(e.x + e.w - 6, ey, 6, e.h);
        ctx.strokeStyle = "rgba(255,255,255,0.4)"; ctx.setLineDash([4, 4]); ctx.strokeRect(e.x, ey, e.w, e.h); ctx.setLineDash([]);
      }
    });
    // Blizzard Radial Mask
    if (w.blizzardAlpha > 0.05) {
      const cx = p.x || 400, cy = (p.y || 0) - camY, r = Math.max(160, 420 * (1 - w.blizzardAlpha));
      const grad = ctx.createRadialGradient(cx, cy, r * 0.4, cx, cy, r);
      grad.addColorStop(0, "rgba(240,248,255,0)"); grad.addColorStop(1, `rgba(220,235,250,${w.blizzardAlpha})`);
      ctx.fillStyle = grad; ctx.fillRect(0, 0, 800, 600);
    }
    // Sub-Top Right HUD: Relics & Biome
    ctx.fillStyle = "rgba(10, 20, 35, 0.75)"; ctx.fillRect(520, 48, 264, 58);
    ctx.strokeStyle = "#4da6ff"; ctx.strokeRect(520, 48, 264, 58);
    ctx.fillStyle = "#fff"; ctx.font = "10px monospace";
    ctx.fillText(`BIOME: ${w.currentBiome || "Resort"}`, 530, 64);
    ctx.fillText(`RELICS: ${(st.inventory.equippedRelics || []).length} | GRIP: ${(p.carveGrip || 1).toFixed(2)}x`, 530, 80);
    ctx.fillText(`NEXT 500m: ${350 - (Math.floor(w.distance || 0) % 500)}m`, 530, 96);

    // 500m Checkpoint Tri-Draft Modal Overlay
    if (st.inventory.activeDraft) {
      ctx.fillStyle = "rgba(5, 10, 20, 0.88)"; ctx.fillRect(100, 160, 600, 280);
      ctx.strokeStyle = "#ffaa00"; ctx.lineWidth = 2; ctx.strokeRect(100, 160, 600, 280);
      ctx.fillStyle = "#ffcc00"; ctx.font = "bold 16px monospace"; ctx.textAlign = "center";
      ctx.fillText("--- ALPINE RELIC SHRINE: SELECT RELIC ---", 400, 195);
      st.inventory.activeDraft.forEach((r, i) => {
        const col = r.rarity === "Cursed" ? "#ff4444" : (r.rarity === "Epic" ? "#c060ff" : (r.rarity === "Rare" ? "#44aaff" : "#aaffaa"));
        ctx.fillStyle = "rgba(255,255,255,0.06)"; ctx.fillRect(125 + i * 190, 220, 170, 190);
        ctx.strokeStyle = col; ctx.strokeRect(125 + i * 190, 220, 170, 190);
        ctx.fillStyle = col; ctx.font = "bold 12px monospace"; ctx.fillText(`[${i+1}] ${r.name}`, 210 + i * 190, 245);
        ctx.fillStyle = "#ddd"; ctx.font = "10px monospace"; ctx.fillText(r.rarity, 210 + i * 190, 265);
        ctx.fillText(r.desc, 210 + i * 190, 310);
      });
      ctx.textAlign = "left";
    }
  }
});
