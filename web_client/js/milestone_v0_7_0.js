// Cohesive Milestone Plugin: v0.7.0 (Operation Bell-Toll Crypts: Swinging Bronze Censers, Bell-Warden & Runic Floor Glyphs)
window.StudioEngine.registerModule("Milestone_v0_7_0", {
  init: function(state, engine) {
    this.roomKey = "";
    this.censer = null;
    this.glyph = null;

    engine.on("PLAYER_ATTACK", () => {
      const p = state.player;
      if (this.censer && Math.hypot(p.x - this.censer.x, p.y - this.censer.y) < 75) {
        this.censer.swingVel = 4.2;
        this.censer.ignited = 4.5;
        for (let k=0; k<8; k++) state.world.particles.push({ x: p.x, y: p.y, vx: (Math.random()-0.5)*180, vy: (Math.random()-0.5)*180, color: '#f59e0b', life: 0.4 });
      }
    });
  },

  syncRoom: function(state) {
    const w = state.world;
    const key = `${w.currentRoom.x},${w.currentRoom.y}`;
    if (this.roomKey === key) return;
    this.roomKey = key;

    const role = w.roomRole || "ENTRY_HALL";
    // Scope Swinging Cathedral Censer strictly to ALTAR_SANCTUM or ENTRY_HALL (1 censer max, never cluttering corridors!)
    if (role === "ALTAR_SANCTUM" || role === "ENTRY_HALL") {
      this.censer = { anchorX: 400, anchorY: 165, x: 400, y: 215, phase: 0, swingVel: 1.2, ignited: 0 };
    } else {
      this.censer = null;
    }

    // Scope Runic Floor Glyph strictly to OSSUARY_PASSAGE or RELIQUARY_VAULT
    if (role === "OSSUARY_PASSAGE" || role === "RELIQUARY_VAULT") {
      this.glyph = { x: 400, y: 315, r: 26, charge: 0, cooldown: 0 };
    } else {
      this.glyph = null;
    }
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    this.syncRoom(state);
    const p = state.player, w = state.world;

    if (this.censer) {
      const c = this.censer;
      c.phase += (1.8 + c.swingVel) * dt;
      c.swingVel = Math.max(0.5, c.swingVel * Math.pow(0.4, dt));
      const amp = 32 + c.swingVel * 16;
      c.x = c.anchorX + Math.sin(c.phase) * amp;
      c.y = c.anchorY + 45 + Math.cos(c.phase * 2) * 6;
      if (c.ignited > 0) {
        c.ignited -= dt;
        for (let i = 0; i < (w.enemies || []).length; i++) {
          const en = w.enemies[i];
          if (Math.hypot(en.x - c.x, en.y - c.y) < 55) {
            en.hp -= 28 * dt;
            en.stagger = 0.4;
          }
        }
      }
    }

    if (this.glyph) {
      const g = this.glyph;
      if (g.cooldown > 0) g.cooldown -= dt;
      else if (Math.hypot(p.x - g.x, p.y - g.y) < g.r + 10) {
        g.charge += dt * 1.1;
        if (g.charge >= 1.0) {
          g.charge = 0;
          g.cooldown = 3.0;
          if (p.invuln <= 0 && p.dashTimer <= 0) {
            p.stress = Math.min(100, (p.stress || 0) + 10);
            w.floatingTexts.push({ text: "✦ RUNIC GLYPH ERUPTION! ✦", x: g.x, y: g.y - 20, color: "#a855f7", life: 1.0 });
          }
        }
      } else {
        g.charge = Math.max(0, g.charge - dt * 0.8);
      }
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const p = state.player, w = state.world, lp = w.lowPoly;
    ctx.save();

    // 1. Render Etched Floor Runic Sigil (No giant solid circles!)
    if (this.glyph) {
      const g = this.glyph;
      ctx.save();
      ctx.translate(g.x, g.y);
      ctx.rotate(performance.now() * 0.001);
      ctx.strokeStyle = g.charge > 0.1 ? "#f43f5e" : "rgba(168, 85, 247, 0.45)";
      ctx.lineWidth = 1.8;
      ctx.beginPath(); ctx.arc(0, 0, g.r, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeRect(-g.r * 0.65, -g.r * 0.65, g.r * 1.3, g.r * 1.3);
      ctx.restore();
    }

    // 2. Render 2.5D Low-Poly Swinging Bronze Cathedral Censer & Iron Chain
    if (this.censer && lp) {
      const c = this.censer;
      ctx.strokeStyle = "#78716c";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.moveTo(c.anchorX, c.anchorY - 30); ctx.lineTo(c.x, c.y - 12); ctx.stroke();
      ctx.setLineDash([]);
      lp.drawLowPolyPrism(ctx, c.x, c.y, 11, 8, 26, 6, c.ignited > 0 ? "#f97316" : "#d97706", p.x, p.y, c.phase);
    }

    ctx.restore();
  }
});
