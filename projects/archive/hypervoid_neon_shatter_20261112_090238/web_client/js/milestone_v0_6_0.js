// Cohesive Milestone Plugin: v0.6.0 (Operation Chrono-Fracture: Quantum Pylons, Phase-Blade Wake & Radial Shockwaves)
window.StudioEngine.registerModule("Milestone_v0_6_0", {
  init: function(state) {
    const w = state.world || (state.world = {});
    this.pylons = [
      { x: 210, y: 190, r: 22, angle: 0, charge: 0, maxCharge: 5, cooldown: 0, color: "#00f3ff" },
      { x: 590, y: 410, r: 22, angle: 1.5, charge: 0, maxCharge: 5, cooldown: 0, color: "#ff007f" }
    ];
    this.ribbonTrail = [];
    this.shockwaves = [];
    this.prevRockCount = 0;
    w.pylons = this.pylons;
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    const p = state.player, w = state.world;
    if (!p || !w) return;

    const lasers = w.lasers || w.bullets || [];
    const rocks = w.asteroids || w.rocks || [];
    const enemies = w.enemies || [];

    // 1. Detect Asteroid Splits -> Trigger Prismatic Radial Shockwaves!
    if (rocks.length > this.prevRockCount && this.prevRockCount > 0) {
      const refRock = rocks[rocks.length - 1];
      if (refRock) {
        this.shockwaves.push({
          x: refRock.x || 400, y: refRock.y || 300,
          r: 8, maxR: 115, life: 0.42, maxLife: 0.42,
          color: (w.beatPulse || 0) > 0.4 ? "#ffea00" : "#00f3ff"
        });
      }
    }
    this.prevRockCount = rocks.length;

    // 2. Update Quantum Singularity Pylons (Wave 2+ or always active geometric monoliths)
    for (let i = 0; i < this.pylons.length; i++) {
      const py = this.pylons[i];
      py.angle += (1.8 + py.charge * 0.6) * dt;
      if (py.cooldown > 0) py.cooldown = Math.max(0, py.cooldown - dt);

      // Slingshot & supercharge player lasers passing near the Pylon
      for (let j = 0; j < lasers.length; j++) {
        const l = lasers[j];
        if (!l || l.boostedByPylon) continue;
        const dx = l.x - py.x, dy = l.y - py.y;
        const dist = Math.hypot(dx, dy);
        if (dist < py.r + 18) {
          l.boostedByPylon = true;
          l.vx *= 1.45;
          l.vy *= 1.45;
          l.color = "#ffea00";
          l.r = (l.r || 3) + 2;
          if (py.cooldown <= 0) {
            py.charge++;
            if (py.charge >= py.maxCharge) {
              // Pylon Overload Implosion Shockwave!
              py.charge = 0;
              py.cooldown = 3.0;
              w.cameraShake = Math.max(w.cameraShake || 0, 9);
              this.shockwaves.push({ x: py.x, y: py.y, r: 10, maxR: 210, life: 0.55, maxLife: 0.55, color: "#ffea00" });
              this.shockwaves.push({ x: py.x, y: py.y, r: 4, maxR: 150, life: 0.40, maxLife: 0.40, color: "#ff007f" });
              for (let k = rocks.length - 1; k >= 0; k--) {
                const rk = rocks[k];
                if (rk && Math.hypot((rk.x || 0) - py.x, (rk.y || 0) - py.y) < 195) {
                  if (typeof rk.hp === "number") rk.hp -= 2;
                  state.score = (state.score || 0) + 120;
                }
              }
              (w.floatingTexts || (w.floatingTexts = [])).push({
                text: "⚡ PYLON SINGULARITY OVERLOAD! ⚡",
                x: py.x, y: py.y - 28, color: "#ffea00", life: 1.1
              });
            }
          }
        }
      }
    }

    // 3. Phasic Blink & High-Velocity Chromatic Ribbon Wake
    const spd = Math.hypot(p.vx || 0, p.vy || 0);
    if (spd > 65 || (p.invuln || 0) > 0.2) {
      this.ribbonTrail.push({
        x: p.x - Math.cos(p.angle || 0) * 10,
        y: p.y - Math.sin(p.angle || 0) * 10,
        color: (p.invuln || 0) > 0.2 ? "#ff007f" : (p.color || "#00f3ff"),
        life: 0.38, maxLife: 0.38
      });
      if (this.ribbonTrail.length > 28) this.ribbonTrail.shift();
    }

    // Phase-Blade Wake damages chasing enemies on contact
    for (let i = this.ribbonTrail.length - 1; i >= 0; i--) {
      const seg = this.ribbonTrail[i];
      seg.life -= dt;
      if (seg.life <= 0) {
        this.ribbonTrail.splice(i, 1);
        continue;
      }
      for (let e = enemies.length - 1; e >= 0; e--) {
        const en = enemies[e];
        if (en && Math.hypot((en.x || 0) - seg.x, (en.y || 0) - seg.y) < 20) {
          if (typeof en.hp === "number") en.hp -= 4 * dt;
          if (en.hp <= 0) {
            enemies.splice(e, 1);
            state.score = (state.score || 0) + 300;
          }
        }
      }
    }

    // Update Radial Shockwaves
    for (let i = this.shockwaves.length - 1; i >= 0; i--) {
      const sw = this.shockwaves[i];
      sw.life -= dt;
      sw.r += (sw.maxR - sw.r) * 7.5 * dt;
      if (sw.life <= 0) this.shockwaves.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const w = state.world;
    if (!w) return;

    ctx.save();

    // 1. Render Chromatic Phase-Blade Ribbon Wake behind Ship
    if (this.ribbonTrail.length > 1) {
      for (let i = 1; i < this.ribbonTrail.length; i++) {
        const a = this.ribbonTrail[i - 1], b = this.ribbonTrail[i];
        if (Math.hypot(b.x - a.x, b.y - a.y) > 100) continue; // skip screen-wrap jump
        ctx.strokeStyle = b.color;
        ctx.globalAlpha = Math.max(0, (b.life / b.maxLife) * 0.65);
        ctx.lineWidth = 3.5 * (b.life / b.maxLife);
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }

    // 2. Render Quantum Singularity Pylons (Rotating Geometric Diamond Monoliths)
    for (let i = 0; i < this.pylons.length; i++) {
      const py = this.pylons[i];
      ctx.save();
      ctx.translate(py.x, py.y);
      ctx.rotate(py.angle);
      ctx.globalAlpha = py.cooldown > 0 ? 0.35 : 0.85;
      ctx.strokeStyle = py.charge >= py.maxCharge - 1 ? "#ffea00" : py.color;
      ctx.shadowBlur = 12 + (w.beatPulse || 0) * 8;
      ctx.shadowColor = py.color;
      ctx.lineWidth = 2;

      // Outer geometric diamond
      ctx.beginPath();
      for (let k = 0; k < 4; k++) {
        const ang = (k / 4) * Math.PI * 2;
        const rx = Math.cos(ang) * py.r, ry = Math.sin(ang) * py.r;
        if (k === 0) ctx.moveTo(rx, ry); else ctx.lineTo(rx, ry);
      }
      ctx.closePath();
      ctx.stroke();

      // Inner charge core
      const coreR = 3 + (py.charge / py.maxCharge) * 12;
      ctx.fillStyle = py.color;
      ctx.beginPath();
      ctx.arc(0, 0, coreR, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // 3. Render Dual-Frequency Radial Tessellation Shockwaves
    for (let i = 0; i < this.shockwaves.length; i++) {
      const sw = this.shockwaves[i];
      ctx.save();
      ctx.globalAlpha = Math.max(0, sw.life / sw.maxLife);
      ctx.strokeStyle = sw.color;
      ctx.shadowBlur = 14;
      ctx.shadowColor = sw.color;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(sw.x, sw.y, sw.r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    ctx.restore();
  }
});
