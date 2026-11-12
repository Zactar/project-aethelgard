// Cohesive Milestone Plugin: v0.8.0 (Operation Obsidian Ironclads: Magnetic Lodestone Pylons & Floor-Grit Dynamics)
window.StudioEngine.registerModule("Milestone_v0_8_0", {
  init: function(state, engine) {
    this.roomKey = "";
    this.lodestone = null;
    this.shockwaves = [];

    engine.on("PLAYER_DODGE", () => {
      const p = state.player;
      if (this.lodestone && Math.hypot(p.x - this.lodestone.x, p.y - this.lodestone.y) < 68) {
        this.shockwaves.push({ x: this.lodestone.x, y: this.lodestone.y, r: 12, maxR: 135, life: 0.45 });
        const enemies = state.world.enemies || [];
        for (let i = 0; i < enemies.length; i++) {
          if (Math.hypot(enemies[i].x - this.lodestone.x, enemies[i].y - this.lodestone.y) < 135) {
            enemies[i].hp -= 22;
            enemies[i].stagger = 0.8;
          }
        }
        for (let k=0; k<8; k++) state.world.particles.push({ x: p.x, y: p.y, vx: (Math.random()-0.5)*180, vy: (Math.random()-0.5)*180, color: '#f59e0b', life: 0.4 });
      }
    });
  },

  syncRoom: function(state) {
    const w = state.world;
    const key = `${w.currentRoom.x},${w.currentRoom.y}`;
    if (this.roomKey === key) return;
    this.roomKey = key;

    // Only spawn Magnetic Lodestone Monolith in SEISMIC_FAULT or RELIQUARY_VAULT rooms!
    const role = w.roomRole || "ENTRY_HALL";
    if (role === "SEISMIC_FAULT" || role === "RELIQUARY_VAULT") {
      this.lodestone = { x: 265, y: 315, r: 16, rot: 0 };
    } else {
      this.lodestone = null;
    }
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    this.syncRoom(state);
    const w = state.world;

    if (this.lodestone) {
      this.lodestone.rot += 1.4 * dt;
      // Gently pull iron-clad skeletons toward the magnetic obelisk
      const enemies = w.enemies || [];
      for (let i = 0; i < enemies.length; i++) {
        const en = enemies[i];
        const dx = this.lodestone.x - en.x, dy = this.lodestone.y - en.y;
        const d = Math.hypot(dx, dy) || 1;
        if (d < 130 && d > 24) {
          en.x += (dx / d) * 28 * dt;
          en.y += (dy / d) * 28 * dt;
        }
      }
    }

    for (let i = this.shockwaves.length - 1; i >= 0; i--) {
      const sw = this.shockwaves[i];
      sw.life -= dt;
      sw.r += (sw.maxR - sw.r) * 7.5 * dt;
      if (sw.life <= 0) this.shockwaves.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const p = state.player, w = state.world, lp = w.lowPoly;
    ctx.save();

    if (this.lodestone && lp) {
      lp.drawLowPolyPrism(ctx, this.lodestone.x, this.lodestone.y, 15, 0, 42, 5, "#0284c7", p.x, p.y, this.lodestone.rot);
    }

    for (let i = 0; i < this.shockwaves.length; i++) {
      const sw = this.shockwaves[i];
      ctx.strokeStyle = "#38bdf8";
      ctx.globalAlpha = Math.max(0, sw.life / 0.45);
      ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.arc(sw.x, sw.y, sw.r, 0, Math.PI * 2); ctx.stroke();
    }

    ctx.restore();
  }
});
