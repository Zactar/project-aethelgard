// Cohesive Milestone Plugin: v0.2.0 (Contender Configuration Modal, 3-Tier Minimax Oracle AI & Threat Telemetry)
window.StudioEngine.registerModule("Milestone_v0_2_0", {
  init: function(state, engine) {
    this.configOpen = true;
    state.paused = true;
    state.modal = "CONFIG";

    engine.on("KEYDOWN", (ev) => {
      const lat = state.world && state.world.lattice;
      if (!lat) return;

      // Allow pressing [KeyC] during gameplay to re-open the Sacred Lattice Architecture modal
      if (!this.configOpen && ev.code === "KeyC") {
        this.configOpen = true;
        state.paused = true;
        state.modal = "CONFIG";
        return;
      }

      if (!this.configOpen) return;

      if (ev.code === "Digit1") lat.aiTier = 1;
      else if (ev.code === "Digit2") lat.aiTier = 2;
      else if (ev.code === "Digit3") lat.aiTier = 3;
      else if (ev.code === "ShiftLeft" || ev.code === "ShiftRight" || ev.code === "KeyE") {
        lat.paletteIdx = (lat.paletteIdx + 1) % lat.palettes.length;
      } else if (ev.code === "KeyS" || ev.code === "ArrowDown") {
        const modes = ["PLAYER", "ARBITER", "ALTERNATE"];
        lat.openingMode = modes[(modes.indexOf(lat.openingMode) + 1) % modes.length];
      } else if (ev.code === "Space" || ev.code === "Enter") {
        this.closeConfig(state, engine);
      }
    });

    engine.on("POINTER_DOWN", (pt) => {
      if (!this.configOpen) return;
      // Clicking the COMMENCE DUEL button (or anywhere inside the modal button region) starts immediately
      if (pt.x >= 250 && pt.x <= 550 && pt.y >= 410 && pt.y <= 475) {
        this.closeConfig(state, engine);
      }
    });
  },

  closeConfig: function(state, engine) {
    this.configOpen = false;
    state.paused = false;
    state.modal = null;
    const m1 = engine.modules["Milestone_v0_1_0"];
    if (m1 && state.world.lattice) {
      state.world.lattice.bout = 0;
      m1.resetBout(state, engine);
    }
  },

  // 3-Tier Synthetic Arbiter AI (Called directly by Milestone_v0_1_0 when aiTimer reaches 0)
  computeArbiterMove: function(lat) {
    const b = lat.board;
    const empty = [];
    for (let i = 0; i < 9; i++) if (b[i] === null) empty.push(i);
    if (empty.length === 0) return -1;

    // Tier I: Opportunist (Takes immediate win if available, otherwise random vacant sector)
    const winMove = this._findTwoInRow(b, "O");
    if (winMove !== -1) return winMove;
    if (lat.aiTier === 1) {
      return empty[Math.floor(Math.random() * empty.length)];
    }

    // Tier II: Tactical Blocker (Blocks opponent 2-in-a-row threats, prefers center/corners)
    const blockMove = this._findTwoInRow(b, "X");
    if (blockMove !== -1) return blockMove;
    if (lat.aiTier === 2) {
      if (b[4] === null && Math.random() < 0.7) return 4;
      return empty[Math.floor(Math.random() * empty.length)];
    }

    // Tier III: Perfect Minimax Oracle
    let bestScore = -999, bestMove = empty[0];
    for (let i = 0; i < empty.length; i++) {
      const idx = empty[i];
      b[idx] = "O";
      const score = this._minimax(b, 0, false);
      b[idx] = null;
      if (score > bestScore) {
        bestScore = score;
        bestMove = idx;
      }
    }
    return bestMove;
  },

  _findTwoInRow: function(b, sym) {
    const triads = [
      [0,1,2],[3,4,5],[6,7,8],
      [0,3,6],[1,4,7],[2,5,8],
      [0,4,8],[2,4,6]
    ];
    for (let i = 0; i < triads.length; i++) {
      const [x, y, z] = triads[i];
      const vals = [b[x], b[y], b[z]];
      if (vals.filter(v => v === sym).length === 2 && vals.includes(null)) {
        if (b[x] === null) return x;
        if (b[y] === null) return y;
        if (b[z] === null) return z;
      }
    }
    return -1;
  },

  _checkWinnerRaw: function(b) {
    const triads = [
      [0,1,2],[3,4,5],[6,7,8],
      [0,3,6],[1,4,7],[2,5,8],
      [0,4,8],[2,4,6]
    ];
    for (let i = 0; i < triads.length; i++) {
      const [x, y, z] = triads[i];
      if (b[x] && b[x] === b[y] && b[x] === b[z]) return b[x];
    }
    return b.every(c => c !== null) ? "DRAW" : null;
  },

  _minimax: function(b, depth, isMaximizing) {
    const res = this._checkWinnerRaw(b);
    if (res === "O") return 10 - depth;
    if (res === "X") return depth - 10;
    if (res === "DRAW") return 0;

    if (isMaximizing) {
      let best = -999;
      for (let i = 0; i < 9; i++) {
        if (b[i] === null) {
          b[i] = "O";
          best = Math.max(best, this._minimax(b, depth + 1, false));
          b[i] = null;
        }
      }
      return best;
    } else {
      let best = 999;
      for (let i = 0; i < 9; i++) {
        if (b[i] === null) {
          b[i] = "X";
          best = Math.min(best, this._minimax(b, depth + 1, true));
          b[i] = null;
        }
      }
      return best;
    }
  },

  update: function(dt, state) {
    if (this.configOpen) {
      state.paused = true;
    }
  },

  render: function(ctx, state, engine) {
    const lat = state.world && state.world.lattice;
    if (!lat) return;
    const pal = lat.palettes[lat.paletteIdx] || lat.palettes[0];
    const m1 = engine.modules["Milestone_v0_1_0"];

    // 1. Render Pre-Series Contender Configuration Modal if Open
    if (this.configOpen) {
      ctx.save();
      ctx.fillStyle = "#090d18";
      ctx.fillRect(215, 118, 370, 375);
      ctx.strokeStyle = "#f43f5e";
      ctx.lineWidth = 2.5;
      ctx.strokeRect(215, 118, 370, 375);

      ctx.textAlign = "center";
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 16px monospace";
      ctx.fillText("SACRED LATTICE ARCHITECTURE", 400, 158);

      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px monospace";
      ctx.fillText("[1-3] COGNITIVE ARBITER TIER", 400, 196);

      const tiers = ["1. I: Opportunist", "2. II: Tactical Blocker", "3. III: Minimax Oracle"];
      for (let i = 0; i < 3; i++) {
        const active = (lat.aiTier === i + 1);
        ctx.fillStyle = active ? "#f43f5e" : "#64748b";
        ctx.font = active ? "bold 12px monospace" : "12px monospace";
        ctx.fillText(tiers[i], 400, 220 + i * 22);
      }

      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px monospace";
      ctx.fillText("[SHIFT/E] PALETTE", 400, 304);
      ctx.fillStyle = "#a855f7";
      ctx.font = "bold 12px monospace";
      ctx.fillText(`CREST THEME: ${pal.name}`, 400, 326);

      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px monospace";
      ctx.fillText("[S/DOWN] TEMPORAL ORDER", 400, 362);
      ctx.fillStyle = "#f8fafc";
      ctx.font = "bold 12px monospace";
      ctx.fillText(`OPENING: ${lat.openingMode}`, 400, 384);

      ctx.fillStyle = "#f43f5e";
      ctx.fillRect(280, 416, 240, 38);
      ctx.fillStyle = "#090d18";
      ctx.font = "bold 12px monospace";
      ctx.fillText("COMMENCE DUEL [SPACE]", 400, 440);
      ctx.restore();
      return;
    }

    if (!m1) return;
    ctx.save();

    // 2. Render Pulsing Collinear Threat-Threads (Whenever 2 of 3 sectors in a triad match!)
    const b = lat.board;
    const pulse = 0.35 + Math.sin(performance.now() * 0.008) * 0.2;
    for (let i = 0; i < m1.TRIADS.length; i++) {
      const [x, y, z] = m1.TRIADS[i];
      const vals = [b[x], b[y], b[z]];
      const xCount = vals.filter(v => v === "X").length;
      const oCount = vals.filter(v => v === "O").length;
      if ((xCount === 2 || oCount === 2) && vals.includes(null)) {
        const p1 = m1.getSectorCenter(x), p2 = m1.getSectorCenter(z);
        ctx.strokeStyle = xCount === 2 ? pal.xCol : pal.oCol;
        ctx.globalAlpha = pulse;
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 6]);
        ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // 3. Render Translucent Ghost-Sigil Hover Preview inside Vacant Cursor Sector
    if (lat.phase === "PLAYER_TURN" && lat.cursor >= 0 && lat.board[lat.cursor] === null) {
      const c = m1.getSectorCenter(lat.cursor);
      ctx.translate(c.x, c.y);
      ctx.strokeStyle = pal.xCol;
      ctx.globalAlpha = 0.25;
      ctx.lineWidth = 3.5;
      const r = 30;
      ctx.beginPath();
      ctx.moveTo(-r, -r); ctx.lineTo(r, r);
      ctx.moveTo(r, -r); ctx.lineTo(-r, r);
      ctx.stroke();
    }

    ctx.restore();
  }
});
