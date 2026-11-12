// Cohesive Milestone Plugin: v0.1.0 (2.5D Low-Poly Faceted Dungeon, Dynamic Shadow Volumes & Souls-Zelda Melee)
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
    w.bloodStains = [];
    w.particles = w.particles || [];
    w.floatingTexts = w.floatingTexts || [];

    // Expose 2.5D Low-Poly Projection & Lambertian Shading Helper on state.world.lowPoly
    w.lowPoly = {
      project: function(x, y, z) {
        const k = z * 0.0022;
        return { x: x + (x - 400) * k, y: y + (y - 310) * k - z * 0.55 };
      },
      shadeHex: function(hex, factor) {
        const c = hex.replace("#", "");
        const num = parseInt(c, 16);
        const r = Math.min(255, Math.max(0, Math.floor(((num >> 16) & 255) * factor)));
        const g = Math.min(255, Math.max(0, Math.floor(((num >> 8) & 255) * factor)));
        const b = Math.min(255, Math.max(0, Math.floor((num & 255) * factor)));
        return `rgb(${r},${g},${b})`;
      },
      drawExtrudedBox: function(ctx, bx, by, bw, bh, bz, baseColor, strokeColor, lightX, lightY) {
        const p00 = this.project(bx, by, 0), p10 = this.project(bx + bw, by, 0);
        const p11 = this.project(bx + bw, by + bh, 0), p01 = this.project(bx, by + bh, 0);
        const t00 = this.project(bx, by, bz), t10 = this.project(bx + bw, by, bz);
        const t11 = this.project(bx + bw, by + bh, bz), t01 = this.project(bx, by + bh, bz);

        const cx = bx + bw * 0.5, cy = by + bh * 0.5;
        const dist = Math.hypot(lightX - cx, lightY - cy) || 1;
        const atten = Math.max(0.28, Math.min(1.35, 220 / (dist + 60)));
        const lx = (lightX - cx) / dist, ly = (lightY - cy) / dist;

        const drawFace = (pts, nx, ny, nz) => {
          const dot = Math.max(0.15, nx * lx + ny * ly + nz * 0.55);
          ctx.fillStyle = this.shadeHex(baseColor, dot * atten);
          ctx.beginPath();
          ctx.moveTo(pts[0].x, pts[0].y);
          for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
          ctx.closePath();
          ctx.fill();
          if (strokeColor) {
            ctx.strokeStyle = strokeColor;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        };

        // Render visible side faces sorted by camera perspective + roof
        if (cy < 310) drawFace([p01, p11, t11, t01], 0, 1, 0.1);
        else drawFace([p00, p10, t10, t00], 0, -1, 0.1);
        drawFace([p01, p11, t11, t01], 0, 1, 0.15); // South front-facing bevel always visible in top-down
        if (cx < 400) drawFace([p10, p11, t11, t10], 1, 0, 0.1);
        else drawFace([p00, p01, t01, t00], -1, 0, 0.1);

        // Top cap (faceted pyramid or flat roof)
        drawFace([t00, t10, t11, t01], 0, 0, 1.0);
      },
drawArticulatedDelver: function(ctx, p, t) {
        const isMoving = Math.hypot(p.vx || 0, p.vy || 0) > 12;
        const stride = isMoving ? Math.sin(t * 14) * 3.5 : 0;
        const breath = Math.sin(t * 3.5) * 1.2;
        const col = p.classColor || "#eab308";

        ctx.save();
        ctx.translate(p.x, p.y);

        // Ground shadow ellipse
        ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
        ctx.beginPath(); ctx.ellipse(0, 12, 13, 6, 0, 0, Math.PI * 2); ctx.fill();

        // Animated Striding Boots
        ctx.fillStyle = "#1e293b";
        ctx.fillRect(-7, 6 + stride, 5, 7);
        ctx.fillRect(2, 6 - stride, 5, 7);

        // Billowing Tattered Dark-Fantasy Cloak (3-point mantle)
        const sway = isMoving ? Math.sin(t * 10) * 4 : Math.sin(t * 2.5) * 1.5;
        ctx.fillStyle = this.shadeHex(col, 0.55);
        ctx.beginPath();
        ctx.moveTo(-11, -6);
        ctx.lineTo(11, -6);
        ctx.lineTo(14 + sway, 11);
        ctx.lineTo(0, 8);
        ctx.lineTo(-14 + sway, 11);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = "#09070e"; ctx.lineWidth = 1.2; ctx.stroke();

        // Armored Pauldrons & Breastplate
        ctx.fillStyle = "#334155";
        ctx.fillRect(-9, -6 + breath * 0.4, 18, 13);
        ctx.fillStyle = col;
        ctx.fillRect(-12, -7 + breath * 0.5, 6, 7);
        ctx.fillRect(6, -7 + breath * 0.5, 6, 7);

        // Articulated Off-Hand Flickering Torch
        const flick = Math.sin(t * 18) * 1.5;
        ctx.strokeStyle = "#78350f"; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.moveTo(-11, -2); ctx.lineTo(-16, -12); ctx.stroke();
        ctx.fillStyle = p.uvTorch ? "#a855f7" : "#f59e0b";
        ctx.beginPath(); ctx.arc(-16, -14, 4.5 + flick * 0.4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fef08a";
        ctx.beginPath(); ctx.arc(-16, -14, 2, 0, Math.PI * 2); ctx.fill();

        // Articulated Main-Hand Weapon (Swings during attackTimer, held at ready otherwise)
        ctx.save();
        const swingOffset = p.attackTimer > 0 ? Math.sin((0.22 - p.attackTimer) / 0.22 * Math.PI) * 1.8 - 0.9 : 0.35;
        ctx.rotate(p.facingAngle + swingOffset);
        ctx.fillStyle = "#cbd5e1";
        ctx.fillRect(8, -2, 22, 4); // Blade shaft
        ctx.fillStyle = p.weaponGlow || col;
        ctx.fillRect(10, -1, 20, 2); // Runic fuller
        ctx.fillStyle = "#eab308";
        ctx.fillRect(7, -6, 3, 12); // Crossguard
        ctx.restore();

        // Knight Greathelm / Cultist Hood + Glowing Visor Slits
        ctx.fillStyle = "#cbd5e1";
        ctx.beginPath();
        ctx.moveTo(-7, -6 + breath);
        ctx.lineTo(0, -17 + breath);
        ctx.lineTo(7, -6 + breath);
        ctx.closePath();
        ctx.fill();
        ctx.fillRect(-6, -13 + breath, 12, 9);
        ctx.strokeStyle = "#0f172a"; ctx.strokeRect(-6, -13 + breath, 12, 9);
        // Visor slit & glowing eyes
        ctx.fillStyle = "#09070e";
        ctx.fillRect(-5, -10 + breath, 10, 3);
        ctx.fillStyle = p.weaponGlow || col;
        ctx.fillRect(-4, -10 + breath, 3, 2);
        ctx.fillRect(1, -10 + breath, 3, 2);

        ctx.restore();
      },
      drawArticulatedEnemy: function(ctx, en, p, t, idx) {
        const bob = Math.sin(t * 7 + idx * 1.7) * 2.2;
        const ang = en.facing !== undefined ? en.facing : Math.atan2(p.y - en.y, p.x - en.x);
        const kind = (en.type || "SKELETON").toUpperCase();

        ctx.save();
        ctx.translate(en.x, en.y);

        // Ground shadow
        ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
        ctx.beginPath(); ctx.ellipse(0, 11, 12, 5, 0, 0, Math.PI * 2); ctx.fill();

        if (kind.includes("NECRO")) {
          // Articulated Crypt Necromancer: Tattered Violet Cultist Robes, Horned Skull Crown & Levitating Staff
          ctx.fillStyle = "#3b0764";
          ctx.beginPath();
          ctx.moveTo(0, -16 + bob); ctx.lineTo(13, 11); ctx.lineTo(-13, 11); ctx.closePath();
          ctx.fill();
          ctx.strokeStyle = "#a855f7"; ctx.lineWidth = 1.5; ctx.stroke();
          // Skull face & glowing purple eyes
          ctx.fillStyle = "#e2e8f0";
          ctx.fillRect(-5, -13 + bob, 10, 8);
          ctx.fillStyle = "#a855f7";
          ctx.fillRect(-4, -10 + bob, 3, 3); ctx.fillRect(1, -10 + bob, 3, 3);
          // Necrotic Orb Staff
          ctx.strokeStyle = "#cbd5e1"; ctx.beginPath(); ctx.moveTo(11, 8); ctx.lineTo(13, -14 - bob); ctx.stroke();
          ctx.fillStyle = "#c084fc"; ctx.beginPath(); ctx.arc(13, -16 - bob, 4.5, 0, Math.PI * 2); ctx.fill();
        } else if (kind.includes("FUNG") || kind.includes("SLIME") || kind.includes("HORROR")) {
          // Articulated Bioluminescent Fungoid Spore-Horror (Multi-cap Mycelium Beast)
          const pulse = Math.sin(t * 5 + idx) * 2;
          // Stalk & tendrils
          ctx.fillStyle = "#064e3b";
          ctx.fillRect(-6, -2, 12, 12);
          // Domed Spore Cap
          ctx.fillStyle = "#059669";
          ctx.beginPath(); ctx.arc(0, -4 + bob * 0.6, 14 + pulse * 0.5, Math.PI, 0); ctx.closePath(); ctx.fill();
          ctx.strokeStyle = "#34d399"; ctx.lineWidth = 1.5; ctx.stroke();
          // Glowing Toxic Spots & Eyes
          ctx.fillStyle = "#a7f3d0";
          ctx.beginPath(); ctx.arc(-6, -9 + bob * 0.6, 2.5, 0, Math.PI * 2); ctx.arc(5, -10 + bob * 0.6, 3, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = "#fef08a";
          ctx.fillRect(-5, 1, 3, 3); ctx.fillRect(2, 1, 3, 3);
        } else if (kind.includes("MIMIC")) {
          // Articulated Tooth-Maw Iron Mimic Chest
          ctx.fillStyle = "#78350f"; ctx.fillRect(-13, -9 + bob * 0.5, 26, 18);
          ctx.strokeStyle = "#eab308"; ctx.lineWidth = 2; ctx.strokeRect(-13, -9 + bob * 0.5, 26, 18);
          ctx.fillStyle = "#dc2626"; ctx.fillRect(-10, -2 + bob * 0.5, 20, 6);
          ctx.fillStyle = "#f8fafc";
          for (let k = -8; k <= 8; k += 4) ctx.fillRect(k, -2 + bob * 0.5, 2, 3);
        } else {
          // Articulated Skeleton / Phalanx Warrior (Ribcage, Skull, Directional Tower Shield & Spear)
          const isPhalanx = kind.includes("PHALANX");
          ctx.fillStyle = en.stagger > 0 ? "#facc15" : "#94a3b8";
          ctx.fillRect(-7, -4 + bob * 0.5, 14, 11); // Ribcage
          ctx.fillStyle = "#0f172a";
          ctx.fillRect(-5, -2 + bob * 0.5, 10, 2); ctx.fillRect(-5, 2 + bob * 0.5, 10, 2);
          // Skull
          ctx.fillStyle = "#f1f5f9";
          ctx.fillRect(-6, -13 + bob, 12, 9);
          ctx.fillStyle = "#dc2626";
          ctx.fillRect(-4, -10 + bob, 3, 3); ctx.fillRect(1, -10 + bob, 3, 3);
          // Directional Weapon & Tower Shield
          ctx.save();
          ctx.rotate(ang);
          ctx.fillStyle = "#cbd5e1";
          ctx.fillRect(6, 5, 16, 2.5); // Spear/Blade
          if (isPhalanx) {
            ctx.strokeStyle = "#38bdf8";
            ctx.fillStyle = "#1e293b";
            ctx.lineWidth = 3;
            ctx.beginPath(); ctx.arc(0, 0, 17, -1.05, 1.05); ctx.stroke();
          }
          ctx.restore();
        }

        // Crisp Enemy Health Bar
        if (en.hp < (en.maxHp || 45)) {
          ctx.fillStyle = "#09070e";
          ctx.fillRect(-14, -22, 28, 4);
          ctx.fillStyle = "#dc2626";
          ctx.fillRect(-14, -22, 28 * Math.max(0, en.hp / (en.maxHp || 45)), 4);
        }
        ctx.restore();
      },

      drawLowPolyPrism: function(ctx, cx, cy, r, zBase, zTop, sides, color, lightX, lightY, rot) {
        const apex = this.project(cx, cy, zTop);
        const dist = Math.hypot(lightX - cx, lightY - cy) || 1;
        const atten = Math.max(0.35, Math.min(1.45, 240 / (dist + 50)));
        const lx = (lightX - cx) / dist, ly = (lightY - cy) / dist;

        for (let i = 0; i < sides; i++) {
          const a1 = (rot || 0) + (i / sides) * Math.PI * 2;
          const a2 = (rot || 0) + ((i + 1) / sides) * Math.PI * 2;
          const v1 = this.project(cx + Math.cos(a1) * r, cy + Math.sin(a1) * r, zBase);
          const v2 = this.project(cx + Math.cos(a2) * r, cy + Math.sin(a2) * r, zBase);
          const midA = (a1 + a2) * 0.5;
          const dot = Math.max(0.22, Math.cos(midA) * lx + Math.sin(midA) * ly + 0.45);
          ctx.fillStyle = this.shadeHex(color, dot * atten);
          ctx.beginPath();
          ctx.moveTo(v1.x, v1.y);
          ctx.lineTo(v2.x, v2.y);
          ctx.lineTo(apex.x, apex.y);
          ctx.closePath();
          ctx.fill();
          ctx.strokeStyle = "rgba(15, 23, 42, 0.65)";
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    };

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
        { name: "PILLARED OSSUARY", floor: "#120e1a", wall: "#2d233d", accent: "#a855f7" },
        { name: "VERDIGRIS CISTERN", floor: "#0b1513", wall: "#1d3530", accent: "#10b981" },
        { name: "BLOOD SANCTUM", floor: "#170b10", wall: "#3d1a24", accent: "#dc2626" },
        { name: "DOOM CATACOMB", floor: "#14110d", wall: "#362d20", accent: "#eab308" },
        { name: "OBSIDIAN HALL", floor: "#0e0c16", wall: "#252136", accent: "#f59e0b" }
      ];
      const arch = archetypes[archetypeIdx];

      const braziers = [
        { x: 135, y: 125, lit: true, r: 14 },
        { x: 665, y: 125, lit: true, r: 14 },
        { x: 135, y: 495, lit: this._seedHash(rx, ry, 2) > 0.2, r: 14 },
        { x: 665, y: 495, lit: this._seedHash(rx, ry, 3) > 0.2, r: 14 }
      ];

      const pillars = [];
      if (archetypeIdx === 0 || archetypeIdx === 4) {
        pillars.push({ x: 245, y: 205, w: 38, h: 38 }, { x: 517, y: 205, w: 38, h: 38 });
        pillars.push({ x: 245, y: 385, w: 38, h: 38 }, { x: 517, y: 385, w: 38, h: 38 });
      } else if (archetypeIdx === 2) {
        pillars.push({ x: 374, y: 284, w: 52, h: 52, isAltar: true });
      } else if (archetypeIdx === 3) {
        pillars.push({ x: 295, y: 230, w: 42, h: 42 }, { x: 465, y: 365, w: 42, h: 42 });
      }

      const acidPools = [];
      if (archetypeIdx === 1) {
        acidPools.push({ x: 240, y: 260, r: 46 }, { x: 560, y: 360, r: 50 });
      }

      const bonePiles = [];
      for (let i = 0; i < 4; i++) {
        const bx = 155 + this._seedHash(rx, ry, 10 + i) * 490;
        const by = 145 + this._seedHash(rx, ry, 20 + i) * 330;
        if (Math.hypot(bx - 400, by - 310) > 80) {
          bonePiles.push({ x: bx, y: by, hp: 1, r: 14 });
        }
      }

      const enemies = [];
      const isStart = (rx === 0 && ry === 0);
      const count = isStart ? 2 : 3 + (Math.abs(rx) + Math.abs(ry)) % 3;
      for (let i = 0; i < count; i++) {
        const ex = 165 + this._seedHash(rx, ry, 30 + i) * 470;
        const ey = 145 + this._seedHash(rx, ry, 40 + i) * 330;
        if (Math.hypot(ex - 400, ey - 310) < 95) continue;
        const kind = (i % 2 === 0) ? "SKELETON" : "SLIME";
        enemies.push({
          type: kind,
          x: ex, y: ey, vx: 0, vy: 0,
          r: kind === "SKELETON" ? 15 : 17,
          hp: kind === "SKELETON" ? 45 : 35,
          maxHp: kind === "SKELETON" ? 45 : 35,
          speed: kind === "SKELETON" ? 72 : 52,
          stagger: 0, color: kind === "SKELETON" ? "#cbd5e1" : "#10b981"
        });
      }

      w.rooms[key] = { rx, ry, arch, braziers, pillars, acidPools, bonePiles, enemies, bloodStains: [] };
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

    p.torchLevel = Math.max(30, (p.torchLevel || 100) - dt * 0.40);
    for (let i = 0; i < (w.braziers || []).length; i++) {
      const b = w.braziers[i];
      if (b.lit && Math.hypot(p.x - b.x, p.y - b.y) < 80) {
        p.torchLevel = Math.min(100, p.torchLevel + dt * 20);
      }
    }

    if (p.stamRegenDelay > 0) p.stamRegenDelay -= dt;
    else p.stamina = Math.min(p.maxStamina || 100, (p.stamina || 0) + 35 * dt);

    let dx = (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
    let dy = (keys.down ? 1 : 0) - (keys.up ? 1 : 0);
    const len = Math.hypot(dx, dy);
    if (len > 0) {
      dx /= len; dy /= len;
      if (p.attackTimer <= 0) p.facingAngle = Math.atan2(dy, dx);
    }

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

    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      const cx = pl.x + pl.w / 2, cy = pl.y + pl.h / 2;
      const ox = p.x - cx, oy = p.y - cy;
      const minDist = pl.w / 2 + 13;
      if (Math.abs(ox) < minDist && Math.abs(oy) < minDist) {
        if (Math.abs(ox) > Math.abs(oy)) p.x = cx + Math.sign(ox) * minDist;
        else p.y = cy + Math.sign(oy) * minDist;
      }
    }

    const inHorizDoor = (p.y > 265 && p.y < 365);
    const inVertDoor = (p.x > 350 && p.x < 450);
    if (p.x < 64 && inHorizDoor) { p.x = 724; this.loadRoom(state, w.currentRoom.x - 1, w.currentRoom.y); return; }
    else if (p.x > 736 && inHorizDoor) { p.x = 76; this.loadRoom(state, w.currentRoom.x + 1, w.currentRoom.y); return; }
    else if (p.y < 82 && inVertDoor) { p.y = 532; this.loadRoom(state, w.currentRoom.x, w.currentRoom.y - 1); return; }
    else if (p.y > 548 && inVertDoor) { p.y = 94; this.loadRoom(state, w.currentRoom.x, w.currentRoom.y + 1); return; }

    p.x = Math.max(66, Math.min(734, p.x));
    p.y = Math.max(84, Math.min(546, p.y));

    for (let i = (w.bonePiles || []).length - 1; i >= 0; i--) {
      const bp = w.bonePiles[i];
      if (Math.hypot(p.x - bp.x, p.y - bp.y) < 26 && (p.attackTimer > 0 || p.dashTimer > 0)) {
        w.bonePiles.splice(i, 1);
        p.gold = (p.gold || 0) + 5;
        p.torchLevel = Math.min(100, p.torchLevel + 8);
        w.floatingTexts.push({ text: "+5G // EMBER", x: bp.x, y: bp.y - 10, color: "#eab308", life: 0.9 });
      }
    }

    const enemies = w.enemies || [];
    for (let i = enemies.length - 1; i >= 0; i--) {
      const en = enemies[i];
      if (en.hp <= 0) {
        w.bloodStains.push({ x: en.x, y: en.y, r: 16 + Math.random() * 8, color: en.type === "SLIME" ? "rgba(16,185,129,0.35)" : "rgba(185,28,28,0.45)" });
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
        if (dist < 290) {
          en.x += (edx / dist) * en.speed * dt;
          en.y += (edy / dist) * en.speed * dt;
        }
        if (dist < en.r + 13) {
          if (p.dashTimer > 0 && p.dashTimer > 0.05) {
            en.stagger = 1.2;
            en.vx = -(edx / dist) * 250;
            en.vy = -(edy / dist) * 250;
            w.floatingTexts.push({ text: "⚔ PARRIED! ⚔", x: p.x, y: p.y - 24, color: "#eab308", life: 0.9 });
            engine.emit("PARRY_SUCCESS", { enemy: en, x: p.x, y: p.y });
          } else if (p.invuln <= 0) {
            p.health = Math.max(0, (p.health || 5) - 1);
            p.shields = p.health;
            p.invuln = 1.1;
            w.cameraShake = 7;
            w.floatingTexts.push({ text: "-1 HP", x: p.x, y: p.y - 20, color: "#dc2626", life: 0.8 });
          }
        }
      }
      en.x = Math.max(72, Math.min(728, en.x));
      en.y = Math.max(90, Math.min(540, en.y));
    }

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
    const reach = p.weaponReach || 60;
    const cleaveDmg = p.weaponDamage || 22;
    const enemies = w.enemies || [];
    const swingArc = p.whirlwindCleave ? Math.PI * 2 : 1.4;

    for (let i = 0; i < enemies.length; i++) {
      const en = enemies[i];
      const dx = en.x - p.x, dy = en.y - p.y;
      const dist = Math.hypot(dx, dy);
      if (dist <= reach + en.r) {
        const angToEnemy = Math.atan2(dy, dx);
        let diff = Math.abs(angToEnemy - p.facingAngle);
        if (diff > Math.PI) diff = Math.PI * 2 - diff;
        if (diff <= swingArc) {
          const isCrit = en.stagger > 0;
          const dmg = isCrit ? Math.floor(cleaveDmg * 1.6) : cleaveDmg;
          en.hp -= dmg;
          en.stagger = 0.42;
          en.vx = Math.cos(angToEnemy) * 210;
          en.vy = Math.sin(angToEnemy) * 210;
          p.hitStop = 0.03;
          w.cameraShake = 3.5;
          w.floatingTexts.push({
            text: isCrit ? `CRIT ${dmg}!` : `${dmg}`,
            x: en.x, y: en.y - 16,
            color: isCrit ? "#eab308" : "#f8fafc", life: 0.75
          });
          for (let k = 0; k < 6; k++) {
            const a = angToEnemy + (Math.random() - 0.5) * 1.2;
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
    const p = state.player, w = state.world, lp = w.lowPoly;
    const roomKey = `${w.currentRoom.x},${w.currentRoom.y}`;
    const room = (w.rooms && w.rooms[roomKey]) || { arch: { name: "CRYPT", floor: "#120e1a", wall: "#2d233d", accent: "#a855f7" }, acidPools: [] };

    ctx.save();
    if (w.cameraShake > 0.3 && !state.paused) {
      ctx.translate((Math.random() - 0.5) * Math.min(w.cameraShake, 6), (Math.random() - 0.5) * Math.min(w.cameraShake, 6));
    }

    // 1. Render Faceted Low-Poly Stone Slabs & Distance-Shaded Cobblestones
    ctx.fillStyle = room.arch.floor;
    ctx.fillRect(0, 36, 800, 564);

    for (let gx = 60; gx < 740; gx += 40) {
      for (let gy = 76; gy < 552; gy += 40) {
        const dLight = Math.hypot((gx + 20) - p.x, (gy + 20) - p.y);
        const lit = Math.max(0.06, Math.min(0.32, 1 - dLight / 340));
        // Beveled 3D stone slab top-left highlight & bottom-right shadow
        ctx.strokeStyle = `rgba(226, 232, 240, ${lit * 0.45})`;
        ctx.beginPath();
        ctx.moveTo(gx + 1, gy + 38); ctx.lineTo(gx + 1, gy + 1); ctx.lineTo(gx + 38, gy + 1);
        ctx.stroke();
        ctx.strokeStyle = "rgba(4, 2, 8, 0.75)";
        ctx.beginPath();
        ctx.moveTo(gx + 39, gy + 1); ctx.lineTo(gx + 39, gy + 39); ctx.lineTo(gx + 1, gy + 39);
        ctx.stroke();
      }
    }

    // 2. Render Dynamic Ray-Cast Shadow Volumes Behind Pillars (From Player Torch!)
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      const cx = pl.x + pl.w * 0.5, cy = pl.y + pl.h * 0.5;
      const ang = Math.atan2(cy - p.y, cx - p.x);
      const perp = ang + Math.PI * 0.5;
      const r = pl.w * 0.52;
      const c1x = cx + Math.cos(perp) * r, c1y = cy + Math.sin(perp) * r;
      const c2x = cx - Math.cos(perp) * r, c2y = cy - Math.sin(perp) * r;
      const s1x = c1x + Math.cos(ang + 0.14) * 360, s1y = c1y + Math.sin(ang + 0.14) * 360;
      const s2x = c2x + Math.cos(ang - 0.14) * 360, s2y = c2y + Math.sin(ang - 0.14) * 360;

      ctx.fillStyle = "rgba(4, 2, 9, 0.52)";
      ctx.beginPath();
      ctx.moveTo(c1x, c1y); ctx.lineTo(c2x, c2y);
      ctx.lineTo(s2x, s2y); ctx.lineTo(s1x, s1y);
      ctx.closePath();
      ctx.fill();
    }

    // Acid Pools & Blood Stains
    for (let i = 0; i < (room.acidPools || []).length; i++) {
      const ap = room.acidPools[i];
      const ag = ctx.createRadialGradient(ap.x, ap.y, 6, ap.x, ap.y, ap.r);
      ag.addColorStop(0, "rgba(52, 211, 153, 0.55)");
      ag.addColorStop(0.7, "rgba(16, 185, 129, 0.28)");
      ag.addColorStop(1, "rgba(6, 78, 59, 0)");
      ctx.fillStyle = ag;
      ctx.beginPath(); ctx.arc(ap.x, ap.y, ap.r, 0, Math.PI * 2); ctx.fill();
    }
    for (let i = 0; i < (w.bloodStains || []).length; i++) {
      const bs = w.bloodStains[i];
      ctx.fillStyle = bs.color;
      ctx.beginPath(); ctx.arc(bs.x, bs.y, bs.r, 0, Math.PI * 2); ctx.fill();
    }

    // 3. Render 2.5D Extruded Low-Poly Outer Dungeon Walls & Carved Archways
    const wc = room.arch.wall || "#2d233d";
    lp.drawExtrudedBox(ctx, 40, 52, 310, 24, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 450, 52, 310, 24, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 40, 550, 310, 24, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 450, 550, 310, 24, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 38, 76, 22, 189, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 38, 365, 22, 185, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 740, 76, 22, 189, 34, wc, "#0f172a", p.x, p.y);
    lp.drawExtrudedBox(ctx, 740, 365, 22, 185, 34, wc, "#0f172a", p.x, p.y);

    // 4. Render 2.5D Extruded Low-Poly Pillars, Obelisks & Blood Altars
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      const pColor = pl.isAltar ? "#7f1d1d" : wc;
      lp.drawExtrudedBox(ctx, pl.x, pl.y, pl.w, pl.h, pl.isAltar ? 28 : 44, pColor, pl.isAltar ? "#ef4444" : "#1e293b", p.x, p.y);
      if (pl.isAltar) {
        lp.drawLowPolyPrism(ctx, pl.x + pl.w * 0.5, pl.y + pl.h * 0.5, 14, 28, 54, 4, "#dc2626", p.x, p.y, performance.now() * 0.002);
      }
    }

    // 5. Render Low-Poly Bone Pyramids & Flickering 3D Braziers
    for (let i = 0; i < (w.bonePiles || []).length; i++) {
      const bp = w.bonePiles[i];
      lp.drawLowPolyPrism(ctx, bp.x, bp.y, 13, 0, 18, 5, "#cbd5e1", p.x, p.y, i);
    }

    const flicker = Math.sin(performance.now() * 0.014) * 6;
    for (let i = 0; i < (w.braziers || []).length; i++) {
      const b = w.braziers[i];
      lp.drawLowPolyPrism(ctx, b.x, b.y, 13, 0, 16, 6, "#475569", p.x, p.y, 0);
      if (b.lit) {
        const bg = ctx.createRadialGradient(b.x, b.y, 4, b.x, b.y, 110 + flicker);
        bg.addColorStop(0, "rgba(245, 158, 11, 0.34)");
        bg.addColorStop(0.5, "rgba(217, 119, 6, 0.14)");
        bg.addColorStop(1, "rgba(245, 158, 11, 0)");
        ctx.fillStyle = bg;
        ctx.beginPath(); ctx.arc(b.x, b.y, 110 + flicker, 0, Math.PI * 2); ctx.fill();
        lp.drawLowPolyPrism(ctx, b.x, b.y, 8, 12, 32 + flicker * 0.5, 5, "#f59e0b", b.x, b.y - 10, performance.now() * 0.006);
      }
    }

    // 6. Render Articulated Dark-Fantasy Enemies (Skeletons, Phalanxes, Necromancers, Fungoid Horrors)
    const nowSec = performance.now() * 0.001;
    for (let i = 0; i < (w.enemies || []).length; i++) {
      lp.drawArticulatedEnemy(ctx, w.enemies[i], p, nowSec, i);
    }

    // 7. Render 2.5D Low-Poly Delver Mesh & Weapon Cleave Arc
    ctx.save();
    if (p.invuln > 0 && Math.floor(performance.now() / 60) % 2 === 0) ctx.globalAlpha = 0.45;

    if (p.attackTimer > 0) {
      const reach = p.weaponReach || 60;
      const arcSpan = p.whirlwindCleave ? Math.PI : 0.95;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.facingAngle);
      ctx.strokeStyle = p.weaponGlow || p.classColor || "#eab308";
      ctx.shadowBlur = 14;
      ctx.shadowColor = ctx.strokeStyle;
      ctx.lineWidth = 7;
      ctx.beginPath(); ctx.arc(0, 0, reach, -arcSpan, arcSpan); ctx.stroke();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(0, 0, reach - 5, -arcSpan * 0.9, arcSpan * 0.9); ctx.stroke();
      ctx.restore();
    }

    // Delver Multi-Part Articulated Dark-Fantasy Rig
    lp.drawArticulatedDelver(ctx, p, nowSec);
    ctx.restore();

    // Particles & Floating Texts
    for (let i = 0; i < w.particles.length; i++) {
      const pt = w.particles[i];
      ctx.fillStyle = pt.color || "#dc2626";
      ctx.fillRect(pt.x - 2, pt.y - 2, 4, 4);
    }
    // UI/UX Spatial De-Collision for Floating Combat & Lore Texts
    ctx.font = "bold 11px monospace";
    ctx.textAlign = "center";
    if (w.floatingTexts.length > 8) w.floatingTexts.splice(0, w.floatingTexts.length - 8);
    for (let i = 0; i < w.floatingTexts.length; i++) {
      const ft = w.floatingTexts[i];
      let drawY = ft.y;
      for (let j = 0; j < i; j++) {
        const prev = w.floatingTexts[j];
        if (Math.abs((prev.x || 0) - (ft.x || 0)) < 75 && Math.abs((prev._drawY || prev.y) - drawY) < 15) {
          drawY = (prev._drawY || prev.y) - 16;
        }
      }
      ft._drawY = drawY;
      ctx.fillStyle = "rgba(5, 3, 10, 0.82)";
      const tw = ctx.measureText(ft.text || "").width + 8;
      ctx.fillRect(ft.x - tw * 0.5, drawY - 10, tw, 14);
      ctx.fillStyle = ft.color || "#f8fafc";
      ctx.fillText(ft.text, ft.x, drawY);
    }

    // 8. Chiaroscuro Multi-Stop Torchlight & Stoner-Metal Color Grading Pass
    const torchR = 180 + (p.torchLevel || 100) * 1.45 + flicker;
    const grad = ctx.createRadialGradient(p.x, p.y, 35, p.x, p.y, torchR);
    if (p.uvTorch) {
      grad.addColorStop(0, "rgba(168, 85, 247, 0.12)");
      grad.addColorStop(0.55, "rgba(18, 9, 36, 0.42)");
      grad.addColorStop(1, "rgba(4, 2, 10, 0.80)");
    } else {
      grad.addColorStop(0, "rgba(245, 158, 11, 0.10)");
      grad.addColorStop(0.55, "rgba(16, 8, 24, 0.40)");
      grad.addColorStop(1, "rgba(5, 3, 10, 0.78)");
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 36, 800, 564);

    ctx.restore(); // End World Camera Shake

    // 9. Rock-Steady Top Gothic Status Ribbon (Zero Overlaps even at 8+ MaxHP!)
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = "#08060d";
    ctx.fillRect(0, 0, 800, 36);
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, 36); ctx.lineTo(800, 36); ctx.stroke();

    const maxH = p.maxHealth || 5;
    const pipW = Math.min(12, Math.floor(96 / maxH) - 3);
    for (let i = 0; i < maxH; i++) {
      ctx.fillStyle = i < (p.health || 0) ? "#dc2626" : "#1e293b";
      ctx.fillRect(10 + i * (pipW + 3), 11, pipW, 14);
      ctx.strokeStyle = "#fca5a5";
      ctx.lineWidth = 1;
      ctx.strokeRect(10 + i * (pipW + 3), 11, pipW, 14);
    }

    // Stamina Bar (x: 118..194)
    ctx.fillStyle = "#1e293b"; ctx.fillRect(118, 12, 76, 11);
    ctx.fillStyle = "#10b981"; ctx.fillRect(118, 12, 76 * Math.max(0, (p.stamina || 0) / (p.maxStamina || 100)), 11);

    // Torch Bar (x: 202..262)
    ctx.fillStyle = "#1e293b"; ctx.fillRect(202, 12, 60, 11);
    ctx.fillStyle = p.uvTorch ? "#a855f7" : "#f59e0b";
    ctx.fillRect(202, 12, 60 * Math.max(0, (p.torchLevel || 0) / 100), 11);

    ctx.font = "bold 11px monospace";
    ctx.textAlign = "left";
    ctx.fillStyle = "#eab308";
    ctx.fillText(`G:${p.gold || 0}`, 270, 22);
    ctx.fillStyle = "#a855f7";
    ctx.fillText(`STRESS:${Math.floor(p.stress || 0)}%`, 322, 22);
    ctx.fillStyle = "#cbd5e1";
    const shortRoom = (w.roomName || "CRYPT").slice(0, 16);
    ctx.fillText(`${shortRoom} [${w.currentRoom.x},${w.currentRoom.y}] D:${w.depth || 1}`, 405, 22);
    ctx.fillStyle = "#f59e0b";
    ctx.textAlign = "right";
    ctx.fillText("[SPC]ATK [SHF/E]ACT", 792, 22);
    ctx.restore();
  }
});
