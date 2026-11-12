// Cohesive Milestone Plugin: v0.1.0 (Procedural OSR Dungeon Rooms, Chiaroscuro Torchlight & Souls-Zelda Melee)
window.StudioEngine.registerModule("Milestone_v0_1_0", {
  init: function(state, engine) {
    const p = state.player;
    const w = state.world;

    p.x = 400; p.y = 310;
    p.vx = 0; p.vy = 0;
    p.width = 22; p.height = 22;
    p.speed = 165;
    p.facingAngle = 0;
    p.health = 5; p.maxHealth = 5;
    p.shields = 5; p.maxShields = 5;
    p.stamina = 100; p.maxStamina = 100;
    p.stamRegenDelay = 0;
    p.torchLevel = 100;
    p.gold = 25;
    p.attackTimer = 0;
    p.attackCooldown = 0;
    p.dashTimer = 0;
    p.dashCooldown = 0;
    p.invuln = 0;
    p.hitStop = 0;

    w.rooms = {};
    w.currentRoom = { x: 0, y: 0 };
    w.depth = 1;
    w.cameraShake = 0;
    w.enemies = [];
    w.bonePiles = [];
    w.braziers = [];
    w.pillars = [];
    w.hazards = [];
    w.bloodStains = [];
    w.particles = w.particles || [];
    w.floatingTexts = w.floatingTexts || [];

    this.loadRoom(state, 0, 0);
  },

  _seedHash: function(rx, ry, salt) {
    const n = Math.sin(rx * 127.1 + ry * 311.7 + salt * 74.7) * 43758.5453;
    return n - Math.floor(n);
  },

  loadRoom: function(state, rx, ry) {
    const w = state.world;
    const key = `${rx},${ry}`;
    w.currentRoom = { x: rx, y: ry };

    if (!w.rooms[key]) {
      const archetypeIdx = Math.floor(this._seedHash(rx, ry, 1) * 5);
      const archetypes = [
        { name: "PILLARED OSSUARY", floor: "#100d16", accent: "#a855f7" },
        { name: "VERDIGRIS ACID CISTERN", floor: "#0b1311", accent: "#10b981" },
        { name: "BLOOD-ALTAR SANCTUM", floor: "#160b0f", accent: "#dc2626" },
        { name: "COLLAPSED CATACOMB", floor: "#12100e", accent: "#eab308" },
        { name: "OBSIDIAN GREAT HALL", floor: "#0d0b14", accent: "#f59e0b" }
      ];
      const arch = archetypes[archetypeIdx];

      const braziers = [
        { x: 130, y: 120, lit: true, r: 14 },
        { x: 670, y: 120, lit: true, r: 14 },
        { x: 130, y: 500, lit: this._seedHash(rx, ry, 2) > 0.25, r: 14 },
        { x: 670, y: 500, lit: this._seedHash(rx, ry, 3) > 0.25, r: 14 }
      ];

      const pillars = [];
      if (archetypeIdx === 0 || archetypeIdx === 4) {
        pillars.push({ x: 250, y: 220, w: 36, h: 36 }, { x: 514, y: 220, w: 36, h: 36 });
        pillars.push({ x: 250, y: 380, w: 36, h: 36 }, { x: 514, y: 380, w: 36, h: 36 });
      } else if (archetypeIdx === 2) {
        pillars.push({ x: 376, y: 286, w: 48, h: 48, isAltar: true });
      } else if (archetypeIdx === 3) {
        pillars.push({ x: 310, y: 240, w: 42, h: 42 }, { x: 450, y: 360, w: 42, h: 42 });
      }

      const acidPools = [];
      if (archetypeIdx === 1) {
        acidPools.push({ x: 240, y: 260, r: 48 }, { x: 560, y: 360, r: 52 });
      }

      const bonePiles = [];
      for (let i = 0; i < 4; i++) {
        const bx = 150 + this._seedHash(rx, ry, 10 + i) * 500;
        const by = 140 + this._seedHash(rx, ry, 20 + i) * 340;
        if (Math.hypot(bx - 400, by - 310) > 75) {
          bonePiles.push({ x: bx, y: by, hp: 1, r: 14 });
        }
      }

      const enemies = [];
      const isStart = (rx === 0 && ry === 0);
      const count = isStart ? 2 : 3 + (Math.abs(rx) + Math.abs(ry)) % 3;
      for (let i = 0; i < count; i++) {
        const ex = 160 + this._seedHash(rx, ry, 30 + i) * 480;
        const ey = 140 + this._seedHash(rx, ry, 40 + i) * 340;
        if (Math.hypot(ex - 400, ey - 310) < 90) continue;
        const kind = (i % 2 === 0) ? "SKELETON" : "SLIME";
        enemies.push({
          type: kind,
          x: ex, y: ey, vx: 0, vy: 0,
          r: kind === "SKELETON" ? 14 : 16,
          hp: kind === "SKELETON" ? 45 : 35,
          maxHp: kind === "SKELETON" ? 45 : 35,
          speed: kind === "SKELETON" ? 72 : 52,
          stagger: 0, windup: 0, color: kind === "SKELETON" ? "#e2e8f0" : "#10b981"
        });
      }

      w.rooms[key] = {
        rx, ry, arch, braziers, pillars, acidPools, bonePiles, enemies, bloodStains: []
      };
    }

    const room = w.rooms[key];
    w.braziers = room.braziers;
    w.pillars = room.pillars;
    w.bonePiles = room.bonePiles;
    w.enemies = room.enemies;
    w.bloodStains = room.bloodStains;
    w.roomName = room.arch.name;
    w.depth = 1 + Math.floor((Math.abs(rx) + Math.abs(ry)) / 2);
  },

  update: function(dt, state, engine) {
    if (!state.running || state.paused || state.gameOver) return;
    const p = state.player, w = state.world, keys = state.keys || {};

    if (p.hitStop > 0) { p.hitStop -= dt; return; }
    if (p.invuln > 0) p.invuln = Math.max(0, p.invuln - dt);
    if (p.attackTimer > 0) p.attackTimer = Math.max(0, p.attackTimer - dt);
    if (p.attackCooldown > 0) p.attackCooldown = Math.max(0, p.attackCooldown - dt);
    if (p.dashTimer > 0) p.dashTimer = Math.max(0, p.dashTimer - dt);
    if (p.dashCooldown > 0) p.dashCooldown = Math.max(0, p.dashCooldown - dt);

    // Torch decay (clamped at 25 minimum so the player is NEVER in 100% blind pitch-black darkness!)
    p.torchLevel = Math.max(25, (p.torchLevel || 100) - dt * 0.45);
    // Standing near a lit brazier warms & restores Torchlight!
    for (let i = 0; i < (w.braziers || []).length; i++) {
      const b = w.braziers[i];
      if (b.lit && Math.hypot(p.x - b.x, p.y - b.y) < 75) {
        p.torchLevel = Math.min(100, p.torchLevel + dt * 18);
      }
    }

    // Stamina regeneration
    if (p.stamRegenDelay > 0) p.stamRegenDelay -= dt;
    else p.stamina = Math.min(p.maxStamina || 100, (p.stamina || 0) + 34 * dt);

    // 8-way Movement
    let dx = (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
    let dy = (keys.down ? 1 : 0) - (keys.up ? 1 : 0);
    const len = Math.hypot(dx, dy);
    if (len > 0) {
      dx /= len; dy /= len;
      if (p.attackTimer <= 0) p.facingAngle = Math.atan2(dy, dx);
    }

    // Dodge-Roll on [SHIFT / E] (`keys.action`)
    if (keys.action && p.dashCooldown <= 0 && p.stamina >= 18) {
      p.dashTimer = 0.20;
      p.dashCooldown = 0.65;
      p.invuln = Math.max(p.invuln, 0.24);
      p.stamina -= 18;
      p.stamRegenDelay = 0.35;
      const rollAngle = len > 0 ? Math.atan2(dy, dx) : p.facingAngle;
      p.vx = Math.cos(rollAngle) * 360;
      p.vy = Math.sin(rollAngle) * 360;
      engine.emit("PLAYER_DODGE", { x: p.x, y: p.y, angle: rollAngle });
    }

    // Directional Melee Cleave on [SPACE] (`keys.jump`)
    if (keys.jump && p.attackCooldown <= 0 && p.stamina >= 14) {
      p.attackTimer = 0.22;
      p.attackCooldown = 0.34;
      p.stamina -= 14;
      p.stamRegenDelay = 0.40;
      p.vx = Math.cos(p.facingAngle) * 95;
      p.vy = Math.sin(p.facingAngle) * 95;
      this.performMeleeCleave(state, engine);
    }

    const moveSpd = p.dashTimer > 0 ? 340 : (p.attackTimer > 0 ? (p.speed || 165) * 0.45 : (p.speed || 165));
    if (p.dashTimer <= 0) {
      p.vx = dx * moveSpd;
      p.vy = dy * moveSpd;
    }

    p.x += p.vx * dt;
    p.y += p.vy * dt;

    // Resolve Pillar Collisions
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      const cx = pl.x + pl.w / 2, cy = pl.y + pl.h / 2;
      const ox = p.x - cx, oy = p.y - cy;
      const minDist = pl.w / 2 + 12;
      if (Math.abs(ox) < minDist && Math.abs(oy) < minDist) {
        if (Math.abs(ox) > Math.abs(oy)) p.x = cx + Math.sign(ox) * minDist;
        else p.y = cy + Math.sign(oy) * minDist;
      }
    }

    // Room-to-Room Archway Transitions (N/S/E/W Doors)
    const inHorizDoor = (p.y > 265 && p.y < 365);
    const inVertDoor = (p.x > 350 && p.x < 450);

    if (p.x < 64 && inHorizDoor) {
      p.x = 724; this.loadRoom(state, w.currentRoom.x - 1, w.currentRoom.y); return;
    } else if (p.x > 736 && inHorizDoor) {
      p.x = 76; this.loadRoom(state, w.currentRoom.x + 1, w.currentRoom.y); return;
    } else if (p.y < 82 && inVertDoor) {
      p.y = 532; this.loadRoom(state, w.currentRoom.x, w.currentRoom.y - 1); return;
    } else if (p.y > 548 && inVertDoor) {
      p.y = 94; this.loadRoom(state, w.currentRoom.x, w.currentRoom.y + 1); return;
    }

    // Clamp to Stone Walls
    p.x = Math.max(66, Math.min(734, p.x));
    p.y = Math.max(84, Math.min(546, p.y));

    // Destructible Bone Piles
    for (let i = (w.bonePiles || []).length - 1; i >= 0; i--) {
      const bp = w.bonePiles[i];
      if (Math.hypot(p.x - bp.x, p.y - bp.y) < 26 && (p.attackTimer > 0 || p.dashTimer > 0)) {
        w.bonePiles.splice(i, 1);
        p.gold = (p.gold || 0) + 5;
        p.torchLevel = Math.min(100, p.torchLevel + 8);
        w.floatingTexts.push({ text: "+5G // TORCH EMBER", x: bp.x, y: bp.y - 10, color: "#eab308", life: 0.9 });
      }
    }

    // Update Dungeon Enemies
    const enemies = w.enemies || [];
    for (let i = enemies.length - 1; i >= 0; i--) {
      const en = enemies[i];
      if (en.hp <= 0) {
        w.bloodStains.push({ x: en.x, y: en.y, r: 16 + Math.random() * 8, color: en.type === "SLIME" ? "rgba(16,185,129,0.35)" : "rgba(185,28,28,0.42)" });
        p.gold = (p.gold || 0) + 12;
        state.score = (state.score || 0) + 150;
        engine.emit("ENEMY_SLAIN", { enemy: en, x: en.x, y: en.y });
        enemies.splice(i, 1);
        continue;
      }
      if (en.stagger > 0) {
        en.stagger -= dt;
        en.x += en.vx * dt; en.y += en.vy * dt;
        en.vx *= 0.88; en.vy *= 0.88;
      } else {
        const edx = p.x - en.x, edy = p.y - en.y;
        const dist = Math.hypot(edx, edy) || 1;
        if (dist < 280) {
          en.x += (edx / dist) * en.speed * dt;
          en.y += (edy / dist) * en.speed * dt;
        }
        if (dist < en.r + 13) {
          if (p.dashTimer > 0 && p.dashTimer > 0.06) {
            // Timed Parry / Riposte Deflection!
            en.stagger = 1.1;
            en.vx = -(edx / dist) * 240;
            en.vy = -(edy / dist) * 240;
            w.floatingTexts.push({ text: "⚔ PARRIED! ⚔", x: p.x, y: p.y - 24, color: "#eab308", life: 0.9 });
            engine.emit("PARRY_SUCCESS", { enemy: en });
          } else if (p.invuln <= 0) {
            p.health = Math.max(0, (p.health || 5) - 1);
            p.shields = p.health;
            p.invuln = 1.1;
            w.cameraShake = 8; // Subtle context-aware world shake
            w.floatingTexts.push({ text: "-1 HP", x: p.x, y: p.y - 20, color: "#dc2626", life: 0.8 });
          }
        }
      }
      en.x = Math.max(72, Math.min(728, en.x));
      en.y = Math.max(90, Math.min(540, en.y));
    }

    // Update Floating Texts & Particles
    for (let i = w.floatingTexts.length - 1; i >= 0; i--) {
      const ft = w.floatingTexts[i];
      ft.y -= 22 * dt;
      ft.life -= dt;
      if (ft.life <= 0) w.floatingTexts.splice(i, 1);
    }
    for (let i = w.particles.length - 1; i >= 0; i--) {
      const pt = w.particles[i];
      pt.x += (pt.vx || 0) * dt;
      pt.y += (pt.vy || 0) * dt;
      pt.life -= dt;
      if (pt.life <= 0) w.particles.splice(i, 1);
    }
  },

  performMeleeCleave: function(state, engine) {
    const p = state.player, w = state.world;
    const reach = p.weaponReach || 58;
    const cleaveDmg = p.weaponDamage || 22;
    const enemies = w.enemies || [];

    for (let i = 0; i < enemies.length; i++) {
      const en = enemies[i];
      const dx = en.x - p.x, dy = en.y - p.y;
      const dist = Math.hypot(dx, dy);
      if (dist <= reach + en.r) {
        const angToEnemy = Math.atan2(dy, dx);
        let diff = Math.abs(angToEnemy - p.facingAngle);
        if (diff > Math.PI) diff = Math.PI * 2 - diff;
        if (diff <= 1.35) {
          const isCrit = en.stagger > 0;
          const dmg = isCrit ? Math.floor(cleaveDmg * 1.6) : cleaveDmg;
          en.hp -= dmg;
          en.stagger = 0.42;
          en.vx = Math.cos(p.facingAngle) * 210;
          en.vy = Math.sin(p.facingAngle) * 210;
          p.hitStop = 0.03;
          w.cameraShake = 3.5;
          w.floatingTexts.push({
            text: isCrit ? `CRIT ${dmg}!` : `${dmg}`,
            x: en.x, y: en.y - 16,
            color: isCrit ? "#eab308" : "#f8fafc", life: 0.75
          });
          for (let k = 0; k < 6; k++) {
            const a = p.facingAngle + (Math.random() - 0.5) * 1.2;
            w.particles.push({
              x: en.x, y: en.y,
              vx: Math.cos(a) * (90 + Math.random() * 90),
              vy: Math.sin(a) * (90 + Math.random() * 90),
              color: en.type === "SLIME" ? "#10b981" : "#dc2626", life: 0.35
            });
          }
        }
      }
    }
    engine.emit("PLAYER_ATTACK", { x: p.x, y: p.y, angle: p.facingAngle });
  },

  render: function(ctx, state) {
    const p = state.player, w = state.world;
    const roomKey = `${w.currentRoom.x},${w.currentRoom.y}`;
    const room = (w.rooms && w.rooms[roomKey]) || { arch: { name: "CRYPT", floor: "#100d16", accent: "#a855f7" }, acidPools: [] };

    // 1. Apply Context-Aware World Screen Shake ONLY to the Dungeon Viewport (NOT the Top Status Bar!)
    ctx.save();
    if (w.cameraShake > 0.3 && !state.paused) {
      const sx = (Math.random() - 0.5) * Math.min(w.cameraShake, 7);
      const sy = (Math.random() - 0.5) * Math.min(w.cameraShake, 7);
      ctx.translate(sx, sy);
    }

    // 2. Render Carved Flagstone Dungeon Floor & Masonry Walls
    ctx.fillStyle = room.arch.floor;
    ctx.fillRect(0, 36, 800, 564);

    // Carved Stone Flagstone Grid with Mortar Bevels
    ctx.strokeStyle = "rgba(148, 163, 184, 0.09)";
    ctx.lineWidth = 1;
    for (let gx = 60; gx < 740; gx += 40) {
      for (let gy = 76; gy < 556; gy += 40) {
        ctx.strokeRect(gx, gy, 40, 40);
      }
    }

    // Outer Obsidian Dungeon Walls (with N/S/E/W Carved Archway Openings)
    ctx.fillStyle = "#1c1926";
    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 2;
    // Top wall (split by North Archway x:350..450)
    ctx.fillRect(40, 56, 310, 22); ctx.strokeRect(40, 56, 310, 22);
    ctx.fillRect(450, 56, 310, 22); ctx.strokeRect(450, 56, 310, 22);
    // Bottom wall (split by South Archway x:350..450)
    ctx.fillRect(40, 554, 310, 22); ctx.strokeRect(40, 554, 310, 22);
    ctx.fillRect(450, 554, 310, 22); ctx.strokeRect(450, 554, 310, 22);
    // Left wall (split by West Archway y:265..365)
    ctx.fillRect(40, 78, 20, 187); ctx.strokeRect(40, 78, 20, 187);
    ctx.fillRect(40, 365, 20, 189); ctx.strokeRect(40, 365, 20, 189);
    // Right wall (split by East Archway y:265..365)
    ctx.fillRect(740, 78, 20, 187); ctx.strokeRect(740, 78, 20, 187);
    ctx.fillRect(740, 365, 20, 189); ctx.strokeRect(740, 365, 20, 189);

    // Glowing Archway Threshold Runes
    ctx.fillStyle = "rgba(234, 179, 8, 0.22)";
    ctx.fillRect(352, 58, 96, 16);
    ctx.fillRect(352, 556, 96, 16);
    ctx.fillRect(42, 267, 16, 96);
    ctx.fillRect(742, 267, 16, 96);

    // Acid Pools / Floor Bloodstains
    for (let i = 0; i < (room.acidPools || []).length; i++) {
      const ap = room.acidPools[i];
      ctx.fillStyle = "rgba(16, 185, 129, 0.24)";
      ctx.beginPath(); ctx.arc(ap.x, ap.y, ap.r, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "#10b981"; ctx.stroke();
    }
    for (let i = 0; i < (w.bloodStains || []).length; i++) {
      const bs = w.bloodStains[i];
      ctx.fillStyle = bs.color;
      ctx.beginPath(); ctx.arc(bs.x, bs.y, bs.r, 0, Math.PI * 2); ctx.fill();
    }

    // Pillars & Blood Altars
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      ctx.fillStyle = pl.isAltar ? "#450a0a" : "#272333";
      ctx.fillRect(pl.x, pl.y, pl.w, pl.h);
      ctx.strokeStyle = pl.isAltar ? "#dc2626" : "#64748b";
      ctx.lineWidth = 2;
      ctx.strokeRect(pl.x, pl.y, pl.w, pl.h);
      // Inner bevel
      ctx.strokeRect(pl.x + 6, pl.y + 6, pl.w - 12, pl.h - 12);
    }

    // Bone Piles
    for (let i = 0; i < (w.bonePiles || []).length; i++) {
      const bp = w.bonePiles[i];
      ctx.fillStyle = "#cbd5e1";
      ctx.fillRect(bp.x - 8, bp.y - 5, 16, 10);
      ctx.fillStyle = "#94a3b8";
      ctx.fillRect(bp.x - 4, bp.y - 8, 8, 8);
    }

    // Flickering Wall Braziers (with Warm Secondary Light Halo!)
    const flicker = Math.sin(performance.now() * 0.012) * 6;
    for (let i = 0; i < (w.braziers || []).length; i++) {
      const b = w.braziers[i];
      if (b.lit) {
        const bg = ctx.createRadialGradient(b.x, b.y, 4, b.x, b.y, 95 + flicker);
        bg.addColorStop(0, "rgba(245, 158, 11, 0.28)");
        bg.addColorStop(1, "rgba(245, 158, 11, 0)");
        ctx.fillStyle = bg;
        ctx.beginPath(); ctx.arc(b.x, b.y, 95 + flicker, 0, Math.PI * 2); ctx.fill();
      }
      ctx.fillStyle = "#334155";
      ctx.beginPath(); ctx.arc(b.x, b.y, 11, 0, Math.PI * 2); ctx.fill();
      if (b.lit) {
        ctx.fillStyle = "#f59e0b";
        ctx.beginPath(); ctx.arc(b.x, b.y, 7 + flicker * 0.2, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fef08a";
        ctx.beginPath(); ctx.arc(b.x, b.y, 3.5, 0, Math.PI * 2); ctx.fill();
      }
    }

    // Enemies (Detailed Skeleton Warriors & Eldritch Sludge-Slimes)
    for (let i = 0; i < (w.enemies || []).length; i++) {
      const en = w.enemies[i];
      ctx.save();
      ctx.translate(en.x, en.y);
      if (en.type === "SKELETON") {
        // Bony Shoulders & Skull
        ctx.fillStyle = en.stagger > 0 ? "#facc15" : "#cbd5e1";
        ctx.fillRect(-10, -8, 20, 16);
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(-5, -4, 3, 3);
        ctx.fillRect(2, -4, 3, 3);
        // Iron Shield & Rusty Blade
        ctx.fillStyle = "#64748b";
        ctx.fillRect(-14, -6, 4, 14);
        ctx.fillStyle = "#dc2626";
        ctx.fillRect(10, -10, 3, 18);
      } else {
        // Pulsing Verdigris Acid Slime
        const pulse = Math.sin(performance.now() * 0.008 + i) * 2.5;
        ctx.fillStyle = "rgba(16, 185, 129, 0.82)";
        ctx.beginPath(); ctx.arc(0, 0, en.r + pulse, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#a7f3d0";
        ctx.fillRect(-5, -4, 4, 4); ctx.fillRect(3, -4, 4, 4);
      }
      // Mini Health Bar above Enemy
      if (en.hp < en.maxHp) {
        ctx.fillStyle = "#1e293b";
        ctx.fillRect(-14, -18, 28, 4);
        ctx.fillStyle = "#dc2626";
        ctx.fillRect(-14, -18, 28 * Math.max(0, en.hp / en.maxHp), 4);
      }
      ctx.restore();
    }

    // 3. Render Detailed OSR Adventurer Sprite & Weapon Cleave Arc
    ctx.save();
    ctx.translate(p.x, p.y);
    if (p.invuln > 0 && Math.floor(performance.now() / 60) % 2 === 0) ctx.globalAlpha = 0.45;

    // Weapon Cleave Slash Arc when attacking
    if (p.attackTimer > 0) {
      const reach = p.weaponReach || 58;
      ctx.save();
      ctx.rotate(p.facingAngle);
      ctx.strokeStyle = p.classColor || "#eab308";
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(0, 0, reach, -0.95, 0.95);
      ctx.stroke();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(0, 0, reach - 5, -0.85, 0.85);
      ctx.stroke();
      ctx.restore();
    }

    // Delver Cloak / Armored Shoulders
    ctx.fillStyle = p.classColor || "#eab308";
    ctx.fillRect(-11, -9, 22, 18);
    // Dark Iron Breastplate
    ctx.fillStyle = "#334155";
    ctx.fillRect(-8, -7, 16, 14);
    // Knight Greathelm / Hood & Glowing Visor Eyes
    ctx.fillStyle = "#e2e8f0";
    ctx.fillRect(-7, -11, 14, 11);
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(-5, -7, 10, 3);
    ctx.fillStyle = p.classColor || "#f59e0b";
    ctx.fillRect(-4, -7, 3, 2);
    ctx.fillRect(1, -7, 3, 2);
    // Flickering Off-Hand Torch
    ctx.fillStyle = "#f59e0b";
    ctx.beginPath(); ctx.arc(-13, -4, 4 + flicker * 0.15, 0, Math.PI * 2); ctx.fill();
    ctx.restore();

    // Particles & Floating Combat Text
    for (let i = 0; i < w.particles.length; i++) {
      const pt = w.particles[i];
      ctx.fillStyle = pt.color || "#dc2626";
      ctx.fillRect(pt.x - 2, pt.y - 2, 4, 4);
    }
    ctx.font = "bold 12px monospace";
    ctx.textAlign = "center";
    for (let i = 0; i < w.floatingTexts.length; i++) {
      const ft = w.floatingTexts[i];
      ctx.fillStyle = ft.color || "#f8fafc";
      ctx.fillText(ft.text, ft.x, ft.y);
    }

    // 4. Chiaroscuro Torchlight Vignette (Balanced so Room Architecture Remains Visible!)
    const torchR = 165 + (p.torchLevel || 100) * 1.35 + flicker;
    const grad = ctx.createRadialGradient(p.x, p.y, 45, p.x, p.y, torchR);
    grad.addColorStop(0, "rgba(245, 158, 11, 0.08)");
    grad.addColorStop(0.55, "rgba(10, 7, 16, 0.38)");
    grad.addColorStop(1, "rgba(5, 3, 9, 0.78)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 36, 800, 564);

    ctx.restore(); // End of World Camera Shake Scope!

    // 5. Render Rock-Steady Single Gothic Status Ribbon at Top (y: 0..36, NEVER shakes!)
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = "#09070e";
    ctx.fillRect(0, 0, 800, 36);
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, 36); ctx.lineTo(800, 36); ctx.stroke();

    // HP Crimson Vessels
    for (let i = 0; i < (p.maxHealth || 5); i++) {
      ctx.fillStyle = i < (p.health || 0) ? "#dc2626" : "#1e293b";
      ctx.fillRect(14 + i * 18, 10, 13, 15);
      ctx.strokeStyle = "#fca5a5";
      ctx.lineWidth = 1;
      ctx.strokeRect(14 + i * 18, 10, 13, 15);
    }

    // Stamina Bar (Verdigris Green)
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(114, 12, 86, 11);
    ctx.fillStyle = "#10b981";
    ctx.fillRect(114, 12, 86 * Math.max(0, (p.stamina || 0) / (p.maxStamina || 100)), 11);

    // Torch Flame Bar (Amber Gold)
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(212, 12, 68, 11);
    ctx.fillStyle = "#f59e0b";
    ctx.fillRect(212, 12, 68 * Math.max(0, (p.torchLevel || 0) / 100), 11);

    // Compact Integrated Status Readout (Fits 100% inside 800px width with ZERO clipping!)
    const stressVal = Math.floor(p.stress || 0);
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "bold 11px monospace";
    ctx.textAlign = "left";
    ctx.fillText(`GOLD:${p.gold || 0}`, 292, 22);
    ctx.fillStyle = "#a855f7";
    ctx.fillText(`STRESS:${stressVal}%`, 362, 22);
    ctx.fillStyle = "#cbd5e1";
    ctx.fillText(`${w.roomName || "CRYPT"} [${w.currentRoom.x},${w.currentRoom.y}] D:${w.depth || 1}`, 448, 22);
    ctx.fillStyle = "#eab308";
    ctx.textAlign = "right";
    ctx.fillText("[SPC]CLEAVE [SHF/E]ROLL", 790, 22);
    ctx.restore();
  }
});
