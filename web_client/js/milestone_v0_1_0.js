// Cohesive Milestone Plugin: v0.1.0 (The Ninefold Matrix, Zero-Lag Input & Collinear Triad Arbiter)
window.StudioEngine.registerModule("Milestone_v0_1_0", {
  init: function(state, engine) {
    const w = state.world;
    this.TRIADS = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8], // 3 Horizontal Ranks
      [0, 3, 6], [1, 4, 7], [2, 5, 8], // 3 Vertical Files
      [0, 4, 8], [2, 4, 6]             // 2 Main Diagonals
    ];

    w.lattice = {
      board: Array(9).fill(null),      // 'X' (Initiator Blades) or 'O' (Arbiter Rings)
      cellAnim: Array(9).fill(0),
      moveOrder: { X: [], O: [] },     // Tracks placement order for v0.4.0 Ephemeral Decay
      phase: "PLAYER_TURN",            // 'PLAYER_TURN' | 'AI_THINKING' | 'ROUND_OVER'
      winner: null,                    // 'X' | 'O' | 'DRAW'
      winTriad: null,
      winBeamProg: 0,
      cursor: 4,
      hovered: -1,
      aiTimer: 0,
      aiTier: 2,                       // 1: Opportunist, 2: Tactical Blocker, 3: Minimax Oracle
      openingMode: "PLAYER",           // 'PLAYER' | 'ARBITER' | 'ALTERNATE'
      paletteIdx: 0,
      palettes: [
        { name: "NEON // VOID", xCol: "#00f3ff", oCol: "#facc15", gridCol: "#00f3ff" },
        { name: "CRIMSON // GOLD", xCol: "#f43f5e", oCol: "#eab308", gridCol: "#f43f5e" },
        { name: "EMERALD // VIOLET", xCol: "#10b981", oCol: "#a855f7", gridCol: "#10b981" }
      ],
      playerWins: 0,
      arbiterWins: 0,
      deadlocks: 0,
      bout: 1,
      streak: 0,
      turnTimer: 12.0,
      maxTurnTimer: 12.0,
      blitzEnabled: true,
      ephemeralMode: false
    };

    w.particles = w.particles || [];

    // Direct, Zero-Lag Keyboard & Mouse Handlers
    engine.on("KEYDOWN", (ev) => {
      if (state.paused || state.modal) return;
      const lat = state.world.lattice;
      if (!lat) return;

      if (lat.phase === "ROUND_OVER") {
        if (ev.code === "Space" || ev.code === "Enter") {
          this.resetBout(state, engine);
        }
        return;
      }

      if (lat.phase !== "PLAYER_TURN") return;

      const r = Math.floor(lat.cursor / 3), c = lat.cursor % 3;
      if (ev.code === "ArrowUp" || ev.code === "KeyW") lat.cursor = ((r + 2) % 3) * 3 + c;
      else if (ev.code === "ArrowDown" || ev.code === "KeyS") lat.cursor = ((r + 1) % 3) * 3 + c;
      else if (ev.code === "ArrowLeft" || ev.code === "KeyA") lat.cursor = r * 3 + ((c + 2) % 3);
      else if (ev.code === "ArrowRight" || ev.code === "KeyD") lat.cursor = r * 3 + ((c + 1) % 3);
      else if (ev.code === "Space" || ev.code === "Enter") {
        this.claimSector(state, engine, lat.cursor, "X");
      }
    });

    engine.on("POINTER_DOWN", (pt) => {
      if (state.paused || state.modal) return;
      const lat = state.world.lattice;
      if (!lat) return;

      if (lat.phase === "ROUND_OVER") {
        this.resetBout(state, engine);
        return;
      }
      if (lat.phase === "PLAYER_TURN") {
        const idx = this.getSectorAtPoint(pt.x, pt.y);
        if (idx !== -1) {
          lat.cursor = idx;
          this.claimSector(state, engine, idx, "X");
        }
      }
    });
  },

  getSectorAtPoint: function(px, py) {
    const gx = 220, gy = 130, size = 360, cell = 120;
    if (px < gx || px >= gx + size || py < gy || py >= gy + size) return -1;
    const col = Math.floor((px - gx) / cell);
    const row = Math.floor((py - gy) / cell);
    return row * 3 + col;
  },

  getSectorCenter: function(idx) {
    const col = idx % 3, row = Math.floor(idx / 3);
    return { x: 220 + col * 120 + 60, y: 130 + row * 120 + 60 };
  },

  claimSector: function(state, engine, idx, symbol) {
    const lat = state.world.lattice;
    if (!lat || idx < 0 || idx > 8 || lat.board[idx] !== null || lat.phase === "ROUND_OVER") return false;

    // Ephemeral Protocol (v0.4.0): If contender already has 3 active sigils, dissolve the oldest one!
    const queue = lat.moveOrder[symbol];
    if (lat.ephemeralMode && queue.length >= 3) {
      const oldestIdx = queue.shift();
      lat.board[oldestIdx] = null;
      lat.cellAnim[oldestIdx] = 0;
      const oldPos = this.getSectorCenter(oldestIdx);
      for (let k = 0; k < 14; k++) {
        const a = (k / 14) * Math.PI * 2;
        state.world.particles.push({
          x: oldPos.x, y: oldPos.y,
          vx: Math.cos(a) * 110, vy: Math.sin(a) * 110,
          color: "#94a3b8", life: 0.45
        });
      }
    }

    lat.board[idx] = symbol;
    lat.cellAnim[idx] = 0.01;
    queue.push(idx);

    const center = this.getSectorCenter(idx);
    const pal = lat.palettes[lat.paletteIdx] || lat.palettes[0];
    const col = symbol === "X" ? pal.xCol : pal.oCol;
    for (let i = 0; i < 16; i++) {
      const a = (i / 16) * Math.PI * 2;
      const spd = 70 + Math.random() * 110;
      state.world.particles.push({
        x: center.x, y: center.y,
        vx: Math.cos(a) * spd, vy: Math.sin(a) * spd,
        color: col, life: 0.42
      });
    }

    engine.emit("SECTOR_INSCRIBED", { index: idx, symbol: symbol, x: center.x, y: center.y });

    // Immediately evaluate Win or 9-Sector Deadlock BEFORE switching turns!
    if (this.evaluateBoard(state, engine)) {
      return true;
    }

    if (symbol === "X") {
      // Award speed bonus if placed quickly
      const timeBonus = Math.floor(Math.max(0, lat.turnTimer) * 25);
      state.score = (state.score || 0) + 100 + timeBonus;
      lat.phase = "AI_THINKING";
      lat.aiTimer = 0.34;
    } else {
      lat.phase = "PLAYER_TURN";
      lat.turnTimer = lat.maxTurnTimer;
    }
    return true;
  },

  evaluateBoard: function(state, engine) {
    const lat = state.world.lattice;
    const b = lat.board;

    for (let i = 0; i < this.TRIADS.length; i++) {
      const [a, c, d] = this.TRIADS[i];
      if (b[a] && b[a] === b[c] && b[a] === b[d]) {
        lat.phase = "ROUND_OVER";
        lat.winner = b[a];
        lat.winTriad = [a, c, d];
        lat.winBeamProg = 0.01;
        if (b[a] === "X") {
          lat.playerWins++;
          lat.streak++;
          state.score = (state.score || 0) + 1000 * Math.max(1, lat.streak);
        } else {
          lat.arbiterWins++;
          lat.streak = 0;
        }
        engine.emit("BOUT_CONCLUDED", { winner: b[a], triad: [a, c, d] });
        return true;
      }
    }

    // Check 9-Sector Equilibrium Deadlock
    if (b.every(cell => cell !== null)) {
      lat.phase = "ROUND_OVER";
      lat.winner = "DRAW";
      lat.winTriad = null;
      lat.deadlocks++;
      state.score = (state.score || 0) + 250;
      engine.emit("BOUT_CONCLUDED", { winner: "DRAW", triad: null });
      return true;
    }

    return false;
  },

  resetBout: function(state, engine) {
    const lat = state.world.lattice;
    lat.board.fill(null);
    lat.cellAnim.fill(0);
    lat.moveOrder = { X: [], O: [] };
    lat.winner = null;
    lat.winTriad = null;
    lat.winBeamProg = 0;
    lat.bout++;
    lat.turnTimer = lat.maxTurnTimer;

    const arbiterStarts = (lat.openingMode === "ARBITER") || (lat.openingMode === "ALTERNATE" && (lat.bout % 2 === 0));
    if (arbiterStarts) {
      lat.phase = "AI_THINKING";
      lat.aiTimer = 0.40;
    } else {
      lat.phase = "PLAYER_TURN";
    }
    engine.emit("BOUT_RESET", { bout: lat.bout });
  },

  update: function(dt, state, engine) {
    if (!state.running || state.paused || state.modal) return;
    const lat = state.world.lattice;
    if (!lat) return;

    // Hover tracking
    const hIdx = this.getSectorAtPoint(state.pointer.x, state.pointer.y);
    lat.hovered = hIdx;
    if (hIdx !== -1 && lat.phase === "PLAYER_TURN") {
      lat.cursor = hIdx;
    }

    // Animate inscribed sigils & winning triad beam
    for (let i = 0; i < 9; i++) {
      if (lat.board[i] !== null && lat.cellAnim[i] < 1) {
        lat.cellAnim[i] = Math.min(1, lat.cellAnim[i] + dt * 6.5);
      }
    }
    if (lat.phase === "ROUND_OVER" && lat.winTriad && lat.winBeamProg < 1) {
      lat.winBeamProg = Math.min(1, lat.winBeamProg + dt * 4.5);
    }

    // AI Turn Execution (Delegates to v0.2.0 Minimax Oracle if registered, else fallback)
    if (lat.phase === "AI_THINKING") {
      lat.aiTimer -= dt;
      if (lat.aiTimer <= 0) {
        const m2 = engine.modules["Milestone_v0_2_0"];
        let chosen = -1;
        if (m2 && typeof m2.computeArbiterMove === "function") {
          chosen = m2.computeArbiterMove(lat);
        } else {
          const empty = [];
          for (let i = 0; i < 9; i++) if (!lat.board[i]) empty.push(i);
          if (empty.length > 0) chosen = empty[Math.floor(Math.random() * empty.length)];
        }
        if (chosen !== -1 && lat.board[chosen] === null) {
          this.claimSector(state, engine, chosen, "O");
        } else {
          this.evaluateBoard(state, engine);
        }
      }
    }

    // Update particles
    const pts = state.world.particles || [];
    for (let i = pts.length - 1; i >= 0; i--) {
      pts[i].x += pts[i].vx * dt;
      pts[i].y += pts[i].vy * dt;
      pts[i].life -= dt;
      if (pts[i].life <= 0) pts.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    const lat = state.world.lattice;
    if (!lat) return;
    const pal = lat.palettes[lat.paletteIdx] || lat.palettes[0];

    ctx.save();
    // 1. Deep Astral Observatory Background
    ctx.fillStyle = "#060811";
    ctx.fillRect(0, 0, 800, 600);

    // 2. Single Top Status Ribbon (y: 0..36)
    ctx.fillStyle = "#090d1a";
    ctx.fillRect(0, 0, 800, 36);
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, 36); ctx.lineTo(800, 36); ctx.stroke();

    ctx.font = "bold 12px monospace";
    ctx.textAlign = "left";
    ctx.fillStyle = pal.xCol;
    ctx.fillText(`TRINITAS // INITIATOR [${lat.playerWins}]`, 24, 23);
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`DEADLOCKS [${lat.deadlocks}]`, 235, 23);
    ctx.fillStyle = pal.oCol;
    ctx.fillText(`SYNTHETIC ARBITER [${lat.arbiterWins}]`, 365, 23);
    ctx.fillStyle = "#e2e8f0";
    ctx.fillText(`SCORE: ${state.score || 0}`, 575, 23);
    ctx.textAlign = "right";
    ctx.fillText(`BOUT: ${lat.bout}`, 776, 23);

    // 3. Render Outer Matrix Frame & Glowing Bisecting Dividers
    const gx = 220, gy = 130, size = 360, cell = 120;
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 3;
    ctx.strokeRect(gx - 6, gy - 6, size + 12, size + 12);

    // Active Cursor / Hover Highlight
    if (lat.phase === "PLAYER_TURN" && lat.cursor >= 0 && lat.cursor < 9) {
      const cx = gx + (lat.cursor % 3) * cell;
      const cy = gy + Math.floor(lat.cursor / 3) * cell;
      ctx.strokeStyle = "rgba(250, 204, 21, 0.45)";
      ctx.lineWidth = 2;
      ctx.strokeRect(cx + 6, cy + 6, cell - 12, cell - 12);
    }

    // Glowing Ninefold Dividers
    ctx.save();
    ctx.strokeStyle = pal.gridCol;
    ctx.shadowBlur = 12;
    ctx.shadowColor = pal.gridCol;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(gx + cell, gy + 8); ctx.lineTo(gx + cell, gy + size - 8);
    ctx.moveTo(gx + cell * 2, gy + 8); ctx.lineTo(gx + cell * 2, gy + size - 8);
    ctx.moveTo(gx + 8, gy + cell); ctx.lineTo(gx + size - 8, gy + cell);
    ctx.moveTo(gx + 8, gy + cell * 2); ctx.lineTo(gx + size - 8, gy + cell * 2);
    ctx.stroke();
    ctx.restore();

    // 4. Render Inscribed Geometric Sigils (Blades 'X' & Concentric Rings 'O')
    for (let i = 0; i < 9; i++) {
      const sym = lat.board[i];
      if (!sym) continue;
      const prog = lat.cellAnim[i] || 1;
      const center = this.getSectorCenter(i);

      ctx.save();
      ctx.translate(center.x, center.y);
      ctx.scale(prog, prog);
      if (sym === "X") {
        ctx.strokeStyle = pal.xCol;
        ctx.shadowBlur = 16;
        ctx.shadowColor = pal.xCol;
        ctx.lineWidth = 5;
        ctx.lineCap = "round";
        const r = 34;
        ctx.beginPath();
        ctx.moveTo(-r, -r); ctx.lineTo(r, r);
        ctx.moveTo(r, -r); ctx.lineTo(-r, r);
        ctx.stroke();
      } else {
        ctx.strokeStyle = pal.oCol;
        ctx.shadowBlur = 16;
        ctx.shadowColor = pal.oCol;
        ctx.lineWidth = 4.5;
        ctx.beginPath(); ctx.arc(0, 0, 36, 0, Math.PI * 2); ctx.stroke();
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(0, 0, 16, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.restore();
    }

    // 5. Render Harmonic Triad Laser Lock on Victory
    if (lat.phase === "ROUND_OVER" && lat.winTriad) {
      const pStart = this.getSectorCenter(lat.winTriad[0]);
      const pEnd = this.getSectorCenter(lat.winTriad[2]);
      const curX = pStart.x + (pEnd.x - pStart.x) * lat.winBeamProg;
      const curY = pStart.y + (pEnd.y - pStart.y) * lat.winBeamProg;
      const beamCol = lat.winner === "X" ? pal.xCol : pal.oCol;

      ctx.save();
      ctx.strokeStyle = beamCol;
      ctx.shadowBlur = 22;
      ctx.shadowColor = beamCol;
      ctx.lineWidth = 7;
      ctx.lineCap = "round";
      ctx.beginPath(); ctx.moveTo(pStart.x, pStart.y); ctx.lineTo(curX, curY); ctx.stroke();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.moveTo(pStart.x, pStart.y); ctx.lineTo(curX, curY); ctx.stroke();
      ctx.restore();
    }

    // 6. Particles & Bottom Status Prompt
    const pts = state.world.particles || [];
    for (let i = 0; i < pts.length; i++) {
      ctx.fillStyle = pts[i].color;
      ctx.fillRect(pts[i].x - 2, pts[i].y - 2, 4, 4);
    }

    ctx.font = "bold 13px monospace";
    ctx.textAlign = "center";
    if (lat.phase === "ROUND_OVER") {
      if (lat.winner === "X") {
        ctx.fillStyle = pal.xCol;
        ctx.fillText("BLADES DOMINATE THE LATTICE // PRESS [SPACE] OR CLICK TO RE-ENGAGE", 400, 536);
      } else if (lat.winner === "O") {
        ctx.fillStyle = pal.oCol;
        ctx.fillText("RINGS DOMINATE THE LATTICE // PRESS [SPACE] OR CLICK TO RE-ENGAGE", 400, 536);
      } else {
        ctx.fillStyle = "#e2e8f0";
        ctx.fillText("EQUILIBRIUM DEADLOCK DETECTED // PRESS [SPACE] OR CLICK TO RE-ENGAGE", 400, 536);
      }
    } else if (lat.phase === "AI_THINKING") {
      ctx.fillStyle = pal.oCol;
      ctx.fillText("ARBITER SYNTHESIZING TRIAD TOPOLOGY...", 400, 536);
    } else {
      ctx.fillStyle = "#94a3b8";
      ctx.fillText(`INITIATOR'S DOMINION // [CLICK / SPACE] INSCRIBE  |  [M] EPHEMERAL: ${lat.ephemeralMode ? "ON (MAX 3)" : "OFF"}  |  [C] CONFIG`, 400, 536);
    }

    ctx.restore();
  }
});
