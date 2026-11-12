// Cohesive Milestone Plugin: v0.9.0 (Operation Brimstone Thurible: Crackling Floor Seams, Pyre-Vault & Wall Gargoyles)
window.StudioEngine.registerModule("Milestone_v0_9_0", {
  init: function(state, engine) {
    this.roomKey = "";
    this.fissure = null;
    this.gargoyle = null;
    this.cinderWaves = [];

    engine.on("PLAYER_DODGE", () => {
      const p = state.player;
      this.cinderWaves.push({ x: p.x, y: p.y, r: 8, maxR: 65, life: 0.32 });
      if (this.fissure && Math.hypot(p.x - this.fissure.x, p.y - this.fissure.y) < 70) {
        this.fissure.ignited = 4.0;
      }
    });
  },

  syncRoom: function(state) {
    const w = state.world;
    const key = `${w.currentRoom.x},${w.currentRoom.y}`;
    if (this.roomKey === key) return;
    this.roomKey = key;

    const role = w.roomRole || "ENTRY_HALL";
    // Scope Jagged Brimstone Floor Fissure strictly to SEISMIC_FAULT or ALCHEMY_CISTERN (Never giant black circles!)
    if (role === "SEISMIC_FAULT" || role === "ALCHEMY_CISTERN") {
      this.fissure = { x: 465, y: 365, ignited: 0 };
    } else {
      this.fissure = null;
    }

    // Scope Gothic Wall Gargoyle strictly to West Wall (x=74, y=210) — NEVER in Top-Right Minimap zone!
    if (role === "ALTAR_SANCTUM" || role === "OSSUARY_PASSAGE") {
      this.gargoyle = { x: 76, y: 205, charge: 0 };
    } else {
      this.gargoyle = null;
    }
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    this.syncRoom(state);
    const w = state.world;

    if (this.fissure && this.fissure.ignited > 0) {
      this.fissure.ignited -= dt;
      for (let i = 0; i < (w.enemies || []).length; i++) {
        const en = w.enemies[i];
        if (Math.hypot(en.x - this.fissure.x, en.y - this.fissure.y) < 55) {
          en.hp -= 24 * dt;
        }
      }
    }

    for (let i = this.cinderWaves.length - 1; i >= 0; i--) {
      const cw = this.cinderWaves[i];
      cw.life -= dt;
      cw.r += (cw.maxR - cw.r) * 8.0 * dt;
      if (cw.life <= 0) this.cinderWaves.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const p = state.player, w = state.world, lp = w.lowPoly;
    ctx.save();

    // 1. Render Jagged Volcanic Floor Fissure Crack (Never a round grey circle!)
    if (this.fissure) {
      const f = this.fissure;
      ctx.strokeStyle = f.ignited > 0 ? "#f97316" : "#451a03";
      ctx.lineWidth = f.ignited > 0 ? 4 : 2.5;
      ctx.beginPath();
      ctx.moveTo(f.x - 36, f.y - 18);
      ctx.lineTo(f.x - 12, f.y - 4);
      ctx.lineTo(f.x + 8, f.y - 14);
      ctx.lineTo(f.x + 28, f.y + 6);
      ctx.lineTo(f.x + 42, f.y + 18);
      ctx.stroke();
    }

    // 2. Render 2.5D Extruded Gothic Stone Gargoyle Statue on West Wall (Away from Minimap!)
    if (this.gargoyle && lp) {
      lp.drawLowPolyPrism(ctx, this.gargoyle.x, this.gargoyle.y, 13, 10, 36, 4, "#475569", p.x, p.y, 0);
      ctx.fillStyle = "#dc2626";
      ctx.fillRect(this.gargoyle.x - 2, this.gargoyle.y - 14, 2, 2);
      ctx.fillRect(this.gargoyle.x + 2, this.gargoyle.y - 14, 2, 2);
    }

    // 3. Render Pyre-Vault Cinder Stomp Rings
    for (let i = 0; i < this.cinderWaves.length; i++) {
      const cw = this.cinderWaves[i];
      ctx.strokeStyle = "#f97316";
      ctx.globalAlpha = Math.max(0, cw.life / 0.32);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(cw.x, cw.y, cw.r, 0, Math.PI * 2); ctx.stroke();
    }

    ctx.restore();
  }
});
