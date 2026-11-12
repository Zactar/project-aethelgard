// Cohesive Milestone Plugin: v0.5.0
// Cohesive Milestone Plugin: v0.5.0 - OMEGA-SYNTH LEVIATHAN, Meltdown FX & Arcade Run Summary
window.StudioEngine.registerModule("Milestone_v0_5_0", {
  init: function(state, engine) {
    state.world = state.world || {};
    state.stats = state.stats || { combo: 1 };
    state.meltdown = null;
    state.modal = state.modal || null;
    this.spacePressed = false;
    this.fanfarePlayed = false;
    this.offCanvas = null;

    // Load High-Score Leaderboard
    try {
      state.stats.leaderboard = JSON.parse(localStorage.getItem('HV_SCORES')) || [
        { name: 'VEX', score: 380000, rank: 'A-RANK' },
        { name: 'NYX', score: 240000, rank: 'B-RANK' },
        { name: 'KAI', score: 110000, rank: 'B-RANK' },
        { name: 'AXL', score: 65000, rank: 'C-RANK' },
        { name: 'ZED', score: 32000, rank: 'D-RANK' }
      ];
    } catch (_) { state.stats.leaderboard = []; }

    // Spawn OMEGA-SYNTH LEVIATHAN Boss
    state.world.boss = {
      active: true, phase: 1, x: 400, y: 150, angle: 0, rotSpeed: 0.008,
      hp: 6000, maxHp: 6000, radius: 72, beamAngle: 0, beamActive: false, attackTimer: 0,
      turrets: [0, 1, 2, 3].map(i => ({ hp: 500, maxHp: 500, relAngle: (i * Math.PI) / 2, dist: 88, active: true }))
    };

    // Helper: Reset Entire Run
    this.resetRun = (s) => {
      s.score = 0; s.stats.combo = 1; s.modal = null; s.paused = false; s.running = true;
      s.meltdown = null; this.fanfarePlayed = false;
      s.player = {
        x: 400, y: 480, vx: 0, vy: 0, angle: -Math.PI / 2, width: 22, height: 26,
        shields: 3, maxShields: 3, hp: 3, maxHp: 3, fireCooldown: 0, trail: [], invuln: 1.5,
        pilotId: s.player ? (s.player.pilotId || 'VALKYRIE') : 'VALKYRIE',
        dashing: false, dashTimer: 0, dashCd: 0
      };
      s.world.asteroids = []; s.world.enemyLasers = []; s.world.particles = []; s.world.floatingTexts = [];
      s.world.boss = {
        active: true, phase: 1, x: 400, y: 150, angle: 0, rotSpeed: 0.008,
        hp: 6000, maxHp: 6000, radius: 72, beamAngle: 0, beamActive: false, attackTimer: 0,
        turrets: [0, 1, 2, 3].map(i => ({ hp: 500, maxHp: 500, relAngle: (i * Math.PI) / 2, dist: 88, active: true }))
      };
    };
  },

  playArpeggio: function(state, freqs) {
    try {
      const a = (state.audio && state.audio.ctx) || (window.AudioContext ? new window.AudioContext() : null);
      if (!a) return;
      if (a.state === 'suspended') a.resume();
      freqs.forEach((f, idx) => {
        const osc = a.createOscillator(), g = a.createGain(), flt = a.createBiquadFilter();
        const t = a.currentTime + idx * 0.12;
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(Math.min(f, 640), t);
        flt.type = 'lowpass';
        flt.frequency.setValueAtTime(1100, t);
        g.gain.setValueAtTime(0.045, t);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.35);
        osc.connect(flt); flt.connect(g); g.connect(a.destination);
        osc.start(t); osc.stop(t + 0.36);
      });
    } catch (_) {}
  },

  update: function(dt, state) {
    const w = state.world, p = state.player, b = w ? w.boss : null;

    // --- RUN SUMMARY MODAL LOGIC ---
    if (state.modal === 'RUN_SUMMARY') {
      const spaceDown = !!(state.keys && (state.keys.jump || state.keys.Space || state.keys.action));
      if (spaceDown && !this.spacePressed) {
        this.spacePressed = true;
        this.resetRun(state);
      } else if (!spaceDown) {
        this.spacePressed = false;
      }
      return;
    }

    // Modal Pause Guard
    if (state.paused) return;

    // Detect Player Wipeout -> Run Summary
    if (p && ((p.shields !== undefined && p.shields <= 0 && p.hp <= 0) || (p.hp !== undefined && p.hp <= 0))) {
      this.triggerRunSummary(state, false);
      return;
    }

    // --- MELTDOWN EXPLOSION LOGIC ---
    if (state.meltdown) {
      const m = state.meltdown;
      m.timer--;
      const effDt = dt * 0.25;
      w.cameraShake = Math.max(w.cameraShake || 0, 14 * (m.timer / 180));

      // Shard bursts outward with quadratic scatter
      for (let i = 0; i < 4; i++) {
        const ang = Math.random() * Math.PI * 2, spd = (180 - m.timer) * 3.5 + Math.random() * 80;
        (w.particles || (w.particles = [])).push({
          x: m.x + (Math.random() - 0.5) * 40, y: m.y + (Math.random() - 0.5) * 40,
          vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd,
          color: ['#ff007f', '#00f3ff', '#ffea00'][Math.floor(Math.random() * 3)],
          life: 0.7, maxLife: 0.7, size: Math.random() * 4 + 2
        });
      }

      if (!this.fanfarePlayed) {
        this.fanfarePlayed = true;
        this.playArpeggio(state, [220, 277.18, 329.63, 440, 554.37, 659.25]);
      }

      if (m.timer <= 0) {
        state.meltdown = null;
        this.triggerRunSummary(state, true);
      }
      return;
    }

    // --- OMEGA-SYNTH LEVIATHAN BOSS LOGIC ---
    if (!b || !b.active) return;
    b.angle += b.rotSpeed;
    b.attackTimer += dt;
    w.enemyLasers = w.enemyLasers || [];

    // Phase Transitions based on HP
    b.phase = b.hp > 4000 ? 1 : b.hp > 1500 ? 2 : 3;
    b.rotSpeed = b.phase === 3 ? 0.018 : b.phase === 2 ? 0.012 : 0.008;

    // Phase 1: Radial Bursts from Active Turrets (Every 1.875s / 4 beats)
    if (b.phase === 1 && b.attackTimer >= 1.875) {
      b.attackTimer = 0;
      b.turrets.forEach(t => {
        if (!t.active) return;
        const tx = b.x + Math.cos(b.angle + t.relAngle) * t.dist;
        const ty = b.y + Math.sin(b.angle + t.relAngle) * t.dist;
        const toP = Math.atan2(p.y - ty, p.x - tx);
        [-0.26, 0, 0.26].forEach(spread => {
          (w.enemyLasers || (w.enemyLasers = [])).push({ x: tx, y: ty, vx: Math.cos(toP + spread) * 190, vy: Math.sin(toP + spread) * 190, r: 4, life: 3.5 });
        });
      });
    }

    // Phase 2: Dual Sweeping Prism Laser Chords
    if (b.phase >= 2) {
      b.beamActive = true;
      b.beamAngle += 0.025;
      const bLen = 650;
      [b.beamAngle, b.beamAngle + Math.PI].forEach(rad => {
        const bx2 = b.x + Math.cos(rad) * bLen, by2 = b.y + Math.sin(rad) * bLen;
        // Collision line-to-circle check against player
        const l2 = bLen * bLen, t = Math.max(0, Math.min(1, ((p.x - b.x) * (bx2 - b.x) + (p.y - b.y) * (by2 - b.y)) / l2));
        const cx = b.x + t * (bx2 - b.x), cy = b.y + t * (by2 - b.y);
        const distSq = (p.x - cx) ** 2 + (p.y - cy) ** 2;
        if (distSq < (18 + (p.width || 12)) ** 2 && (!p.invuln || p.invuln <= 0) && !p.dashing) {
          p.shields = (p.shields || 1) - 1;
          p.invuln = 1.2;
          w.cameraShake = 16;
        }
      });
    }

    // Phase 3: 16-way Spiral Projectile Volleys
    if (b.phase === 3 && b.attackTimer >= 0.75) {
      b.attackTimer = 0;
      for (let i = 0; i < 16; i++) {
        const theta = b.angle * 2 + (i * Math.PI * 2) / 16;
        (w.enemyLasers || (w.enemyLasers = [])).push({ x: b.x, y: b.y, vx: Math.cos(theta) * 210, vy: Math.sin(theta) * 210, r: 4.5, life: 3.0 });
      }
    }

    // Player Projectile Collisions with Turrets & Leviathan Core
    const playerLasers = w.lasers || [];
    for (let j = playerLasers.length - 1; j >= 0; j--) {
      const l = playerLasers[j];
      let hit = false;
      // Test active turrets first
      for (let k = 0; k < b.turrets.length; k++) {
        const t = b.turrets[k];
        if (!t.active) continue;
        const tx = b.x + Math.cos(b.angle + t.relAngle) * t.dist;
        const ty = b.y + Math.sin(b.angle + t.relAngle) * t.dist;
        if ((l.x - tx) ** 2 + (l.y - ty) ** 2 < 22 * 22) {
          t.hp -= 40; hit = true;
          if (t.hp <= 0) {
            t.active = false; b.hp = Math.max(0, b.hp - 500);
            w.cameraShake = 12;
            for (let s = 0; s < 18; s++) {
              const sa = Math.random() * Math.PI * 2, sp = 50 + Math.random() * 120;
              (w.particles || (w.particles = [])).push({ x: tx, y: ty, vx: Math.cos(sa) * sp, vy: Math.sin(sa) * sp, color: '#ffea00', life: 0.6, maxLife: 0.6, size: 3 });
            }
          }
          break;
        }
      }
      // Test Core
      if (!hit && (l.x - b.x) ** 2 + (l.y - b.y) ** 2 < b.radius ** 2) {
        b.hp = Math.max(0, b.hp - 35);
        state.score = (state.score || 0) + 120 * (state.stats.combo || 1);
        hit = true;
      }
      if (hit) {
        playerLasers.splice(j, 1);
        if (b.hp <= 0) {
          b.active = false;
          w.hitStop = 0.04;
          state.meltdown = { timer: 180, x: b.x, y: b.y, intensity: 1.0 };
          break;
        }
      }
    }
  },

  triggerRunSummary: function(state, victory) {
    state.paused = true;
    state.modal = 'RUN_SUMMARY';
    const sc = Math.floor(state.score || 0);
    const rk = sc > 500000 ? 'S-RANK: NEON DEITY' : sc > 300000 ? 'A-RANK: CHROME GLADIATOR' : sc > 150000 ? 'B-RANK: VECTOR ACE' : sc > 50000 ? 'C-RANK: VOID RUNNER' : 'D-RANK: STATIC';
    state.runSummary = {
      score: sc, rank: rk, victory,
      pilot: (state.player && state.player.pilotId) || 'VALKYRIE',
      quote: victory ? "SYNTH MATRIX OVERRIDDEN. SYSTEM ASCENDANT." : "SIGNAL FRAGMENTED IN THE EVENT HORIZON."
    };
    state.stats.leaderboard = state.stats.leaderboard || [];
    (state.stats.leaderboard || (state.stats.leaderboard = [])).push({ name: state.runSummary.pilot.slice(0, 3).toUpperCase(), score: sc, rank: rk.split(':')[0] });
    state.stats.leaderboard.sort((a, b) => b.score - a.score);
    state.stats.leaderboard = state.stats.leaderboard.slice(0, 5);
    try { localStorage.setItem('HV_SCORES', JSON.stringify(state.stats.leaderboard)); } catch (_) {}
  },

  render: function(ctx, state) {
    const w = state.world, b = w ? w.boss : null;

    // --- MELTDOWN CHROMATIC SPLIT DRAW ---
    if (state.meltdown && ctx.canvas) {
      const m = state.meltdown, cv = ctx.canvas;
      if (!this.offCanvas) {
        this.offCanvas = document.createElement('canvas');
        this.offCanvas.width = cv.width; this.offCanvas.height = cv.height;
      }
      const offCtx = this.offCanvas.getContext('2d');
      offCtx.clearRect(0, 0, cv.width, cv.height);
      offCtx.drawImage(cv, 0, 0);
      const dx = (m.timer / 180) * 14 * Math.sin(m.timer * 0.4);
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.drawImage(this.offCanvas, dx, 0);
      ctx.drawImage(this.offCanvas, -dx, 0);
      ctx.restore();
    }

    // Modal isolation: do not draw combat entities over non-summary menus
    if (state.paused && state.modal !== 'RUN_SUMMARY') return;

    // --- RENDER BOSS DIEGETICALLY ---
    if (b && b.active && !state.paused) {
      ctx.save();
      ctx.translate(b.x, b.y);

      // Sweeping Laser Chords
      if (b.beamActive) {
        ctx.strokeStyle = '#00f3ff';
        ctx.shadowColor = '#00f3ff';
        ctx.shadowBlur = 16;
        ctx.lineWidth = 4 + Math.sin(b.angle * 8) * 2;
        [b.beamAngle, b.beamAngle + Math.PI].forEach(ang => {
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(Math.cos(ang - b.angle) * 650, Math.sin(ang - b.angle) * 650);
          ctx.stroke();
        });
      }

      // Dreadnought Rotating Outer Polygonal Ring
      ctx.rotate(b.angle);
      ctx.strokeStyle = b.phase === 3 ? '#ff007f' : b.phase === 2 ? '#ffea00' : '#00f3ff';
      ctx.shadowColor = ctx.strokeStyle;
      ctx.shadowBlur = 14;
      ctx.lineWidth = 3.5;
      ctx.beginPath();
      for (let i = 0; i < 8; i++) {
        const rad = (i * Math.PI) / 4, r = b.radius + (i % 2 === 0 ? 12 : -6);
        ctx[i === 0 ? 'moveTo' : 'lineTo'](Math.cos(rad) * r, Math.sin(rad) * r);
      }
      ctx.closePath();
      ctx.stroke();

      // Pulsing Core
      ctx.fillStyle = '#05020d';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(0, 0, 24, 0, Math.PI * 2);
      ctx.strokeStyle = '#ff007f';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Destructible Turrets
      b.turrets.forEach(t => {
        const tx = Math.cos(t.relAngle) * t.dist, ty = Math.sin(t.relAngle) * t.dist;
        ctx.beginPath();
        ctx.arc(tx, ty, 10, 0, Math.PI * 2);
        ctx.strokeStyle = t.active ? '#39ff14' : '#444';
        ctx.shadowColor = t.active ? '#39ff14' : 'transparent';
        ctx.lineWidth = 2.5;
        ctx.stroke();
      });
      ctx.restore();

      // Diegetic Boss Hull Health Arc (Centered over boss, no HUD boxes)
      ctx.save();
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.radius + 24, -Math.PI * 0.8, -Math.PI * 0.8 + (Math.PI * 1.6) * (b.hp / b.maxHp));
      ctx.strokeStyle = '#ff007f';
      ctx.shadowColor = '#ff007f';
      ctx.shadowBlur = 10;
      ctx.lineWidth = 4;
      ctx.stroke();
      ctx.restore();
    }

    // --- RENDER ARCADE RUN SUMMARY MODAL ---
    if (state.modal === 'RUN_SUMMARY' && state.runSummary) {
      const s = state.runSummary;
      ctx.save();
      ctx.fillStyle = 'rgba(5, 2, 13, 0.92)';
      ctx.fillRect(0, 0, 800, 600);

      // Vector Framelines
      ctx.strokeStyle = s.victory ? '#00f3ff' : '#ff007f';
      ctx.shadowColor = ctx.strokeStyle;
      ctx.shadowBlur = 18;
      ctx.lineWidth = 3;
      ctx.strokeRect(60, 40, 680, 520);

      ctx.textAlign = 'center';
      ctx.font = '900 32px monospace';
      ctx.fillStyle = s.victory ? '#00f3ff' : '#ff007f';
      ctx.fillText(s.victory ? 'MISSION COMPLETE // VOID CONQUERED' : 'PILOT TERMINATED // HYPERVOID COLLAPSE', 400, 95);

      ctx.font = '700 20px monospace';
      ctx.fillStyle = '#ffea00';
      ctx.fillText(s.rank, 400, 140);

      ctx.font = '600 15px monospace';
      ctx.fillStyle = '#39ff14';
      ctx.fillText(`FINAL SCORE: ${s.score.toLocaleString()} PTS`, 400, 175);

      ctx.font = 'italic 13px monospace';
      ctx.fillStyle = '#a0a0b0';
      ctx.fillText(`"${s.quote}"`, 400, 210);

      // Top 5 High Score Leaderboard Table
      ctx.textAlign = 'left';
      ctx.font = '700 14px monospace';
      ctx.fillStyle = '#00f3ff';
      ctx.fillText('TOP SYNTH PILOTS:', 240, 260);

      (state.stats.leaderboard || []).forEach((entry, idx) => {
        const y = 295 + idx * 30;
        ctx.fillStyle = idx === 0 ? '#ffea00' : '#ffffff';
        ctx.fillText(`${idx + 1}. [${entry.name}]`, 240, y);
        ctx.textAlign = 'right';
        ctx.fillText(`${entry.score.toLocaleString()}  (${entry.rank})`, 560, y);
        ctx.textAlign = 'left';
      });

      // Press Space Indicator
      ctx.textAlign = 'center';
      ctx.font = '700 16px monospace';
      ctx.fillStyle = '#ff007f';
      ctx.shadowColor = '#ff007f';
      ctx.shadowBlur = 10;
      ctx.fillText('PRESS [SPACE] TO RE-ENTER THE VOID', 400, 515);

      ctx.restore();
    }
  }
});
