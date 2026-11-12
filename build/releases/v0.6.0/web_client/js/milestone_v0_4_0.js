// Cohesive Milestone Plugin: v0.4.0
// Cohesive Milestone Plugin: v0.4.0 (Ephemeral Protocol, Dissolving Sigil Queues & Micro-Diamond Age Pips)
window.StudioEngine.registerModule("Milestone_v0_4_0", {
  init: function(state, engine) {
    state.stats = state.stats || {};
    state.stats.ephemeralProtocol = state.stats.ephemeralProtocol || false;
    state.stats.p1Queue = state.stats.p1Queue || [];
    state.stats.p2Queue = state.stats.p2Queue || [];
    state.world.particles = state.world.particles || [];
    state.world.time = state.world.time || 0;

    // Toggle Ephemeral Protocol Mutator via [KeyM]
    engine.on("KEYDOWN", (ev) => {
      if (state.paused || state.modal) return;
      if (ev.code === "KeyM") {
        state.stats.ephemeralProtocol = !state.stats.ephemeralProtocol;
        const lat = state.world && state.world.lattice;
        if (lat) {
          lat.ephemeralMode = state.stats.ephemeralProtocol;
          // Synchronize queues with current board state if toggled mid-bout
          this.rebuildQueues(state);
        }
      }
    });

    // Intercept sector inscription to enforce max 3 active sigils per contender
    engine.on("SECTOR_INSCRIBED", (ev) => {
      if (!state.stats.ephemeralProtocol) return;
      const isP1 = ev.symbol === "X";
      const queue = isP1 ? state.stats.p1Queue : state.stats.p2Queue;
      const faction = isP1 ? "X" : "O";

      if (queue.length >= 3) {
        const evicted = queue.shift();
        const lat = state.world.lattice;
        if (lat && lat.board) {
          lat.board[evicted] = null;
          lat.cellAnim[evicted] = 0;
        }
        if (state.world.matrix) state.world.matrix[evicted] = 0;

        engine.emit("EPHEMERAL_EVICT", { sector: evicted, faction: faction });
        this.spawnDissipationBurst(state, evicted, faction);
      }
      queue.push(ev.index);
    });

    // Rebuild fresh queues on bout resets
    engine.on("BOUT_RESET", () => {
      state.stats.p1Queue = [];
      state.stats.p2Queue = [];
    });
  },

  rebuildQueues: function(state) {
    const lat = state.world && state.world.lattice;
    if (!lat || !lat.board) return;
    state.stats.p1Queue = [];
    state.stats.p2Queue = [];
    lat.board.forEach((val, idx) => {
      if (val === "X" && state.stats.p1Queue.length < 3) (state.stats.p1Queue || (state.stats.p1Queue = [])).push(idx);
      else if (val === "O" && state.stats.p2Queue.length < 3) (state.stats.p2Queue || (state.stats.p2Queue = [])).push(idx);
    });
  },

  spawnDissipationBurst: function(state, sectorIdx, faction) {
    const lat = state.world && state.world.lattice;
    const pal = (lat && lat.palettes[lat.paletteIdx]) || { xCol: "#00f3ff", oCol: "#facc15" };
    const col = faction === "X" ? pal.xCol : pal.oCol;
    const r = Math.floor(sectorIdx / 3), c = sectorIdx % 3;
    const cx = 400 + (c - 1) * 120, cy = 310 + (r - 1) * 120;

    for (let i = 0; i < 24; i++) {
      const ang = (Math.PI * 2 * i) / 24 + (Math.random() - 0.5) * 0.3;
      const spd = 35 + Math.random() * 55;
      (state.world.particles || (state.world.particles = [])).push({
        x: cx, y: cy,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd,
        life: 0.65, maxLife: 0.65,
        color: col, size: 2.2 + Math.random() * 2
      });
    }
  },

  update: function(dt, state) {
    if (state.paused) return;
    state.world.time = (state.world.time || 0) + dt;
    if (!state.stats.ephemeralProtocol) return;

    const lat = state.world && state.world.lattice;
    if (!lat || lat.phase === "ROUND_OVER") return;

    // Continuous decay particle motes emitted from target sectors queued to vanish next
    const checkTarget = (queue, sym) => {
      if (queue.length === 3) {
        const target = queue[0];
        const r = Math.floor(target / 3), c = target % 3;
        const cx = 400 + (c - 1) * 120, cy = 310 + (r - 1) * 120;
        const pal = lat.palettes[lat.paletteIdx] || { xCol: "#00f3ff", oCol: "#facc15" };
        const col = sym === "X" ? pal.xCol : pal.oCol;

        if (Math.random() < 0.45) {
          (state.world.particles || (state.world.particles = [])).push({
            x: cx + (Math.random() - 0.5) * 44,
            y: cy + (Math.random() - 0.5) * 44,
            vx: (Math.random() - 0.5) * 28,
            vy: -Math.random() * 35 - 10,
            life: 0.6, maxLife: 0.6,
            color: col, size: 1.8
          });
        }
      }
    };

    checkTarget(state.stats.p1Queue, "X");
    checkTarget(state.stats.p2Queue, "O");
  },

  render: function(ctx, state) {
    if (!state.stats.ephemeralProtocol) return;
    const lat = state.world && state.world.lattice;
    if (!lat || !lat.board) return;

    const pal = lat.palettes[lat.paletteIdx] || { xCol: "#00f3ff", oCol: "#facc15" };
    const t = state.world.time || 0;

    ctx.save();

    // Render shimmering half-life caustics on the oldest sigil when queue is saturated (3/3)
    const renderHalflife = (queue, factionCol) => {
      if (queue.length !== 3) return;
      const target = queue[0];
      const r = Math.floor(target / 3), c = target % 3;
      const cx = 400 + (c - 1) * 120, cy = 310 + (r - 1) * 120;
      const alpha = 0.5 + 0.5 * Math.sin(t * 6);
      const jx = (Math.random() - 0.5) * 2.2, jy = (Math.random() - 0.5) * 2.2;

      ctx.save();
      ctx.strokeStyle = factionCol;
      ctx.globalAlpha = Math.max(0.1, alpha * 0.85);
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(cx - 52 + jx, cy - 52 + jy, 104, 104);
      ctx.restore();
    };

    renderHalflife(state.stats.p1Queue, pal.xCol);
    renderHalflife(state.stats.p2Queue, pal.oCol);

    // Diegetic turn-order micro-diamonds (1=oldest, 3=newest) etched in occupied sector corners
    lat.board.forEach((val, idx) => {
      if (!val) return;
      const queue = val === "X" ? state.stats.p1Queue : state.stats.p2Queue;
      const queueIdx = queue.indexOf(idx);
      if (queueIdx === -1) return;

      const pipCount = queueIdx + 1; // 1, 2, or 3
      const r = Math.floor(idx / 3), c = idx % 3;
      const sx = 400 + (c - 1) * 120 - 60, sy = 310 + (r - 1) * 120 - 60;
      const baseCol = val === "X" ? pal.xCol : pal.oCol;

      for (let p = 0; p < pipCount; p++) {
        const px = sx + 104 - (pipCount - 1 - p) * 7.5;
        const py = sy + 14;
        let alpha = 0.85;

        // Oldest pip (p === 0 when pipCount === 1, or decaying next) flickers erratically
        if (p === 0 && queueIdx === 0 && queue.length === 3) {
          alpha = Math.sin(t * 12) > 0 ? 0.3 : 0.95;
        }

        ctx.save();
        ctx.fillStyle = (p === 0 && queue.length === 3) ? baseCol : "#e2e8f0";
        ctx.shadowColor = baseCol;
        ctx.shadowBlur = 4;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.moveTo(px, py - 2.5);
        ctx.lineTo(px + 2.5, py);
        ctx.lineTo(px, py + 2.5);
        ctx.lineTo(px - 2.5, py);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
    });

    ctx.restore();
  }
});
