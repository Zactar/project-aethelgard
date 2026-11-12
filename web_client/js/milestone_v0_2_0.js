// Cohesive Milestone Plugin: v0.2.0
window.StudioEngine.registerModule("Milestone_v0_2_0", {
  init: function(state) {
    state.menu = state.menu || {};
    state.menu.pilotSelect = {
      active: true,
      selectedIndex: 0,
      transitionT: 1.0,
      pilots: [
        { id: 'vex', name: 'VEX // VIPER', color: '#00f3ff', weapon: 'TWIN', speed: 1.25, turn: 1.15, maxCd: 180, desc: 'Twin Pulse & Phase Dash',
          map: [0x07e,0x0ff,0x1e7,0x1bd,0x1ff,0x1ff,0x0ff,0x0bd,0x099,0x0ff,0x1ff,0x3e7] },
        { id: 'kaze', name: 'KAZE // GHOST', color: '#39ff14', weapon: 'RAIL', speed: 1.4, turn: 0.9, maxCd: 300, desc: 'Piercing Rail & Quantum Warp',
          map: [0x018,0x03c,0x07e,0x0ff,0x1db,0x1ff,0x1ff,0x0bd,0x07e,0x1c3,0x381,0x300] },
        { id: 'bass', name: 'BASS // TITAN', color: '#ffea00', weapon: 'SCATTER', speed: 0.85, turn: 0.8, maxCd: 420, desc: 'Sonic Scatter & Stasis EMP',
          map: [0x3ff,0x3ff,0x201,0x2db,0x3ff,0x3c3,0x3ff,0x1bd,0x0ff,0x1e7,0x3ff,0x3ff] },
        { id: 'nyx', name: 'NYX // MIRAGE', color: '#ff007f', weapon: 'MISSILE', speed: 1.05, turn: 1.3, maxCd: 360, desc: 'Homing Pods & Decoy Flare',
          map: [0x03c,0x07e,0x1ff,0x155,0x1ff,0x0ff,0x0bd,0x099,0x181,0x3c3,0x3c3,0x181] }
      ]
    };
    state.player.pilot = state.player.pilot || state.menu.pilotSelect.pilots[0];
    state.player.abilityCd = 0;
    state.player.abilityMaxCd = 180;
    state.player.regenTimer = 0;
    state.player.lastHitTimer = 0;
    state.player.decoy = null;
    state.stats = state.stats || {};
    state.stats.combo = 1.0;
    state.world.empWave = null;
    this.audioCtx = null;
    this.prevKeys = {};
  },

  playSynth: function(f, type, dur, gVal) {
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!this.audioCtx && AC) this.audioCtx = new AC();
      if (this.audioCtx && this.audioCtx.state === 'suspended') this.audioCtx.resume();
      if (!this.audioCtx) return;
      const osc = this.audioCtx.createOscillator(), g = this.audioCtx.createGain();
      osc.type = type; osc.frequency.setValueAtTime(f, this.audioCtx.currentTime);
      g.gain.setValueAtTime(gVal || 0.12, this.audioCtx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + dur);
      osc.connect(g); g.connect(this.audioCtx.destination);
      osc.start(); osc.stop(this.audioCtx.currentTime + dur);
    } catch (_) {}
  },

  fireWeapon: function(state) {
    const p = state.player, cos = Math.cos(p.angle), sin = Math.sin(p.angle);
    const sz = 1 + (state.stats.combo - 1) * 0.08;
    this.playSynth(p.pilot.weapon === 'RAIL' ? 880 : 360, 'sawtooth', 0.1, 0.15);
    p.vx -= cos * 30; p.vy -= sin * 30; // Visceral kickback
    if (p.pilot.weapon === 'TWIN') {
      const ox = -sin * 7, oy = cos * 7;
      [-1, 1].forEach(s => {
        (state.world.lasers || (state.world.lasers = [])).push({ x: p.x + ox * s, y: p.y + oy * s, vx: cos * 520, vy: sin * 520, life: 1.2, r: 3 * sz, pierce: 1, c: p.pilot.color });
      });
    } else if (p.pilot.weapon === 'RAIL') {
      (state.world.lasers || (state.world.lasers = [])).push({ x: p.x + cos * 15, y: p.y + sin * 15, vx: cos * 900, vy: sin * 900, life: 0.9, r: 4.5 * sz, pierce: 6, c: '#39ff14' });
    } else if (p.pilot.weapon === 'SCATTER') {
      for (let i = -3; i <= 3; i++) {
        const a = p.angle + i * 0.11;
        (state.world.lasers || (state.world.lasers = [])).push({ x: p.x, y: p.y, vx: Math.cos(a) * (420 + Math.random() * 60), vy: Math.sin(a) * (420 + Math.random() * 60), life: 0.65, r: 2.5 * sz, pierce: 1, c: '#ffea00' });
      }
    } else if (p.pilot.weapon === 'MISSILE') {
      [-1, 1].forEach(s => {
        const a = p.angle + s * 0.45;
        (state.world.lasers || (state.world.lasers = [])).push({ x: p.x, y: p.y, vx: Math.cos(a) * 220, vy: Math.sin(a) * 220, life: 1.8, r: 3.5 * sz, homing: true, pierce: 1, c: '#ff007f' });
      });
    }
  },

  triggerAbility: function(state) {
    const p = state.player, pilot = p.pilot;
    if (p.abilityCd > 0) return;
    p.abilityCd = p.abilityMaxCd;
    this.playSynth(700, 'square', 0.25, 0.2);
    if (pilot.id === 'vex') {
      p.vx += Math.cos(p.angle) * 450; p.vy += Math.sin(p.angle) * 450;
      p.invuln = 45; state.world.cameraShake = Math.max(state.world.cameraShake, 9);
    } else if (pilot.id === 'kaze') {
      p.x = (p.x + Math.cos(p.angle) * 220 + 800) % 800; p.y = (p.y + Math.sin(p.angle) * 220 + 600) % 600;
      p.invuln = 60; state.world.cameraShake = Math.max(state.world.cameraShake, 14);
    } else if (pilot.id === 'bass') {
      state.world.empWave = { x: p.x, y: p.y, r: 10, maxR: 260 };
      (state.world.asteroids || []).forEach(a => { if (Math.hypot(a.x - p.x, a.y - p.y) < 260) { a.vx *= 0.1; a.vy *= 0.1; a.vRot *= 0.1; } });
    } else if (pilot.id === 'nyx') {
      state.player.decoy = { x: p.x, y: p.y, life: 240, r: 18 };
      p.vx = -p.vx; p.vy = -p.vy;
    }
  },

  update: function(dt, state) {
    const k = state.keys || {}, ps = state.menu.pilotSelect, p = state.player;
    if (ps && ps.active) {
      if (k.left && !this.prevKeys.left) { ps.selectedIndex = (ps.selectedIndex + 3) % 4; this.playSynth(440, 'sine', 0.05, 0.1); }
      if (k.right && !this.prevKeys.right) { ps.selectedIndex = (ps.selectedIndex + 1) % 4; this.playSynth(520, 'sine', 0.05, 0.1); }
      if ((k.action || k.jump) && !this.prevKeys.action && !this.prevKeys.jump) {
        p.pilot = ps.pilots[ps.selectedIndex];
        p.abilityMaxCd = p.pilot.maxCd; p.abilityCd = 0;
        ps.active = false; this.playSynth(660, 'triangle', 0.25, 0.2);
      }
      this.prevKeys = { left: !!k.left, right: !!k.right, action: !!k.action, jump: !!k.jump };
      return;
    }
    this.prevKeys = { left: !!k.left, right: !!k.right, action: !!k.action, jump: !!k.jump };

    if (!state.running || state.paused) return;
    p.abilityCd = Math.max(0, p.abilityCd - 1);
    p.lastHitTimer = (p.lastHitTimer || 0) + 1;
    if (p.shields < p.maxShields && p.lastHitTimer > 300) {
      p.regenTimer = (p.regenTimer || 0) + 1;
      if (p.regenTimer >= 120) { p.shields++; p.regenTimer = 0; this.playSynth(587, 'sine', 0.2, 0.15); }
    } else { p.regenTimer = 0; }

    if ((k.shift || k.action) && p.abilityCd === 0) this.triggerAbility(state);
    if (k.jump && (p.fireCooldown || 0) <= 0) { this.fireWeapon(state); p.fireCooldown = 14; }

    // EMP propagation & Decoy decay
    if (state.world.empWave) {
      state.world.empWave.r += 6;
      if (state.world.empWave.r >= state.world.empWave.maxR) state.world.empWave = null;
    }
    if (p.decoy) { p.decoy.life--; if (p.decoy.life <= 0) p.decoy = null; }

    // Homing missiles guidance
    (state.world.lasers || []).forEach(l => {
      if (!l.homing) return;
      let target = null, minDist = 280;
      (state.world.asteroids || []).forEach(a => {
        const d = Math.hypot(a.x - l.x, a.y - l.y);
        if (d < minDist) { minDist = d; target = a; }
      });
      if (target) {
        const desired = Math.atan2(target.y - l.y, target.x - l.x), cur = Math.atan2(l.vy, l.vx);
        let da = desired - cur;
        while (da < -Math.PI) da += Math.PI * 2; while (da > Math.PI) da -= Math.PI * 2;
        const newAng = cur + Math.sign(da) * Math.min(Math.abs(da), 0.14), spd = Math.hypot(l.vx, l.vy);
        l.vx = Math.cos(newAng) * spd; l.vy = Math.sin(newAng) * spd;
      }
    });

    // Near-Miss "Graze" Mechanics & Overdrive Multiplier
    const pR = (p.width || 22) * 0.5;
    (state.world.asteroids || []).forEach(a => {
      const d = Math.hypot(p.x - a.x, p.y - a.y);
      if (d > pR + a.r && d <= pR + a.r + 34 && !a.grazed) {
        a.grazed = true;
        state.score += 150;
        state.stats.combo = Math.min(16.0, Number(((state.stats.combo || 1.0) + 0.25).toFixed(2)));
        state.world.floatingTexts = state.world.floatingTexts || [];
        (state.world.floatingTexts || (state.world.floatingTexts = [])).push({ x: p.x, y: p.y - 18, text: `GRAZE! ${state.stats.combo}x`, color: '#00f3ff', life: 35 });
        this.playSynth(784, 'triangle', 0.08, 0.12);
      }
    });
    state.stats.combo = Math.max(1.0, (state.stats.combo || 1.0) - 0.003 * dt);
  },

  render: function(ctx, state) {
    ctx.save();
    const ps = state.menu.pilotSelect, p = state.player, t = state.tick || 0;
    // Diegetic Ability Ring & Shield Pulse around player
    if (!ps.active && p) {
      const cdFrac = p.abilityCd / (p.abilityMaxCd || 1);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 24, -Math.PI * 0.5, -Math.PI * 0.5 + (1 - cdFrac) * Math.PI * 2);
      ctx.strokeStyle = p.pilot ? p.pilot.color : '#00f3ff';
      ctx.lineWidth = 2.5; ctx.shadowBlur = 9; ctx.shadowColor = ctx.strokeStyle;
      ctx.stroke();
      if (p.shields < p.maxShields && p.regenTimer > 0) {
        ctx.beginPath(); ctx.arc(p.x, p.y, 20 + (p.regenTimer % 30) * 0.4, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 243, 255, ${0.4 + (p.regenTimer / 120) * 0.5})`;
        ctx.lineWidth = 1.5; ctx.stroke();
      }
      if (p.decoy) {
        ctx.beginPath(); ctx.arc(p.decoy.x, p.decoy.y, p.decoy.r + Math.sin(t * 0.2) * 3, 0, Math.PI * 2);
        ctx.strokeStyle = '#ff007f'; ctx.lineWidth = 2; ctx.stroke();
      }
      if (state.world.empWave) {
        ctx.beginPath(); ctx.arc(state.world.empWave.x, state.world.empWave.y, state.world.empWave.r, 0, Math.PI * 2);
        ctx.strokeStyle = '#ffea00'; ctx.lineWidth = 3; ctx.shadowBlur = 12; ctx.stroke();
      }
    }

    // Neo-80s Pilot Select Modal Overlay
    if (ps && ps.active) {
      ctx.fillStyle = 'rgba(5, 2, 13, 0.94)';
      ctx.fillRect(0, 0, 800, 600);
      ctx.fillStyle = 'rgba(0, 243, 255, 0.035)';
      for (let y = 0; y < 600; y += 3) ctx.fillRect(0, y, 800, 1.2);

      ctx.textAlign = 'center'; ctx.font = 'bold 22px monospace';
      ctx.fillStyle = '#00f3ff'; ctx.shadowBlur = 14; ctx.shadowColor = '#00f3ff';
      ctx.fillText('// SELECT PILOT TRANSMISSION //', 400, 68);
      ctx.font = '12px monospace'; ctx.fillStyle = '#ffffff'; ctx.shadowBlur = 0;
      ctx.fillText('< LEFT / RIGHT > TO CYCLE -- [SPACE/ENTER] TO ENGAGE', 400, 94);

      ps.pilots.forEach((plt, i) => {
        const cx = 135 + i * 175, cy = 300, isSel = i === ps.selectedIndex;
        ctx.save();
        ctx.translate(cx, cy);
        if (isSel) {
          ctx.strokeStyle = plt.color; ctx.lineWidth = 2.5; ctx.shadowBlur = 18; ctx.shadowColor = plt.color;
          ctx.strokeRect(-76, -160, 152, 340);
        } else {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)'; ctx.lineWidth = 1; ctx.strokeRect(-76, -160, 152, 340);
        }

        // Procedural 12x12 Pixel Portrait
        ctx.fillStyle = plt.color; ctx.shadowBlur = isSel ? 10 : 0;
        for (let r = 0; r < 12; r++) {
          const rowBits = plt.map[r];
          for (let c = 0; c < 12; c++) {
            if (rowBits & (1 << (11 - c))) ctx.fillRect(-48 + c * 8, -135 + r * 8, 7, 7);
          }
        }

        // Vector Ship Hull Preview
        ctx.save();
        ctx.translate(0, 25);
        ctx.rotate((t + i * 40) * 0.035);
        ctx.beginPath();
        ctx.moveTo(0, -22); ctx.lineTo(16, 16); ctx.lineTo(0, 8); ctx.lineTo(-16, 16); ctx.closePath();
        ctx.strokeStyle = plt.color; ctx.lineWidth = isSel ? 2.5 : 1.5; ctx.shadowBlur = isSel ? 14 : 4; ctx.shadowColor = plt.color;
        ctx.stroke();
        ctx.restore();

        // Pilot Telemetry & Description
        ctx.textAlign = 'center'; ctx.font = 'bold 13px monospace'; ctx.fillStyle = isSel ? '#ffffff' : '#888888';
        ctx.fillText(plt.name, 0, 90);
        ctx.font = '10px monospace'; ctx.fillStyle = plt.color;
        ctx.fillText(plt.desc, 0, 115);

        // Relative Stat Bars
        const bar = (val, y, lbl) => {
          ctx.textAlign = 'left'; ctx.font = '9px monospace'; ctx.fillStyle = '#aaaaaa'; ctx.fillText(lbl, -65, y);
          ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fillRect(-15, y - 7, 75, 6);
          ctx.fillStyle = plt.color; ctx.fillRect(-15, y - 7, 75 * (val / 1.5), 6);
        };
        bar(plt.speed, 140, 'SPD'); bar(plt.turn, 155, 'AGI');
        ctx.restore();
      });
    }
    ctx.restore();
  }
});
