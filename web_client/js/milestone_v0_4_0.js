// Cohesive Milestone Plugin: v0.4.0
// Cohesive Milestone Plugin: v0.4.0 (OSR Monster Ecology, Dungeon Alignments & Dynamic Quests)
window.StudioEngine.registerModule("Milestone_v0_4_0", {
  init: function(state, engine) {
    const w = state.world;
    w.monsters = w.monsters || [];
    w.loreNodes = w.loreNodes || [];
    w.altars = w.altars || [];
    w.hazards = w.hazards || [];
    w.textParticles = w.textParticles || [];
    w.alignment = w.alignment || "NEUTRAL";
    this.spawnedRoomKey = "";
    this.actCooldown = 0;

    // Procedural OSR Quest Engine initialization
    const QUEST_POOL = [
      { id: "SHATTER_MONOLITHS", title: "Shatter 3 Cursed Blood-Monoliths", type: "MONOLITH", targetCount: 3 },
      { id: "PURGE_FUNGAL_SUMP", title: "Purge 4 Acid Fungoid Horrors", type: "FUNGUS", targetCount: 4 },
      { id: "EXECUTE_NECROMANCERS", title: "Slay 2 Crypt Necromancers", type: "NECRO", targetCount: 2 }
    ];
    if (!w.quest) {
      const q = QUEST_POOL[Math.floor(Math.random() * QUEST_POOL.length)];
      w.quest = { id: q.id, title: q.title, type: q.type, targetCount: q.targetCount, currentCount: 0, completed: false };
    }

    // Engine Event listener for quest updates
    engine.on("ENEMY_KILLED", (payload, st) => {
      if (!st.world.quest || st.world.quest.completed) return;
      const q = st.world.quest;
      if (q.type === payload.type) {
        q.currentCount++;
        (st.world.floatingTexts || (st.world.floatingTexts = [])).push({ text: `📜 ${q.title} (${q.currentCount}/${q.targetCount})`, x: payload.x, y: payload.y - 20, color: "#eab308", life: 1.4 });
        if (q.currentCount >= q.targetCount) {
          q.completed = true;
          st.player.gold = (st.player.gold || 0) + 120;
          st.world.cameraShake = 16;
          engine.emit("QUEST_OBJECTIVE_COMPLETED", q);
        }
      }
    });
  },

  seedRoomEcology: function(state) {
    const w = state.world;
    const p = state.player;
    const rKey = `${w.currentRoom.x},${w.currentRoom.y}_v04`;
    if (this.spawnedRoomKey === rKey) return;
    this.spawnedRoomKey = rKey;

    w.monsters = [];
    w.loreNodes = [];
    w.altars = [];
    w.hazards = [];

    // Apply alignment mutation: Defiled rooms flood with toxic Crimson Ichor
    if (w.alignment === "DEFILED") {
      for (let i = 0; i < 4; i++) {
        (w.hazards || (w.hazards = [])).push({
          x: 200 + (i % 2) * 380 + (Math.random() * 40 - 20),
          y: 180 + Math.floor(i / 2) * 200 + (Math.random() * 40 - 20),
          r: 65, type: "ICHOR", color: "rgba(185, 28, 28, 0.45)"
        });
      }
    }

    // Interactive Altar of Transmutation
    (w.altars || (w.altars = [])).push({
      x: 400, y: 190, r: 24,
      consecrated: w.alignment === "CONSECRATED",
      defiled: w.alignment === "DEFILED"
    });

    // Inscribed Lore Slabs and Corpse Stories
    const loreQuotes = [
      "Here fell Brother Osric; his shield shattered under phalanx iron.",
      "Beware the chests that wheeze; their teeth hunger for marrow.",
      "The violet flame whispers of doom, yet repels the creeping dark.",
      "Altar of the Old Gods: defile for ruinous power, or consecrate for gold."
    ];
    (w.loreNodes || (w.loreNodes = [])).push({
      x: 260 + Math.random() * 80, y: 440,
      type: "CORPSE",
      text: loreQuotes[Math.floor(Math.random() * loreQuotes.length)]
    });
    (w.loreNodes || (w.loreNodes = [])).push({
      x: 520 + Math.random() * 80, y: 440,
      type: "RUNE_SLAB",
      text: "RUNIC CARVING: 'Only a flank stroke pierces the Phalanx guard.'"
    });

    // Distinct Monster Ecology Archetypes
    // 1. Phalanx Shield Skeleton (120-deg frontal shield blocks frontal attacks)
    (w.monsters || (w.monsters = [])).push({
      id: "phalanx_1", type: "PHALANX", x: 300, y: 260, hp: 45, maxHp: 45, angle: 0,
      speed: 55, poise: 40, shieldArc: 2.1, color: "#94a3b8", r: 16
    });

    // 2. Fungoid Horror (Kites 130-180px, fires acid blobs leaving caustic pools)
    (w.monsters || (w.monsters = [])).push({
      id: "fungus_1", type: "FUNGUS", x: 560, y: 240, hp: 35, maxHp: 35, angle: 0,
      speed: 65, spitTimer: 1.8, color: "#10b981", r: 18
    });

    // 3. Teleporting Necromancer (Channels revive on bone piles, flees when approached)
    (w.monsters || (w.monsters = [])).push({
      id: "necro_1", type: "NECRO", x: 420, y: 390, hp: 40, maxHp: 40, angle: 0,
      speed: 40, channelTimer: 0, tpTimer: 4.5, color: "#a855f7", r: 16
    });

    // 4. Mimic Chest (Lies dormant until attacked or opened with [E]/[SHIFT])
    (w.monsters || (w.monsters = [])).push({
      id: "mimic_1", type: "MIMIC", x: 230, y: 200, hp: 55, maxHp: 55, angle: Math.PI / 2,
      speed: 130, awakened: false, biteCooldown: 0, color: "#b45309", r: 16
    });

    // Elite Void Cultists if room is Defiled
    if (w.alignment === "DEFILED") {
      (w.monsters || (w.monsters = [])).push({
        id: "cultist_1", type: "CULTIST", x: 400, y: 460, hp: 60, maxHp: 60, angle: 0,
        speed: 85, color: "#dc2626", r: 17
      });
    }
  },

  update: function(dt, state, engine) {
    if (state.paused || state.gameOver) return;
    this.seedRoomEcology(state);

    const p = state.player;
    const w = state.world;
    if (this.actCooldown > 0) this.actCooldown -= dt;

    // Environmental Hazards (Ichor slow & damage)
    for (let i = w.hazards.length - 1; i >= 0; i--) {
      const hz = w.hazards[i];
      if (Math.hypot(p.x - hz.x, p.y - hz.y) < hz.r) {
        p.vx *= 0.65; p.vy *= 0.65;
        if (Math.random() < dt * 4) {
          p.health = Math.max(0, p.health - 1);
          w.cameraShake = 4;
          (w.floatingTexts || (w.floatingTexts = [])).push({ text: "ICHOR SEEP -1", x: p.x, y: p.y - 18, color: "#dc2626", life: 0.5 });
        }
      }
      if (hz.ttl) {
        hz.ttl -= dt;
        if (hz.ttl <= 0) w.hazards.splice(i, 1);
      }
    }

    // Lore Node & Altar Interactions [SHIFT/E / state.keys.action]
    if (state.keys.action && this.actCooldown <= 0) {
      for (const node of w.loreNodes) {
        if (Math.hypot(p.x - node.x, p.y - node.y) <= 38) {
          this.actCooldown = 0.5;
          (w.textParticles || (w.textParticles = [])).push({ x: node.x, y: node.y - 32, text: node.text, ttl: 4.0, color: "#f59e0b" });
          (w.floatingTexts || (w.floatingTexts = [])).push({ text: "📖 EXAMINED", x: node.x, y: node.y - 15, color: "#f59e0b", life: 0.9 });
          break;
        }
      }

      for (const altar of w.altars) {
        if (Math.hypot(p.x - altar.x, p.y - altar.y) <= 44) {
          this.actCooldown = 0.6;
          if (w.alignment === "NEUTRAL") {
            w.alignment = "CONSECRATED";
            altar.consecrated = true;
            p.torchLevel = 100;
            w.hazards = [];
            (w.floatingTexts || (w.floatingTexts = [])).push({ text: "✨ ALTAR CONSECRATED: VAULTS OPEN!", x: altar.x, y: altar.y - 28, color: "#eab308", life: 2.0 });
          } else if (w.alignment === "CONSECRATED") {
            w.alignment = "DEFILED";
            altar.consecrated = false;
            altar.defiled = true;
            w.cameraShake = 22;
            p.gold = (p.gold || 0) + 150;
            (w.floatingTexts || (w.floatingTexts = [])).push({ text: "🩸 BLOOD DEFILEMENT: +150G & ICHOR FLOOD", x: altar.x, y: altar.y - 28, color: "#dc2626", life: 2.2 });
          }
          break;
        }
      }
    }

    // Monsters Behavioral AI & Ecology Loop
    for (let i = w.monsters.length - 1; i >= 0; i--) {
      const m = w.monsters[i];
      const dx = p.x - m.x;
      const dy = p.y - m.y;
      const dist = Math.hypot(dx, dy) || 1;
      m.angle = Math.atan2(dy, dx);

      // Phalanx Skeleton: Advances cautiously with shield up
      if (m.type === "PHALANX") {
        if (dist > 34) {
          m.x += (dx / dist) * m.speed * dt;
          m.y += (dy / dist) * m.speed * dt;
        } else if (p.invuln <= 0) {
          p.health = Math.max(0, p.health - 1);
          p.invuln = 0.6;
          w.cameraShake = 8;
        }
      }

      // Fungoid Horror: Stays at 140px range & spits caustic globs
      else if (m.type === "FUNGUS") {
        if (dist < 120) {
          m.x -= (dx / dist) * m.speed * dt;
          m.y -= (dy / dist) * m.speed * dt;
        } else if (dist > 180) {
          m.x += (dx / dist) * m.speed * dt;
          m.y += (dy / dist) * m.speed * dt;
        }
        m.spitTimer -= dt;
        if (m.spitTimer <= 0) {
          m.spitTimer = 2.4;
          w.projectiles = w.projectiles || [];
          (w.projectiles || (w.projectiles = [])).push({
            x: m.x, y: m.y, vx: (dx / dist) * 190, vy: (dy / dist) * 190,
            r: 7, dmg: 1, color: "#10b981", life: 1.5, spawnAcid: true
          });
        }
      }

      // Crypt Necromancer: Resurrects bone piles into phalanx minions
      else if (m.type === "NECRO") {
        m.tpTimer -= dt;
        if (m.tpTimer <= 0 || dist < 65) {
          m.tpTimer = 5.0;
          m.x = 220 + Math.random() * 360;
          m.y = 190 + Math.random() * 240;
          (w.particles || (w.particles = [])).push({ x: m.x, y: m.y, vx: 0, vy: -30, color: "#a855f7", life: 0.6 });
        }
        m.channelTimer += dt;
        if (m.channelTimer >= 3.5 && (w.bonePiles || []).length > 0) {
          m.channelTimer = 0;
          const bp = w.bonePiles.pop();
          (w.monsters || (w.monsters = [])).push({
            id: `revived_${Date.now()}`, type: "PHALANX", x: bp.x, y: bp.y,
            hp: 25, maxHp: 25, angle: 0, speed: 60, poise: 20, shieldArc: 2.1, color: "#cbd5e1", r: 15
          });
          (w.floatingTexts || (w.floatingTexts = [])).push({ text: "💀 SKELETON REANIMATED", x: bp.x, y: bp.y - 18, color: "#a855f7", life: 1.0 });
        }
      }

      // Mimic Chest: Dormant until attacked or approached
      else if (m.type === "MIMIC") {
        if (!m.awakened) {
          if (dist <= 36 && state.keys.action) {
            m.awakened = true;
            p.health = Math.max(0, p.health - 2);
            p.invuln = 0.8;
            w.cameraShake = 18;
            (w.floatingTexts || (w.floatingTexts = [])).push({ text: "⚠️ MIMIC BITE AMBUSH!", x: p.x, y: p.y - 25, color: "#dc2626", life: 1.4 });
          }
        } else {
          m.x += (dx / dist) * m.speed * dt;
          m.y += (dy / dist) * m.speed * dt;
          if (dist < 30 && p.invuln <= 0) {
            p.health = Math.max(0, p.health - 1);
            p.invuln = 0.6;
            w.cameraShake = 10;
          }
        }
      }

      // Cultist berserk rush
      else if (m.type === "CULTIST") {
        m.x += (dx / dist) * m.speed * dt;
        m.y += (dy / dist) * m.speed * dt;
        if (dist < 26 && p.invuln <= 0) {
          p.health = Math.max(0, p.health - 1);
          p.invuln = 0.6;
        }
      }

      // Melee Cleave Interaction with Monsters
      if (p.attackTimer > 0) {
        const weaponReach = p.weaponReach || 56;
        if (dist <= weaponReach) {
          const attackAngle = p.facingAngle || 0;
          const angleToMonster = Math.atan2(m.y - p.y, m.x - p.x);
          let diff = Math.abs(attackAngle - angleToMonster);
          if (diff > Math.PI) diff = 2 * Math.PI - diff;

          if (diff < 1.1) {
            let absorbed = false;
            // Phalanx Shield-Wall Mechanics: Frontal attacks are deflected!
            if (m.type === "PHALANX") {
              const facingDiff = Math.abs(m.angle - (angleToMonster + Math.PI));
              if (facingDiff < m.shieldArc * 0.5) {
                absorbed = true;
                w.cameraShake = 5;
                (w.floatingTexts || (w.floatingTexts = [])).push({ text: "🛡️ DEFLECTED! (FLANK TO HIT)", x: m.x, y: m.y - 20, color: "#94a3b8", life: 0.6 });
              }
            }

            if (!absorbed) {
              const dmg = (p.weaponDamage || 18) * dt * 2.8;
              m.hp -= dmg;
              if (m.type === "MIMIC") m.awakened = true;
            }
          }
        }
      }

      // Monster Death & Loot/Quest check
      if (m.hp <= 0) {
        engine.emit("ENEMY_KILLED", { type: m.type, x: m.x, y: m.y });
        (w.particles || (w.particles = [])).push({ x: m.x, y: m.y, vx: 0, vy: -20, color: m.color, life: 0.5 });
        w.bonePiles = w.bonePiles || [];
        (w.bonePiles || (w.bonePiles = [])).push({ x: m.x, y: m.y });
        w.monsters.splice(i, 1);
      }
    }

    // Text Particle TTL decay
    for (let i = w.textParticles.length - 1; i >= 0; i--) {
      w.textParticles[i].ttl -= dt;
      if (w.textParticles[i].ttl <= 0) w.textParticles.splice(i, 1);
    }
  },

  render: function(ctx, state, engine) {
    if (state.paused || state.gameOver) return;
    const w = state.world;
    const p = state.player;

    // Apply Camera Shake in World Space Only
    ctx.save();
    if (w.cameraShake > 0) {
      const shakeAmt = w.cameraShake;
      ctx.translate((Math.random() - 0.5) * shakeAmt, (Math.random() - 0.5) * shakeAmt);
    }

    // 1. Draw Environmental Hazards (Ichor Pools)
    for (const hz of w.hazards) {
      ctx.beginPath();
      ctx.arc(hz.x, hz.y, hz.r, 0, Math.PI * 2);
      ctx.fillStyle = hz.color;
      ctx.fill();
      ctx.strokeStyle = "#991b1b";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // 2. Draw Lore Slabs & Corpses
    for (const node of w.loreNodes) {
      if (node.type === "CORPSE") {
        ctx.fillStyle = "#64748b";
        ctx.fillRect(node.x - 12, node.y - 6, 24, 12);
        ctx.fillStyle = "#cbd5e1";
        ctx.beginPath();
        ctx.arc(node.x - 12, node.y, 5, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillStyle = "#1e293b";
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 1.5;
        ctx.fillRect(node.x - 10, node.y - 14, 20, 28);
        ctx.strokeRect(node.x - 10, node.y - 14, 20, 28);
      }
      if (Math.hypot(p.x - node.x, p.y - node.y) <= 38) {
        ctx.fillStyle = "#f59e0b";
        ctx.font = "bold 10px monospace";
        ctx.fillText("[E] EXAMINE", node.x - 24, node.y - 20);
      }
    }

    // 3. Draw Monoliths / Altars (Low-Poly Prism & Facets)
    for (const a of w.altars) {
      if (w.lowPoly && w.lowPoly.drawExtrudedBox) {
        const c = a.consecrated ? "#eab308" : (a.defiled ? "#dc2626" : "#475569");
        w.lowPoly.drawExtrudedBox(ctx, a.x - 16, a.y - 16, 32, 32, 28, c, "#0f172a", p.x, p.y);
      } else {
        ctx.fillStyle = a.consecrated ? "#eab308" : (a.defiled ? "#dc2626" : "#475569");
        ctx.fillRect(a.x - 16, a.y - 16, 32, 32);
      }
      if (Math.hypot(p.x - a.x, p.y - a.y) <= 44) {
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px monospace";
        ctx.fillText("[E] TRANSMUTE ALTAR", a.x - 50, a.y - 28);
      }
    }

    // 4. Draw Ecology Monsters
    for (const m of w.monsters) {
      ctx.save();
      ctx.translate(m.x, m.y);
      ctx.rotate(m.angle);

      if (m.type === "PHALANX") {
        ctx.fillStyle = m.color;
        ctx.fillRect(-m.r, -m.r, m.r * 2, m.r * 2);
        // Heavy Frontal Tower Shield Arc
        ctx.beginPath();
        ctx.arc(0, 0, m.r + 5, -1.0, 1.0);
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 4;
        ctx.stroke();
      } else if (m.type === "FUNGUS") {
        ctx.fillStyle = m.color;
        ctx.beginPath();
        ctx.arc(0, 0, m.r, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#065f46";
        ctx.beginPath();
        ctx.arc(m.r * 0.4, 0, 5, 0, Math.PI * 2);
        ctx.fill();
      } else if (m.type === "NECRO") {
        ctx.fillStyle = m.color;
        ctx.fillRect(-10, -14, 20, 28);
        ctx.strokeStyle = "#c084fc";
        ctx.strokeRect(-10, -14, 20, 28);
      } else if (m.type === "MIMIC") {
        if (!m.awakened) {
          ctx.fillStyle = "#78350f";
          ctx.fillRect(-14, -10, 28, 20);
          ctx.fillStyle = "#facc15";
          ctx.fillRect(-3, -2, 6, 6);
        } else {
          ctx.fillStyle = "#dc2626";
          ctx.fillRect(-14, -10, 28, 20);
          ctx.fillStyle = "#ffffff";
          for (let tx = -12; tx < 12; tx += 6) {
            ctx.fillRect(tx, -8, 3, 5);
            ctx.fillRect(tx, 3, 3, 5);
          }
        }
      } else {
        ctx.fillStyle = m.color;
        ctx.beginPath();
        ctx.arc(0, 0, m.r, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();

      // Health bar above active monsters
      if (m.hp < m.maxHp) {
        ctx.fillStyle = "#1e293b";
        ctx.fillRect(m.x - 16, m.y - m.r - 8, 32, 4);
        ctx.fillStyle = "#dc2626";
        ctx.fillRect(m.x - 16, m.y - m.r - 8, Math.max(0, (m.hp / m.maxHp) * 32), 4);
      }
    }

    // 5. In-World Diegetic Lore Inscriptions
    for (const tp of w.textParticles) {
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.fillRect(tp.x - 140, tp.y - 12, 280, 24);
      ctx.strokeStyle = tp.color;
      ctx.lineWidth = 1;
      ctx.strokeRect(tp.x - 140, tp.y - 12, 280, 24);
      ctx.fillStyle = tp.color;
      ctx.font = "bold 10px monospace";
      ctx.textAlign = "center";
      ctx.fillText(tp.text, tp.x, tp.y + 4);
      ctx.textAlign = "left";
    }

    ctx.restore();

    // 6. Diegetic HUD: Reserved Top-Right Dock (x: 580..788, y: 46..106)
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.textAlign = "left";
    const q = w.quest;
    ctx.fillStyle = "rgba(10, 10, 15, 0.82)";
    ctx.fillRect(580, 46, 208, 56);
    ctx.strokeStyle = w.alignment === "CONSECRATED" ? "#eab308" : (w.alignment === "DEFILED" ? "#dc2626" : "#475569");
    ctx.lineWidth = 1.5;
    ctx.strokeRect(580, 46, 208, 56);

    ctx.fillStyle = "#f59e0b";
    ctx.font = "bold 9px monospace";
    ctx.fillText(`ALIGNMENT: ${w.alignment}`, 588, 58);

    if (q) {
      ctx.fillStyle = q.completed ? "#10b981" : "#e2e8f0";
      ctx.font = "bold 9px monospace";
      ctx.fillText(q.completed ? "QUEST COMPLETED" : q.title.slice(0, 26), 588, 74);
      ctx.fillStyle = "#94a3b8";
      ctx.fillText(`PROGRESS: [${q.currentCount}/${q.targetCount}]`, 588, 90);
    }
    ctx.restore();
  }
});
