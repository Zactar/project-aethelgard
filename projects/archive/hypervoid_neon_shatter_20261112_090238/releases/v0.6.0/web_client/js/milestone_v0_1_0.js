// Cohesive Milestone Plugin: v0.1.0
window.StudioEngine.registerModule("Milestone_v0_1_0", {
  init: function(state) {
    state.running = true; state.score = 0; state.stats = state.stats || { combo: 1 };
    state.player = {
      x: 400, y: 300, vx: 0, vy: 0, angle: -Math.PI / 2, width: 22, height: 26,
      shields: 3, maxShields: 3, fireCooldown: 0, trail: [], invuln: 0
    };
    state.world = {
      cameraShake: 0, hitStop: 0, beatPulse: 0, wave: 1, comboTimer: 0,
      lasers: [], asteroids: [], gems: [], particles: [], floatingTexts: [],
      stars: Array.from({ length: 70 }, () => ({ x: Math.random() * 800, y: Math.random() * 600, s: Math.random() * 1.5 + 0.5, c: Math.random() > 0.5 ? '#00f3ff' : '#ff007f' }))
    };
    this.audioCtx = null;
    this.spawnAsteroid = (tier, x, y) => {
      const r = tier === 3 ? 40 : tier === 2 ? 22 : 11;
      const pts = Array.from({ length: 9 }, (_, i) => {
        const a = (i / 9) * Math.PI * 2, rad = r * (0.75 + Math.random() * 0.5);
        return { x: Math.cos(a) * rad, y: Math.sin(a) * rad };
      });
      const ang = Math.random() * Math.PI * 2, spd = (4 - tier) * 35 + Math.random() * 25;
      return { tier, x, y, r, vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd, rot: 0, vRot: (Math.random() - 0.5) * 2, pts, hp: tier, color: tier === 3 ? '#ff007f' : tier === 2 ? '#ffea00' : '#00f3ff' };
    };
    for (let i = 0; i < 4; i++) {
      const ex = Math.random() < 0.5 ? Math.random() * 200 : 600 + Math.random() * 200;
      (state.world.asteroids || (state.world.asteroids = [])).push(this.spawnAsteroid(3, ex, Math.random() * 600));
    }
  },

  playSynth: function(freq, type, dur, gainVal) {
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!this.audioCtx && AC) this.audioCtx = new AC();
      if (this.audioCtx && this.audioCtx.state === 'suspended') this.audioCtx.resume();
      if (!this.audioCtx) return;
      const osc = this.audioCtx.createOscillator(), g = this.audioCtx.createGain();
      osc.type = type; osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
      g.gain.setValueAtTime(gainVal || 0.15, this.audioCtx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + dur);
      osc.connect(g); g.connect(this.audioCtx.destination);
      osc.start(); osc.stop(this.audioCtx.currentTime + dur);
    } catch (_) {}
  },

  update: function(dt, state) {
    if (!state.running || state.paused) return;
    const w = state.world, p = state.player, keys = state.keys || {};
    if (w.hitStop > 0) { w.hitStop -= dt; return; }

    w.beatPulse = Math.sin(state.tick * 0.08) * 0.5 + 0.5;
    if (w.cameraShake > 0) w.cameraShake = Math.max(0, w.cameraShake - dt * 18);
    if (w.comboTimer > 0) { w.comboTimer -= dt; if (w.comboTimer <= 0) state.stats.combo = 1; }
    if (p.invuln > 0) p.invuln -= dt;

    // Kinematics & Controls
    const rotSpd = 4.2;
    if (keys.left || keys.a) p.angle -= rotSpd * dt;
    if (keys.right || keys.d) p.angle += rotSpd * dt;
    if (keys.up || keys.w) {
      const thrust = 360;
      p.vx += Math.cos(p.angle) * thrust * dt;
      p.vy += Math.sin(p.angle) * thrust * dt;
      (w.particles || (w.particles = [])).push({
        x: p.x - Math.cos(p.angle) * 14, y: p.y - Math.sin(p.angle) * 14,
        vx: -Math.cos(p.angle + (Math.random() - 0.5) * 0.6) * 120,
        vy: -Math.sin(p.angle + (Math.random() - 0.5) * 0.6) * 120,
        life: 0.25, maxLife: 0.25, color: '#00f3ff', r: 3
      });
    }
    p.vx *= 0.985; p.vy *= 0.985;
    p.x = (p.x + p.vx * dt + 800) % 800; p.y = (p.y + p.vy * dt + 600) % 600;
    p.trail.unshift({ x: p.x, y: p.y, angle: p.angle });
    if (p.trail.length > 10) p.trail.pop();

    // Weapon Fire
    p.fireCooldown -= dt;
    if ((keys.jump || keys.space) && p.fireCooldown <= 0) {
      p.fireCooldown = 0.14;
      const lx = p.x + Math.cos(p.angle) * 16, ly = p.y + Math.sin(p.angle) * 16;
      (w.lasers || (w.lasers = [])).push({ x: lx, y: ly, vx: Math.cos(p.angle) * 650 + p.vx * 0.3, vy: Math.sin(p.angle) * 650 + p.vy * 0.3, life: 1.1 });
       
      this.playSynth(780, 'sawtooth', 0.08, 0.12);
    }

    // Lasers update
    for (let i = w.lasers.length - 1; i >= 0; i--) {
      const l = w.lasers[i]; l.life -= dt;
      l.x = (l.x + l.vx * dt + 800) % 800; l.y = (l.y + l.vy * dt + 600) % 600;
      if (l.life <= 0) w.lasers.splice(i, 1);
    }

    // Asteroids update & Laser Collision
    for (let i = w.asteroids.length - 1; i >= 0; i--) {
      const a = w.asteroids[i];
      a.x = (a.x + a.vx * dt + 800) % 800; a.y = (a.y + a.vy * dt + 600) % 600; a.rot += a.vRot * dt;
      for (let j = w.lasers.length - 1; j >= 0; j--) {
        const l = w.lasers[j];
        if (Math.hypot(a.x - l.x, a.y - l.y) < a.r + 4) {
          w.lasers.splice(j, 1); a.hp--;
          w.cameraShake = Math.max(w.cameraShake, 3);
          for (let k = 0; k < 6; k++) (w.particles || (w.particles = [])).push({ x: l.x, y: l.y, vx: (Math.random() - 0.5) * 180, vy: (Math.random() - 0.5) * 180, life: 0.3, maxLife: 0.3, color: a.color, r: 2 });
          if (a.hp <= 0) {
            w.hitStop = 0.04; w.cameraShake += a.tier * 3.5;
            this.playSynth(140 + a.tier * 90, 'triangle', 0.22, 0.25);
            state.score += a.tier * 100 * state.stats.combo;
            if (a.tier === 3) {
              (w.asteroids || (w.asteroids = [])).push(this.spawnAsteroid(2, a.x, a.y), this.spawnAsteroid(2, a.x, a.y));
            } else if (a.tier === 2) {
              (w.asteroids || (w.asteroids = [])).push(this.spawnAsteroid(1, a.x, a.y), this.spawnAsteroid(1, a.x, a.y), this.spawnAsteroid(1, a.x, a.y));
            } else {
              const shards = 4 + Math.floor(Math.random() * 4);
              for (let s = 0; s < shards; s++) {
                const ga = Math.random() * Math.PI * 2, gspd = 50 + Math.random() * 80;
                (w.gems || (w.gems = [])).push({ x: a.x, y: a.y, vx: Math.cos(ga) * gspd, vy: Math.sin(ga) * gspd, life: 7 });
              }
            }
            w.asteroids.splice(i, 1);
            break;
          }
        }
      }
      // Asteroid vs Ship
      if (w.asteroids[i] && p.invuln <= 0 && Math.hypot(a.x - p.x, a.y - p.y) < a.r + 10) {
        p.shields = Math.max(0, (p.shields || 0) - 1); p.invuln = 1.5; w.cameraShake = 14; w.hitStop = 0.06;
        this.playSynth(90, 'sawtooth', 0.35, 0.3);
        if (p.shields <= 0) { p.shields = 0; state.running = false; }
      }
    }

    // Magnetic Score Gems
    for (let i = w.gems.length - 1; i >= 0; i--) {
      const g = w.gems[i]; g.life -= dt;
      const dx = p.x - g.x, dy = p.y - g.y, d = Math.hypot(dx, dy);
      if (d < 160) { const pull = (4200 / (d + 20)) * dt; g.vx += (dx / d) * pull; g.vy += (dy / d) * pull; }
      g.vx *= 0.96; g.vy *= 0.96; g.x = (g.x + g.vx * dt + 800) % 800; g.y = (g.y + g.vy * dt + 600) % 600;
      if (d < 16) {
        state.score += 50 * state.stats.combo; state.stats.combo = Math.min(16, state.stats.combo + 1);
        w.comboTimer = 3.5; this.playSynth(520 + state.stats.combo * 40, 'sine', 0.1, 0.12);
        w.gems.splice(i, 1);
      } else if (g.life <= 0) w.gems.splice(i, 1);
    }

    // Particles
    for (let i = w.particles.length - 1; i >= 0; i--) {
      const pt = w.particles[i]; pt.life -= dt;
      pt.x += pt.vx * dt; pt.y += pt.vy * dt;
      if (pt.life <= 0) w.particles.splice(i, 1);
    }

    // Wave Progression Spawner
    if (w.asteroids.length === 0) {
      w.wave++;
      for (let i = 0; i < 3 + w.wave; i++) {
        const sx = Math.random() < 0.5 ? 40 : 760, sy = Math.random() * 600;
        (w.asteroids || (w.asteroids = [])).push(this.spawnAsteroid(3, sx, sy));
      }
    }
  },

  render: function(ctx, state) {
    ctx.save();
    const w = state.world, p = state.player;
    const sx = (Math.random() - 0.5) * w.cameraShake, sy = (Math.random() - 0.5) * w.cameraShake;
    ctx.translate(sx, sy);
    ctx.fillStyle = '#05020d'; ctx.fillRect(-10, -10, 820, 620);

    // Parallax Starfield & Neon Warp-Grid
    w.stars.forEach(s => {
      ctx.fillStyle = s.c;
      ctx.fillRect((s.x - p.x * 0.05 * s.s + 800) % 800, (s.y - p.y * 0.05 * s.s + 600) % 600, s.s * 1.5, s.s * 1.5);
    });
    ctx.strokeStyle = '#1a0e38'; ctx.lineWidth = 1;
    for (let x = 0; x <= 800; x += 80) {
      ctx.beginPath();
      for (let y = 0; y <= 600; y += 40) {
        const offX = Math.sin(state.tick * 0.04 + y * 0.02) * (w.cameraShake * 1.2 + w.beatPulse * 4);
        y === 0 ? ctx.moveTo(x + offX, y) : ctx.lineTo(x + offX, y);
      }
      ctx.stroke();
    }

    // Gems
    ctx.shadowBlur = 8; ctx.shadowColor = '#39ff14'; ctx.fillStyle = '#39ff14';
    w.gems.forEach(g => { ctx.fillRect(g.x - 2, g.y - 2, 4, 4); });

    // Asteroids
    w.asteroids.forEach(a => {
      ctx.save(); ctx.translate(a.x, a.y); ctx.rotate(a.rot);
      ctx.strokeStyle = a.color; ctx.shadowColor = a.color; ctx.shadowBlur = 10; ctx.lineWidth = 2;
      ctx.beginPath();
      a.pts.forEach((pt, idx) => { idx === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y); });
      ctx.closePath(); ctx.stroke();
      ctx.restore();
    });

    // Lasers
    ctx.strokeStyle = '#00f3ff'; ctx.shadowColor = '#00f3ff'; ctx.shadowBlur = 12; ctx.lineWidth = 2.5;
    w.lasers.forEach(l => {
      ctx.beginPath(); ctx.moveTo(l.x, l.y); ctx.lineTo(l.x - l.vx * 0.02, l.y - l.vy * 0.02); ctx.stroke();
    });

    // Thruster & Combat Particles
    w.particles.forEach(pt => {
      ctx.shadowBlur = 6; ctx.shadowColor = pt.color; ctx.fillStyle = pt.color;
      ctx.globalAlpha = Math.max(0, pt.life / pt.maxLife);
      ctx.beginPath(); ctx.arc(pt.x, pt.y, pt.r, 0, Math.PI * 2); ctx.fill();
    });
    ctx.globalAlpha = 1.0;

    // Ship Trails (Afterimages)
    p.trail.forEach((t, i) => {
      ctx.save(); ctx.translate(t.x, t.y); ctx.rotate(t.angle);
      ctx.strokeStyle = '#ff007f'; ctx.shadowBlur = 0; ctx.globalAlpha = (1 - i / p.trail.length) * 0.25;
      ctx.beginPath(); ctx.moveTo(14, 0); ctx.lineTo(-10, -8); ctx.lineTo(-6, 0); ctx.lineTo(-10, 8); ctx.closePath(); ctx.stroke();
      ctx.restore();
    });

    // Player Ship
    if (p.invuln <= 0 || Math.floor(state.tick * 0.4) % 2 === 0) {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.angle);
      ctx.strokeStyle = '#00f3ff'; ctx.shadowColor = '#00f3ff'; ctx.shadowBlur = 12; ctx.lineWidth = 2;
      ctx.fillStyle = '#081726';
      ctx.beginPath(); ctx.moveTo(14, 0); ctx.lineTo(-11, -8); ctx.lineTo(-6, 0); ctx.lineTo(-11, 8); ctx.closePath();
      ctx.fill(); ctx.stroke();
      ctx.strokeStyle = '#ff007f'; ctx.beginPath(); ctx.arc(-6, 0, 3, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
    }
    ctx.restore();

    // STRICT HUD TOP RIBBON CONTRACT (y: 0..34)
    ctx.save();
    ctx.fillStyle = 'rgba(13, 8, 38, 0.88)'; ctx.fillRect(0, 0, 800, 34);
    ctx.strokeStyle = '#00f3ff'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, 34); ctx.lineTo(800, 34); ctx.stroke();

    ctx.textAlign = 'left'; ctx.font = 'bold 13px monospace';
    ctx.fillStyle = '#00f3ff'; ctx.fillText('SCORE ' + state.score.toString().padStart(6, '0'), 18, 22);
    ctx.fillStyle = '#ffea00'; ctx.fillText('COMBO x' + (state.stats.combo || 1), 210, 22);

    ctx.fillStyle = '#a094b8'; ctx.fillText('SHIELDS', 400, 22);
    for (let s = 0; s < p.maxShields; s++) {
      ctx.fillStyle = s < p.shields ? '#ff007f' : '#2a1a45';
      ctx.fillRect(470 + s * 22, 12, 16, 11);
      ctx.strokeStyle = '#00f3ff'; ctx.strokeRect(470 + s * 22, 12, 16, 11);
    }

    ctx.fillStyle = '#39ff14'; ctx.fillText('WAVE ' + (w.wave || 1), 700, 22);
    ctx.restore();
  }
});
