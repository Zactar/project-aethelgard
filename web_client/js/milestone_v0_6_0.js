// Cohesive Milestone Plugin: v0.6.0 (Diegetic Phantom Ghost Skier, Boost Ramps & Relic Forge)
window.StudioEngine.registerModule("Milestone_v0_6_0", {
  init: function(st, eng) {
    this.ghostPath = [];
    this.bestGhostPath = [];
    this.ramps = [];
    this.nextRampDist = 180;
    this.boostTimer = 0;

    // Spawn initial on-slope blue jump/boost chevrons
    for (let i = 0; i < 3; i++) {
      this.ramps.push({ x: 140 + i * 240, y: 360 + i * 160, w: 44, h: 16 });
    }

    // Key [F] or [E] Chalet Relic Transmutation: fuse 2 relics into an Empowered Mythic surge
    eng.on("KEYDOWN", (ev) => {
      if (ev.code === "KeyF" && st.inventory && (st.inventory.relics || []).length >= 2) {
        st.inventory.relics.splice(0, 2);
        st.stats.xp = (st.stats.xp || 0) + 250;
        if (st.player.wipeouts > 0) st.player.wipeouts--;
        (st.world.floatingTexts || (st.world.floatingTexts = [])).push({
          text: "RELICS TRANSMUTED! +1 HEALTH & +250 XP",
          x: st.player.x,
          y: st.player.y - 30,
          life: 1.4
        });
      }
    });
  },

  update: function(dt, st) {
    if (st.paused) return;
    const p = st.player, w = st.world;

    // Record player trajectory for diegetic Phantom Ghost playback
    if (st.tick % 3 === 0) {
      this.ghostPath.push({ x: p.x, dist: Math.floor(w.distance || 0) });
      if (this.ghostPath.length > 600) this.ghostPath.shift();
    }

    // If player resets run, promote recorded path to Personal Best Ghost
    if ((w.distance || 0) < 15 && this.ghostPath.length > 30) {
      this.bestGhostPath = this.ghostPath.slice();
      this.ghostPath = [];
    }

    if (this.boostTimer > 0) {
      this.boostTimer -= dt;
      w.distance = (w.distance || 0) + 140 * dt;
    }

    // Update on-slope Glacial Boost Ramps
    const scrollSpd = (w.speed || 220) * dt;
    for (let i = 0; i < this.ramps.length; i++) {
      const r = this.ramps[i];
      r.y -= scrollSpd;
      if (r.y < -30) {
        r.y = 620 + Math.random() * 140;
        r.x = 90 + Math.random() * 620;
      }
      // Player hits boost ramp -> launch airborne + speed surge + XP
      if (Math.abs(p.x - r.x) < 28 && Math.abs((p.y || 200) - r.y) < 20 && this.boostTimer <= 0) {
        this.boostTimer = 1.2;
        p.isAirborne = true;
        p.z = 18;
        st.stats.xp = (st.stats.xp || 0) + 45;
        (w.floatingTexts || (w.floatingTexts = [])).push({
          text: "GLACIAL RAMP BOOST! +45 XP",
          x: p.x,
          y: (p.y || 200) - 24,
          life: 0.9
        });
      }
    }
  },

  render: function(ctx, st) {
    const p = st.player, w = st.world;

    // 1. Render Diegetic On-Slope Glacial Boost Ramps (Cyan Chevrons on the Snow)
    ctx.save();
    for (let i = 0; i < this.ramps.length; i++) {
      const r = this.ramps[i];
      ctx.fillStyle = "rgba(56, 189, 248, 0.35)";
      ctx.fillRect(r.x - 20, r.y - 8, 40, 16);
      ctx.strokeStyle = "#0284c7";
      ctx.lineWidth = 2;
      ctx.strokeRect(r.x - 20, r.y - 8, 40, 16);
      ctx.fillStyle = "#0369a1";
      ctx.font = "bold 10px monospace";
      ctx.textAlign = "center";
      ctx.fillText("▲▲▲", r.x, r.y + 4);
    }

    // 2. Render Translucent Phantom Pace-Skier on the Slope (Zero HUD clutter!)
    const curDist = Math.floor(w.distance || 0);
    const ghostX = 400 + Math.sin(curDist * 0.025) * 180;
    const ghostY = (p.y || 200) + Math.cos(curDist * 0.015) * 45;
    ctx.globalAlpha = 0.42;
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(ghostX - 6, ghostY - 12, 12, 24);
    ctx.font = "bold 9px monospace";
    ctx.textAlign = "center";
    ctx.fillText("PACE GHOST", ghostX, ghostY - 16);
    ctx.restore();
  }
});
