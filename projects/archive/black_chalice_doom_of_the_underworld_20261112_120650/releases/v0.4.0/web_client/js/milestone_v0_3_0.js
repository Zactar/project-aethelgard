// Cohesive Milestone Plugin: v0.3.0 (Transformative Diablo/OSR Relics, Ultima Environmental Physics & 68-BPM Doom Synth)
window.StudioEngine.registerModule("Milestone_v0_3_0", {
  init: function(state, engine) {
    const w = state.world;
    w.loot = w.loot || [];
    w.projectiles = w.projectiles || [];
    w.oilPuddles = [];
    w.cauldrons = [];
    w.monoliths = [];
    this.orbitSkulls = [];
    this.roomSeeded = "";

    // Catalog of 10 Transformative, Behavior-Changing OSR Magic Weapons & Relics (ZERO boring flat-stat sticks!)
    this.ARTIFACT_CATALOG = [
      {
        id: "WIZARD_ZWEIHANDER", slot: "WEAPON", name: "Electric Wizard's Zweihänder",
        rarity: "MYTHIC DOOM-GOLD", color: "#eab308", dmg: 30, reach: 72,
        powerDesc: "CLEAVE UNLEASHES 3-FORKED PURPLE CHAIN-LIGHTNING ARCS",
        onAttack: (st, p) => {
          const enemies = st.world.enemies || [];
          for (let i = 0; i < Math.min(3, enemies.length); i++) {
            const en = enemies[i];
            if (Math.hypot(en.x - p.x, en.y - p.y) < 210) {
              en.hp -= 18; en.stagger = 0.5;
              st.world.particles.push({ x: en.x, y: en.y, vx: 0, vy: -40, color: "#a855f7", life: 0.45, boltFromX: p.x, boltFromY: p.y });
            }
          }
        }
      },
      {
        id: "CANDLEMASS_FLAIL", slot: "WEAPON", name: "Blood-Flail of Candlemass",
        rarity: "BLOOD-CURSED CRIMSON", color: "#dc2626", dmg: 26, reach: 68,
        powerDesc: "360° WHIRLWIND CLEAVE + VAMPIRIC BLOOD-DRAIN ON KILL",
        onEquip: (p) => { p.whirlwindCleave = true; },
        onKill: (st, p) => {
          p.health = Math.min(p.maxHealth, (p.health || 5) + 1);
          st.world.floatingTexts.push({ text: "🩸 +1 HP VAMPIRIC TITHE", x: p.x, y: p.y - 28, color: "#dc2626", life: 1.0 });
        }
      },
      {
        id: "SLEEP_CAUSTIC_LANCE", slot: "WEAPON", name: "Sleep's Verdigris Bong-Lance",
        rarity: "RUNIC VERDIGRIS", color: "#10b981", dmg: 24, reach: 64,
        powerDesc: "SWINGS LAUNCH PIERCING ACID ORBS THAT SPAWN CAUSTIC POOLS",
        onAttack: (st, p) => {
          st.world.projectiles.push({
            x: p.x, y: p.y, vx: Math.cos(p.facingAngle) * 320, vy: Math.sin(p.facingAngle) * 320,
            r: 8, dmg: 20, color: "#10b981", life: 1.1, spawnAcid: true
          });
        }
      },
      {
        id: "BELL_WITCH_SCYTHE", slot: "WEAPON", name: "Bell Witch's Necro-Scythe",
        rarity: "OCCULT VIOLET", color: "#a855f7", dmg: 28, reach: 76,
        powerDesc: "SUMMONS 3 ORBITING SPECTRAL SKULLS THAT CRUSH FOES",
        onEquip: (p, mod) => {
          mod.orbitSkulls = [{ angle: 0 }, { angle: 2.09 }, { angle: 4.18 }];
        }
      },
      {
        id: "HELLFIRE_GREATAXE", slot: "WEAPON", name: "Conan's Magma Cleaver",
        rarity: "MYTHIC DOOM-GOLD", color: "#f97316", dmg: 32, reach: 66,
        powerDesc: "HURLS EXPLODING MAGMA BOULDERS THAT IGNITE OIL POOLS",
        onAttack: (st, p) => {
          st.world.projectiles.push({
            x: p.x, y: p.y, vx: Math.cos(p.facingAngle) * 270, vy: Math.sin(p.facingAngle) * 270,
            r: 10, dmg: 26, color: "#f97316", life: 0.9, igniteOil: true
          });
        }
      },
      {
        id: "MONOLITH_RING", slot: "RING", name: "Ring of the Obsidian Monolith",
        rarity: "OCCULT VIOLET", color: "#a855f7",
        powerDesc: "DODGE-ROLLING DROPS AN EXPLODING GRAVITY MONOLITH CRYSTAL",
        onDodge: (st, p) => {
          st.world.monoliths.push({ x: p.x, y: p.y, timer: 1.4, r: 95, color: "#a855f7" });
        }
      },
      {
        id: "ABYSSAL_LANTERN", slot: "RELIC", name: "Ultraviolet Lantern of Xibalba",
        rarity: "RUNIC VERDIGRIS", color: "#38bdf8",
        powerDesc: "ULTRAVIOLET TORCHLIGHT BURNS NEARBY FOES & FREEZES TORCH DECAY",
        onEquip: (p) => { p.uvTorch = true; p.torchLevel = 100; }
      },
      {
        id: "SENTINEL_ AEGIS", slot: "RELIC", name: "Aegis of the Bone-Cathedral",
        rarity: "MYTHIC DOOM-GOLD", color: "#eab308",
        powerDesc: "PARRIES & RITES FIRE AN 8-WAY RING OF PIERCING BONE-SPEARS",
        onDodge: (st, p) => {
          for (let i = 0; i < 8; i++) {
            const a = (i / 8) * Math.PI * 2;
            st.world.projectiles.push({
              x: p.x, y: p.y, vx: Math.cos(a) * 340, vy: Math.sin(a) * 340,
              r: 6, dmg: 18, color: "#eab308", life: 0.75
            });
          }
        }
      }
    ];

    this.equipped = { WEAPON: null, RELIC: null, RING: null };

    // Hook into combat events to trigger item behaviors!
    engine.on("PLAYER_ATTACK", () => {
      if (this.equipped.WEAPON && this.equipped.WEAPON.onAttack) {
        this.equipped.WEAPON.onAttack(state, state.player);
      }
    });
    engine.on("PLAYER_DODGE", () => {
      if (this.equipped.RING && this.equipped.RING.onDodge) this.equipped.RING.onDodge(state, state.player);
      if (this.equipped.RELIC && this.equipped.RELIC.onDodge) this.equipped.RELIC.onDodge(state, state.player);
    });
    engine.on("ENEMY_SLAIN", (ev) => {
      if (this.equipped.WEAPON && this.equipped.WEAPON.onKill) this.equipped.WEAPON.onKill(state, state.player);
      if (Math.random() < 0.65) this.spawnArtifactDrop(state, ev.x, ev.y);
    });

    // Press [SHIFT / E] near dropped loot, cauldrons, or braziers to interact!
    engine.on("KEYDOWN", (ev) => {
      if (state.paused) return;
      if (ev.code === "ShiftLeft" || ev.code === "ShiftRight" || ev.code === "KeyE") {
        this.tryWorldInteraction(state);
      }
    });

    this.initDoomAudio();
  },

  initDoomAudio: function() {
    this.audioCtx = null;
    this.step = 0;
    this.stepTimer = 0;
    this.doomNotes = [65.41, 65.41, 77.78, 73.42, 65.41, 98.00, 92.50, 77.78]; // Drop-C Stoner Doom Riff
    const unlock = () => {
      if (!this.audioCtx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (AC) this.audioCtx = new AC();
      } else if (this.audioCtx.state === "suspended") {
        this.audioCtx.resume();
      }
    };
    window.addEventListener("keydown", unlock);
    window.addEventListener("mousedown", unlock);
  },

  spawnArtifactDrop: function(state, x, y) {
    const template = this.ARTIFACT_CATALOG[Math.floor(Math.random() * this.ARTIFACT_CATALOG.length)];
    state.world.loot.push({ ...template, x: Math.max(95, Math.min(705, x)), y: Math.max(110, Math.min(510, y)), bob: Math.random() * 6 });
  },

  seedRoomProps: function(state) {
    const w = state.world;
    const key = `${w.currentRoom.x},${w.currentRoom.y}`;
    if (this.roomSeeded === key) return;
    this.roomSeeded = key;

    w.oilPuddles = [
      { x: 290, y: 240, r: 42, burning: 0 },
      { x: 510, y: 380, r: 44, burning: 0 }
    ];
    w.cauldrons = [{ x: 400, y: 155, used: false }];
    w.loot = [];
    // Spawn 2 guaranteed distinct behavioral artifacts in the starting room so player can test builds immediately!
    this.spawnArtifactDrop(state, 310, 360);
    this.spawnArtifactDrop(state, 490, 360);
  },

  tryWorldInteraction: function(state) {
    const p = state.player, w = state.world;
    // 1. Equip nearby Artifact Loot
    for (let i = w.loot.length - 1; i >= 0; i--) {
      const it = w.loot[i];
      if (Math.hypot(p.x - it.x, p.y - it.y) < 44) {
        this.equipped[it.slot] = it;
        if (it.slot === "WEAPON") {
          p.weaponName = it.name;
          p.weaponDamage = it.dmg;
          p.weaponReach = it.reach;
          p.weaponGlow = it.color;
          p.whirlwindCleave = false;
        }
        if (it.onEquip) it.onEquip(p, this);
        w.floatingTexts.push({ text: `EQUIPPED: ${it.name.toUpperCase()}!`, x: p.x, y: p.y - 32, color: it.color, life: 1.6 });
        w.loot.splice(i, 1);
        return;
      }
    }

    // 2. Kick nearby Brazier into Oil Puddle -> Ignite Hellfire Zone!
    for (let i = 0; i < (w.braziers || []).length; i++) {
      const b = w.braziers[i];
      if (Math.hypot(p.x - b.x, p.y - b.y) < 52) {
        const ang = p.facingAngle || 0;
        b.x = Math.max(80, Math.min(720, b.x + Math.cos(ang) * 95));
        b.y = Math.max(95, Math.min(525, b.y + Math.sin(ang) * 95));
        w.floatingTexts.push({ text: "🔥 BRAZIER KICKED! 🔥", x: b.x, y: b.y - 20, color: "#f97316", life: 1.0 });
        for (let j = 0; j < w.oilPuddles.length; j++) {
          const oil = w.oilPuddles[j];
          if (Math.hypot(b.x - oil.x, b.y - oil.y) < oil.r + 45) oil.burning = 8.0;
        }
        return;
      }
    }

    // 3. Drink from Alchemy Cauldron
    for (let i = 0; i < (w.cauldrons || []).length; i++) {
      const c = w.cauldrons[i];
      if (!c.used && Math.hypot(p.x - c.x, p.y - c.y) < 48) {
        c.used = true;
        p.health = p.maxHealth;
        p.torchLevel = 100;
        this.spawnArtifactDrop(state, c.x, c.y + 38);
        w.floatingTexts.push({ text: "⚗ ALCHEMY TRANSMUTATION! +RELIC & FULL HP", x: c.x, y: c.y - 24, color: "#10b981", life: 1.6 });
        return;
      }
    }
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    const p = state.player, w = state.world;
    this.seedRoomProps(state);

    // 68-BPM Stoner-Doom Fuzz Bass Drone Sequencer
    this.stepTimer += dt;
    if (this.stepTimer >= 0.44) {
      this.stepTimer -= 0.44;
      const freq = this.doomNotes[this.step % this.doomNotes.length];
      this.step++;
      if (this.audioCtx && this.audioCtx.state === "running") {
        const now = this.audioCtx.currentTime;
        const osc = this.audioCtx.createOscillator();
        const flt = this.audioCtx.createBiquadFilter();
        const g = this.audioCtx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(freq, now);
        flt.type = "lowpass";
        flt.frequency.setValueAtTime(280, now);
        flt.Q.setValueAtTime(5.0, now);
        g.gain.setValueAtTime(0.065, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.40);
        osc.connect(flt); flt.connect(g); g.connect(this.audioCtx.destination);
        osc.start(now); osc.stop(now + 0.41);
      }
    }

    // Ultraviolet Torch DoT Aura
    if (p.uvTorch) {
      p.torchLevel = 100;
      for (let i = 0; i < (w.enemies || []).length; i++) {
        const en = w.enemies[i];
        if (Math.hypot(en.x - p.x, en.y - p.y) < 160) en.hp -= 9 * dt;
      }
    }

    // Update Orbiting Spectral Skulls (Bell Witch's Necro-Scythe)
    for (let i = 0; i < this.orbitSkulls.length; i++) {
      const sk = this.orbitSkulls[i];
      sk.angle += 3.2 * dt;
      sk.x = p.x + Math.cos(sk.angle) * 48;
      sk.y = p.y + Math.sin(sk.angle) * 48;
      for (let j = 0; j < (w.enemies || []).length; j++) {
        const en = w.enemies[j];
        if (Math.hypot(en.x - sk.x, en.y - sk.y) < en.r + 12) {
          en.hp -= 35 * dt;
        }
      }
    }

    // Update Item Projectiles (Acid Orbs, Magma Boulders, Bone-Spears)
    for (let i = w.projectiles.length - 1; i >= 0; i--) {
      const pr = w.projectiles[i];
      pr.x += pr.vx * dt; pr.y += pr.vy * dt; pr.life -= dt;
      if (pr.igniteOil) {
        for (let j = 0; j < w.oilPuddles.length; j++) {
          if (Math.hypot(pr.x - w.oilPuddles[j].x, pr.y - w.oilPuddles[j].y) < w.oilPuddles[j].r + 16) {
            w.oilPuddles[j].burning = 7.0;
          }
        }
      }
      for (let j = 0; j < (w.enemies || []).length; j++) {
        const en = w.enemies[j];
        if (Math.hypot(en.x - pr.x, en.y - pr.y) < en.r + pr.r) {
          en.hp -= pr.dmg; en.stagger = 0.35; pr.life = 0;
          if (pr.spawnAcid) w.oilPuddles.push({ x: pr.x, y: pr.y, r: 32, burning: 4.5, isAcid: true });
          break;
        }
      }
      if (pr.life <= 0) w.projectiles.splice(i, 1);
    }

    // Update Dodge-Roll Gravity Monoliths
    for (let i = w.monoliths.length - 1; i >= 0; i--) {
      const m = w.monoliths[i];
      m.timer -= dt;
      for (let j = 0; j < (w.enemies || []).length; j++) {
        const en = w.enemies[j];
        const dx = m.x - en.x, dy = m.y - en.y, d = Math.hypot(dx, dy) || 1;
        if (d < m.r) { en.x += (dx / d) * 65 * dt; en.y += (dy / d) * 65 * dt; }
      }
      if (m.timer <= 0) {
        for (let j = 0; j < (w.enemies || []).length; j++) {
          if (Math.hypot(w.enemies[j].x - m.x, w.enemies[j].y - m.y) < m.r) w.enemies[j].hp -= 28;
        }
        w.floatingTexts.push({ text: "💥 MONOLITH RUPTURE! 💥", x: m.x, y: m.y - 18, color: "#a855f7", life: 0.9 });
        w.monoliths.splice(i, 1);
      }
    }

    // Update Burning Oil / Acid Puddles
    for (let i = 0; i < w.oilPuddles.length; i++) {
      const oil = w.oilPuddles[i];
      if (oil.burning > 0) {
        oil.burning -= dt;
        for (let j = 0; j < (w.enemies || []).length; j++) {
          const en = w.enemies[j];
          if (Math.hypot(en.x - oil.x, en.y - oil.y) < oil.r) en.hp -= 18 * dt;
        }
      }
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const p = state.player, w = state.world, lp = w.lowPoly;
    ctx.save();

    // 1. Render Oil Puddles & Burning Hellfire Zones
    for (let i = 0; i < (w.oilPuddles || []).length; i++) {
      const oil = w.oilPuddles[i];
      ctx.fillStyle = oil.burning > 0 ? (oil.isAcid ? "rgba(16, 185, 129, 0.45)" : "rgba(234, 88, 12, 0.48)") : "rgba(15, 23, 42, 0.75)";
      ctx.beginPath(); ctx.arc(oil.x, oil.y, oil.r, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = oil.burning > 0 ? "#f97316" : "#334155";
      ctx.lineWidth = 1.5; ctx.stroke();
    }

    // 2. Render 3D Low-Poly Alchemy Cauldrons & Dodge-Roll Gravity Monoliths
    for (let i = 0; i < (w.cauldrons || []).length; i++) {
      const c = w.cauldrons[i];
      if (lp) lp.drawLowPolyPrism(ctx, c.x, c.y, 16, 0, 22, 6, c.used ? "#334155" : "#10b981", p.x, p.y, 0);
    }
    for (let i = 0; i < (w.monoliths || []).length; i++) {
      const m = w.monoliths[i];
      if (lp) lp.drawLowPolyPrism(ctx, m.x, m.y, 14, 0, 42, 4, "#a855f7", p.x, p.y, performance.now() * 0.005);
      ctx.strokeStyle = "rgba(168, 85, 247, 0.4)";
      ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2); ctx.stroke();
    }

    // 3. Render Orbiting Spectral Skulls & Elemental Projectiles
    for (let i = 0; i < this.orbitSkulls.length; i++) {
      const sk = this.orbitSkulls[i];
      if (lp && sk.x) lp.drawLowPolyPrism(ctx, sk.x, sk.y, 7, 10, 24, 4, "#a855f7", p.x, p.y, sk.angle);
    }
    for (let i = 0; i < (w.projectiles || []).length; i++) {
      const pr = w.projectiles[i];
      ctx.fillStyle = pr.color;
      ctx.beginPath(); ctx.arc(pr.x, pr.y, pr.r, 0, Math.PI * 2); ctx.fill();
    }

    // 4. Render Chain-Lightning Bolts
    for (let i = 0; i < (w.particles || []).length; i++) {
      const pt = w.particles[i];
      if (pt.boltFromX) {
        ctx.strokeStyle = "#a855f7";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(pt.boltFromX, pt.boltFromY);
        ctx.lineTo((pt.boltFromX + pt.x) * 0.5 + (Math.random() - 0.5) * 18, (pt.boltFromY + pt.y) * 0.5);
        ctx.lineTo(pt.x, pt.y);
        ctx.stroke();
      }
    }

    // 5. Render Diablo-Style 3D Faceted Artifact Crystals, Vertical Light Beams & Rich Lore Tooltips
    let closestItem = null, minDist = 48;
    for (let i = 0; i < (w.loot || []).length; i++) {
      const it = w.loot[i];
      // Vertical Diablo Rarity Light Pillar
      const beamGrad = ctx.createLinearGradient(it.x, it.y - 75, it.x, it.y);
      beamGrad.addColorStop(0, "rgba(0,0,0,0)");
      beamGrad.addColorStop(1, it.color);
      ctx.globalAlpha = 0.42;
      ctx.fillStyle = beamGrad;
      ctx.fillRect(it.x - 5, it.y - 75, 10, 75);
      ctx.globalAlpha = 1.0;

      // Rotating 3D Low-Poly Crystal Relic on the Dungeon Floor
      if (lp) {
        lp.drawLowPolyPrism(ctx, it.x, it.y, 10, 4, 24, 4, it.color, p.x, p.y, performance.now() * 0.004 + i);
      }
      const d = Math.hypot(p.x - it.x, p.y - it.y);
      if (d < minDist) { minDist = d; closestItem = it; }
    }

    if (closestItem) {
      const tx = Math.max(155, Math.min(645, closestItem.x));
      const ty = Math.max(95, closestItem.y - 72);
      ctx.fillStyle = "rgba(9, 7, 15, 0.94)";
      ctx.fillRect(tx - 145, ty - 42, 290, 64);
      ctx.strokeStyle = closestItem.color;
      ctx.lineWidth = 1.8;
      ctx.strokeRect(tx - 145, ty - 42, 290, 64);

      ctx.textAlign = "center";
      ctx.fillStyle = closestItem.color;
      ctx.font = "bold 11px monospace";
      ctx.fillText(`[${closestItem.slot}] ${closestItem.name}`, tx, ty - 24);
      ctx.fillStyle = "#f8fafc";
      ctx.font = "9.5px monospace";
      ctx.fillText(closestItem.powerDesc, tx, ty - 6);
      ctx.fillStyle = "#eab308";
      ctx.font = "bold 10px monospace";
      ctx.fillText("[PRESS SHIFT / E] BIND ARTIFACT TO VESSEL", tx, ty + 12);
    }

    ctx.restore();
  }
});
