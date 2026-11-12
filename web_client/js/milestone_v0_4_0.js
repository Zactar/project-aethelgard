// Cohesive Milestone Plugin: v0.4.0 (Ephemeral 3-Sigil Decay Mutator, Half-Life Shimmer & Turn-Order Age Pips)
window.StudioEngine.registerModule("Milestone_v0_4_0", {
  init: function(state, engine) {
    this.motes = [];

    // Toggle Ephemeral Protocol anytime with [KeyM]
    engine.on("KEYDOWN", (ev) => {
      const lat = state.world && state.world.lattice;
      if (!lat) return;
      if (ev.code === "KeyM") {
        lat.ephemeralMode = !lat.ephemeralMode;
        const m1 = engine.modules["Milestone_v0_1_0"];
        if (m1 && lat.phase !== "ROUND_OVER") {
          m1.resetBout(state, engine);
        }
      }
    });
  },

  update: function(dt, state, engine) {
    if (!state.running || state.paused || state.modal) return;
    const lat = state.world && state.world.lattice;
    const m1 = engine.modules["Milestone_v0_1_0"];
    if (!lat || !m1) return;

    // Emit shimmering disintegration motes from any sigil that is oldest in a 3-sigil queue (queued to vanish next!)
    if (lat.ephemeralMode && lat.phase !== "ROUND_OVER") {
      ["X", "O"].forEach(sym => {
        const q = lat.moveOrder[sym] || [];
        if (q.length >= 3 && Math.random() < 0.35) {
          const oldestIdx = q[0];
          const c = m1.getSectorCenter(oldestIdx);
          const a = Math.random() * Math.PI * 2;
          this.motes.push({
            x: c.x + Math.cos(a) * 28,
            y: c.y + Math.sin(a) * 28,
            vx: Math.cos(a) * 22,
            vy: -18 - Math.random() * 20,
            color: sym === "X" ? "#38bdf8" : "#facc15",
            life: 0.55
          });
        }
      });
    }

    for (let i = this.motes.length - 1; i >= 0; i--) {
      const m = this.motes[i];
      m.x += m.vx * dt;
      m.y += m.vy * dt;
      m.life -= dt;
      if (m.life <= 0) this.motes.splice(i, 1);
    }
  },

  render: function(ctx, state, engine) {
    const lat = state.world && state.world.lattice;
    const m1 = engine.modules["Milestone_v0_1_0"];
    if (!lat || !m1 || state.paused || state.modal) return;
    const pal = lat.palettes[lat.paletteIdx] || lat.palettes[0];

    ctx.save();

    // 1. Render Turn-Order Age Pips ('I', 'II', 'III') in the top-left corner of each occupied sector
    const numerals = ["I", "II", "III", "IV", "V"];
    ["X", "O"].forEach(sym => {
      const q = lat.moveOrder[sym] || [];
      const col = sym === "X" ? pal.xCol : pal.oCol;
      for (let pos = 0; pos < q.length; pos++) {
        const idx = q[pos];
        if (lat.board[idx] !== sym) continue;
        const colIdx = idx % 3, rowIdx = Math.floor(idx / 3);
        const sx = 220 + colIdx * 120 + 12;
        const sy = 130 + rowIdx * 120 + 20;

        const isExpiringNext = lat.ephemeralMode && q.length >= 3 && pos === 0;
        ctx.fillStyle = isExpiringNext ? "#f43f5e" : col;
        ctx.globalAlpha = isExpiringNext ? (0.45 + Math.sin(performance.now() * 0.015) * 0.45) : 0.75;
        ctx.font = "bold 10px monospace";
        ctx.textAlign = "left";
        ctx.fillText(isExpiringNext ? "I [DECAY]" : numerals[pos] || "", sx, sy);

        // Shimmering half-life warning ring around sigil queued to vanish on next move
        if (isExpiringNext && lat.phase !== "ROUND_OVER") {
          const center = m1.getSectorCenter(idx);
          ctx.strokeStyle = "#f43f5e";
          ctx.lineWidth = 1.8;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.arc(center.x, center.y, 46 + Math.sin(performance.now() * 0.012) * 3, 0, Math.PI * 2);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    });

    // 2. Render Disintegration Motes
    ctx.globalAlpha = 1.0;
    for (let i = 0; i < this.motes.length; i++) {
      const m = this.motes[i];
      ctx.fillStyle = m.color;
      ctx.fillRect(m.x - 1.5, m.y - 1.5, 3, 3);
    }

    ctx.restore();
  }
});
