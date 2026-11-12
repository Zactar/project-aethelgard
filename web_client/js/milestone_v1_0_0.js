// Cohesive Milestone Plugin: v1.0.0
// Cohesive Milestone Plugin: v1.0.0 (The Black Chalice Reliquary, Bone-Splinter Ricochet & Gold Master Seal)
window.StudioEngine.registerModule("Milestone_v1_0_0", {
  init: function(state, engine) {
    const p = state.player, w = state.world;
    p.ascended = false;
    p.chaliceConsumed = false;
    this.reliquary = null;
    this.splinters = [];
    this.ashMotes = [];
    this.time = 0;
    this.roomKey = "";

    // Synthesize 64 drifting crypt ash motes
    for (let i = 0; i < 64; i++) {
      (this.ashMotes || (this.ashMotes = [])).push({
        x: Math.random() * 800,
        y: Math.random() * 560 + 40,
        seed: Math.random() * 100,
        size: Math.random() * 2 + 1,
        alpha: Math.random() * 0.6 + 0.2
      });
    }

    // Splinter launch listener on player melee cleave
    engine.on("PLAYER_ATTACK", () => {
      if (!p.ascended) return;
      const baseAng = p.facingAngle !== undefined ? p.facingAngle : (p.angle || 0);
      const offsets = [-0.35, 0, 0.35];
      for (let i = 0; i < 3; i++) {
        const ang = baseAng + offsets[i];
        (this.splinters || (this.splinters = [])).push({
          x: p.x + Math.cos(ang) * 16,
          y: p.y + Math.sin(ang) * 16,
          vx: Math.cos(ang) * 420,
          vy: Math.sin(ang) * 420,
          bounces: 0,
          trail: []
        });
      }
    });
  },

  syncReliquary: function(state) {
    const w = state.world;
    const key = `${w.currentRoom ? w.currentRoom.x : 0},${w.currentRoom ? w.currentRoom.y : 0}`;
    if (this.roomKey === key) return;
    this.roomKey = key;

    const questDone = w.quest && w.quest.stage >= (w.quest.maxStage || 3);
    const eligibleDepth = (w.depth || 1) >= 3 || questDone;
    const isAltar = w.roomRole === "ALTAR_SANCTUM" || w.roomRole === "CRYPT_BOSS" || eligibleDepth;
    if (eligibleDepth && isAltar && !state.player.chaliceConsumed) {
      this.reliquary = { x: 400, y: 280, active: true };
    } else {
      this.reliquary = null;
    }
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    this.time += dt;
    this.syncReliquary(state);
    const p = state.player, w = state.world;

    // Crypt Ash Drifting simulation
    for (let i = 0; i < this.ashMotes.length; i++) {
      const m = this.ashMotes[i];
      m.x += Math.sin(this.time * 1.0 + m.seed) * 12 * dt;
      m.y += (Math.cos(this.time * 0.8) * 8 - 14) * dt;
      if (m.y < 36) m.y = 590;
      if (m.x < 30) m.x = 770;
      if (m.x > 770) m.x = 30;
    }

    // Chalice Reliquary interaction
    if (this.reliquary && this.reliquary.active && !p.chaliceConsumed) {
      const dist = Math.hypot(p.x - this.reliquary.x, p.y - this.reliquary.y);
      if (dist < 36 && state.keys && state.keys.action) {
        p.ascended = true;
        p.chaliceConsumed = true;
        this.reliquary.active = false;
        w.cameraShake = Math.max(w.cameraShake || 0, 12);
        for (let i = 0; i < 24; i++) {
          const a = (i / 24) * Math.PI * 2;
          (w.particles = w.particles || []).push({
            x: this.reliquary.x,
            y: this.reliquary.y,
            vx: Math.cos(a) * 160,
            vy: Math.sin(a) * 160,
            life: 0.65,
            color: "#eab308"
          });
        }
      }
    }

    // Bone-Splinter Projectiles physics, wall bounce & enemy damage
    const walls = { minX: 68, maxX: 732, minY: 78, maxY: 522 };
    for (let i = this.splinters.length - 1; i >= 0; i--) {
      const sp = this.splinters[i];
      sp.trail.unshift({ x: sp.x, y: sp.y });
      if (sp.trail.length > 4) sp.trail.pop();

      sp.x += sp.vx * dt;
      sp.y += sp.vy * dt;

      // Surface normal reflections
      let bounced = false;
      if (sp.x <= walls.minX && sp.vx < 0) { sp.vx = -sp.vx; bounced = true; }
      else if (sp.x >= walls.maxX && sp.vx > 0) { sp.vx = -sp.vx; bounced = true; }
      if (sp.y <= walls.minY && sp.vy < 0) { sp.vy = -sp.vy; bounced = true; }
      else if (sp.y >= walls.maxY && sp.vy > 0) { sp.vy = -sp.vy; bounced = true; }

      if (bounced) {
        sp.bounces++;
        if (sp.bounces > 2) { this.splinters.splice(i, 1); continue; }
      }

      // Enemy collisions
      let hit = false;
      const enemies = w.enemies || [];
      for (let j = 0; j < enemies.length; j++) {
        const en = enemies[j];
        if (Math.hypot(sp.x - en.x, sp.y - en.y) < 22) {
          en.hp = (en.hp || 30) - 18;
          en.poise = (en.poise || 40) - 25;
          hit = true;
          break;
        }
      }
      if (hit) this.splinters.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const p = state.player, w = state.world, lp = w.lowPoly;

    ctx.save();
    if (w.cameraShake > 0) {
      const s = (Math.random() - 0.5) * w.cameraShake;
      ctx.translate(s, s);
    }

    // 1. Drifting Subterranean Volumetric Ash
    for (let i = 0; i < this.ashMotes.length; i++) {
      const m = this.ashMotes[i];
      ctx.fillStyle = `rgba(245, 158, 11, ${m.alpha * 0.4})`;
      ctx.fillRect(m.x, m.y, m.size, m.size);
    }

    // 2. Articulated 2.5D Black Chalice Pedestal & Goblet Geometry
    if (this.reliquary && this.reliquary.active) {
      const rx = this.reliquary.x, ry = this.reliquary.y;
      if (lp && lp.drawExtrudedBox) {
        lp.drawExtrudedBox(ctx, rx - 18, ry - 14, 36, 28, 20, "#1f1d24", "#d97706", p.x, p.y);
      }
      // Pulsing radial aura
      const auraR = 28 + 6 * Math.sin(this.time * 4);
      const radGrd = ctx.createRadialGradient(rx, ry - 16, 2, rx, ry - 16, auraR);
      radGrd.addColorStop(0, "rgba(234, 179, 8, 0.45)");
      radGrd.addColorStop(0.6, "rgba(220, 38, 38, 0.22)");
      radGrd.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = radGrd;
      ctx.beginPath();
      ctx.arc(rx, ry - 16, auraR, 0, Math.PI * 2);
      ctx.fill();

      // Articulated chalice goblet
      ctx.strokeStyle = "#eab308";
      ctx.fillStyle = "#dc2626";
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(rx - 8, ry - 30);
      ctx.lineTo(rx + 8, ry - 30);
      ctx.lineTo(rx + 4, ry - 20);
      ctx.lineTo(rx + 2, ry - 15);
      ctx.lineTo(rx + 6, ry - 12);
      ctx.lineTo(rx - 6, ry - 12);
      ctx.lineTo(rx - 2, ry - 15);
      ctx.lineTo(rx - 4, ry - 20);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // 3. Bone-Splinter Ricochet Ribbon Trails
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    for (let i = 0; i < this.splinters.length; i++) {
      const sp = this.splinters[i];
      if (sp.trail.length > 1) {
        ctx.strokeStyle = "#dc2626";
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.moveTo(sp.trail[0].x, sp.trail[0].y);
        for (let t = 1; t < sp.trail.length; t++) {
          ctx.lineTo(sp.trail[t].x, sp.trail[t].y);
        }
        ctx.stroke();
      }
      ctx.fillStyle = "#fef08a";
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    // 4. Atmospheric Chiaroscuro Vignette
    const vig = ctx.createRadialGradient(p.x, p.y, 40, p.x, p.y, 360);
    vig.addColorStop(0, "rgba(7, 5, 10, 0)");
    vig.addColorStop(0.78, "rgba(7, 5, 10, 0.45)");
    vig.addColorStop(1, "#07050a");
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, 800, 600);
    ctx.restore();

    // 5. Gold Master Seal & Relic HUD inside top ribbon (y: 0..36, x: [0, 640])
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);

    // Active Relic Chalice icon
    if (p.ascended) {
      const cx = 278, cy = 6;
      ctx.fillStyle = "#07050a";
      ctx.fillRect(cx, cy, 22, 24);
      ctx.strokeStyle = "#ca8a04";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(cx + 0.5, cy + 0.5, 21, 23);

      const pulse = 0.5 + 0.5 * Math.sin(this.time * 6);
      ctx.fillStyle = pulse > 0.5 ? "#ef4444" : "#b91c1c";
      ctx.beginPath();
      ctx.moveTo(cx + 6, cy + 5);
      ctx.lineTo(cx + 16, cy + 5);
      ctx.lineTo(cx + 13, cy + 13);
      ctx.lineTo(cx + 11, cy + 17);
      ctx.lineTo(cx + 14, cy + 20);
      ctx.lineTo(cx + 8, cy + 20);
      ctx.lineTo(cx + 11, cy + 17);
      ctx.lineTo(cx + 9, cy + 13);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // Etched gothic seal
    ctx.font = "bold 10px monospace";
    ctx.textAlign = "left";
    ctx.fillStyle = "#07050a";
    ctx.fillText("v1.0.0 GOLD MASTER", 311, 23);
    ctx.fillStyle = "#ca8a04";
    ctx.fillText("v1.0.0 GOLD MASTER", 310, 22);
    ctx.restore();
  }
});
