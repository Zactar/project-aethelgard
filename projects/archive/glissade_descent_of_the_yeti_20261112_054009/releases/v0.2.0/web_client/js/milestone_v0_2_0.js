// Cohesive Milestone Plugin: v0.2.0
// Cohesive Milestone Plugin: v0.2.0 - Stats, Slalom, Level-Up & Class Selection
window.StudioEngine.registerModule("Milestone_v0_2_0", {
  init(st, eng) {
    st.world.gameState = "CLASS_SELECT";
    st.player.level = 1; st.player.xp = 0; st.player.slalomStreak = 0; st.player.classId = null;
    st.stats = { velocity: 10, agility: 10, balance: 10, moxie: 10, luck: 10 };
    st.inventory = st.inventory || { items: [], relics: [], traits: [] };
    st.world.gates = []; st.world.floatingTexts = []; st.world.nextGateY = 600;
    this.classes = [
      { id: "Olympian", d: "Speed & poise", s: { velocity: 3, balance: 2 }, c: "#3b82f6" },
      { id: "Daredevil", d: "Agile & brazen", s: { agility: 3, moxie: 2 }, c: "#ef4444" },
      { id: "Ranger", d: "Swift & fortunate", s: { agility: 2, luck: 3 }, c: "#10b981" },
      { id: "Occultist", d: "Risk & arcane luck", s: { moxie: 4, luck: 1 }, c: "#8b5cf6" }
    ];
    this.selClass = 0; this.levelDraft = [];
    eng.stats = { recalculate: () => {
      const s = st.stats, p = st.player;
      for (let k in s) s[k] = Math.max(1, Math.min(99, s[k]));
      p.vMax = 12 + 1.2 * s.velocity; p.aX = 0.8 + 0.15 * s.agility;
      p.tRec = Math.max(0.4, 2.0 - 0.12 * s.balance);
      p.mXp = 1.0 + 0.08 * s.moxie; p.wRare = 1.0 + 0.05 * s.luck;
    }};
    eng.stats.recalculate();
  },
  reqXp(lvl) { return Math.floor(100 * Math.pow(lvl, 1.4)); },
  addXp(st, eng, amt, x, y, label) {
    st.player.xp += amt * st.player.mXp;
    st.world.floatingTexts.push({ text: `+${Math.floor(amt * st.player.mXp)} ${label}`, x, y, life: 1.0 });
    const req = this.reqXp(st.player.level);
    if (st.player.xp >= req) {
      st.player.xp -= req; st.player.level++; st.world.gameState = "LEVEL_UP"; st.paused = true;
      const keys = ["velocity", "agility", "balance", "moxie", "luck"];
      this.levelDraft = keys.sort(() => 0.5 - Math.random()).slice(0, 3);
      eng.emit("LEVEL_UP", { level: st.player.level });
    }
  },
  update(dt, st, eng) {
    const k = st.keys || {}, gs = st.world.gameState, p = st.player, w = st.world;
    if (gs === "CLASS_SELECT") {
      if (k.left && !this._pl) { this.selClass = (this.selClass + 3) % 4; this._pl = true; } else if (!k.left) this._pl = false;
      if (k.right && !this._pr) { this.selClass = (this.selClass + 1) % 4; this._pr = true; } else if (!k.right) this._pr = false;
      if (k.jump || k.action) {
        const cls = this.classes[this.selClass]; p.classId = cls.id;
        for (let s in cls.s) st.stats[s] += cls.s[s];
        st.inventory.traits.push(cls.id); eng.stats.recalculate();
        st.world.gameState = "RUNNING";
      }
      return;
    }
    if (gs === "LEVEL_UP") {
      [1, 2, 3].forEach((n, i) => {
        if (k[`digit${n}`] || (k.jump && i === 0)) {
          st.stats[this.levelDraft[i]]++; eng.stats.recalculate();
          st.paused = false; st.world.gameState = "RUNNING";
        }
      });
      return;
    }
    if (st.paused) return;
    const sdt = Math.min(dt, 0.05);
    while (w.nextGateY < p.y + 1600) {
      const gx = 100 + Math.random() * 600, color = (w.gates.length % 2 === 0) ? "#ef4444" : "#3b82f6";
      w.gates.push({ x1: gx - 32, x2: gx + 32, y: w.nextGateY, color, passed: false });
      w.nextGateY += 180 + (Math.random() * 80 - 40);
    }
    for (let g of w.gates) {
      if (!g.passed && p.y >= g.y) {
        g.passed = true;
        if (p.x >= g.x1 && p.x <= g.x2) {
          p.slalomStreak++; const bonus = 50 * Math.min(p.slalomStreak, 10);
          this.addXp(st, eng, bonus, p.x, p.y - 20, "GATE!");
          st.score += Math.floor(bonus * (1 + 0.1 * p.slalomStreak));
          eng.emit("SLALOM_CLEAR", { streak: p.slalomStreak });
        } else {
          p.slalomStreak = 0; eng.emit("SLALOM_MISSED", {});
          w.floatingTexts.push({ text: "MISSED!", x: p.x, y: p.y - 20, life: 0.8 });
        }
      }
    }
    w.gates = w.gates.filter(g => g.y > p.y - 300);
    for (let o of w.obstacles) {
      if (!o.grazed && !o.low && Math.abs(p.x - o.x) <= 22 && Math.abs(p.y - o.y) <= 16) {
        o.grazed = true; this.addXp(st, eng, 25 * (p.vy / 100), p.x, p.y - 10, "GRAZE");
      }
    }
    for (let i = w.floatingTexts.length - 1; i >= 0; i--) {
      const ft = w.floatingTexts[i]; ft.y -= 40 * sdt; ft.life -= sdt;
      if (ft.life <= 0) w.floatingTexts.splice(i, 1);
    }
  },
  render(ctx, st, eng) {
    const gs = st.world.gameState, p = st.player, w = st.world, cx = Math.floor(w.camX - 400), cy = Math.floor(w.camY - 180);
    if (gs === "CLASS_SELECT") {
      ctx.fillStyle = "rgba(10, 15, 30, 0.95)"; ctx.fillRect(0, 0, 800, 600);
      ctx.fillStyle = "#fff"; ctx.font = "bold 24px monospace"; ctx.textAlign = "center";
      ctx.fillText("SELECT YOUR ALPINIST", 400, 120);
      this.classes.forEach((c, i) => {
        const x = 110 + i * 150, sel = this.selClass === i;
        ctx.fillStyle = sel ? c.c : "#1e293b"; ctx.fillRect(x, 180, 130, 220);
        ctx.strokeStyle = sel ? "#fff" : "#475569"; ctx.lineWidth = sel ? 3 : 1; ctx.strokeRect(x, 180, 130, 220);
        ctx.fillStyle = "#fff"; ctx.font = "bold 16px monospace"; ctx.fillText(c.id, x + 65, 215);
        ctx.font = "11px monospace"; ctx.fillText(c.d, x + 65, 245);
        let sy = 280; for (let s in c.s) { ctx.fillText(`+${c.s[s]} ${s.toUpperCase().slice(0,3)}`, x + 65, sy); sy += 20; }
      });
      ctx.fillStyle = "#cbd5e1"; ctx.font = "14px monospace"; ctx.fillText("[LEFT / RIGHT] Navigate  |  [SPACE] Descend", 400, 480);
      return;
    }
    ctx.save(); ctx.translate(-cx, -cy);
    for (let g of w.gates) {
      ctx.fillStyle = g.color; ctx.fillRect(g.x1 - 3, g.y - 14, 6, 14); ctx.fillRect(g.x2 - 3, g.y - 14, 6, 14);
      ctx.beginPath(); ctx.moveTo(g.x1, g.y - 14); ctx.lineTo(g.x1 + 10, g.y - 8); ctx.lineTo(g.x1, g.y - 2); ctx.fill();
      ctx.beginPath(); ctx.moveTo(g.x2, g.y - 14); ctx.lineTo(g.x2 - 10, g.y - 8); ctx.lineTo(g.x2, g.y - 2); ctx.fill();
    }
    ctx.font = "bold 12px monospace"; ctx.textAlign = "center";
    for (let ft of w.floatingTexts) { ctx.fillStyle = `rgba(255, 220, 0, ${Math.max(0, ft.life)})`; ctx.fillText(ft.text, ft.x, ft.y); }
    ctx.restore();
    ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(10, 10, 240, 52);
    ctx.fillStyle = "#fff"; ctx.font = "11px monospace"; ctx.textAlign = "left";
    ctx.fillText(`LVL ${p.level} [${p.classId || "ROOKIE"}] | STREAK: x${p.slalomStreak}`, 16, 26);
    const req = this.reqXp(p.level), pct = Math.min(1, p.xp / req);
    ctx.fillStyle = "#334155"; ctx.fillRect(16, 36, 228, 14); ctx.fillStyle = "#38bdf8"; ctx.fillRect(16, 36, 228 * pct, 14);
    ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.fillText(`${Math.floor(p.xp)} / ${req} XP`, 130, 47);
    if (gs === "LEVEL_UP") {
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)"; ctx.fillRect(150, 180, 500, 240);
      ctx.fillStyle = "#facc15"; ctx.font = "bold 20px monospace"; ctx.fillText("LEVEL UP - ATTRIBUTE UPGRADE", 400, 220);
      this.levelDraft.forEach((attr, idx) => {
        ctx.fillStyle = "#1e293b"; ctx.fillRect(180 + idx * 150, 260, 130, 100);
        ctx.fillStyle = "#fff"; ctx.font = "bold 14px monospace";
        ctx.fillText(`[${idx + 1}] +1 ${attr.toUpperCase()}`, 245 + idx * 150, 305);
        ctx.font = "12px monospace"; ctx.fillStyle = "#94a3b8"; ctx.fillText(`Now: ${st.stats[attr]}`, 245 + idx * 150, 335);
      });
    }
  }
});
