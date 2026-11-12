// Cohesive Milestone Plugin: v0.5.0 (Abominable Yeti, Web Audio & Run Obituary)
window.StudioEngine.registerModule("Milestone_v0_5_0", {
  init: function(st, eng) {
    const w = st.world, p = st.player;
    w.yetiSpawnThreshold = 400; // Spawns at 400m!
    w.yeti = { active: false, x: 400, y: 40, vx: 0, vy: 0, state: "CHASE", timer: 0, leapCd: 3.5 };
    this.obituary = null;
    this.leaderboard = [
      { name: "K. Vesper", dist: 2450, score: 18400 },
      { name: "S. Clark", dist: 1920, score: 14200 },
      { name: "N. Vance", dist: 1380, score: 9800 }
    ];
    this.audioCtx = null;
    this.soundEnabled = false;

    const initAudio = () => {
      if (!this.audioCtx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (AC) {
          this.audioCtx = new AC();
          this.soundEnabled = true;
          // Create 2-second procedural white-noise buffer for continuous snow carve swoosh & alpine wind
          const sr = this.audioCtx.sampleRate;
          const buf = this.audioCtx.createBuffer(1, sr * 2, sr);
          const data = buf.getChannelData(0);
          for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;

          const noise = this.audioCtx.createBufferSource();
          noise.buffer = buf;
          noise.loop = true;

          this.windFilter = this.audioCtx.createBiquadFilter();
          this.windFilter.type = "bandpass";
          this.windFilter.frequency.value = 420;
          this.windFilter.Q.value = 1.8;

          this.windGain = this.audioCtx.createGain();
          this.windGain.gain.value = 0.0;

          noise.connect(this.windFilter);
          this.windFilter.connect(this.windGain);
          this.windGain.connect(this.audioCtx.destination);
          noise.start();
        }
      } else if (this.audioCtx.state === "suspended") {
        this.audioCtx.resume();
      }
    };
    window.addEventListener("keydown", initAudio, { once: true });
    window.addEventListener("mousedown", initAudio, { once: true });

    this.playTone = (freq, type, dur, vol) => {
      if (!this.audioCtx || this.audioCtx.state !== "running") return;
      try {
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.type = type || "sawtooth";
        osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
        gain.gain.setValueAtTime(vol || 0.06, this.audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + dur);
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);
        osc.start();
        osc.stop(this.audioCtx.currentTime + dur);
      } catch (e) {}
    };

    const triggerDeath = (cause) => {
      if (w.mode === "OBITUARY") return;
      w.mode = "OBITUARY";
      st.paused = true;
      const dist = Math.floor(w.distance || 0);
      const relics = ((st.inventory && st.inventory.relics) || []).length;
      const score = dist * 5 + (st.stats.xp || 0) * 2 + relics * 250;
      this.obituary = { cause, dist, relics, score, level: st.stats.level || 1, cls: st.stats.characterClass || "Alpinist" };
      this.leaderboard.push({ name: "YOU (" + this.obituary.cls + ")", dist, score });
      this.leaderboard.sort((a, b) => b.score - a.score);
      this.leaderboard = this.leaderboard.slice(0, 5);
      this.playTone(95, "sawtooth", 0.6, 0.12);
    };

    eng.on("YETI_ROAR", () => {
      this.playTone(110, "sawtooth", 0.45, 0.12);
      setTimeout(() => this.playTone(75, "square", 0.55, 0.12), 120);
    });
    eng.on("YETI_MAUL", () => triggerDeath("Run Down & Mauled by the Abominable Yeti"));
    eng.on("PLAYER_WIPEOUT", () => {
      this.playTone(140, "triangle", 0.25, 0.08);
      if ((st.player.wipeouts || 0) >= (st.player.maxHealth || 3)) {
        triggerDeath("Fatal Alpine Trauma (3/3 Wipeouts)");
      }
    });
  },

  update: function(dt, st, eng) {
    const w = st.world, p = st.player, y = w.yeti;
    const dist = Math.floor(w.distance || 0);

    // Handle Obituary Restart
    if (w.mode === "OBITUARY") {
      st.paused = true;
      if (this.windGain && this.audioCtx) this.windGain.gain.setTargetAtTime(0.0, this.audioCtx.currentTime, 0.04);
      if (st.keys.jump || st.pointer.clicked) {
        w.mode = "PLAY";
        this.obituary = null;
        p.wipeouts = 0;
        p.health = p.maxHealth || 3;
        w.distance = 0;
        y.active = false;
        y.y = 40;
        st.paused = false;
        st.keys.jump = false;
      }
      return;
    }

    // Immediate backup check if wipeouts reached 3
    if ((p.wipeouts || 0) >= (p.maxHealth || 3)) {
      eng.emit("PLAYER_WIPEOUT", { wipeouts: p.wipeouts });
      return;
    }

    if (st.paused) { if (this.windGain && this.audioCtx) this.windGain.gain.setTargetAtTime(0.0, this.audioCtx.currentTime, 0.04); return; }

    // Continuous Procedural Snow Carve Swoosh & Wind Rush (BiquadFilter modulated by speed & carving)
    if (this.audioCtx && this.windGain && this.windFilter) {
      const now = this.audioCtx.currentTime;
      const spdRatio = Math.min(1.5, Math.max(0.1, (w.speed || 200) / 260));
      const isCarving = st.keys.left || st.keys.right;
      const isBraking = st.keys.up;
      const targetFreq = isBraking ? 950 : (isCarving ? 680 + spdRatio * 240 : 280 + spdRatio * 160);
      const targetQ = isCarving ? 1.2 : 3.0;
      const targetGain = p.isAirborne ? 0.015 : (isCarving ? 0.095 : 0.032 * spdRatio);
      this.windFilter.frequency.setTargetAtTime(targetFreq, now, 0.05);
      this.windFilter.Q.setTargetAtTime(targetQ, now, 0.05);
      this.windGain.gain.setTargetAtTime(targetGain, now, 0.06);
    }

    // Spawn Yeti at 400m!
    if (dist >= w.yetiSpawnThreshold && !y.active) {
      y.active = true;
      y.x = p.x;
      y.y = 30;
      y.state = "CHASE";
      y.leapCd = 2.5;
      eng.emit("YETI_ROAR");
    }

    if (!y.active) return;

    // Yeti AI State Machine in Screen Space (Player is near p.y ~ 180..220)
    const targetY = p.y || 200;
    if (y.state === "STUMBLE") {
      y.timer -= dt;
      y.y = Math.max(20, y.y - 90 * dt);
      if (y.timer <= 0) {
        y.state = "CHASE";
        eng.emit("YETI_ROAR");
      }
    } else if (y.state === "LEAP") {
      y.timer -= dt;
      y.x += (p.x - y.x) * 4.2 * dt;
      y.y += 185 * dt;
      if (y.timer <= 0 || y.y >= targetY + 35) {
        y.state = "CHASE";
        y.leapCd = 3.2;
      }
    } else {
      // CHASE state: stalks player from behind (top of screen y=50..160)
      const dx = p.x - y.x;
      y.x += Math.sign(dx) * Math.min(Math.abs(dx) * 3.5, 195) * dt;
      const desiredY = st.keys.down ? 75 : (st.keys.up ? 155 : 115);
      y.y += (desiredY - y.y) * 1.8 * dt;
      y.leapCd -= dt;
      if (y.leapCd <= 0 && Math.abs(p.x - y.x) < 120) {
        y.state = "LEAP";
        y.timer = 0.65;
        eng.emit("YETI_ROAR");
      }
    }

    // Check if Yeti trips on an obstacle tree/rock
    const obsList = w.obstacles || [];
    for (let i = 0; i < obsList.length; i++) {
      const o = obsList[i];
      const oy = o.y !== undefined ? o.y : o.worldY;
      if (Math.abs((o.x || 0) - y.x) < 22 && Math.abs((oy || 0) - y.y) < 22 && y.state !== "STUMBLE") {
        y.state = "STUMBLE";
        y.timer = 1.3;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: "YETI TRIPPED!", x: y.x, y: y.y, life: 0.9 });
        break;
      }
    }

    // Check Yeti Maul Collision with Player
    if (y.state !== "STUMBLE" && Math.hypot(p.x - y.x, targetY - y.y) < 26 && !p.isAirborne) {
      eng.emit("YETI_MAUL");
    }
  },

  render: function(ctx, st) {
    const w = st.world, p = st.player, y = w.yeti;

    // 1. Render Diegetic Abominable Yeti Boss in World Space
    if (y && y.active) {
      ctx.save();
      ctx.translate(y.x, y.y);
      if (y.state === "STUMBLE") ctx.rotate(0.45);
      const scale = y.state === "LEAP" ? 1.25 : 1.0;
      ctx.scale(scale, scale);

      // Shadow
      ctx.fillStyle = "rgba(15, 23, 42, 0.35)";
      ctx.beginPath();
      ctx.ellipse(0, 22, 20, 8, 0, 0, Math.PI * 2);
      ctx.fill();

      // Shaggy White/Ice-Blue Fur Body
      ctx.fillStyle = y.state === "LEAP" ? "#fef2f2" : "#e2e8f0";
      ctx.fillRect(-18, -18, 36, 36);
      ctx.fillStyle = "#94a3b8";
      ctx.fillRect(-22, -10, 8, 22);
      ctx.fillRect(14, -10, 8, 22);

      // Horns & Glowing Crimson Eyes
      ctx.fillStyle = "#334155";
      ctx.fillRect(-14, -24, 6, 6);
      ctx.fillRect(8, -24, 6, 6);
      ctx.fillStyle = "#ef4444";
      ctx.fillRect(-8, -10, 5, 4);
      ctx.fillRect(3, -10, 5, 4);

      // Roaring Maw
      ctx.fillStyle = "#7f1d1d";
      ctx.fillRect(-7, -2, 14, 7);

      // Warning Indicator above Yeti
      ctx.fillStyle = y.state === "LEAP" ? "#ef4444" : "#f59e0b";
      ctx.font = "bold 11px monospace";
      ctx.textAlign = "center";
      ctx.fillText(y.state === "LEAP" ? "!! YETI LEAP !!" : (y.state === "STUMBLE" ? "STUNNED" : "YETI"), 0, -28);
      ctx.restore();
    }

    // 2. Render Bottom-Right Dock (x: 520, y: 536)
    ctx.save();
    ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
    ctx.fillRect(520, 536, 268, 52);
    ctx.strokeStyle = y && y.active ? "#ef4444" : "#475569";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(520, 536, 268, 52);

    const distToYeti = y && y.active ? Math.max(0, Math.floor((p.y || 200) - y.y)) : Math.max(0, 400 - Math.floor(w.distance || 0));
    ctx.fillStyle = y && y.active ? "#fca5a5" : "#94a3b8";
    ctx.font = "bold 11px monospace";
    ctx.textAlign = "left";
    ctx.fillText(y && y.active ? `RADAR // YETI: ${distToYeti}M [${y.state}]` : `RADAR // YETI AMBUSH IN ${distToYeti}M`, 530, 555);
    ctx.fillStyle = "#38bdf8";
    ctx.fillText(`AUDIO: ${this.soundEnabled ? "SYNTH ON" : "CLICK/KEY"}   HI: ${this.leaderboard[0].score}`, 530, 575);
    ctx.restore();

    // 3. Render Terminal Run Obituary Modal (if dead)
    if (w.mode === "OBITUARY" && this.obituary) {
      ctx.save();
      ctx.fillStyle = "rgba(15, 23, 42, 0.98)";
      ctx.fillRect(140, 100, 520, 390);
      ctx.strokeStyle = "#ef4444";
      ctx.lineWidth = 3;
      ctx.strokeRect(140, 100, 520, 390);

      ctx.textAlign = "center";
      ctx.fillStyle = "#ef4444";
      ctx.font = "bold 22px monospace";
      ctx.fillText("RUN TERMINATED // ALPINE OBITUARY", 400, 145);

      ctx.fillStyle = "#f8fafc";
      ctx.font = "14px monospace";
      ctx.fillText(`CAUSE: ${this.obituary.cause}`, 400, 180);
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 15px monospace";
      ctx.fillText(`DISTANCE: ${this.obituary.dist}M  |  RELICS: ${this.obituary.relics}  |  FINAL SCORE: ${this.obituary.score}`, 400, 212);

      // High Score Leaderboard Table
      ctx.fillStyle = "#facc15";
      ctx.font = "bold 14px monospace";
      ctx.fillText("--- PEAK EXPEDITION LEADERBOARD ---", 400, 252);

      ctx.font = "13px monospace";
      for (let i = 0; i < this.leaderboard.length; i++) {
        const row = this.leaderboard[i];
        const ry = 280 + i * 24;
        ctx.fillStyle = row.name.startsWith("YOU") ? "#4ade80" : "#cbd5e1";
        ctx.textAlign = "left";
        ctx.fillText(`${i + 1}. ${row.name}`, 210, ry);
        ctx.textAlign = "right";
        ctx.fillText(`${row.dist}M  (${row.score} PTS)`, 590, ry);
      }

      ctx.textAlign = "center";
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 15px monospace";
      ctx.fillText("[PRESS SPACE OR CLICK TO LAUNCH NEW DESCENT]", 400, 455);
      ctx.restore();
    }
  }
});
