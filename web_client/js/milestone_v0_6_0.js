// Cohesive Milestone Plugin: v0.6.0 (Operation Celestial Flux: Astra-Singularity Nodes & Kinetic Overcharge)
window.StudioEngine.registerModule("Milestone_v0_6_0", {
  init: function(state, engine) {
    // 4 Inner Intersection Nodes of the Ninefold Matrix
    this.nodes = [
      { x: 340, y: 250 },
      { x: 460, y: 250 },
      { x: 340, y: 370 },
      { x: 460, y: 370 }
    ];
    this.pulsePhase = 0;
    this.overchargeRings = [];

    engine.on("SECTOR_INSCRIBED", (ev) => {
      const lat = state.world && state.world.lattice;
      if (!lat) return;
      // If inscribed while the Astra-Singularity pulse is near peak (>0.65), trigger a Kinetic Overcharge Wave!
      const resonance = (Math.sin(this.pulsePhase) + 1) * 0.5;
      if (resonance > 0.55) {
        state.score = (state.score || 0) + 150;
        this.overchargeRings.push({
          x: ev.x, y: ev.y, r: 14, maxR: 135,
          color: ev.symbol === "X" ? "#38bdf8" : "#facc15",
          life: 0.55, maxLife: 0.55
        });
      }
    });
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.modal) return;
    this.pulsePhase += dt * 3.2;

    for (let i = this.overchargeRings.length - 1; i >= 0; i--) {
      const r = this.overchargeRings[i];
      r.life -= dt;
      r.r += (r.maxR - r.r) * 6.5 * dt;
      if (r.life <= 0) this.overchargeRings.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    const lat = state.world && state.world.lattice;
    if (!lat || state.paused || state.modal) return;
    const pal = lat.palettes[lat.paletteIdx] || lat.palettes[0];
    const resonance = (Math.sin(this.pulsePhase) + 1) * 0.5;

    ctx.save();

    // 1. Render 4 Pulsing Astra-Singularity Graviton Nodes at the Matrix Intersections
    for (let i = 0; i < this.nodes.length; i++) {
      const nd = this.nodes[i];
      ctx.save();
      ctx.translate(nd.x, nd.y);
      ctx.rotate(this.pulsePhase * 0.5 + i);
      ctx.strokeStyle = resonance > 0.55 ? "#ffffff" : pal.gridCol;
      ctx.lineWidth = 1.5;
      const s = 5 + resonance * 4;
      ctx.strokeRect(-s, -s, s * 2, s * 2);

      ctx.fillStyle = pal.gridCol;
      ctx.globalAlpha = 0.35 + resonance * 0.45;
      ctx.beginPath();
      ctx.arc(0, 0, 2.5 + resonance * 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // 2. Render Kinetic Overcharge Shockwave Rings
    for (let i = 0; i < this.overchargeRings.length; i++) {
      const rg = this.overchargeRings[i];
      ctx.strokeStyle = rg.color;
      ctx.globalAlpha = Math.max(0, rg.life / rg.maxLife);
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(rg.x, rg.y, rg.r, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.restore();
  }
});
