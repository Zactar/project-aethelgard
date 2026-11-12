// Cohesive Milestone Plugin: v0.7.0
// Cohesive Milestone Plugin: v0.7.0 (Weather Systems, Avalanche Hazard, Freestyle Tricks & LCD Telemetry)
window.StudioEngine.registerModule("Milestone_v0_7_0", {
  init: function(st) {
    st.world = st.world || {};
    st.stats = st.stats || {};
    st.player = st.player || { x: 400, y: 200, vx: 0, vy: 140, z: 0 };
    st.stats.adrenaline = st.stats.adrenaline || 0;
    st.stats.xpMultiplier = 1.0;
    st.player.trickRotation = 0;
    st.player.currentTrick = null;
    st.world.weather = { type: 'CLEAR', intensity: 0.0, windVec: [0, 80], fovRadius: 500 };
    st.world.avalancheY = -300;
    st.world.yetiAggression = 1.0;
    st.world.yetiStunTimer = 0;
    this.nextWeatherDist = 300;
    this.snowBuff = Array.from({ length: 200 }, () => ({
      x: Math.random() * 800, y: Math.random() * 600, z: 0.5 + Math.random() * 1.5, l: 2 + Math.random() * 4
    }));
  },

  update: function(dt, st) {
    if (st.paused || !st.running) return;
    const p = st.player, w = st.world, s = st.stats, k = st.keys || {}, d = w.distance || 0;
    if (d >= this.nextWeatherDist) {
      this.nextWeatherDist += 300;
      const roll = Math.random(), altFactor = Math.min(1.0, d / 4000);
      if (roll < 0.35) {
        w.weather = { type: 'BLIZZARD', intensity: 0.6 + altFactor * 0.4, windVec: [-140, 220], fovRadius: 180 };
      } else if (roll < 0.65) {
        w.weather = { type: 'WIND_SHEAR', intensity: 0.7, windVec: [Math.random() < 0.5 ? -260 : 260, 90], fovRadius: 360 };
      } else if (roll < 0.85 && d > 600) {
        w.weather = { type: 'AVALANCHE', intensity: 1.0, windVec: [0, 320], fovRadius: 280 };
        w.avalancheY = -220;
      } else {
        w.weather = { type: 'CLEAR', intensity: 0.0, windVec: [0, 70], fovRadius: 520 };
      }
    }
    const weath = w.weather;
    w.yetiAggression = 1.0 + (weath.intensity * 0.5);
    if (weath.type === 'BLIZZARD') w.friction = 0.65;
    if (weath.type === 'WIND_SHEAR') p.vx += weath.windVec[0] * dt * 0.6;
    if (weath.type === 'AVALANCHE') {
      w.cameraShake = Math.max(w.cameraShake || 0, 4);
      w.avalancheY += (Math.max(160, p.vy || 160) * 1.25) * dt;
      if (Math.abs((p.y || 200) - w.avalancheY) < 110) {
        p.state = 0x08; p.wipeouts = (p.wipeouts || 0) + 1; p.wipeoutTimer = 2.0; w.avalancheY = -350;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: "AVALANCHE BURIAL!", x: p.x, y: p.y - 20, life: 1.5 });
      }
    }
    const airborne = p.z > 0 || p.isAirborne;
    if (airborne) {
      let trickName = null;
      if (k.up) { trickName = "FRONT-FLIP"; p.trickRotation += 400 * dt; }
      else if (k.down) { trickName = "BACK-FLIP"; p.trickRotation += 380 * dt; }
      else if (k.left) { trickName = "METHOD GRAB"; p.trickRotation += 290 * dt; }
      else if (k.right) { trickName = "TAIL GRAB"; p.trickRotation += 290 * dt; }
      if (trickName) p.currentTrick = trickName;
    } else if (p.currentTrick) {
      const landedDeg = Math.abs(p.trickRotation % 360);
      if (landedDeg <= 28 || landedDeg >= 332) {
        const pts = Math.floor(p.trickRotation * 1.2) + 60;
        s.xp = (s.xp || 0) + pts;
        s.adrenaline = Math.min(100, (s.adrenaline || 0) + 28);
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: `${p.currentTrick}! +${pts}XP`, x: p.x, y: p.y - 25, life: 1.2 });
      } else {
        p.state = 0x08; p.wipeoutTimer = 1.4; p.wipeouts = (p.wipeouts || 0) + 1;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: "CRASH LANDING!", x: p.x, y: p.y - 20, life: 1.2 });
      }
      p.currentTrick = null; p.trickRotation = 0;
    }
    s.adrenaline = Math.max(0, (s.adrenaline || 0) - dt * 5.5);
    if (s.adrenaline >= 80) { w.yetiStunTimer = Math.max(w.yetiStunTimer || 0, 2.0); s.xpMultiplier = 3.0; }
    else s.xpMultiplier = 1.0 + (s.adrenaline / 80) * 1.2;
    for (let i = 0; i < this.snowBuff.length; i++) {
      const pt = this.snowBuff[i];
      pt.x += (weath.windVec[0] * 0.4 + (p.vx || 0) * -0.2) * dt * pt.z;
      pt.y += (weath.windVec[1] + (p.vy || 140)) * dt * 0.45 * pt.z;
      if (pt.y > 600) { pt.y = -10; pt.x = Math.random() * 800; }
      if (pt.x > 800) pt.x = 0; else if (pt.x < 0) pt.x = 800;
    }
  },

  render: function(ctx, st) {
    const w = st.world, p = st.player, weath = w.weather;
    ctx.save();
    if (weath.type === 'AVALANCHE') {
      ctx.fillStyle = "rgba(255, 255, 255, 0.88)";
      ctx.fillRect(0, Math.max(0, w.avalancheY - 50), 800, 75);
      ctx.fillStyle = "#FF1A1A"; ctx.font = "bold 15px monospace"; ctx.textAlign = "center";
      ctx.fillText("▲ ▲ AVALANCHE COLLAPSE HAZARD ▲ ▲", 400, 30);
    }
    ctx.strokeStyle = "rgba(240, 248, 255, 0.75)"; ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < this.snowBuff.length; i++) {
      const pt = this.snowBuff[i];
      ctx.moveTo(pt.x, pt.y);
      ctx.lineTo(pt.x + (weath.windVec[0] * 0.04), pt.y + pt.l * pt.z);
    }
    ctx.stroke();
    if (weath.fovRadius < 420) {
      const g = ctx.createRadialGradient(p.x, p.y || 200, weath.fovRadius * 0.4, p.x, p.y || 200, weath.fovRadius);
      g.addColorStop(0, "rgba(215, 235, 250, 0)"); g.addColorStop(0.7, "rgba(180, 215, 240, 0.45)"); g.addColorStop(1, "rgba(120, 160, 205, 0.94)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, 800, 600);
    }
    // Mid-Screen Diegetic Freestyle Stunt Indicator
    if (p.currentTrick && (p.z > 0 || p.isAirborne)) {
      ctx.save();
      ctx.translate(p.x, p.y - 36);
      ctx.rotate((p.trickRotation * Math.PI) / 180);
      ctx.fillStyle = "#00FFFF"; ctx.fillRect(-12, -4, 24, 8);
      ctx.restore();
      ctx.textAlign = "center"; ctx.fillStyle = "#FFE800"; ctx.font = "bold 13px monospace";
      ctx.fillText(`${p.currentTrick} ${Math.floor(p.trickRotation)}°`, p.x, p.y - 48);
    }
    // Diegetic Retro LCD Ski Altimeter & Telemetry Cluster (Offset 450, 84 - Clears All Reserved Corners)
    ctx.fillStyle = "rgba(10, 24, 20, 0.82)"; ctx.strokeStyle = "#49E27E"; ctx.lineWidth = 1.5;
    ctx.fillRect(450, 84, 126, 44); ctx.strokeRect(450, 84, 126, 44);
    ctx.textAlign = "left"; ctx.font = "9px monospace"; ctx.fillStyle = "#49E27E";
    ctx.fillText(`ALT: ${Math.floor(2800 - (w.distance || 0) * 0.4)}m`, 456, 96);
    ctx.fillText(`PITCH: ${Math.min(52, Math.floor(18 + (w.distance || 0) * 0.006))}°`, 456, 107);
    ctx.fillText(`ADR:`, 456, 120);
    ctx.fillStyle = "#1b4d2e"; ctx.fillRect(482, 113, 88, 7);
    ctx.fillStyle = (st.stats.adrenaline || 0) >= 80 ? "#FF3344" : "#00FF99";
    ctx.fillRect(482, 113, Math.min(88, (88 * (st.stats.adrenaline || 0)) / 100), 7);
    ctx.restore();
  }
});
