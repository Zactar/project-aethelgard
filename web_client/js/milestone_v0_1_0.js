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

        // Articulated Oversized Doom-Blade / War-Scythe (Full 210-degree sweeping arc during attack!)
        ctx.save();
        const atkProg = p.attackTimer > 0 ? (1.0 - p.attackTimer / 0.24) : -1;
        const swingAngle = atkProg >= 0 ? (-1.75 + atkProg * 3.5) : 0.55;
        ctx.rotate(p.facingAngle + swingAngle);

        // Pommel & Long Two-Handed Grip
        ctx.fillStyle = "#eab308";
        ctx.fillRect(2, -2, 8, 4);
        // Spiked Cruciform Crossguard
        ctx.fillStyle = "#94a3b8";
        ctx.beginPath();
        ctx.moveTo(9, -10); ctx.lineTo(13, 0); ctx.lineTo(9, 10); ctx.lineTo(7, 0);
        ctx.closePath();
        ctx.fill();
        // Colossal Notched Broad-Blade
        const bladeLen = (p.weaponReach || 62) * 0.62;
        ctx.fillStyle = "#e2e8f0";
        ctx.beginPath();
        ctx.moveTo(11, -4.5);
        ctx.lineTo(11 + bladeLen * 0.75, -6);
        ctx.lineTo(11 + bladeLen, 0);
        ctx.lineTo(11 + bladeLen * 0.75, 6);
        ctx.lineTo(11, 4.5);
        ctx.closePath();
        ctx.fill();
        // Glowing Blood/Rune Fuller down the blade spine
        ctx.fillStyle = p.weaponGlow || col;
        ctx.fillRect(13, -1.8, bladeLen * 0.78, 3.6);
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

  _edgeOpen: function(x1, y1, x2, y2) {
    // Origin (0,0) always connects North, East, West so player has 3 initial paths
    if ((x1 === 0 && y1 === 0) || (x2 === 0 && y2 === 0)) {
      const ox = x1 === 0 && y1 === 0 ? x2 : x1;
      const oy = x1 === 0 && y1 === 0 ? y2 : y1;
      if (oy === 1 && ox === 0) return false; // South wall sealed at start for dramatic throne backdrop
      return true;
    }
    const ax = Math.min(x1, x2), ay = Math.min(y1, y2);
    const bx = Math.max(x1, x2), by = Math.max(y1, y2);
    const h = this._seedHash(ax * 31 + bx, ay * 37 + by, 77);
    if (h > 0.34) return true;
    // Guarantee every room has at least 2 open doors (no unreachable islands)
    return ((Math.abs(ax + ay) % 2) === 0);
  },

  _getRoomDoors: function(rx, ry) {
    const d = {
      N: this._edgeOpen(rx, ry, rx, ry - 1),
      S: this._edgeOpen(rx, ry, rx, ry + 1),
      W: this._edgeOpen(rx, ry, rx - 1, ry),
      E: this._edgeOpen(rx, ry, rx + 1, ry)
    };
    if (!d.N && !d.S && !d.W && !d.E) { d.N = true; d.E = true; }
    return d;
  },
  _seedHash: function(rx, ry, salt) {
    const n = Math.sin(rx * 127.1 + ry * 311.7 + salt * 74.7) * 43758.5453;
    return n - Math.floor(n);
  },

  loadRoom: function(state, rx, ry, entryDir) {
    const w = state.world, p = state.player;
    const key = `${rx},${ry}`;
    w.currentRoom = { x: rx, y: ry };
    w.visitedRooms = w.visitedRooms || {};

    if (!w.rooms[key]) {
      const doors = this._getRoomDoors(rx, ry);
      if (entryDir && !doors[entryDir]) doors[entryDir] = true;

      // Determine Room Role (1 focal gameplay theme per room -> zero clutter!)
      const roles = ["ENTRY_HALL", "ALTAR_SANCTUM", "ALCHEMY_CISTERN", "SEISMIC_FAULT", "RELIQUARY_VAULT", "OSSUARY_PASSAGE"];
      const roleIdx = (rx === 0 && ry === 0) ? 0 : (1 + Math.floor(this._seedHash(rx, ry, 5) * (roles.length - 1)));
      const role = roles[roleIdx];

      // Determine Room Shape & Architectural Footprint (7 distinct shapes & sizes!)
      let shape = "CRUCIFORM";
      if (rx === 0 && ry === 0) shape = "CRUCIFORM";
      else if (!doors.N && !doors.S && doors.E && doors.W) shape = "CORRIDOR_EW";
      else if (doors.N && doors.S && !doors.E && !doors.W) shape = "CORRIDOR_NS";
      else {
        const shapePool = ["CRUCIFORM", "CORRIDOR_EW", "CORRIDOR_NS", "L_CHAMBER", "CHASM_BRIDGE", "COMPACT_VAULT", "BASTION_HALL"];
        shape = shapePool[Math.floor(this._seedHash(rx, ry, 9) * shapePool.length)];
        // Ensure corridor shapes don't block open doors
        if (shape === "CORRIDOR_EW" && (doors.N || doors.S)) shape = "CHASM_BRIDGE";
        if (shape === "CORRIDOR_NS" && (doors.E || doors.W)) shape = "CRUCIFORM";
      }

      const themes = {
        ENTRY_HALL:      { name: "OBSIDIAN VESTIBULE", floor: "#110d18", wall: "#2b223a", accent: "#eab308" },
        ALTAR_SANCTUM:   { name: "BLOOD-ALTAR SANCTUM", floor: "#160a0f", wall: "#3d1822", accent: "#dc2626" },
        ALCHEMY_CISTERN: { name: "VERDIGRIS CISTERN", floor: "#0a1412", wall: "#1b332e", accent: "#10b981" },
        SEISMIC_FAULT:   { name: "TECTONIC FAULT CRYPT", floor: "#13100d", wall: "#332a1e", accent: "#f97316" },
        RELIQUARY_VAULT: { name: "SUNKEN RELIQUARY", floor: "#120e1c", wall: "#2f2447", accent: "#a855f7" },
        OSSUARY_PASSAGE: { name: "CATACOMB GALLERY", floor: "#0e0c14", wall: "#252033", accent: "#94a3b8" }
      };
      const arch = themes[role] || themes.OSSUARY_PASSAGE;

      // Build Extruded Interior Wall Bastions & Chasms that physically reshape the room!
      const pillars = [];
      const chasms = [];
      let bounds = { minX: 66, maxX: 734, minY: 84, maxY: 546 };

      if (shape === "CRUCIFORM") {
        // 4 massive corner stone bastions forming a Gothic Cross floorplan
        pillars.push(
          { x: 60, y: 76, w: 155, h: 115, isWall: true },
          { x: 585, y: 76, w: 155, h: 115, isWall: true },
          { x: 60, y: 435, w: 155, h: 115, isWall: true },
          { x: 585, y: 435, w: 155, h: 115, isWall: true }
        );
      } else if (shape === "CORRIDOR_EW") {
        // Narrow East-West Catacomb Tunnel
        bounds = { minX: 66, maxX: 734, minY: 205, maxY: 425 };
        pillars.push(
          { x: 60, y: 76, w: 680, h: 115, isWall: true },
          { x: 60, y: 440, w: 680, h: 110, isWall: true }
        );
      } else if (shape === "CORRIDOR_NS") {
        // Narrow North-South Ossuary Gallery
        bounds = { minX: 245, maxX: 555, minY: 84, maxY: 546 };
        pillars.push(
          { x: 60, y: 76, w: 170, h: 474, isWall: true },
          { x: 570, y: 76, w: 170, h: 474, isWall: true }
        );
      } else if (shape === "L_CHAMBER") {
        // Asymmetric L-Shaped Crypt (one giant quadrant walled off + 1 counterweight pillar)
        const quad = Math.floor(this._seedHash(rx, ry, 14) * 2);
        if (quad === 0) {
          pillars.push({ x: 60, y: 76, w: 250, h: 170, isWall: true }, { x: 520, y: 380, w: 42, h: 42 });
        } else {
          pillars.push({ x: 490, y: 76, w: 250, h: 170, isWall: true }, { x: 240, y: 380, w: 42, h: 42 });
        }
      } else if (shape === "CHASM_BRIDGE") {
        // Twin Abyssal Chasms framing a central narrow stone bridge
        chasms.push({ x: 165, y: 120, w: 165, h: 145 }, { x: 470, y: 365, w: 165, h: 145 });
        pillars.push({ x: 165, y: 120, w: 165, h: 145, isChasm: true }, { x: 470, y: 365, w: 165, h: 145, isChasm: true });
      } else if (shape === "COMPACT_VAULT") {
        // Smaller, intimate sunken chamber with thick perimeter masonry
        pillars.push(
          { x: 60, y: 76, w: 110, h: 175, isWall: true },
          { x: 60, y: 375, w: 110, h: 175, isWall: true },
          { x: 630, y: 76, w: 110, h: 175, isWall: true },
          { x: 630, y: 375, w: 110, h: 175, isWall: true }
        );
      } else if (shape === "BASTION_HALL") {
        // Central colonnade pillars
        pillars.push({ x: 270, y: 215, w: 38, h: 38 }, { x: 492, y: 215, w: 38, h: 38 });
        pillars.push({ x: 270, y: 385, w: 38, h: 38 }, { x: 492, y: 385, w: 38, h: 38 });
      }

      // Place only 2 atmospheric braziers matching the room geometry
      const braziers = shape === "CORRIDOR_EW"
        ? [{ x: 220, y: 225, lit: true, r: 12 }, { x: 580, y: 405, lit: true, r: 12 }]
        : (shape === "CORRIDOR_NS"
          ? [{ x: 275, y: 180, lit: true, r: 12 }, { x: 525, y: 440, lit: true, r: 12 }]
          : [{ x: 245, y: 155, lit: true, r: 12 }, { x: 555, y: 465, lit: this._seedHash(rx, ry, 3) > 0.2, r: 12 }]);

      // Sparse bone piles (0–2 max so floor stays clean!)
      const bonePiles = [];
      if (role === "OSSUARY_PASSAGE" || role === "ENTRY_HALL") {
        bonePiles.push({ x: 320, y: 380, hp: 1, r: 13 }, { x: 480, y: 250, hp: 1, r: 13 });
      }

      // Spawn 1–3 enemies inside valid walkable central space
      const enemies = [];
      const count = (rx === 0 && ry === 0) ? 2 : (role === "RELIQUARY_VAULT" ? 1 : 2 + (Math.abs(rx + ry) % 2));
      for (let i = 0; i < count; i++) {
        const ang = (i / count) * Math.PI * 2 + this._seedHash(rx, ry, 30 + i);
        const ex = 400 + Math.cos(ang) * 115;
        const ey = 315 + Math.sin(ang) * 75;
        const kind = (i % 2 === 0) ? "SKELETON" : "SLIME";
        enemies.push({
          type: kind, x: ex, y: ey, vx: 0, vy: 0,
          r: kind === "SKELETON" ? 15 : 17,
          hp: kind === "SKELETON" ? 45 : 35, maxHp: kind === "SKELETON" ? 45 : 35,
          speed: kind === "SKELETON" ? 72 : 52, stagger: 0, color: "#cbd5e1"
        });
      }

      w.rooms[key] = {
        rx, ry, role, shape, doors, bounds, arch, braziers, pillars, chasms,
        acidPools: role === "ALCHEMY_CISTERN" ? [{ x: 400, y: 315, r: 44 }] : [],
        bonePiles, enemies, bloodStains: []
      };
    }

    const room = w.rooms[key];
    w.visitedRooms[key] = { rx, ry, shape: room.shape, role: room.role, doors: room.doors };
    w.braziers = room.braziers;
    w.pillars = room.pillars;
    w.bonePiles = room.bonePiles;
    w.enemies = room.enemies;
    w.bloodStains = room.bloodStains;
    w.roomName = room.arch.name;
    w.roomRole = room.role;
    w.roomShape = room.shape;
    w.roomDoors = room.doors;
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
      p.attackTimer = 0.24;
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

    // AABB Collision against Rectangular Wall Bastions, Chasms & Pillars
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      const pad = 12;
      if (p.x > pl.x - pad && p.x < pl.x + pl.w + pad && p.y > pl.y - pad && p.y < pl.y + pl.h + pad) {
        const dl = Math.abs(p.x - (pl.x - pad));
        const dr = Math.abs((pl.x + pl.w + pad) - p.x);
        const dtTop = Math.abs(p.y - (pl.y - pad));
        const db = Math.abs((pl.y + pl.h + pad) - p.y);
        const m = Math.min(dl, dr, dtTop, db);
        if (m === dl) p.x = pl.x - pad;
        else if (m === dr) p.x = pl.x + pl.w + pad;
        else if (m === dtTop) p.y = pl.y - pad;
        else p.y = pl.y + pl.h + pad;
      }
    }

    // Maze Doorway Transitions (Only traverse if that direction has an open door in w.roomDoors!)
    const doors = w.roomDoors || { N: true, S: true, E: true, W: true };
    const inHorizDoor = (p.y > 265 && p.y < 365);
    const inVertDoor = (p.x > 350 && p.x < 450);
    if (doors.W && p.x < 64 && inHorizDoor) { p.x = 720; p.y = 315; this.loadRoom(state, w.currentRoom.x - 1, w.currentRoom.y, "E"); return; }
    else if (doors.E && p.x > 736 && inHorizDoor) { p.x = 80; p.y = 315; this.loadRoom(state, w.currentRoom.x + 1, w.currentRoom.y, "W"); return; }
    else if (doors.N && p.y < 82 && inVertDoor) { p.x = 400; p.y = 530; this.loadRoom(state, w.currentRoom.x, w.currentRoom.y - 1, "S"); return; }
    else if (doors.S && p.y > 548 && inVertDoor) { p.x = 400; p.y = 96; this.loadRoom(state, w.currentRoom.x, w.currentRoom.y + 1, "N"); return; }

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
    for (let s = -3; s <= 3; s++) {
      const sa = p.facingAngle + s * 0.28;
      w.particles.push({
        x: p.x + Math.cos(sa) * (reach * 0.75),
        y: p.y + Math.sin(sa) * (reach * 0.75),
        vx: Math.cos(sa) * 140, vy: Math.sin(sa) * 140,
        color: p.weaponGlow || p.classColor || "#eab308", life: 0.22
      });
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

    // 1. Render Stoner-Metal Album Crypt Floor: Irregular Weathered Flagstones & Occult Ritual Sigil
    ctx.fillStyle = room.arch.floor;
    ctx.fillRect(0, 36, 800, 564);

    // Staggered, weathered stone masonry blocks (offset rows + procedural diagonal fracture lines)
    for (let row = 0; row < 8; row++) {
      const gy = 76 + row * 60;
      const rowOffset = (row % 2) * 45;
      for (let gx = 60 - rowOffset; gx < 740; gx += 90) {
        const cx = gx + 45, cy = gy + 30;
        const dLight = Math.hypot(cx - p.x, cy - p.y);
        const lit = Math.max(0.04, Math.min(0.28, 1 - dLight / 320));
        ctx.strokeStyle = "rgba(3, 2, 6, 0.85)";
        ctx.lineWidth = 2;
        ctx.strokeRect(Math.max(60, gx), gy, Math.min(90, 740 - gx), 60);
        ctx.strokeStyle = `rgba(245, 158, 11, ${lit * 0.32})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(gx + 8, gy + 14);
        ctx.lineTo(gx + 28, gy + 26);
        ctx.lineTo(gx + 22, gy + 44);
        ctx.stroke();
      }
    }

    // Etched Occult Ritual Sigil (Drawn ONLY in ALTAR_SANCTUM or RELIQUARY_VAULT rooms so floors vary!)
    if (room.role === "ALTAR_SANCTUM" || room.role === "RELIQUARY_VAULT") {
      ctx.save();
      ctx.translate(400, 315);
      ctx.rotate(performance.now() * 0.00015);
      ctx.strokeStyle = room.arch.accent || "#dc2626";
      ctx.globalAlpha = 0.24;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(0, 0, 110, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath();
      for (let k = 0; k < 6; k++) {
        const a = (k * 4 * Math.PI) / 5 - Math.PI / 2;
        if (k === 0) ctx.moveTo(Math.cos(a) * 110, Math.sin(a) * 110);
        else ctx.lineTo(Math.cos(a) * 110, Math.sin(a) * 110);
      }
      ctx.stroke();
      ctx.restore();
    }

    // 2. Render Dynamic Ray-Cast Shadow Volumes (Only for compact freestanding pillars, not giant wall blocks)
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      if (pl.isWall || pl.isChasm) continue;
      const cx = pl.x + pl.w * 0.5, cy = pl.y + pl.h * 0.5;
      const ang = Math.atan2(cy - p.y, cx - p.x);
      const perp = ang + Math.PI * 0.5;
      const r = pl.w * 0.52;
      ctx.fillStyle = "rgba(4, 2, 9, 0.50)";
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(perp) * r, cy + Math.sin(perp) * r);
      ctx.lineTo(cx - Math.cos(perp) * r, cy - Math.sin(perp) * r);
      ctx.lineTo(cx - Math.cos(perp) * r + Math.cos(ang - 0.14) * 320, cy - Math.sin(perp) * r + Math.sin(ang - 0.14) * 320);
      ctx.lineTo(cx + Math.cos(perp) * r + Math.cos(ang + 0.14) * 320, cy + Math.sin(perp) * r + Math.sin(ang + 0.14) * 320);
      ctx.closePath();
      ctx.fill();
    }

    for (let i = 0; i < (room.acidPools || []).length; i++) {
      const ap = room.acidPools[i];
      const ag = ctx.createRadialGradient(ap.x, ap.y, 6, ap.x, ap.y, ap.r);
      ag.addColorStop(0, "rgba(52, 211, 153, 0.55)");
      ag.addColorStop(1, "rgba(6, 78, 59, 0)");
      ctx.fillStyle = ag;
      ctx.beginPath(); ctx.arc(ap.x, ap.y, ap.r, 0, Math.PI * 2); ctx.fill();
    }
    for (let i = 0; i < (w.bloodStains || []).length; i++) {
      const bs = w.bloodStains[i];
      ctx.fillStyle = bs.color;
      ctx.beginPath(); ctx.arc(bs.x, bs.y, bs.r, 0, Math.PI * 2); ctx.fill();
    }

    // 3. Render 2.5D Extruded Outer Walls & Maze Doorways (Sealed directions render as solid stone!)
    const wc = room.arch.wall || "#2d233d";
    const doors = room.doors || { N: true, S: true, E: true, W: true };
    if (doors.N) {
      lp.drawExtrudedBox(ctx, 40, 52, 310, 24, 34, wc, "#09070e", p.x, p.y);
      lp.drawExtrudedBox(ctx, 450, 52, 310, 24, 34, wc, "#09070e", p.x, p.y);
      ctx.fillStyle = "rgba(245, 158, 11, 0.22)"; ctx.fillRect(352, 56, 96, 16);
    } else {
      lp.drawExtrudedBox(ctx, 40, 52, 720, 24, 34, wc, "#09070e", p.x, p.y);
    }
    if (doors.S) {
      lp.drawExtrudedBox(ctx, 40, 550, 310, 24, 34, wc, "#09070e", p.x, p.y);
      lp.drawExtrudedBox(ctx, 450, 550, 310, 24, 34, wc, "#09070e", p.x, p.y);
      ctx.fillStyle = "rgba(245, 158, 11, 0.22)"; ctx.fillRect(352, 554, 96, 16);
    } else {
      lp.drawExtrudedBox(ctx, 40, 550, 720, 24, 34, wc, "#09070e", p.x, p.y);
    }
    if (doors.W) {
      lp.drawExtrudedBox(ctx, 38, 76, 22, 189, 34, wc, "#09070e", p.x, p.y);
      lp.drawExtrudedBox(ctx, 38, 365, 22, 185, 34, wc, "#09070e", p.x, p.y);
      ctx.fillStyle = "rgba(245, 158, 11, 0.22)"; ctx.fillRect(42, 267, 16, 96);
    } else {
      lp.drawExtrudedBox(ctx, 38, 76, 22, 474, 34, wc, "#09070e", p.x, p.y);
    }
    if (doors.E) {
      lp.drawExtrudedBox(ctx, 740, 76, 22, 189, 34, wc, "#09070e", p.x, p.y);
      lp.drawExtrudedBox(ctx, 740, 365, 22, 185, 34, wc, "#09070e", p.x, p.y);
      ctx.fillStyle = "rgba(245, 158, 11, 0.22)"; ctx.fillRect(742, 267, 16, 96);
    } else {
      lp.drawExtrudedBox(ctx, 740, 76, 22, 474, 34, wc, "#09070e", p.x, p.y);
    }

    // 4. Render 2.5D Extruded Wall Bastions, Abyssal Chasms & Freestanding Columns
    for (let i = 0; i < (w.pillars || []).length; i++) {
      const pl = w.pillars[i];
      if (pl.isChasm) {
        ctx.fillStyle = "#030206";
        ctx.fillRect(pl.x, pl.y, pl.w, pl.h);
        ctx.strokeStyle = "#334155";
        ctx.lineWidth = 2;
        ctx.strokeRect(pl.x, pl.y, pl.w, pl.h);
      } else {
        const zH = pl.isWall ? 34 : 44;
        lp.drawExtrudedBox(ctx, pl.x, pl.y, pl.w, pl.h, zH, wc, "#09070e", p.x, p.y);
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

    // Defer Enemies, Delver, Torchlight Shader, Top HUD & Cartography Minimap to Post-World Pass
    // so v0.2.0..v0.9.0 floor hazards/props render UNDERNEATH the player, torchlight, and UI!
    ctx.restore();
  },

  renderPostWorldPass: function(ctx, state) {
    const p = state.player, w = state.world, lp = w.lowPoly;
    const flicker = Math.sin(performance.now() * 0.014) * 6;
    ctx.save();
    if (w.cameraShake > 0.3 && !state.paused) {
      ctx.translate((Math.random() - 0.5) * Math.min(w.cameraShake, 6), (Math.random() - 0.5) * Math.min(w.cameraShake, 6));
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
      const reach = p.weaponReach || 64;
      const prog = 1.0 - (p.attackTimer / 0.24);
      const arcSpan = p.whirlwindCleave ? Math.PI : 1.25;
      const col = p.weaponGlow || p.classColor || "#eab308";

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.facingAngle);

      // Outer Tapered Crescent Smear Polygon (Thick leading edge -> razor tail)
      ctx.fillStyle = col;
      ctx.shadowBlur = 18;
      ctx.shadowColor = col;
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      const steps = 16;
      for (let s = 0; s <= steps; s++) {
        const u = s / steps;
        const a = -arcSpan + u * (arcSpan * 2);
        const rOut = reach + Math.sin(u * Math.PI) * 10;
        const px = Math.cos(a) * rOut, py = Math.sin(a) * rOut;
        if (s === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      for (let s = steps; s >= 0; s--) {
        const u = s / steps;
        const a = -arcSpan + u * (arcSpan * 2);
        const thickness = Math.sin(u * Math.PI) * 26 * (1.1 - prog * 0.4);
        const rIn = Math.max(12, reach - thickness);
        ctx.lineTo(Math.cos(a) * rIn, Math.sin(a) * rIn);
      }
      ctx.closePath();
      ctx.fill();

      // White-Hot Inner Edge Core & Jagged Motion Spikes
      ctx.fillStyle = "#ffffff";
      ctx.globalAlpha = 0.92;
      ctx.beginPath();
      ctx.arc(0, 0, reach + 2, -arcSpan * 0.75, arcSpan * 0.85);
      ctx.arc(0, 0, reach - 7, arcSpan * 0.85, -arcSpan * 0.75, true);
      ctx.closePath();
      ctx.fill();
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
    if (w.quest) {
      ctx.textAlign = "left";
      ctx.font = "bold 11px monospace";
      ctx.fillStyle = w.quest.completed ? "#10b981" : "#eab308";
      const qStatus = w.quest.completed ? "COMPLETED" : `[${w.quest.progress}/${w.quest.target}]`;
      ctx.fillText(`⚔ OSR QUEST: ${w.quest.title} ${qStatus}  |  PACT: ${w.quest.alignment}`, 14, 52);
    }
    ctx.restore();

    // 10. Darkened Cartographer's Parchment Inset Minimap (Reveals Procedural Maze & Room Shapes!)
    if (!state.paused && !state.gameOver) {
      ctx.save();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      const mx = 656, my = 44, mw = 132, mh = 102;

      // Aged Burnt-Umber Parchment Background & Ink Vignette
      const pGrad = ctx.createRadialGradient(mx + mw * 0.5, my + mh * 0.5, 10, mx + mw * 0.5, my + mh * 0.5, 85);
      pGrad.addColorStop(0, "rgba(42, 31, 21, 0.92)");
      pGrad.addColorStop(1, "rgba(18, 13, 9, 0.96)");
      ctx.fillStyle = pGrad;
      ctx.fillRect(mx, my, mw, mh);

      // Faint Cartographer Latitude/Longitude Ink Grid
      ctx.strokeStyle = "rgba(180, 140, 85, 0.12)";
      ctx.lineWidth = 1;
      for (let gx = mx + 16; gx < mx + mw; gx += 16) {
        ctx.beginPath(); ctx.moveTo(gx, my); ctx.lineTo(gx, my + mh); ctx.stroke();
      }
      for (let gy = my + 16; gy < my + mh; gy += 16) {
        ctx.beginPath(); ctx.moveTo(mx, gy); ctx.lineTo(mx + mw, gy); ctx.stroke();
      }

      // Double-Rimmed Ornate Parchment Frame
      ctx.strokeStyle = "#785832";
      ctx.lineWidth = 2;
      ctx.strokeRect(mx, my, mw, mh);
      ctx.strokeStyle = "rgba(217, 175, 110, 0.35)";
      ctx.lineWidth = 1;
      ctx.strokeRect(mx + 3, my + 3, mw - 6, mh - 6);

      // Render Discovered Rooms & Unexplored Neighboring '?' Fog around Current Room
      const curX = w.currentRoom.x, curY = w.currentRoom.y;
      const centerX = mx + mw * 0.5, centerY = my + mh * 0.5 + 4;
      const cellStep = 22;
      const visited = w.visitedRooms || {};

      for (let dy = -2; dy <= 2; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
          const rx = curX + dx, ry = curY + dy;
          const rKey = `${rx},${ry}`;
          const vRoom = visited[rKey];
          const cx = centerX + dx * cellStep;
          const cy = centerY + dy * cellStep;
          if (cx < mx + 12 || cx > mx + mw - 12 || cy < my + 18 || cy > my + mh - 10) continue;

          if (vRoom) {
            const isCur = (dx === 0 && dy === 0);
            const d = vRoom.doors || {};
            // Draw sepia ink doorway connectors
            ctx.strokeStyle = "#a17c4b";
            ctx.lineWidth = 2;
            ctx.beginPath();
            if (d.N) { ctx.moveTo(cx, cy - 5); ctx.lineTo(cx, cy - 11); }
            if (d.S) { ctx.moveTo(cx, cy + 5); ctx.lineTo(cx, cy + 11); }
            if (d.W) { ctx.moveTo(cx - 5, cy); ctx.lineTo(cx - 11, cy); }
            if (d.E) { ctx.moveTo(cx + 5, cy); ctx.lineTo(cx + 11, cy); }
            ctx.stroke();

            // Draw miniature shape reflecting the room's actual footprint!
            ctx.fillStyle = isCur ? "#eab308" : "#5c4328";
            ctx.strokeStyle = isCur ? "#fef08a" : "#b89158";
            ctx.lineWidth = 1;
            const sh = vRoom.shape || "CRUCIFORM";
            if (sh === "CORRIDOR_EW") {
              ctx.fillRect(cx - 7, cy - 3, 14, 6); ctx.strokeRect(cx - 7, cy - 3, 14, 6);
            } else if (sh === "CORRIDOR_NS") {
              ctx.fillRect(cx - 3, cy - 7, 6, 14); ctx.strokeRect(cx - 3, cy - 7, 6, 14);
            } else if (sh === "COMPACT_VAULT") {
              ctx.fillRect(cx - 4, cy - 4, 8, 8); ctx.strokeRect(cx - 4, cy - 4, 8, 8);
            } else if (sh === "L_CHAMBER") {
              ctx.beginPath();
              ctx.moveTo(cx - 6, cy - 6); ctx.lineTo(cx + 2, cy - 6); ctx.lineTo(cx + 2, cy);
              ctx.lineTo(cx + 6, cy); ctx.lineTo(cx + 6, cy + 6); ctx.lineTo(cx - 6, cy + 6);
              ctx.closePath(); ctx.fill(); ctx.stroke();
            } else {
              // Cruciform / Hall
              ctx.fillRect(cx - 6, cy - 6, 12, 12); ctx.strokeRect(cx - 6, cy - 6, 12, 12);
            }

            // Player position dot inside current room
            if (isCur) {
              const pxOff = ((p.x - 400) / 340) * 4;
              const pyOff = ((p.y - 315) / 230) * 4;
              ctx.fillStyle = "#dc2626";
              ctx.beginPath(); ctx.arc(cx + pxOff, cy + pyOff, 2.2, 0, Math.PI * 2); ctx.fill();
            }
          } else {
            // Check if adjacent to a visited room via an open door -> draw faint '?' unexplored ink mark
            const adjN = visited[`${rx},${ry - 1}`], adjS = visited[`${rx},${ry + 1}`];
            const adjW = visited[`${rx - 1},${ry}`], adjE = visited[`${rx + 1},${ry}`];
            if ((adjN && adjN.doors.S) || (adjS && adjS.doors.N) || (adjW && adjW.doors.E) || (adjE && adjE.doors.W)) {
              ctx.strokeStyle = "rgba(161, 124, 75, 0.38)";
              ctx.strokeRect(cx - 4, cy - 4, 8, 8);
              ctx.fillStyle = "rgba(217, 175, 110, 0.55)";
              ctx.font = "8px monospace";
              ctx.textAlign = "center";
              ctx.fillText("?", cx, cy + 3);
            }
          }
        }
      }

      // Cartographer Header Label
      ctx.fillStyle = "#d9af6e";
      ctx.font = "bold 8.5px monospace";
      ctx.textAlign = "left";
      ctx.fillText(`CARTOGRAPHY [${curX},${curY}]`, mx + 6, my + 11);
      ctx.restore();
    }

  }
});
