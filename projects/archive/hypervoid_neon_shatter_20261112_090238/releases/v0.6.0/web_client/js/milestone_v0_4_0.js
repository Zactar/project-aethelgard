// Cohesive Milestone Plugin: v0.4.0
// --- LOADED MODULE: milestone_v0_4_0.js ---
// Cohesive Milestone Plugin: v0.4.0
window.StudioEngine.registerModule("Milestone_v0_4_0", {
  init: function(state, engine) {
    state.director = state.director || {
      wave: 1, budget: 100, spawnedBudget: 0, spawnQueue: [], timer: 0, lastBatteryDrop: -99
    };
    state.world.barrels = state.world.barrels || [];
    state.world.enemies = state.world.enemies || [];
    state.world.singularities = state.world.singularities || [];
    state.world.shockwaves = state.world.shockwaves || [];
    state.world.enemyLasers = state.world.enemyLasers || [];
    state.world.batteries = state.world.batteries || [];

    // Ensure player dash properties
    state.player.dashing = state.player.dashing || false;
    state.player.dashTimer = state.player.dashTimer || 0;
    state.player.dashCd = state.player.dashCd || 0;

    // Seed initial plasma barrels
    if (state.world.barrels.length === 0) {
      for (let i = 0; i < 3; i++) {
        (state.world.barrels || (state.world.barrels = [])).push({
          x: 150 + Math.random() * 500, y: 120 + Math.random() * 360,
          hp: 30, maxHp: 30, r: 14, pulse: Math.random() * Math.PI
        });
      }
    }
  },

  playTone: function(state, freq, type, dur, gainVal) {
    try {
      const a = state.audio && state.audio.ctx ? state.audio.ctx : (this.audioCtx || (window.AudioContext ? new window.AudioContext() : null));
      this.audioCtx = a;
      if (!a) return;
      if (a.state === 'suspended') a.resume();
      const osc = a.createOscillator(), g = a.createGain();
      osc.type = type || 'sine';
      osc.frequency.setValueAtTime(Math.min(freq, 620), a.currentTime);
      g.gain.setValueAtTime(Math.min(gainVal || 0.05, 0.06), a.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + dur);
      osc.connect(g);
      g.connect(a.destination);
      osc.start();
      osc.stop(a.currentTime + dur);
    } catch (_) {}
  },

  update: function(dt, state, engine) {
    if (!state.running || state.paused || ((state.world && state.world.wave) || 1) < 2) return;
    const w = state.world, p = state.player, dir = state.director;

    // Handle Player Dash Input (Space / Shift / Action)
    if (p.dashCd > 0) p.dashCd -= dt;
    if (p.dashTimer > 0) {
      p.dashTimer -= dt;
      p.dashing = p.dashTimer > 0;
    } else {
      p.dashing = false;
    }

    if ((state.keys.shift || state.keys.action || state.keys.jump) && false) {
      p.dashing = true;
      p.dashTimer = 0.22;
      p.dashCd = 0.85;
      const spd = 420;
      p.vx = Math.cos(p.angle) * spd;
      p.vy = Math.sin(p.angle) * spd;
      this.playTone(state, 540, 'triangle', 0.18, 0.05);
      if (w.floatingTexts) (w.floatingTexts || (w.floatingTexts = [])).push({ text: "DASH", x: p.x, y: p.y - 18, life: 0.35, color: '#00f3ff' });
    }

    // 1. WAVE DIRECTOR & SPAWN QUEUE
    const currentWave = w.wave || dir.wave || 1;
    if (dir.wave !== currentWave) {
      dir.wave = currentWave;
      dir.budget = Math.floor(100 * Math.pow(1.25, dir.wave - 1));
      dir.spawnedBudget = 0;
    }

    dir.timer += dt;
    if (dir.spawnedBudget < dir.budget && dir.timer > 1.4) {
      dir.timer = 0;
      const rem = dir.budget - dir.spawnedBudget;
      let cost = 10, type = 'swarmer';
      if (rem >= 70 && Math.random() < 0.25) { cost = 70; type = 'singularity'; }
      else if (rem >= 35 && Math.random() < 0.5) { cost = 35; type = 'saucer'; }
      dir.spawnedBudget += cost;
      const sx = 60 + Math.random() * 680, sy = 60 + Math.random() * 480;
      (dir.spawnQueue || (dir.spawnQueue = [])).push({ type, x: sx, y: sy, timer: 0.8 });
    }

    // Process Warp Reticles
    for (let i = dir.spawnQueue.length - 1; i >= 0; i--) {
      const q = dir.spawnQueue[i];
      q.timer -= dt;
      if (q.timer <= 0) {
        if (q.type === 'swarmer') {
          (w.enemies || (w.enemies = [])).push({ type: 'swarmer', x: q.x, y: q.y, vx: 0, vy: 0, hp: 18, maxHp: 18, r: 10, color: '#ffea00' });
        } else if (q.type === 'saucer') {
          (w.enemies || (w.enemies = [])).push({ type: 'saucer', x: q.x, y: q.y, vx: 0, vy: 0, hp: 45, maxHp: 45, r: 16, fireTimer: 0.8, color: '#ff007f' });
        } else if (q.type === 'singularity') {
          (w.singularities || (w.singularities = [])).push({ x: q.x, y: q.y, hp: 300, maxHp: 300, r: 24, life: 8.0, pulse: 0 });
        }
        this.playTone(state, 220, 'square', 0.12, 0.04);
        dir.spawnQueue.splice(i, 1);
      }
    }

    // 2. SINGULARITIES (GRAVITY WELLS & DAMAGE COLLAPSE)
    for (let i = w.singularities.length - 1; i >= 0; i--) {
      const s = w.singularities[i];
      s.life -= dt;
      s.pulse += dt * 4;
      if (s.life <= 0 || s.hp <= 0) {
        (w.shockwaves || (w.shockwaves = [])).push({ x: s.x, y: s.y, r: 0, maxR: 160, life: 0.3, dmg: 180 });
        this.playTone(state, 110, 'sawtooth', 0.25, 0.06);
        w.singularities.splice(i, 1);
        continue;
      }
      const G = 120000, maxPull = 600;
      // Pull lasers
      const lasers = w.lasers || [];
      for (let l of lasers) {
        const dx = s.x - l.x, dy = s.y - l.y, d2 = dx * dx + dy * dy + 400;
        const dist = Math.sqrt(d2);
        const F = Math.min(G / d2, maxPull);
        l.vx = (l.vx || 0) + (dx / dist) * F * dt;
        l.vy = (l.vy || 0) + (dy / dist) * F * dt;
        if (dist < s.r + 8) {
          s.hp -= 15;
          l.life = 0;
        }
      }
      // Pull Asteroids
      const asts = w.asteroids || [];
      for (let a of asts) {
        const dx = s.x - a.x, dy = s.y - a.y, d2 = dx * dx + dy * dy + 800;
        const dist = Math.sqrt(d2);
        const F = Math.min((G * 0.8) / d2, 400);
        a.vx = (a.vx || 0) + (dx / dist) * F * dt;
        a.vy = (a.vy || 0) + (dy / dist) * F * dt;
      }
    }

    // 3. ENEMY SQUADRON AI (SAUCERS & SWARMERS)
    for (let i = w.enemies.length - 1; i >= 0; i--) {
      const e = w.enemies[i];
      if (e.type === 'swarmer') {
        const dx = p.x - e.x, dy = p.y - e.y, d = Math.hypot(dx, dy) || 1;
        const ax = (dx / d) * 320 - e.vx * 1.5;
        const ay = (dy / d) * 320 - e.vy * 1.5;
        e.vx += ax * dt; e.vy += ay * dt;
        e.x += e.vx * dt; e.y += e.vy * dt;
      } else if (e.type === 'saucer') {
        const dx = p.x - e.x, dy = p.y - e.y, d = Math.hypot(dx, dy) || 1;
        const perpX = -dy / d, perpY = dx / d;
        e.vx = perpX * 180 + (d > 220 ? (dx / d) * 60 : (d < 140 ? -(dx / d) * 80 : 0));
        e.vy = perpY * 180 + (d > 220 ? (dy / d) * 60 : (d < 140 ? -(dy / d) * 80 : 0));
        e.x += e.vx * dt; e.y += e.vy * dt;

        e.fireTimer = (e.fireTimer || 1.2) - dt;
        if (e.fireTimer <= 0) {
          e.fireTimer = 1.2;
          const bspd = 260;
          (w.enemyLasers || (w.enemyLasers = [])).push({
            x: e.x, y: e.y, vx: (dx / d) * bspd, vy: (dy / d) * bspd,
            r: 5, friendly: false, dmg: 1
          });
          this.playTone(state, 380, 'sine', 0.08, 0.04);
        }
      }

      // Check bullet collisions with enemies
      const lasers = w.lasers || [];
      for (let l of lasers) {
        if (l.life > 0 && Math.hypot(l.x - e.x, l.y - e.y) < e.r + 6) {
          l.life = 0;
          e.hp -= 20;
          if (e.hp <= 0) break;
        }
      }

      // Death & Battery Drops
      if (e.hp <= 0) {
        state.score += (e.type === 'saucer' ? 300 : 120);
        const combo = (state.stats && state.stats.combo) || 1;
        const now = state.tick ? state.tick * 0.016 : Date.now() * 0.001;
        if (combo >= 10 && (now - dir.lastBatteryDrop > 15)) {
          dir.lastBatteryDrop = now;
          (w.batteries || (w.batteries = [])).push({ x: e.x, y: e.y, life: 12.0, pulse: 0 });
          if (w.floatingTexts) (w.floatingTexts || (w.floatingTexts = [])).push({ text: "SHIELD BATTERY", x: e.x, y: e.y - 12, life: 0.6, color: '#39ff14' });
        }
        w.enemies.splice(i, 1);
      }
    }

    // 4. VOLATILE NEON PLASMA BARRELS
    for (let i = w.barrels.length - 1; i >= 0; i--) {
      const b = w.barrels[i];
      b.pulse += dt * 3;
      // Laser hits barrel
      const lasers = w.lasers || [];
      for (let l of lasers) {
        if (l.life > 0 && Math.hypot(l.x - b.x, l.y - b.y) < b.r + 6) {
          l.life = 0;
          b.hp -= 15;
        }
      }
      if (b.hp <= 0) {
        (w.shockwaves || (w.shockwaves = [])).push({ x: b.x, y: b.y, r: 0, maxR: 140, life: 0.25, dmg: 150 });
        this.playTone(state, 140, 'sawtooth', 0.2, 0.06);
        w.barrels.splice(i, 1);
      }
    }

    // 5. SHOCKWAVE PROPAGATION & CHAIN REACTIONS
    for (let i = w.shockwaves.length - 1; i >= 0; i--) {
      const sw = w.shockwaves[i];
      sw.r += (sw.maxR / 0.25) * dt;
      sw.life -= dt;
      // Detonate nearby barrels
      for (let b of w.barrels) {
        if (Math.hypot(b.x - sw.x, b.y - sw.y) <= sw.r + b.r) {
          b.hp = 0;
        }
      }
      // Damage enemies
      for (let e of w.enemies) {
        if (Math.hypot(e.x - sw.x, e.y - sw.y) <= sw.r + e.r) {
          e.hp -= sw.dmg * dt * 4;
        }
      }
      if (sw.life <= 0 || sw.r >= sw.maxR) {
        w.shockwaves.splice(i, 1);
      }
    }

    // 6. ENEMY PROJECTILES & DASH-PARRY MECHANIC
    for (let i = w.enemyLasers.length - 1; i >= 0; i--) {
      const b = w.enemyLasers[i];
      b.x += b.vx * dt;
      b.y += b.vy * dt;

      // Dash Parry Detection
      const distP = Math.hypot(b.x - p.x, b.y - p.y);
      if (!b.friendly && p.dashing && p.dashTimer > 0 && distP < 18 + b.r) {
        b.friendly = true;
        b.vx = -b.vx * 1.8;
        b.vy = -b.vy * 1.8;
        b.dmg = (b.dmg || 1) * 3;
        state.score += 250;
        if (state.engine) state.engine.hitStop = 0.04;
        if (w.floatingTexts) (w.floatingTexts || (w.floatingTexts = [])).push({ text: "PARRY! 3x", x: p.x, y: p.y - 20, life: 0.5, color: '#00f3ff' });
        this.playTone(state, 600, 'sine', 0.15, 0.06);
        continue;
      }

      // Friendly projectile striking enemies
      if (b.friendly) {
        for (let e of w.enemies) {
          if (Math.hypot(b.x - e.x, b.y - e.y) < e.r + b.r) {
            e.hp -= 40 * b.dmg;
            b.dead = true;
            break;
          }
        }
      } else if (!p.dashing && distP < (p.width * 0.5 || 12) + b.r) {
        // Player hit
        if (!p.invuln || p.invuln <= 0) {
          p.shields = Math.max(0, (p.shields || 1) - 1);
          p.invuln = 1.0;
          this.playTone(state, 120, 'sawtooth', 0.18, 0.06);
        }
        b.dead = true;
      }

      if (b.dead || b.x < -20 || b.x > 820 || b.y < -20 || b.y > 620) {
        w.enemyLasers.splice(i, 1);
      }
    }

    // 7. SHIELD BATTERY PICKUPS
    for (let i = w.batteries.length - 1; i >= 0; i--) {
      const bat = w.batteries[i];
      bat.life -= dt;
      bat.pulse += dt * 4;
      if (Math.hypot(bat.x - p.x, bat.y - p.y) < 22) {
        p.shields = Math.min((p.shields || 0) + 1, p.maxShields || 3);
        this.playTone(state, 440, 'triangle', 0.25, 0.05);
        if (w.floatingTexts) (w.floatingTexts || (w.floatingTexts = [])).push({ text: "+1 SHIELD", x: p.x, y: p.y - 16, life: 0.5, color: '#39ff14' });
        w.batteries.splice(i, 1);
        continue;
      }
      if (bat.life <= 0) w.batteries.splice(i, 1);
    }
  },

  render: function(ctx, state, engine) { if (state.paused || ((state.world && state.world.wave) || 1) < 2) return;
    ctx.save();
    const w = state.world, dir = state.director;

    // 1. Warp Reticles (Warning)
    if (dir && dir.spawnQueue) {
      for (let q of dir.spawnQueue) {
        const progress = 1 - (q.timer / 0.8);
        const radius = 35 * (1 - progress * 0.5);
        ctx.strokeStyle = q.type === 'singularity' ? '#bc13fe' : q.type === 'saucer' ? '#ff007f' : '#ffea00';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(q.x, q.y, radius, 0, Math.PI * 2);
        ctx.stroke();
        // Crosshair reticle
        ctx.beginPath();
        ctx.moveTo(q.x - 8, q.y); ctx.lineTo(q.x + 8, q.y);
        ctx.moveTo(q.x, q.y - 8); ctx.lineTo(q.x, q.y + 8);
        ctx.stroke();
      }
    }

    // 2. Singularities (Purple Gravity Wells)
    if (w.singularities) {
      for (let s of w.singularities) {
        ctx.save();
        ctx.translate(s.x, s.y);
        ctx.shadowColor = '#bc13fe';
        ctx.shadowBlur = 16;
        ctx.strokeStyle = '#d568ff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(0, 0, s.r + Math.sin(s.pulse) * 3, 0, Math.PI * 2);
        ctx.stroke();
        // Inner spiral core
        ctx.fillStyle = '#160028';
        ctx.beginPath();
        ctx.arc(0, 0, s.r * 0.7, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    // 3. Volatile Plasma Barrels
    if (w.barrels) {
      for (let b of w.barrels) {
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.shadowColor = '#00f3ff';
        ctx.shadowBlur = 10;
        ctx.strokeStyle = '#00f3ff';
        ctx.fillStyle = '#051824';
        ctx.lineWidth = 2;
        // Hex barrel
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
          const a = (i / 6) * Math.PI * 2;
          const px = Math.cos(a) * b.r, py = Math.sin(a) * b.r;
          if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill(); ctx.stroke();
        // Core glowing hazard dot
        ctx.fillStyle = '#ffea00';
        ctx.beginPath();
        ctx.arc(0, 0, 3 + Math.sin(b.pulse) * 1.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    // 4. Shockwaves
    if (w.shockwaves) {
      for (let sw of w.shockwaves) {
        ctx.strokeStyle = 'rgba(255, 0, 127, ' + Math.max(0, sw.life / 0.25) + ')';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(sw.x, sw.y, sw.r, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    // 5. Hostile Squadron AI
    if (w.enemies) {
      for (let e of w.enemies) {
        ctx.save();
        ctx.translate(e.x, e.y);
        ctx.shadowColor = e.color;
        ctx.shadowBlur = 12;
        ctx.strokeStyle = e.color;
        ctx.lineWidth = 2;
        if (e.type === 'swarmer') {
          const a = Math.atan2(e.vy, e.vx);
          ctx.rotate(a);
          ctx.beginPath();
          ctx.moveTo(10, 0); ctx.lineTo(-8, -6); ctx.lineTo(-4, 0); ctx.lineTo(-8, 6);
          ctx.closePath();
          ctx.stroke();
        } else if (e.type === 'saucer') {
          ctx.beginPath();
          ctx.ellipse(0, 0, 16, 7, 0, 0, Math.PI * 2);
          ctx.stroke();
          ctx.beginPath();
          ctx.arc(0, -3, 5, Math.PI, 0);
          ctx.stroke();
        }
        ctx.restore();
      }
    }

    // 6. Enemy Lasers
    if (w.enemyLasers) {
      for (let b of w.enemyLasers) {
        ctx.fillStyle = b.friendly ? '#00f3ff' : '#ff0055';
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // 7. Shield Batteries
    if (w.batteries) {
      for (let bat of w.batteries) {
        ctx.save();
        ctx.translate(bat.x, bat.y);
        ctx.shadowColor = '#39ff14';
        ctx.shadowBlur = 14;
        ctx.strokeStyle = '#39ff14';
        ctx.lineWidth = 2;
        ctx.strokeRect(-7, -9, 14, 18);
        ctx.fillStyle = '#39ff14';
        ctx.fillRect(-4, -12, 8, 3);
        ctx.fillRect(-4, -5 + Math.sin(bat.pulse) * 2, 8, 10);
        ctx.restore();
      }
    }

    // 8. Dash Parry Visualizer Aura around Player
    const p = state.player;
    if (p && p.dashing && p.dashTimer > 0) {
      ctx.strokeStyle = '#00f3ff';
      ctx.lineWidth = 3;
      ctx.shadowColor = '#00f3ff';
      ctx.shadowBlur = 16;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 18, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.restore();
  }
});
