// Cohesive Milestone Plugin: v0.5.0
// Cohesive Milestone Plugin: v0.5.0 (Lich-Colossus Boss, Multi-Phase Eclipse & OSR Chronicle Ascension)
window.StudioEngine.registerModule("Milestone_v0_5_0", {
  init: function(state, engine) {
    const w = state.world;
    state.chronicle = { active: false, victory: false, obituary: "", rank: "", topLegends: [] };
    state.fx = { eclipseAlpha: 0, shards: [] };

    w.boss = {
      name: "MALAKOR, ARCHITECT OF THE BLACK CHALICE",
      x: 400, y: 190, r: 38,
      hp: 1200, maxHp: 1200, poise: 100, maxPoise: 100,
      phase: 1, stateTimer: 0, attackState: "IDLE", attackCd: 1.8,
      facing: Math.PI / 2, scytheAngle: 0, scytheActive: false,
      eclipseWaves: [], active: false, defeated: false
    };

    this.audioCtx = null;
    this.loadLegends();

    engine.on("PLAYER_DIED", () => this.openChronicle(state, false));
    engine.on("BOSS_DEFEATED", () => {
      w.boss.defeated = true;
      w.boss.active = false;
      this.playDoomGuitar(engine, true);
      this.openChronicle(state, true);
    });

    engine.on("BOSS_PHASE_TRANSITION", (phase) => {
      w.cameraShake = 18;
      state.fx.eclipseAlpha = 1.0;
      this.spawnGlassShards(state, w.boss.x, w.boss.y);
      this.playDoomGuitar(engine, false);
      (w.floatingTexts || (w.floatingTexts = [])).push({
        text: `★ MALAKOR ENTERS PHASE ${phase} ★`,
        x: w.boss.x, y: w.boss.y - 50, color: "#dc2626", life: 2.5
      });
    });

    engine.on("KEYDOWN", (ev) => {
      if (!state.chronicle.active) return;
      if (ev.code === "Space") this.resetDelve(state, engine);
      if (ev.code === "KeyC") {
        const classes = ["GRAVE_KNIGHT", "OCCULT_SCHOLAR", "BLOOD_OUTCAST"];
        const cur = state.stats && state.stats.characterClass ? state.stats.characterClass : classes[0];
        const next = classes[(classes.indexOf(cur) + 1) % classes.length];
        if (state.stats) state.stats.characterClass = next;
        this.openChronicle(state, state.chronicle.victory);
      }
    });
  },

  loadLegends: function() {
    try {
      this.legends = JSON.parse(localStorage.getItem("BC_CRYPT_LEGENDS")) || [
        { name: "Alador The Ashen", depth: 5, score: 3200, rank: "CHALICE BREAKER" },
        { name: "Vorgath Bone-Eater", depth: 4, score: 2450, rank: "CRYPT MARAUDER" },
        { name: "Lyra Of The Bleeding Hand", depth: 3, score: 1780, rank: "TOMB CRAWLER" },
        { name: "Morvath Iron-Vow", depth: 2, score: 980, rank: "TORCH SLAVE" },
        { name: "Kaelen The Unburied", depth: 1, score: 410, rank: "BONESMITH FLEDGLING" }
      ];
    } catch(e) { this.legends = []; }
  },

  spawnGlassShards: function(state, x, y) {
    const colors = ["#a855f7", "#dc2626", "#f59e0b", "#10b981", "#ffffff"];
    for (let i = 0; i < 48; i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = 60 + Math.random() * 200;
      (state.fx.shards || (state.fx.shards = [])).push({
        x: x + (Math.random() - 0.5) * 30, y: y + (Math.random() - 0.5) * 30,
        vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd - 60,
        sz: 3 + Math.random() * 5, rot: Math.random() * Math.PI * 2,
        vrot: (Math.random() - 0.5) * 8, color: colors[i % colors.length], life: 1.6
      });
    }
  },

  playDoomGuitar: function(engine, isVictory) {
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!this.audioCtx) this.audioCtx = new AC();
      const ctx = this.audioCtx;
      if (ctx.state === "suspended") ctx.resume();

      const notes = isVictory ? [73.42, 87.31, 98.00, 103.83, 98.00, 146.83] : [65.41, 77.78, 87.31, 92.50, 87.31, 65.41];
      const step = 0.22;
      const shaper = ctx.createWaveShaper();
      const n = 4096, curve = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        const x = (i * 2) / n - 1;
        curve[i] = ((Math.PI + 350) * x) / (Math.PI + 350 * Math.abs(x));
      }
      shaper.curve = curve;
      shaper.oversample = "2x";

      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(1200, ctx.currentTime);
      filter.Q.setValueAtTime(8, ctx.currentTime);

      const master = ctx.createGain();
      master.gain.setValueAtTime(0.045, ctx.currentTime);
      shaper.connect(filter);
      filter.connect(master);
      master.connect(ctx.destination);

      notes.forEach((freq, idx) => {
        const t = ctx.currentTime + idx * step;
        const o1 = ctx.createOscillator(), o2 = ctx.createOscillator(), g = ctx.createGain();
        o1.type = "sawtooth"; o2.type = "square";
        o1.frequency.setValueAtTime(freq, t);
        o2.frequency.setValueAtTime(freq * 1.008, t);
        g.gain.setValueAtTime(0.001, t);
        g.gain.exponentialRampToValueAtTime(0.05, t + 0.04);
        g.gain.exponentialRampToValueAtTime(0.0001, t + step * 0.95);
        o1.connect(g); o2.connect(g);
        g.connect(shaper);
        o1.start(t); o2.start(t);
        o1.stop(t + step); o2.stop(t + step);
      });
    } catch(e) {}
  },

  openChronicle: function(state, victory) {
    state.chronicle.active = true;
    state.chronicle.victory = victory;
    state.paused = true;
    const p = state.player, w = state.world;
    const gold = p.gold || 0;
    const depth = w.depth || 1;
    const rankIndex = Math.min(6, Math.floor(gold / 300) + depth);
    const ranks = ["CRAWLER RAT", "BONESMITH FLEDGLING", "TORCH SLAVE", "TOMB CRAWLER", "CRYPT MARAUDER", "DOOM KNIGHT", "CHALICE BREAKER"];
    state.chronicle.rank = ranks[rankIndex];
    state.chronicle.obituary = victory
      ? "MALAKOR HAS FALLEN. THE OBSIDIAN ARCHES SHATTER INTO ASH AND TRIUMPH."
      : "CONSUMED BY THE DARK ARCHITECT'S SCYTHE. FLESH JOINED WITH THE LIVING CRYPT.";

    const score = Math.floor(depth * 500 + gold * 2);
    (this.legends || (this.legends = [])).push({
      name: (state.stats && state.stats.characterClass ? state.stats.characterClass.replace("_", " ") : "DELVER"),
      depth: depth, score: score, rank: state.chronicle.rank
    });
    this.legends.sort((a, b) => b.score - a.score || b.depth - a.depth);
    this.legends = this.legends.slice(0, 5);
    try { localStorage.setItem("BC_CRYPT_LEGENDS", JSON.stringify(this.legends)); } catch(e) {}
  },

  resetDelve: function(state, engine) {
    state.chronicle.active = false;
    state.paused = false;
    const p = state.player, w = state.world;
    p.health = p.maxHealth || 5;
    p.stamina = p.maxStamina || 100;
    p.x = 400; p.y = 480; p.vx = 0; p.vy = 0;
    w.depth = 1;
    w.enemies = [];
    w.boss.hp = w.boss.maxHp;
    w.boss.phase = 1;
    w.boss.active = false;
    w.boss.defeated = false;
    w.boss.eclipseWaves = [];
    if (w.quest) { w.quest.progress = 0; w.quest.completed = false; }
    engine.emit("DELVE_RESET", {});
  },

  update: function(dt, state, engine) {
    const fx = state.fx, w = state.world, p = state.player;
    if (fx.eclipseAlpha > 0) fx.eclipseAlpha = Math.max(0, fx.eclipseAlpha - dt * 0.55);

    // Update glass shards
    for (let i = fx.shards.length - 1; i >= 0; i--) {
      const s = fx.shards[i];
      s.x += s.vx * dt; s.y += s.vy * dt; s.vy += 600 * dt;
      s.rot += s.vrot * dt; s.life -= dt;
      if (s.life <= 0) fx.shards.splice(i, 1);
    }

    if (state.chronicle.active) return;

    // Boss Activation gate: depth >= 5
    const b = w.boss;
    if (w.depth >= 5 && !b.defeated) {
      b.active = true;
      p.y = Math.min(p.y, 560); // Portcullis gate seals playfield at bottom
    } else {
      b.active = false;
      return;
    }

    // Boss Phase Transitions
    const hpPct = b.hp / b.maxHp;
    if (b.phase === 1 && hpPct <= 0.75) {
      b.phase = 2;
      engine.emit("BOSS_PHASE_TRANSITION", 2);
      w.bonePillars = [];
      for (let i = 0; i < 4; i++) {
        const ang = (Math.PI / 4) + i * (Math.PI / 2);
        (w.bonePillars || (w.bonePillars = [])).push({
          x: b.x + Math.cos(ang) * 180, y: b.y + Math.sin(ang) * 180,
          w: 26, h: 26, hp: 40, maxHp: 40
        });
      }
    } else if (b.phase === 2 && hpPct <= 0.35) {
      b.phase = 3;
      engine.emit("BOSS_PHASE_TRANSITION", 3);
    }

    // Boss AI & Facing
    const dx = p.x - b.x, dy = p.y - b.y;
    b.facing = Math.atan2(dy, dx);
    b.stateTimer += dt;

    // Movement: slow menacing drift toward arena center / player
    const targetX = 400 + Math.sin(b.stateTimer * 0.8) * 80;
    const targetY = 190 + Math.cos(b.stateTimer * 0.6) * 35;
    b.x += (targetX - b.x) * dt * 0.8;
    b.y += (targetY - b.y) * dt * 0.8;

    // Phase 1 Attack: Cleave Sweep
    b.attackCd -= dt;
    if (b.attackCd <= 0 && b.attackState === "IDLE") {
      b.attackState = "CLEAVE_WINDUP";
      b.stateTimer = 0;
    }
    if (b.attackState === "CLEAVE_WINDUP" && b.stateTimer >= 0.7) {
      b.attackState = "CLEAVE_STRIKE";
      b.stateTimer = 0;
      b.scytheAngle = b.facing - 1.2;
    }
    if (b.attackState === "CLEAVE_STRIKE") {
      b.scytheAngle += dt * 7.5;
      const reach = 140;
      const dist = Math.hypot(p.x - b.x, p.y - b.y);
      const angleToP = Math.atan2(p.y - b.y, p.x - b.x);
      let angleDiff = Math.abs(b.scytheAngle - angleToP);
      while (angleDiff > Math.PI) angleDiff -= Math.PI * 2;
      if (dist < reach && Math.abs(angleDiff) < 0.45 && !p.dashTimer && p.invuln <= 0) {
        p.health -= 25;
        p.invuln = 0.8;
        w.cameraShake = 12;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: "-25 CLEAVE", x: p.x, y: p.y - 20, color: "#dc2626", life: 1.2 });
        if (p.health <= 0) engine.emit("PLAYER_DIED", {});
      }
      if (b.scytheAngle >= b.facing + 1.2) {
        b.attackState = "IDLE";
        b.attackCd = b.phase === 3 ? 1.4 : 2.2;
      }
    }

    // Phase 3: Concentric Eclipse Waves every 4.5s
    if (b.phase >= 3) {
      this.eclipseTimer = (this.eclipseTimer || 0) + dt;
      if (this.eclipseTimer >= 4.5) {
        this.eclipseTimer = 0;
        (b.eclipseWaves || (b.eclipseWaves = [])).push({ x: b.x, y: b.y, radius: 20, speed: 160, thick: 24 });
      }
    }

    // Eclipse Wave Propagation & Collision
    for (let i = b.eclipseWaves.length - 1; i >= 0; i--) {
      const wave = b.eclipseWaves[i];
      wave.radius += wave.speed * dt;
      const dist = Math.hypot(p.x - wave.x, p.y - wave.y);

      // Check bone pillar occlusion
      let occluded = false;
      if (w.bonePillars) {
        for (let bp of w.bonePillars) {
          if (bp.hp > 0 && Math.hypot(p.x - bp.x, p.y - bp.y) < 32) { occluded = true; break; }
        }
      }

      if (!occluded && Math.abs(dist - wave.radius) < wave.thick && !p.dashTimer && p.invuln <= 0) {
        p.health -= 15;
        p.invuln = 0.7;
        w.cameraShake = 9;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: "-15 ECLIPSE", x: p.x, y: p.y - 20, color: "#a855f7", life: 1.2 });
        if (p.health <= 0) engine.emit("PLAYER_DIED", {});
      }
      if (wave.radius > 550) b.eclipseWaves.splice(i, 1);
    }

    // Player cleave hitting boss
    if (p.attackTimer > 0) {
      const hitDist = Math.hypot(b.x - p.x, b.y - p.y);
      if (hitDist < (p.weaponReach || 55) + b.r && !b.hitCooldown) {
        b.hp -= (p.weaponDamage || 15);
        b.poise = Math.max(0, b.poise - 12);
        b.hitCooldown = 0.25;
        w.cameraShake = 5;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: `${p.weaponDamage || 15}`, x: b.x, y: b.y - 35, color: "#f59e0b", life: 0.8 });
        if (b.hp <= 0) { b.hp = 0; engine.emit("BOSS_DEFEATED", {}); }
      }
    }
    if (b.hitCooldown > 0) b.hitCooldown -= dt;
  },

  render: function(ctx, state, engine) {
    const w = state.world, b = w.boss, fx = state.fx;

    // Draw Boss entities in world coordinates
    if (b.active && !b.defeated) {
      ctx.save();
      if (w.cameraShake > 0) {
        const sx = (Math.random() - 0.5) * w.cameraShake;
        const sy = (Math.random() - 0.5) * w.cameraShake;
        ctx.translate(sx, sy);
      }

      // 1. Eclipse Wave Rings
      b.eclipseWaves.forEach(wave => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(wave.x, wave.y, wave.radius, 0, Math.PI * 2);
        ctx.strokeStyle = "#a855f7";
        ctx.lineWidth = wave.thick * 0.45;
        ctx.shadowColor = "#a855f7";
        ctx.shadowBlur = 14;
        ctx.stroke();
        ctx.restore();
      });

      // 2. Bone Pillars (Phase 2 & 3)
      if (w.bonePillars) {
        w.bonePillars.forEach(bp => {
          if (bp.hp <= 0) return;
          if (w.lowPoly) {
            w.lowPoly.drawExtrudedBox(ctx, bp.x - bp.w / 2, bp.y - bp.h / 2, bp.w, bp.h, 44, "#3a3447", "#1a1622", state.player.x, state.player.y);
          }
          ctx.fillStyle = "#e2e8f0";
          ctx.beginPath();
          ctx.arc(bp.x, bp.y - 24, 7, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      // 3. Boss Silhouette (Malakor, Lich-Colossus)
      ctx.save();
      ctx.translate(b.x, b.y);

      // Radial aura
      const aura = ctx.createRadialGradient(0, 0, 10, 0, 0, b.r + 28);
      aura.addColorStop(0, "rgba(168, 85, 247, 0.4)");
      aura.addColorStop(1, "rgba(7, 5, 10, 0)");
      ctx.fillStyle = aura;
      ctx.beginPath();
      ctx.arc(0, 0, b.r + 28, 0, Math.PI * 2);
      ctx.fill();

      // Robe / Body
      ctx.fillStyle = "#120e1c";
      ctx.strokeStyle = "#a855f7";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(-b.r * 0.8, b.r * 1.1);
      ctx.lineTo(-b.r * 0.4, -b.r * 0.7);
      ctx.lineTo(0, -b.r * 1.1);
      ctx.lineTo(b.r * 0.4, -b.r * 0.7);
      ctx.lineTo(b.r * 0.8, b.r * 1.1);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Horned Skull Mask
      ctx.fillStyle = "#e2e8f0";
      ctx.beginPath();
      ctx.arc(0, -b.r * 0.35, 13, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#dc2626";
      ctx.fillRect(-6, -b.r * 0.35 - 2, 4, 3);
      ctx.fillRect(2, -b.r * 0.35 - 2, 4, 3);

      // Scythe Swing / Idle Orientation
      const sAng = b.attackState === "CLEAVE_STRIKE" ? b.scytheAngle - b.facing : Math.sin(b.stateTimer * 2) * 0.2;
      ctx.save();
      ctx.rotate(b.facing + sAng);
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(0, 0); ctx.lineTo(110, -25);
      ctx.stroke();
      // Scythe Blade Crescent
      ctx.strokeStyle = "#eab308";
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.arc(110, -25, 42, -Math.PI * 0.4, Math.PI * 0.4);
      ctx.stroke();
      ctx.restore();

      ctx.restore(); // end Boss translate

      // Portcullis Spikes at y=560
      ctx.strokeStyle = "#64748b";
      ctx.lineWidth = 4;
      /* removed bottom sawtooth clutter */
      ctx.restore();
    }

    // Render Shattered Stained-Glass Shards
    if (fx.shards.length > 0) {
      ctx.save();
      fx.shards.forEach(s => {
        ctx.save();
        ctx.translate(s.x, s.y);
        ctx.rotate(s.rot);
        ctx.fillStyle = s.color;
        ctx.beginPath();
        ctx.moveTo(-s.sz, -s.sz); ctx.lineTo(s.sz, -s.sz * 0.5); ctx.lineTo(0, s.sz);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      });
      ctx.restore();
    }

    // Eclipse Transition Screen Wash
    if (fx.eclipseAlpha > 0) {
      ctx.save();
      ctx.fillStyle = `rgba(168, 85, 247, ${fx.eclipseAlpha * 0.42})`;
      ctx.fillRect(0, 0, 800, 600);
      ctx.restore();
    }

    // Steady Boss Health Bar docked directly beneath status ribbon (y: 38..48)
    if (b.active && !b.defeated) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.save();
      ctx.fillStyle = "rgba(7, 5, 10, 0.85)";
      ctx.fillRect(180, 38, 440, 10);
      const bossHpPct = Math.max(0, b.hp / b.maxHp);
      ctx.fillStyle = b.phase === 3 ? "#dc2626" : (b.phase === 2 ? "#a855f7" : "#eab308");
      ctx.fillRect(182, 39, 436 * bossHpPct, 8);
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 1;
      ctx.strokeRect(180, 38, 440, 10);
      ctx.fillStyle = "#f8fafc";
      ctx.font = "9px monospace";
      ctx.fillText(b.name, 184, 46);
      ctx.restore();
    }

    // Illustrated OSR Chronicle Modal (Death & Victory)
    if (state.chronicle.active) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.save();
      ctx.fillStyle = "rgba(4, 3, 6, 0.94)";
      ctx.fillRect(0, 0, 800, 600);

      // Parchment Chiaroscuro Box
      const bx = 80, by = 44, bw = 640, bh = 512;
      ctx.fillStyle = "#0c0a12";
      ctx.fillRect(bx, by, bw, bh);
      ctx.strokeStyle = state.chronicle.victory ? "#eab308" : "#dc2626";
      ctx.lineWidth = 3;
      ctx.strokeRect(bx, by, bw, bh);

      ctx.fillStyle = state.chronicle.victory ? "#eab308" : "#dc2626";
      ctx.font = "bold 20px monospace";
      ctx.fillText(state.chronicle.victory ? "★ ASCENSION ACHIEVED // THE BLACK CHALICE SHATTERED ★" : "✝ DELVER RECORD OF DEATH & DISCORD ✝", bx + 24, by + 40);

      ctx.font = "12px monospace";
      ctx.fillStyle = "#cbd5e1";
      ctx.fillText(`EPITAPH: "${state.chronicle.obituary}"`, bx + 24, by + 68);
      ctx.fillText(`OSR ADVENTURER RANK: [ ${state.chronicle.rank} ]`, bx + 24, by + 94);
      ctx.fillText(`CLASS ARCHETYPE: ${state.stats && state.stats.characterClass ? state.stats.characterClass : "GRAVE KNIGHT"}`, bx + 24, by + 116);
      ctx.fillText(`PURGED DEPTH: ${w.depth}    LOOT HOARD: ${state.player.gold || 0}G`, bx + 24, by + 138);

      // Leaderboard
      ctx.strokeStyle = "#334155";
      ctx.strokeRect(bx + 24, by + 160, bw - 48, 190);
      ctx.fillStyle = "#94a3b8";
      ctx.font = "11px monospace";
      ctx.fillText("── TOP-5 CRYPT LEGENDS (LOCAL OBSIDIAN TABLET) ──", bx + 36, by + 180);

      this.legends.forEach((entry, idx) => {
        const rowY = by + 208 + idx * 26;
        ctx.fillStyle = idx === 0 ? "#eab308" : "#e2e8f0";
        ctx.fillText(`${idx + 1}. ${entry.name.padEnd(20, " ")} DEPTH ${entry.depth}   ${entry.rank.padEnd(20, " ")} ${entry.score} PTS`, bx + 36, rowY);
      });

      // Interactive Prompts
      ctx.fillStyle = "#f59e0b";
      ctx.font = "bold 13px monospace";
      ctx.fillText("[SPACE] COMMENCE NEW DELVE        [C] CYCLE CLASS ARCHETYPE", bx + 64, by + 475);
      ctx.restore();
    }
  }
});
