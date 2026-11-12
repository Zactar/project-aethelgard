// Cohesive Milestone Plugin: v0.2.0 (Pixel-Art Pilot Select, Signature Weapons & Overdrive Specials)
window.StudioEngine.registerModule("Milestone_v0_2_0", {
  init: function(state, engine) {
    this.pilots = [
      {
        id: "VEX", name: "VEX // VIPER", color: "#00f3ff", accent: "#ff007f",
        desc: "Twin Pulse & Phase Dash", spd: 0.9, agi: 0.85,
        weaponName: "TWIN PULSE LASERS", specialName: "PHASE-BLINK NOVA", cdMax: 4.5,
        bitmap: [0b001111,0b011111,0b111111,0b110000,0b110000,0b111111,0b111111,0b011110,0b011011,0b001111,0b001110,0b000100]
      },
      {
        id: "KAZE", name: "KAZE // GHOST", color: "#39ff14", accent: "#ffea00",
        desc: "Piercing Rail & Cyber Slash", spd: 0.95, agi: 0.75,
        weaponName: "PIERCING RAIL-LANCE", specialName: "360° KATANA EMP SLASH", cdMax: 5.0,
        bitmap: [0b000111,0b011111,0b111111,0b011111,0b110001,0b111111,0b011110,0b011111,0b001101,0b011001,0b010000,0b000000]
      },
      {
        id: "BASS", name: "BASS // TITAN", color: "#ffea00", accent: "#ff007f",
        desc: "5-Way Scatter & Bass Shockwave", spd: 0.70, agi: 0.65,
        weaponName: "5-WAY SONIC SCATTER", specialName: "SUBWOOFER BASS-DROP", cdMax: 6.0,
        bitmap: [0b011111,0b111111,0b110111,0b110000,0b110000,0b111111,0b111001,0b111111,0b110111,0b111111,0b011110,0b001100]
      },
      {
        id: "NYX", name: "NYX // MIRAGE", color: "#ff007f", accent: "#00f3ff",
        desc: "Homing Pods & Chrono-Overclock", spd: 0.85, agi: 0.95,
        weaponName: "HOMING SYNTH-PODS", specialName: "CHRONO-TIME OVERCLOCK", cdMax: 6.5,
        bitmap: [0b000111,0b001111,0b011111,0b111001,0b110000,0b111001,0b011111,0b011110,0b001111,0b011011,0b110001,0b100000]
      }
    ];

    this.menuActive = true;
    this.selectedIdx = 0;
    this.fireTimer = 0;
    this.specialCd = 0;
    this.specialFx = [];
    this.afterimages = [];
    this.chronoTimer = 0;
    this.bannerTimer = 0;
    this.bannerText = "";

    state.paused = true;
    state.player.pilot = this.pilots[0];
    state.player.color = this.pilots[0].color;

    engine.on("KEYDOWN", (ev) => {
      if (this.menuActive) {
        if (ev.code === "ArrowLeft" || ev.code === "KeyA") {
          this.selectedIdx = (this.selectedIdx + 3) % 4;
        } else if (ev.code === "ArrowRight" || ev.code === "KeyD") {
          this.selectedIdx = (this.selectedIdx + 1) % 4;
        } else if (ev.code === "Digit1") { this.selectedIdx = 0; this.confirmPilot(state); }
        else if (ev.code === "Digit2") { this.selectedIdx = 1; this.confirmPilot(state); }
        else if (ev.code === "Digit3") { this.selectedIdx = 2; this.confirmPilot(state); }
        else if (ev.code === "Digit4") { this.selectedIdx = 3; this.confirmPilot(state); }
        else if (ev.code === "Space" || ev.code === "Enter") {
          this.confirmPilot(state);
        }
        return;
      }

      // Active Gameplay: [SHIFT] or [E] triggers Pilot Signature Overdrive Special!
      if (!state.paused && (ev.code === "ShiftLeft" || ev.code === "ShiftRight" || ev.code === "KeyE")) {
        this.triggerPilotSpecial(state, engine);
      }
    });
  },

  confirmPilot: function(state) {
    const chosen = this.pilots[this.selectedIdx];
    this.menuActive = false;
    state.player.pilot = chosen;
    state.player.color = chosen.color;
    state.stats.characterClass = chosen.name;
    state.player.shields = 3;
    state.player.health = 3;
    state.player.invuln = 2.0;
    this.specialCd = 0;
    this.bannerText = `${chosen.name} ENGAGED // [SPACE] ${chosen.weaponName} | [SHIFT/E] ${chosen.specialName}`;
    this.bannerTimer = 4.0;
    state.paused = false;
    state.keys.jump = false;
  },

  _getBulletsArray: function(state) {
    const w = state.world;
    if (Array.isArray(w.lasers)) return w.lasers;
    if (Array.isArray(w.bullets)) return w.bullets;
    if (Array.isArray(w.projectiles)) return w.projectiles;
    w.lasers = [];
    return w.lasers;
  },

  _getAsteroidsArray: function(state) {
    const w = state.world;
    if (Array.isArray(w.asteroids)) return w.asteroids;
    if (Array.isArray(w.rocks)) return w.rocks;
    if (Array.isArray(w.entities)) return w.entities;
    return [];
  },

  triggerPilotSpecial: function(state, engine) {
    if (this.specialCd > 0) return;
    const p = state.player, w = state.world;
    const pilot = p.pilot || this.pilots[0];
    this.specialCd = pilot.cdMax;
    p.invuln = Math.max(p.invuln || 0, 1.2);
    w.cameraShake = 14;

    const bullets = this._getBulletsArray(state);
    const rocks = this._getAsteroidsArray(state);

    if (pilot.id === "VEX") {
      // PHASE-BLINK NOVA: Leave 5 cyan afterimages, teleport 170px forward, and detonate arrival ring!
      const startX = p.x, startY = p.y;
      for (let i = 1; i <= 5; i++) {
        this.afterimages.push({
          x: (startX + Math.cos(p.angle) * (i * 32) + 800) % 800,
          y: (startY + Math.sin(p.angle) * (i * 32) + 600) % 600,
          angle: p.angle, color: "#00f3ff", life: 0.55
        });
      }
      p.x = (p.x + Math.cos(p.angle) * 170 + 800) % 800;
      p.y = (p.y + Math.sin(p.angle) * 170 + 600) % 600;
      this.specialFx.push({ type: "RING", x: p.x, y: p.y, r: 10, maxR: 150, color: "#00f3ff", life: 0.45, maxLife: 0.45 });
      // Fire 12 radial plasma bolts from arrival point
      for (let i = 0; i < 12; i++) {
        const a = (i / 12) * Math.PI * 2;
        bullets.push({ x: p.x, y: p.y, vx: Math.cos(a) * 520, vy: Math.sin(a) * 520, life: 0.65, r: 4, color: "#00f3ff" });
      }
    } else if (pilot.id === "KAZE") {
      // 360° CYBER-KATANA EMP SLASH: Vaporize nearby rocks/projectiles & launch 8 piercing kunai beams!
      this.specialFx.push({ type: "SLASH", x: p.x, y: p.y, r: 145, color: "#39ff14", life: 0.4, maxLife: 0.4 });
      for (let i = rocks.length - 1; i >= 0; i--) {
        const rk = rocks[i];
        if (Math.hypot((rk.x || 0) - p.x, (rk.y || 0) - p.y) < 155) {
          rk.hp = 0;
          state.score += 250;
        }
      }
      for (let i = 0; i < 8; i++) {
        const a = p.angle + (i / 8) * Math.PI * 2;
        bullets.push({ x: p.x, y: p.y, vx: Math.cos(a) * 680, vy: Math.sin(a) * 680, life: 0.8, r: 5, color: "#39ff14", piercing: true });
      }
    } else if (pilot.id === "BASS") {
      // SUBWOOFER BASS-DROP SHOCKWAVE: Screen-wide expanding golden shockwave that damages all rocks & enemies!
      this.specialFx.push({ type: "RING", x: p.x, y: p.y, r: 15, maxR: 460, color: "#ffea00", life: 0.7, maxLife: 0.7 });
      this.specialFx.push({ type: "RING", x: p.x, y: p.y, r: 5, maxR: 320, color: "#ff007f", life: 0.55, maxLife: 0.55 });
      for (let i = 0; i < rocks.length; i++) {
        const rk = rocks[i];
        const dx = (rk.x || 0) - p.x, dy = (rk.y || 0) - p.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 420) {
          rk.vx = (dx / dist) * 260;
          rk.vy = (dy / dist) * 260;
          if (typeof rk.hp === "number") rk.hp -= 3;
          state.score += 150;
        }
      }
    } else if (pilot.id === "NYX") {
      // CHRONO-MIRAGE OVERCLOCK: Slow all asteroids/enemies by 75% for 4.0s & fire homing swarm!
      this.chronoTimer = 4.0;
      this.specialFx.push({ type: "DECOY", x: p.x, y: p.y, color: "#ff007f", life: 4.0, maxLife: 4.0 });
      for (let i = 0; i < 10; i++) {
        const a = (i / 10) * Math.PI * 2;
        bullets.push({ x: p.x, y: p.y, vx: Math.cos(a) * 460, vy: Math.sin(a) * 460, life: 1.3, r: 4, color: "#ff007f", homing: true });
      }
    }

    (w.floatingTexts || (w.floatingTexts = [])).push({
      text: `⚡ ${pilot.specialName}! ⚡`,
      x: p.x, y: Math.max(60, p.y - 36), color: pilot.color, life: 1.2
    });
    engine.emit("PILOT_SPECIAL", { pilot: pilot.id });
  },

  update: function(dt, state) {
    if (this.menuActive) {
      state.paused = true;
      return;
    }
    if (!state.running || state.paused) return;

    const p = state.player, w = state.world;
    const pilot = p.pilot || this.pilots[0];

    if (this.specialCd > 0) this.specialCd = Math.max(0, this.specialCd - dt);
    if (this.bannerTimer > 0) this.bannerTimer = Math.max(0, this.bannerTimer - dt);

    // Chrono-Mirage time-slow effect on asteroids
    const rocks = this._getAsteroidsArray(state);
    if (this.chronoTimer > 0) {
      this.chronoTimer -= dt;
      for (let i = 0; i < rocks.length; i++) {
        rocks[i].x -= (rocks[i].vx || 0) * dt * 0.72;
        rocks[i].y -= (rocks[i].vy || 0) * dt * 0.72;
      }
    }

    // Pilot-Specific Primary Weapon Patterns on [SPACE] (`state.keys.jump`)
    this.fireTimer -= dt * (this.chronoTimer > 0 ? 1.8 : 1.0);
    if (state.keys.jump && this.fireTimer <= 0) {
      const bullets = this._getBulletsArray(state);
      const spd = 620;
      const nx = Math.cos(p.angle), ny = Math.sin(p.angle);
      const px = -ny, py = nx; // perpendicular wing offset

      if (pilot.id === "VEX") {
        // Twin parallel cyan pulse lasers
        this.fireTimer = 0.13;
        bullets.push({ x: p.x + px * 7, y: p.y + py * 7, vx: nx * spd, vy: ny * spd, life: 0.85, r: 3, color: "#00f3ff" });
        bullets.push({ x: p.x - px * 7, y: p.y - py * 7, vx: nx * spd, vy: ny * spd, life: 0.85, r: 3, color: "#ff007f" });
      } else if (pilot.id === "KAZE") {
        // High-velocity piercing rail-lance
        this.fireTimer = 0.22;
        bullets.push({ x: p.x + nx * 14, y: p.y + ny * 14, vx: nx * 880, vy: ny * 880, life: 0.75, r: 5, color: "#39ff14", piercing: true });
        this.specialFx.push({ type: "BEAM", x1: p.x, y1: p.y, x2: p.x + nx * 260, y2: p.y + ny * 260, color: "#39ff14", life: 0.12, maxLife: 0.12 });
      } else if (pilot.id === "BASS") {
        // 5-Way Sonic Scatter-Shot
        this.fireTimer = 0.26;
        for (let s = -2; s <= 2; s++) {
          const a = p.angle + s * 0.14;
          bullets.push({ x: p.x, y: p.y, vx: Math.cos(a) * 540, vy: Math.sin(a) * 540, life: 0.65, r: 4, color: "#ffea00" });
        }
      } else if (pilot.id === "NYX") {
        // Twin Homing Synth-Pods
        this.fireTimer = 0.17;
        bullets.push({ x: p.x + px * 8, y: p.y + py * 8, vx: nx * 500, vy: ny * 500, life: 1.2, r: 4, color: "#ff007f", homing: true });
        bullets.push({ x: p.x - px * 8, y: p.y - py * 8, vx: nx * 500, vy: ny * 500, life: 1.2, r: 4, color: "#00f3ff", homing: true });
      }
    }

    // Update Homing Bullets (for NYX)
    const bullets = this._getBulletsArray(state);
    for (let i = 0; i < bullets.length; i++) {
      const b = bullets[i];
      if (b.homing && rocks.length > 0) {
        let nearest = null, bestD = 320;
        for (let j = 0; j < rocks.length; j++) {
          const d = Math.hypot((rocks[j].x || 0) - b.x, (rocks[j].y || 0) - b.y);
          if (d < bestD) { bestD = d; nearest = rocks[j]; }
        }
        if (nearest) {
          const desiredA = Math.atan2(nearest.y - b.y, nearest.x - b.x);
          const curSpd = Math.hypot(b.vx, b.vy) || 500;
          b.vx += (Math.cos(desiredA) * curSpd - b.vx) * 6.0 * dt;
          b.vy += (Math.sin(desiredA) * curSpd - b.vy) * 6.0 * dt;
        }
      }
    }

    // Update Special Visual FX & Afterimages
    for (let i = this.specialFx.length - 1; i >= 0; i--) {
      const fx = this.specialFx[i];
      fx.life -= dt;
      if (fx.type === "RING") {
        fx.r += ((fx.maxR - fx.r) * 6.5) * dt;
      }
      if (fx.life <= 0) this.specialFx.splice(i, 1);
    }
    for (let i = this.afterimages.length - 1; i >= 0; i--) {
      this.afterimages[i].life -= dt;
      if (this.afterimages[i].life <= 0) this.afterimages.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    const p = state.player;
    const pilot = p.pilot || this.pilots[0];

    // 1. Render Pilot Select Modal if active
    if (this.menuActive) {
      ctx.save();
      ctx.fillStyle = "rgba(5, 2, 13, 0.94)";
      ctx.fillRect(0, 36, 800, 564);

      ctx.textAlign = "center";
      ctx.shadowBlur = 14;
      ctx.shadowColor = "#00f3ff";
      ctx.fillStyle = "#00f3ff";
      ctx.font = "bold 22px monospace";
      ctx.fillText("// SELECT PILOT TRANSMISSION //", 400, 78);

      ctx.shadowBlur = 0;
      ctx.fillStyle = "#e2e8f0";
      ctx.font = "12px monospace";
      ctx.fillText("< LEFT / RIGHT > TO CYCLE  --  [SPACE / ENTER] TO ENGAGE", 400, 102);

      const t = performance.now() * 0.002;
      for (let i = 0; i < 4; i++) {
        const pl = this.pilots[i];
        const cx = 62 + i * 172;
        const cy = 126;
        const cw = 156, ch = 370;
        const sel = (i === this.selectedIdx);

        ctx.save();
        ctx.fillStyle = sel ? "rgba(15, 23, 42, 0.95)" : "rgba(9, 13, 24, 0.85)";
        ctx.fillRect(cx, cy, cw, ch);
        ctx.strokeStyle = sel ? pl.color : "#1e293b";
        ctx.lineWidth = sel ? 2.5 : 1;
        if (sel) { ctx.shadowBlur = 16; ctx.shadowColor = pl.color; }
        ctx.strokeRect(cx, cy, cw, ch);
        ctx.shadowBlur = 0;

        // Symmetric 12x12 Pixel-Art Cyber-Helmet Portrait
        const pxSize = 8;
        const startX = cx + (cw - 12 * pxSize) / 2;
        const startY = cy + 24;
        for (let r = 0; r < 12; r++) {
          const rowBits = pl.bitmap[r];
          for (let c = 0; c < 12; c++) {
            const bitIdx = c < 6 ? (5 - c) : (c - 6);
            if ((rowBits >> bitIdx) & 1) {
              const isVisor = (r >= 3 && r <= 5 && c >= 3 && c <= 8);
              ctx.fillStyle = isVisor ? "#ffffff" : pl.color;
              ctx.fillRect(startX + c * pxSize, startY + r * pxSize, pxSize - 1, pxSize - 1);
            }
          }
        }

        // Rotating Ship Vector Preview
        ctx.save();
        ctx.translate(cx + cw / 2, cy + 168);
        ctx.rotate(t + i * 1.1);
        ctx.strokeStyle = pl.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(16, 0);
        ctx.lineTo(-12, -11);
        ctx.lineTo(-6, 0);
        ctx.lineTo(-12, 11);
        ctx.closePath();
        ctx.stroke();
        ctx.restore();

        ctx.textAlign = "center";
        ctx.fillStyle = sel ? "#ffffff" : "#94a3b8";
        ctx.font = "bold 13px monospace";
        ctx.fillText(pl.name, cx + cw / 2, cy + 225);

        ctx.fillStyle = pl.color;
        ctx.font = "10px monospace";
        ctx.fillText(pl.weaponName, cx + cw / 2, cy + 246);
        ctx.fillStyle = pl.accent;
        ctx.font = "8.5px monospace";
        ctx.fillText("[SHIFT/E] " + pl.specialName, cx + cw / 2, cy + 262);
        ctx.font = "10px monospace";

        // Stat bars
        ctx.textAlign = "left";
        ctx.fillStyle = "#64748b";
        ctx.fillText("SPD", cx + 14, cy + 292);
        ctx.fillRect(cx + 44, cy + 283, 96, 7);
        ctx.fillStyle = pl.color;
        ctx.fillRect(cx + 44, cy + 283, 96 * pl.spd, 7);

        ctx.fillStyle = "#64748b";
        ctx.fillText("AGI", cx + 14, cy + 312);
        ctx.fillRect(cx + 44, cy + 303, 96, 7);
        ctx.fillStyle = pl.color;
        ctx.fillRect(cx + 44, cy + 303, 96 * pl.agi, 7);
        ctx.restore();
      }

      // Clear Control Legend Ribbon at Bottom of Pilot Select
      ctx.fillStyle = "#00f3ff";
      ctx.font = "bold 12px monospace";
      ctx.textAlign = "center";
      ctx.fillText("CONTROLS: [W/UP] Thrust | [A/D] Rotate | [S/DOWN] Retro-Brake | [SPACE] Fire | [SHIFT / E] Overdrive Special", 400, 545);
      ctx.restore();
      return;
    }

    // 2. Render Active Gameplay Pilot Afterimages & Special Ability FX
    ctx.save();
    for (let i = 0; i < this.afterimages.length; i++) {
      const ai = this.afterimages[i];
      ctx.save();
      ctx.globalAlpha = Math.max(0, ai.life / 0.55) * 0.6;
      ctx.translate(ai.x, ai.y);
      ctx.rotate(ai.angle);
      ctx.strokeStyle = ai.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(14, 0); ctx.lineTo(-10, -9); ctx.lineTo(-10, 9); ctx.closePath();
      ctx.stroke();
      ctx.restore();
    }

    for (let i = 0; i < this.specialFx.length; i++) {
      const fx = this.specialFx[i];
      ctx.save();
      ctx.globalAlpha = Math.max(0, fx.life / (fx.maxLife || 0.5));
      ctx.strokeStyle = fx.color;
      ctx.shadowBlur = 16;
      ctx.shadowColor = fx.color;
      if (fx.type === "RING" || fx.type === "SLASH") {
        ctx.lineWidth = fx.type === "SLASH" ? 6 : 3.5;
        ctx.beginPath();
        ctx.arc(fx.x, fx.y, fx.r, 0, Math.PI * 2);
        ctx.stroke();
      } else if (fx.type === "BEAM") {
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(fx.x1, fx.y1);
        ctx.lineTo(fx.x2, fx.y2);
        ctx.stroke();
      } else if (fx.type === "DECOY") {
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(fx.x, fx.y, 22 + Math.sin(performance.now() * 0.02) * 5, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }

    // 3. Diegetic Cooldown Ring around Ship + Brief Launch Control Banner
    const cdRatio = 1 - Math.min(1, this.specialCd / (pilot.cdMax || 5));
    ctx.beginPath();
    ctx.strokeStyle = cdRatio >= 1 ? pilot.color : "#ff007f";
    ctx.lineWidth = cdRatio >= 1 ? 2.5 : 1.5;
    ctx.arc(p.x, p.y, 22, -Math.PI / 2, -Math.PI / 2 + cdRatio * Math.PI * 2);
    ctx.stroke();

    if (this.bannerTimer > 0) {
      ctx.globalAlpha = Math.min(1, this.bannerTimer);
      ctx.fillStyle = pilot.color;
      ctx.font = "bold 12px monospace";
      ctx.textAlign = "center";
      ctx.fillText(this.bannerText, 400, 582);
    }
    ctx.restore();
  }
});
