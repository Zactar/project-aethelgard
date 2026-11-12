// Cohesive Milestone Plugin: v0.4.0 (Dynamic OSR Quests, Faction Altars, Monster Ecology & UI/UX Polish)
window.StudioEngine.registerModule("Milestone_v0_4_0", {
  init: function(state, engine) {
    const w = state.world;
    w.quest = {
      title: "Purge 3 Crypt Horrors",
      progress: 0,
      target: 3,
      alignment: "UNSWORN",
      completed: false
    };
    this.roomPopulated = "";
    this.seepCooldown = 0;

    engine.on("ENEMY_SLAIN", () => {
      if (w.quest && !w.quest.completed) {
        w.quest.progress++;
        if (w.quest.progress >= w.quest.target) {
          w.quest.completed = true;
          state.player.gold = (state.player.gold || 0) + 100;
          state.player.maxHealth = (state.player.maxHealth || 5) + 1;
          state.player.health = state.player.maxHealth;
          w.floatingTexts.push({
            text: "★ QUEST FULFILLED! +1 MAX HP VESSEL & +100G ★",
            x: state.player.x, y: state.player.y - 38, color: "#eab308", life: 2.4
          });
        }
      }
    });

    // Interact with Blood-Altar or Fallen Delver Corpse on [SHIFT / E]
    engine.on("KEYDOWN", (ev) => {
      if (state.paused) return;
      if (ev.code === "ShiftLeft" || ev.code === "ShiftRight" || ev.code === "KeyE") {
        this.tryAltarOrLoreInteraction(state);
      }
    });
  },

  populateRoomEcology: function(state) {
    const w = state.world, p = state.player;
    const key = `${w.currentRoom.x},${w.currentRoom.y}`;
    if (this.roomPopulated === key) return;
    this.roomPopulated = key;

    const role = w.roomRole || "ENTRY_HALL";
    // Only spawn the Blood-Altar in ALTAR_SANCTUM rooms, and the Lore Corpse in OSSUARY_PASSAGE rooms!
    w.altar = (role === "ALTAR_SANCTUM")
      ? { x: 400, y: 255, r: 22, state: w.quest.alignment, used: false }
      : null;
    w.corpse = (role === "OSSUARY_PASSAGE")
      ? { x: 310, y: 360, looted: false, inscription: "RUNIC ETCHING: 'Strike Phalanx shields from the flank, or parry their lunge.'" }
      : null;
    w.ichorPools = (role === "ALTAR_SANCTUM" && w.quest.alignment === "DEFILED")
      ? [{ x: 280, y: 340, r: 24 }]
      : [];

    // 3. Upgrade Room Enemies into Distinct Monster Ecology (Phalanx, Necromancer, Fungoid Horror)
    const enemies = w.enemies || [];
    const types = ["PHALANX_SKELETON", "CRYPT_NECROMANCER", "FUNGOID_HORROR"];
    for (let i = 0; i < enemies.length; i++) {
      const en = enemies[i];
      en.type = types[i % types.length];
      en.facing = Math.atan2(p.y - en.y, p.x - en.x);
      en.castTimer = 2.0 + i * 0.8;
    }
  },

  tryAltarOrLoreInteraction: function(state) {
    const p = state.player, w = state.world;
    if (w.altar && !w.altar.used && Math.hypot(p.x - w.altar.x, p.y - w.altar.y) < 54) {
      w.altar.used = true;
      if ((p.stress || 0) < 40) {
        w.quest.alignment = "CONSECRATED";
        p.health = p.maxHealth;
        p.torchLevel = 100;
        w.floatingTexts.push({ text: "☀ ALTAR CONSECRATED: FULL HP & SOLAR BLESSING", x: w.altar.x, y: w.altar.y - 28, color: "#eab308", life: 1.8 });
      } else {
        w.quest.alignment = "DEFILED";
        p.weaponDamage = (p.weaponDamage || 24) + 10;
        w.floatingTexts.push({ text: "🩸 ALTAR DEFILED: +10 DOOM DAMAGE", x: w.altar.x, y: w.altar.y - 28, color: "#dc2626", life: 1.8 });
      }
    }
    if (w.corpse && !w.corpse.looted && Math.hypot(p.x - w.corpse.x, p.y - w.corpse.y) < 48) {
      w.corpse.looted = true;
      p.gold = (p.gold || 0) + 35;
      p.torchLevel = Math.min(100, (p.torchLevel || 60) + 30);
      w.floatingTexts.push({ text: "LOOTED FALLEN DELVER: +35G & TORCH OIL", x: w.corpse.x, y: w.corpse.y - 24, color: "#38bdf8", life: 1.6 });
    }
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.gameOver) return;
    const p = state.player, w = state.world;
    this.populateRoomEcology(state);

    if (this.seepCooldown > 0) this.seepCooldown -= dt;

    // Subtle Ichor Fissure Hazard (Throttled to 1.2s cooldown so text NEVER stacks!)
    for (let i = 0; i < (w.ichorPools || []).length; i++) {
      const pool = w.ichorPools[i];
      if (Math.hypot(p.x - pool.x, p.y - pool.y) < pool.r && p.dashTimer <= 0 && this.seepCooldown <= 0) {
        this.seepCooldown = 1.25;
        p.stress = Math.min(100, (p.stress || 0) + 6);
        w.floatingTexts.push({ text: "+6% STRESS (ICHOR)", x: p.x, y: p.y - 22, color: "#a855f7", life: 0.85 });
      }
    }

    // Update Monster Ecology Behaviors
    const enemies = w.enemies || [];
    for (let i = 0; i < enemies.length; i++) {
      const en = enemies[i];
      const targetAng = Math.atan2(p.y - en.y, p.x - en.x);
      en.facing = targetAng;
      en.castTimer = (en.castTimer || 2.5) - dt;

      if (en.type === "CRYPT_NECROMANCER" && en.castTimer <= 0) {
        en.castTimer = 3.4;
        // Fire a slow, readable purple hex-orb
        (w.projectiles || (w.projectiles = [])).push({
          x: en.x, y: en.y,
          vx: Math.cos(targetAng) * 145, vy: Math.sin(targetAng) * 145,
          r: 6, dmg: 1, color: "#a855f7", life: 1.8, enemyShot: true
        });
      }
    }
  },

  render: function(ctx, state) {
    if (state.paused || state.gameOver) return;
    const p = state.player, w = state.world, lp = w.lowPoly;
    const t = performance.now() * 0.001;

    ctx.save();

    // 1. Render Compact Dark-Crimson Ichor Fissures on the Stone Floor
    for (let i = 0; i < (w.ichorPools || []).length; i++) {
      const pool = w.ichorPools[i];
      const ig = ctx.createRadialGradient(pool.x, pool.y, 4, pool.x, pool.y, pool.r);
      ig.addColorStop(0, "rgba(153, 27, 27, 0.55)");
      ig.addColorStop(0.7, "rgba(69, 10, 10, 0.30)");
      ig.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = ig;
      ctx.beginPath(); ctx.arc(pool.x, pool.y, pool.r, 0, Math.PI * 2); ctx.fill();
    }

    // 2. Render 2.5D Low-Poly Faction Blood-Altar Monolith
    if (w.altar && lp) {
      const aCol = w.quest.alignment === "CONSECRATED" ? "#eab308" : (w.quest.alignment === "DEFILED" ? "#dc2626" : "#a855f7");
      lp.drawLowPolyPrism(ctx, w.altar.x, w.altar.y, 20, 0, 18, 6, "#1e293b", p.x, p.y, 0);
      lp.drawLowPolyPrism(ctx, w.altar.x, w.altar.y, 11, 16, 46 + Math.sin(t * 3) * 4, 4, aCol, p.x, p.y, t * 1.2);
    }

    // 3. Render Fallen OSR Delver Skeleton & Etched Floor Runes (Only shows whisper tooltip when player is close!)
    if (w.corpse) {
      ctx.fillStyle = w.corpse.looted ? "#475569" : "#cbd5e1";
      ctx.fillRect(w.corpse.x - 8, w.corpse.y - 4, 16, 8);
      ctx.fillStyle = "#eab308";
      ctx.fillRect(w.corpse.x + 6, w.corpse.y - 6, 4, 10);

      if (Math.hypot(p.x - w.corpse.x, p.y - w.corpse.y) < 68) {
        ctx.fillStyle = "rgba(9, 7, 15, 0.92)";
        ctx.fillRect(w.corpse.x - 175, w.corpse.y - 44, 350, 28);
        ctx.strokeStyle = "#f59e0b";
        ctx.lineWidth = 1;
        ctx.strokeRect(w.corpse.x - 175, w.corpse.y - 44, 350, 28);
        ctx.fillStyle = "#fde68a";
        ctx.font = "10px monospace";
        ctx.textAlign = "center";
        ctx.fillText(w.corpse.inscription, w.corpse.x, w.corpse.y - 26);
      }
    }

    ctx.restore();

    // 4. UI/UX Z-Topmost Whisper Ribbon (No rectangular HUD boxes! Renders clean 1-line Quest Tracker at y=48)
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (w.quest) {
      ctx.textAlign = "left";
      ctx.font = "bold 11px monospace";
      ctx.fillStyle = w.quest.completed ? "#10b981" : "#eab308";
      const qStatus = w.quest.completed ? "COMPLETED" : `[${w.quest.progress}/${w.quest.target}]`;
      ctx.fillText(`⚔ OSR QUEST: ${w.quest.title} ${qStatus}  |  PACT: ${w.quest.alignment}`, 14, 52);
    }
    ctx.restore();
  }
});
