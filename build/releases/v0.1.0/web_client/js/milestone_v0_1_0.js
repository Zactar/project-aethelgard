// Cohesive Milestone Plugin: v0.1.0
window.StudioEngine.registerModule("Milestone_v0_1_0", {
  init: function(state, engine) {
    state.world = state.world || {};
    state.stats = state.stats || {};
    state.pointer = state.pointer || { x: 400, y: 300, clicked: false };
    state.keys = state.keys || {};
    state.score = state.score || 0;

    state.world.matrix = { x: 220, y: 130, size: 360, cellSize: 120, selectedIndex: 4 };
    state.world.inscriptions = [];
    state.world.particles = [];
    state.world.floatingTexts = [];
    state.world.cameraShake = 0;

    state.stats.grid = Array(9).fill(null);
    state.stats.phase = 'PLAYER_TURN';
    state.stats.winner = null;
    state.stats.winVector = null;
    state.stats.aiTimer = 0;
    state.stats.roundsPlayed = 0;
    state.stats.initiatorWins = 0;
    state.stats.arbiterWins = 0;

    this.lines = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8],
      [0, 3, 6], [1, 4, 7], [2, 5, 8],
      [0, 4, 8], [2, 4, 6]
    ];
    this.prevKey = {};
    this.actx = null;

    engine.on("CELL_INSCRIBED", (payload, st) => {
      const idx = payload.cellIndex;
      const type = payload.type;
      (st.world.inscriptions || (st.world.inscriptions = [])).push({ cellIndex: idx, type: type, progress: 0 });
      const row = Math.floor(idx / 3), col = idx % 3;
      const cx = st.world.matrix.x + col * 120 + 60;
      const cy = st.world.matrix.y + row * 120 + 60;
      const color = type === 'BLADES' ? '#00f0ff' : '#ffd700';

      for (let i = 0; i < 24; i++) {
        const theta = (Math.PI * 2 * i) / 24 + (Math.random() - 0.5) * 0.4;
        const spd = 60 + Math.random() * 140;
        (st.world.particles || (st.world.particles = [])).push({
          x: cx, y: cy, vx: Math.cos(theta) * spd, vy: Math.sin(theta) * spd,
          life: 0.6 + Math.random() * 0.3, maxLife: 0.9, color: color, size: 2 + Math.random() * 2
        });
      }
      st.world.cameraShake = 4.5;
      this.playTone(type === 'BLADES' ? 360 : 280, 0.05, 'triangle', 0.14);
    });
  },

  playTone: function(freq, gainVal, type, dur) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!this.actx && AudioCtx) this.actx = new AudioCtx();
      if (!this.actx) return;
      if (this.actx.state === 'suspended') this.actx.resume();
      const osc = this.actx.createOscillator();
      const g = this.actx.createGain();
      osc.type = type || 'sine';
      osc.frequency.setValueAtTime(freq, this.actx.currentTime);
      g.gain.setValueAtTime(Math.min(gainVal, 0.06), this.actx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0001, this.actx.currentTime + dur);
      osc.connect(g);
      g.connect(this.actx.destination);
      osc.start();
      osc.stop(this.actx.currentTime + dur);
    } catch (_) {}
  },

  checkTerminal: function(state) {
    const g = state.stats.grid;
    for (let l of this.lines) {
      const [a, b, c] = l;
      if (g[a] && g[a] === g[b] && g[a] === g[c]) {
        state.stats.winner = g[a];
        state.stats.winVector = l;
        state.stats.phase = 'ROUND_OVER';
        if (g[a] === 'BLADES') { state.stats.initiatorWins++; state.score += 100; }
        else { state.stats.arbiterWins++; }
        this.playTone(g[a] === 'BLADES' ? 520 : 220, 0.06, 'sawtooth', 0.35);
        return true;
      }
    }
    if (g.every(c => c !== null)) {
      state.stats.winner = 'DEADLOCK';
      state.stats.winVector = null;
      state.stats.phase = 'ROUND_OVER';
      this.playTone(180, 0.04, 'sine', 0.25);
      return true;
    }
    return false;
  },

  resetBout: function(state) {
    state.stats.grid.fill(null);
    state.stats.winner = null;
    state.stats.winVector = null;
    state.stats.phase = 'PLAYER_TURN';
    state.stats.aiTimer = 0;
    state.stats.roundsPlayed++;
    state.world.inscriptions = [];
    this.playTone(440, 0.05, 'triangle', 0.1);
  },

  update: function(dt, state, engine) {
    const mat = state.world.matrix;
    const k = state.keys, pk = this.prevKey;

    if (state.pointer.x >= mat.x && state.pointer.x <= mat.x + mat.size &&
        state.pointer.y >= mat.y && state.pointer.y <= mat.y + mat.size) {
      const col = Math.min(2, Math.floor((state.pointer.x - mat.x) / mat.cellSize));
      const row = Math.min(2, Math.floor((state.pointer.y - mat.y) / mat.cellSize));
      mat.selectedIndex = row * 3 + col;
    } else {
      let r = Math.floor(mat.selectedIndex / 3);
      let c = mat.selectedIndex % 3;
      if ((k.left && !pk.left)) c = (c + 2) % 3;
      if ((k.right && !pk.right)) c = (c + 1) % 3;
      if ((k.up && !pk.up)) r = (r + 2) % 3;
      if ((k.down && !pk.down)) r = (r + 1) % 3;
      mat.selectedIndex = r * 3 + c;
    }

    const clickTrigger = (k.jump && !pk.jump) || state.pointer.clicked;
    if (state.pointer.clicked) state.pointer.clicked = false;

    if (state.stats.phase === 'ROUND_OVER') {
      if (clickTrigger) this.resetBout(state);
    } else if (state.stats.phase === 'PLAYER_TURN') {
      if (clickTrigger && state.stats.grid[mat.selectedIndex] === null) {
        state.stats.grid[mat.selectedIndex] = 'BLADES';
        engine.emit("CELL_INSCRIBED", { cellIndex: mat.selectedIndex, type: 'BLADES' });
        if (!this.checkTerminal(state)) {
          state.stats.phase = 'AI_THINKING';
          state.stats.aiTimer = 0.35;
        }
      }
    } else if (state.stats.phase === 'AI_THINKING') {
      state.stats.aiTimer -= dt;
      if (state.stats.aiTimer <= 0) {
        const bestMove = this.computeArbiterMove(state.stats.grid);
        if (bestMove !== -1) {
          state.stats.grid[bestMove] = 'RINGS';
          engine.emit("CELL_INSCRIBED", { cellIndex: bestMove, type: 'RINGS' });
          if (!this.checkTerminal(state)) state.stats.phase = 'PLAYER_TURN';
        }
      }
    }

    for (let ins of state.world.inscriptions) {
      if (ins.progress < 1) ins.progress = Math.min(1, ins.progress + dt * 3.8);
    }
    for (let i = state.world.particles.length - 1; i >= 0; i--) {
      const p = state.world.particles[i];
      p.x += p.vx * dt; p.y += p.vy * dt;
      p.vx *= 0.92; p.vy *= 0.92;
      p.life -= dt;
      if (p.life <= 0) state.world.particles.splice(i, 1);
    }
    if (state.world.cameraShake > 0) state.world.cameraShake = Math.max(0, state.world.cameraShake - dt * 14);

    this.prevKey = { up: !!k.up, down: !!k.down, left: !!k.left, right: !!k.right, jump: !!k.jump };
  },

  computeArbiterMove: function(grid) {
    for (let l of this.lines) {
      const [a, b, c] = l;
      const vals = [grid[a], grid[b], grid[c]];
      if (vals.filter(v => v === 'RINGS').length === 2 && vals.includes(null)) {
        return l[vals.indexOf(null)];
      }
    }
    for (let l of this.lines) {
      const [a, b, c] = l;
      const vals = [grid[a], grid[b], grid[c]];
      if (vals.filter(v => v === 'BLADES').length === 2 && vals.includes(null)) {
        return l[vals.indexOf(null)];
      }
    }
    if (grid[4] === null) return 4;
    const corners = [0, 2, 6, 8].filter(i => grid[i] === null);
    if (corners.length > 0) return corners[Math.floor(Math.random() * corners.length)];
    const empties = grid.map((v, i) => v === null ? i : null).filter(v => v !== null);
    return empties.length > 0 ? empties[Math.floor(Math.random() * empties.length)] : -1;
  },

  render: function(ctx, state) {
    const t = (state.tick || 0) * 0.016;
    ctx.save();
    ctx.fillStyle = '#070913';
    ctx.fillRect(0, 0, 800, 600);

    ctx.save();
    if (state.world.cameraShake > 0) {
      const ox = (Math.random() - 0.5) * state.world.cameraShake * 2;
      const oy = (Math.random() - 0.5) * state.world.cameraShake * 2;
      ctx.translate(ox, oy);
    }

    const mat = state.world.matrix;
    const gGrad = ctx.createRadialGradient(400, 310, 10, 400, 310, 240);
    gGrad.addColorStop(0, 'rgba(0, 240, 255, 0.05)');
    gGrad.addColorStop(1, 'rgba(7, 9, 19, 0)');
    ctx.fillStyle = gGrad;
    ctx.fillRect(mat.x - 40, mat.y - 40, mat.size + 80, mat.size + 80);

    ctx.lineWidth = 3;
    ctx.strokeStyle = '#1a233a';
    ctx.strokeRect(mat.x, mat.y, mat.size, mat.size);

    ctx.shadowBlur = 14;
    ctx.shadowColor = '#00f0ff';
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.8)';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(mat.x + 120, mat.y + 6); ctx.lineTo(mat.x + 120, mat.y + mat.size - 6);
    ctx.moveTo(mat.x + 240, mat.y + 6); ctx.lineTo(mat.x + 240, mat.y + mat.size - 6);
    ctx.moveTo(mat.x + 6, mat.y + 120); ctx.lineTo(mat.x + mat.size - 6, mat.y + 120);
    ctx.moveTo(mat.x + 6, mat.y + 240); ctx.lineTo(mat.x + mat.size - 6, mat.y + 240);
    ctx.stroke();
    ctx.shadowBlur = 0;

    const sRow = Math.floor(mat.selectedIndex / 3), sCol = mat.selectedIndex % 3;
    const hx = mat.x + sCol * 120, hy = mat.y + sRow * 120;
    ctx.fillStyle = state.stats.phase === 'PLAYER_TURN' ? 'rgba(0, 240, 255, 0.08)' : 'rgba(255, 215, 0, 0.05)';
    ctx.fillRect(hx + 4, hy + 4, 112, 112);
    ctx.strokeStyle = state.stats.phase === 'PLAYER_TURN' ? 'rgba(0, 240, 255, 0.4)' : 'rgba(255, 215, 0, 0.3)';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(hx + 6, hy + 6, 108, 108);

    for (let ins of state.world.inscriptions) {
      const idx = ins.cellIndex;
      const r = Math.floor(idx / 3), c = idx % 3;
      const cx = mat.x + c * 120 + 60, cy = mat.y + r * 120 + 60;
      const p = Math.min(1, Math.max(0, ins.progress));

      if (ins.type === 'BLADES') {
        ctx.shadowBlur = 12; ctx.shadowColor = '#00f0ff';
        ctx.strokeStyle = '#00f0ff'; ctx.lineWidth = 4; ctx.lineCap = 'round';
        ctx.beginPath();
        const arm = 34 * p;
        ctx.moveTo(cx - arm, cy - arm); ctx.lineTo(cx + arm, cy + arm);
        if (p > 0.4) {
          const arm2 = 34 * ((p - 0.4) / 0.6);
          ctx.moveTo(cx + arm2, cy - arm2); ctx.lineTo(cx - arm2, cy + arm2);
        }
        ctx.stroke();
      } else {
        ctx.shadowBlur = 12; ctx.shadowColor = '#ffd700';
        ctx.strokeStyle = '#ffd700'; ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(cx, cy, 32, -Math.PI / 2, -Math.PI / 2 + p * Math.PI * 2);
        ctx.stroke();
        if (p > 0.6) {
          ctx.beginPath();
          ctx.arc(cx, cy, 14, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
      ctx.shadowBlur = 0;
    }

    if (state.stats.winVector) {
      const [i1, , i3] = state.stats.winVector;
      const c1x = mat.x + (i1 % 3) * 120 + 60, c1y = mat.y + Math.floor(i1 / 3) * 120 + 60;
      const c3x = mat.x + (i3 % 3) * 120 + 60, c3y = mat.y + Math.floor(i3 / 3) * 120 + 60;
      const glow = 0.8 + 0.2 * Math.sin(t * 12);
      ctx.save();
      ctx.strokeStyle = state.stats.winner === 'BLADES' ? `rgba(0, 240, 255, ${glow})` : `rgba(255, 215, 0, ${glow})`;
      ctx.shadowColor = state.stats.winner === 'BLADES' ? '#00f0ff' : '#ffd700';
      ctx.shadowBlur = 18; ctx.lineWidth = 6; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(c1x, c1y); ctx.lineTo(c3x, c3y); ctx.stroke();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2.5; ctx.stroke();
      ctx.restore();
    }

    for (let p of state.world.particles) {
      ctx.fillStyle = p.color;
      ctx.globalAlpha = Math.max(0, p.life / p.maxLife);
      ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
    }
    ctx.globalAlpha = 1.0;
    ctx.restore();

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = 'rgba(7, 9, 19, 0.9)';
    ctx.fillRect(0, 0, 800, 42);
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
    ctx.beginPath(); ctx.moveTo(0, 42); ctx.lineTo(800, 42); ctx.stroke();

    ctx.font = '600 13px "Courier New", monospace';
    ctx.fillStyle = '#00f0ff';
    ctx.fillText(`TRINITAS // INITIATOR [${state.stats.initiatorWins}]`, 20, 26);
    ctx.fillStyle = '#ffd700';
    ctx.fillText(`SYNTHETIC ARBITER [${state.stats.arbiterWins}]`, 240, 26);
    ctx.fillStyle = '#8a99ad';
    ctx.fillText(`SCORE: ${Math.floor(state.score)}`, 490, 26);
    ctx.fillText(`BOUT: ${state.stats.roundsPlayed + 1}`, 690, 26);

    ctx.font = '600 14px "Courier New", monospace';
    ctx.textAlign = 'center';
    if (state.stats.phase === 'PLAYER_TURN') {
      ctx.fillStyle = '#00f0ff';
      ctx.fillText("INITIATOR'S DOMINION // SELECT VACANT SECTOR [SPACE / CLICK]", 400, 530);
    } else if (state.stats.phase === 'AI_THINKING') {
      ctx.fillStyle = '#ffd700';
      ctx.fillText("ARBITER SYNTHESIZING TRIAD TOPOLOGY...", 400, 530);
    } else {
      ctx.fillStyle = state.stats.winner === 'DEADLOCK' ? '#ffffff' : (state.stats.winner === 'BLADES' ? '#00f0ff' : '#ffd700');
      const banner = state.stats.winner === 'DEADLOCK' ? "EQUILIBRIUM DEADLOCK DETECTED" : `${state.stats.winner} DOMINATE THE LATTICE`;
      ctx.fillText(`${banner} // PRESS [SPACE] TO RE-ENGAGE`, 400, 530);
    }
    ctx.restore();
  }
});
