// Cohesive Milestone Plugin: v0.2.0 (Interactive OSR Character Customizer, 3d6 Stat Roller, Pacts & Resolve)
window.StudioEngine.registerModule("Milestone_v0_2_0", {
  init: function(state, engine) {
    this.classes = [
      {
        id: "PALADIN", name: "Doomblade Paladin", color: "#eab308",
        weapons: [
          { name: "Colossal Zweihänder", reach: 68, dmg: 28 },
          { name: "Sanctified War-Flail", reach: 56, dmg: 32 }
        ],
        rite: "Holy Aegis Nova",
        stats: { STR: 16, DEX: 11, CON: 15, ARC: 8 },
        // Winged Greathelm with Cross Visor
        bitmap: [0b100111,0b110111,0b011111,0b011111,0b011000,0b011110,0b011000,0b011011,0b011011,0b011111,0b001110,0b000100]
      },
      {
        id: "WARLOCK", name: "Acid Warlock", color: "#10b981",
        weapons: [
          { name: "Verdigris Hex-Cane", reach: 64, dmg: 24 },
          { name: "Dopethrone Censer", reach: 74, dmg: 21 }
        ],
        rite: "Caustic Rupture",
        stats: { STR: 8, DEX: 12, CON: 10, ARC: 17 },
        // Pointed Cultist Hood with Glowing Third Eye
        bitmap: [0b000011,0b000111,0b001111,0b011101,0b011000,0b111011,0b111111,0b011001,0b011111,0b001110,0b011100,0b110000]
      },
      {
        id: "RANGER", name: "Grave-Stalker", color: "#a855f7",
        weapons: [
          { name: "Dual Kris Blades", reach: 50, dmg: 25 },
          { name: "Graveyard Crossbow", reach: 82, dmg: 20 }
        ],
        rite: "Shadow Step Cleave",
        stats: { STR: 11, DEX: 17, CON: 12, ARC: 10 },
        // Wide-Brimmed Witch-Hunter Hat & Mask
        bitmap: [0b000111,0b001111,0b111111,0b111111,0b011001,0b011001,0b011111,0b001111,0b011110,0b011100,0b001000,0b000000]
      },
      {
        id: "FLAGELLANT", name: "Crypt Flagellant", color: "#dc2626",
        weapons: [
          { name: "Barbed Blood-Whip", reach: 72, dmg: 26 },
          { name: "Martyr's Iron Mace", reach: 54, dmg: 31 }
        ],
        rite: "Martyrdom Frenzy",
        stats: { STR: 14, DEX: 10, CON: 16, ARC: 11 },
        // Spiked Crown of Thorns & Iron Mask
        bitmap: [0b101010,0b011111,0b111111,0b011001,0b011001,0b011111,0b011011,0b011001,0b001111,0b001010,0b001010,0b000000]
      }
    ];

    this.pacts = [
      { name: "Electric Wizard Initiate", bonus: "+15% Arcane Reach & Torch Glow", gold: 30, torch: 100 },
      { name: "Catacomb Tomb-Robber", bonus: "+45 Starting Gold & Sprint Speed", gold: 70, torch: 90 },
      { name: "Exiled Iron Inquisitor", bonus: "+1 Max HP Vessel & Poise Damage", gold: 25, torch: 100, hpBonus: 1 },
      { name: "Black Chalice Penitent", bonus: "+25% Cleave Damage, Starts Stressed", gold: 35, torch: 85, dmgBonus: 6 }
    ];

    this.sheetOpen = true;
    this.selectedClass = 0;
    this.selectedStatIdx = 0; // 0:STR, 1:DEX, 2:CON, 3:ARC
    this.statKeys = ["STR", "DEX", "CON", "ARC"];
    this.bonusPoints = 3;
    this.pactIdx = 0;
    this.weaponIdx = 0;
    this.riteCooldown = 0;
    this.riteFx = [];

    state.paused = true;
    state.player.stress = 0;
    state.player.resolveState = "STEADY";

    engine.on("KEYDOWN", (ev) => {
      if (this.sheetOpen) {
        if (ev.code === "ArrowLeft" || ev.code === "KeyA") {
          this.selectedClass = (this.selectedClass + 3) % 4;
        } else if (ev.code === "ArrowRight" || ev.code === "KeyD") {
          this.selectedClass = (this.selectedClass + 1) % 4;
        } else if (ev.code === "ArrowUp" || ev.code === "KeyW") {
          this.selectedStatIdx = (this.selectedStatIdx + 3) % 4;
        } else if (ev.code === "ArrowDown" || ev.code === "KeyS") {
          this.selectedStatIdx = (this.selectedStatIdx + 1) % 4;
        } else if (ev.code === "KeyE" || ev.code === "Equal") {
          // Allocate bonus stat point
          const stKey = this.statKeys[this.selectedStatIdx];
          const cls = this.classes[this.selectedClass];
          if (this.bonusPoints > 0 && cls.stats[stKey] < 18) {
            cls.stats[stKey]++;
            this.bonusPoints--;
          }
        } else if (ev.code === "KeyQ" || ev.code === "Minus") {
          // Refund stat point
          const stKey = this.statKeys[this.selectedStatIdx];
          const cls = this.classes[this.selectedClass];
          if (cls.stats[stKey] > 6) {
            cls.stats[stKey]--;
            this.bonusPoints++;
          }
        } else if (ev.code === "KeyR") {
          // Roll 3d6 OSR Ability Scores!
          const cls = this.classes[this.selectedClass];
          const roll3d6 = () => (1 + Math.floor(Math.random() * 6)) + (1 + Math.floor(Math.random() * 6)) + (1 + Math.floor(Math.random() * 6));
          cls.stats.STR = Math.max(7, roll3d6());
          cls.stats.DEX = Math.max(7, roll3d6());
          cls.stats.CON = Math.max(8, roll3d6());
          cls.stats.ARC = Math.max(7, roll3d6());
          this.bonusPoints = 3;
        } else if (ev.code === "KeyT") {
          this.pactIdx = (this.pactIdx + 1) % this.pacts.length;
        } else if (ev.code === "KeyV") {
          this.weaponIdx = (this.weaponIdx + 1) % 2;
        } else if (ev.code === "Space" || ev.code === "Enter") {
          this.confirmCharacter(state);
        }
        return;
      }

      // Active Dungeon: [SHIFT / E] triggers Blood-Rite Special when ready
      if (!state.paused && (ev.code === "ShiftLeft" || ev.code === "ShiftRight" || ev.code === "KeyE")) {
        if (this.riteCooldown <= 0) {
          this.triggerBloodRite(state, engine);
        }
      }
    });
  },

  confirmCharacter: function(state) {
    const cls = this.classes[this.selectedClass];
    const pact = this.pacts[this.pactIdx];
    const wep = cls.weapons[this.weaponIdx];
    const p = state.player;

    this.sheetOpen = false;
    p.classColor = cls.color;
    p.characterClass = cls.name;
    p.pactName = pact.name;
    p.weaponName = wep.name;
    p.weaponReach = wep.reach + (cls.stats.ARC - 10) * 1.5;
    p.weaponDamage = wep.dmg + (cls.stats.STR - 10) * 1.4 + (pact.dmgBonus || 0);
    p.speed = 155 + (cls.stats.DEX - 10) * 4.5;
    p.maxHealth = 4 + Math.floor(cls.stats.CON / 5) + (pact.hpBonus || 0);
    p.health = p.maxHealth;
    p.shields = p.maxHealth;
    p.gold = pact.gold;
    p.torchLevel = pact.torch;
    state.stats.characterClass = cls.name;
    state.stats.attributes = { ...cls.stats };

    (state.world.floatingTexts || (state.world.floatingTexts = [])).push({
      text: `${cls.name.toUpperCase()} // ${wep.name.toUpperCase()}`,
      x: p.x, y: p.y - 28, color: cls.color, life: 2.2
    });
    state.paused = false;
    state.keys.jump = false;
  },

  triggerBloodRite: function(state, engine) {
    const cls = this.classes[this.selectedClass];
    const p = state.player, w = state.world;
    this.riteCooldown = 5.0;
    this.riteFx.push({ x: p.x, y: p.y, r: 12, maxR: 135, color: cls.color, life: 0.45, maxLife: 0.45 });

    if (cls.id === "PALADIN") {
      p.torchLevel = Math.min(100, (p.torchLevel || 50) + 25);
      p.stress = Math.max(0, (p.stress || 0) - 20);
    }
    const enemies = w.enemies || [];
    for (let i = 0; i < enemies.length; i++) {
      const en = enemies[i];
      if (Math.hypot(en.x - p.x, en.y - p.y) < 140) {
        en.hp -= 24;
        en.stagger = 0.9;
      }
    }
    w.floatingTexts.push({ text: `✦ RITE: ${cls.rite.toUpperCase()}! ✦`, x: p.x, y: p.y - 34, color: cls.color, life: 1.1 });
    engine.emit("BLOOD_RITE_CAST", { rite: cls.rite });
  },

  update: function(dt, state) {
    if (this.sheetOpen) {
      state.paused = true;
      return;
    }
    if (!state.running || state.paused || state.gameOver) return;

    const p = state.player, w = state.world;
    if (this.riteCooldown > 0) this.riteCooldown = Math.max(0, this.riteCooldown - dt);

    // Darkest Dungeon Stress & Resolve test in low torchlight
    if ((p.torchLevel || 100) < 45) {
      p.stress = Math.min(100, (p.stress || 0) + dt * 3.2);
      if (p.stress >= 100) {
        p.stress = 35;
        const virtuous = Math.random() > 0.35;
        p.resolveState = virtuous ? "DOOM TRANSCENDENCE" : "ABYSSAL FRENZY";
        if (virtuous) {
          p.health = Math.min(p.maxHealth, p.health + 2);
          p.torchLevel = 90;
        }
        w.floatingTexts.push({
          text: `RESOLVE TEST: ${p.resolveState}!`,
          x: p.x, y: p.y - 40, color: virtuous ? "#eab308" : "#dc2626", life: 2.0
        });
      }
    }

    for (let i = this.riteFx.length - 1; i >= 0; i--) {
      const fx = this.riteFx[i];
      fx.life -= dt;
      fx.r += (fx.maxR - fx.r) * 7.0 * dt;
      if (fx.life <= 0) this.riteFx.splice(i, 1);
    }
  },

  render: function(ctx, state) {
    // 1. Render Interactive OSR Character Creation & Customization Sheet
    if (this.sheetOpen) {
      ctx.save();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.fillStyle = "rgba(7, 5, 11, 0.96)";
      ctx.fillRect(0, 36, 800, 564);

      ctx.strokeStyle = "#b45309";
      ctx.lineWidth = 2;
      ctx.strokeRect(48, 48, 704, 532);

      ctx.textAlign = "center";
      ctx.fillStyle = "#f59e0b";
      ctx.font = "bold 19px monospace";
      ctx.fillText("--- OSR DELVER COVENANT & CHARACTER CUSTOMIZATION ---", 400, 76);

      ctx.fillStyle = "#cbd5e1";
      ctx.font = "11px monospace";
      ctx.fillText("[A/D] Class | [R] Roll 3d6 Stats | [W/S + Q/E] Spend Stat Pts | [T] Pact | [V] Weapon | [SPACE] Delve", 400, 96);

      for (let i = 0; i < 4; i++) {
        const cls = this.classes[i];
        const sel = (i === this.selectedClass);
        const cx = 68 + i * 168;
        const cy = 112;
        const cw = 156, ch = 352;
        const wep = cls.weapons[sel ? this.weaponIdx : 0];

        ctx.fillStyle = sel ? "#1c1512" : "#0e0c14";
        ctx.fillRect(cx, cy, cw, ch);
        ctx.strokeStyle = sel ? cls.color : "#334155";
        ctx.lineWidth = sel ? 2.5 : 1;
        ctx.strokeRect(cx, cy, cw, ch);

        // Unique Symmetric 12x12 Class Helmet/Hood Portrait
        const px = 5;
        const sx = cx + (cw - 12 * px) / 2;
        const sy = cy + 16;
        for (let r = 0; r < 12; r++) {
          const bits = cls.bitmap[r];
          for (let c = 0; c < 12; c++) {
            const bitIdx = c < 6 ? (5 - c) : (c - 6);
            if ((bits >> bitIdx) & 1) {
              const isEye = (r === 4 && (c === 4 || c === 7));
              ctx.fillStyle = isEye ? "#ffffff" : cls.color;
              ctx.fillRect(sx + c * px, sy + r * px, px - 1, px - 1);
            }
          }
        }

        ctx.textAlign = "center";
        ctx.fillStyle = sel ? cls.color : "#e2e8f0";
        ctx.font = "bold 13px monospace";
        ctx.fillText(cls.name, cx + cw / 2, cy + 98);

        ctx.fillStyle = "#94a3b8";
        ctx.font = "10px monospace";
        ctx.fillText((sel ? "⚔ " : "") + wep.name, cx + cw / 2, cy + 115);

        // 3d6 Ability Score Bars (Interactive on Selected Card)
        const sNames = ["STR", "DEX", "CON", "ARC"];
        ctx.textAlign = "left";
        for (let s = 0; s < 4; s++) {
          const k = sNames[s];
          const val = cls.stats[k];
          const by = cy + 142 + s * 36;
          const activeStat = sel && (s === this.selectedStatIdx);
          ctx.fillStyle = activeStat ? "#facc15" : "#cbd5e1";
          ctx.font = activeStat ? "bold 11px monospace" : "11px monospace";
          ctx.fillText(`${activeStat ? ">" : " "}${k} ${val}`, cx + 12, by);
          ctx.fillStyle = "#1e293b";
          ctx.fillRect(cx + 14, by + 6, 128, 8);
          ctx.fillStyle = cls.color;
          ctx.fillRect(cx + 14, by + 6, Math.min(128, (val / 18) * 128), 8);
        }

        ctx.fillStyle = "#f59e0b";
        ctx.font = "10px monospace";
        ctx.textAlign = "center";
        ctx.fillText(`RITE: ${cls.rite}`, cx + cw / 2, cy + 312);
        if (sel) {
          ctx.fillStyle = "#38bdf8";
          ctx.fillText(`UNSPENT STAT PTS: ${this.bonusPoints}`, cx + cw / 2, cy + 334);
        }
      }

      // Bottom OSR Customization Bar (Pact & Weapon Loadout Preview)
      const activePact = this.pacts[this.pactIdx];
      const activeCls = this.classes[this.selectedClass];
      const activeWep = activeCls.weapons[this.weaponIdx];

      ctx.fillStyle = "#14101c";
      ctx.fillRect(68, 476, 660, 88);
      ctx.strokeStyle = activeCls.color;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(68, 476, 660, 88);

      ctx.textAlign = "left";
      ctx.fillStyle = "#eab308";
      ctx.font = "bold 12px monospace";
      ctx.fillText(`[T] BACKGROUND PACT: ${activePact.name} (${activePact.bonus})`, 84, 500);
      ctx.fillStyle = "#10b981";
      ctx.fillText(`[V] STARTING ARMAMENT: ${activeWep.name} (DMG: ${activeWep.dmg} | REACH: ${activeWep.reach})`, 84, 522);
      ctx.fillStyle = "#f8fafc";
      ctx.fillText(`[R] RE-ROLL 3d6 DICE   |   [W/S + Q/E] ADJUST STATS   |   [SPACE / ENTER] DESCEND INTO CRYPT`, 84, 546);

      ctx.restore();
      return;
    }

    // 2. Render Active Gameplay Blood-Rite Shockwaves
    ctx.save();
    for (let i = 0; i < this.riteFx.length; i++) {
      const fx = this.riteFx[i];
      ctx.globalAlpha = Math.max(0, fx.life / fx.maxLife);
      ctx.strokeStyle = fx.color;
      ctx.lineWidth = 3.5;
      ctx.beginPath();
      ctx.arc(fx.x, fx.y, fx.r, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }
});
