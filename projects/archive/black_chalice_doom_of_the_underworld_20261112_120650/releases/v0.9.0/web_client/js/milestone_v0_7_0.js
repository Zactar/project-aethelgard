// Cohesive Milestone Plugin: v0.7.0
// Cohesive Milestone Plugin: v0.7.0 (Catacomb Bell-Warden Automaton, Suspended Bronze Censers & Eldritch Runic Detonations)
window.StudioEngine.registerModule("Milestone_v0_7_0", {
  init: function(state, engine) {
    const w = state.world;
    w.entities = w.entities || [];
    w.hazards = w.hazards || [];
    w.censers = w.censers || [];
    w.glyphs = w.glyphs || [];
    w.particles = w.particles || [];
    w.floatingTexts = w.floatingTexts || [];

    // Spawn 1 Bell-Warden Automaton in Catacombs
    if (!w.entities.some(e => e.type === "bell_warden")) {
      (w.entities || (w.entities = [])).push({
        type: "bell_warden", state: "patrol", timer: 0, poise: 120, maxPoise: 120,
        x: 480, y: 280, vx: 0, vy: 0, facingAngle: Math.PI, hp: 160, maxHp: 160, width: 34, height: 38
      });
    }

    // Spawn 2 Bronze Ceiling-Suspended Censers
    if (w.censers.length === 0) {
      (w.censers || (w.censers = [])).push(
        { id: "censer_1", anchorX: 320, anchorY: 140, length: 75, angle: 0.15, angularVel: 0, angularAcc: 0, ashTimer: 0 },
        { id: "censer_2", anchorX: 490, anchorY: 150, length: 80, angle: -0.1, angularVel: 0, angularAcc: 0, ashTimer: 0 }
      );
    }

    // Spawn Diegetic Fractured Floor Glyphs
    if (w.glyphs.length === 0) {
      (w.glyphs || (w.glyphs = [])).push(
        { id: "gl_1", x: 280, y: 340, radius: 28, state: "dormant", timer: 0 },
        { id: "gl_2", x: 520, y: 370, radius: 28, state: "dormant", timer: 0 },
        { id: "gl_3", x: 390, y: 440, radius: 28, state: "dormant", timer: 0 }
      );
    }

    // Interactive Strike Listener for Suspended Censers & Warden Poise
    engine.on("PLAYER_ATTACK", (atk) => {
      const p = state.player;
      const fdx = Math.cos(p.facingAngle || 0);
      const fdy = Math.sin(p.facingAngle || 0);
      w.censers.forEach(c => {
        const cx = c.anchorX + Math.sin(c.angle) * c.length;
        const cy = c.anchorY + Math.cos(c.angle) * c.length;
        if (Math.hypot(p.x - cx, p.y - cy) < (p.weaponReach || 44) + 18) {
          c.angularVel += (p.vx * 0.05) + (fdx * 0.14);
          w.cameraShake = Math.max(w.cameraShake || 0, 3.5);
          for (let i = 0; i < 9; i++) {
            (w.particles || (w.particles = [])).push({
              x: cx + (Math.random() - 0.5) * 14, y: cy + (Math.random() - 0.5) * 14,
              vx: (Math.random() - 0.5) * 60 + fdx * 40, vy: (Math.random() - 0.5) * 60 + fdy * 40,
              life: 0.5, maxLife: 0.5, color: "#f59e0b", size: 3
            });
          }
        }
      });
    });
  },

  update: function(dt, state, engine) {
    if (state.paused) return;
    const p = state.player;
    const w = state.world;
    const isRolling = (p.dashTimer > 0) || (p.isRolling === true);

    // 1. Catacomb Bell-Warden Automaton AI & Shockwave Mechanics
    w.entities.forEach(ent => {
      if (ent.type !== "bell_warden" || ent.hp <= 0) return;
      ent.timer = (ent.timer || 0) + 1;
      const dx = p.x - ent.x, dy = p.y - ent.y;
      const dist = Math.hypot(dx, dy) || 1;
      ent.facingAngle = Math.atan2(dy, dx);

      if (ent.state === "patrol") {
        if (dist > 85) {
          ent.vx = (dx / dist) * 38;
          ent.vy = (dy / dist) * 38;
        } else {
          ent.vx *= 0.8; ent.vy *= 0.8;
        }
        ent.x += ent.vx * dt;
        ent.y += ent.vy * dt;
        if (ent.timer >= 315) {
          ent.state = "windup";
          ent.timer = 0;
          ent.vx = 0; ent.vy = 0;
        }
      } else if (ent.state === "windup") {
        if (ent.timer >= 45) {
          ent.state = "chime";
          ent.timer = 0;
          (w.hazards || (w.hazards = [])).push({
            type: "bell_shockwave", x: ent.x, y: ent.y, r: 12, maxR: 140, speed: 4.5 * 60,
            growthPerSec: 270, life: 140 / 270, dmg: 45, hitPlayer: false
          });
          w.cameraShake = Math.max(w.cameraShake || 0, 7.5);
          for (let k = 0; k < 18; k++) {
            const rad = (Math.PI * 2 * k) / 18;
            (w.particles || (w.particles = [])).push({
              x: ent.x, y: ent.y, vx: Math.cos(rad) * 110, vy: Math.sin(rad) * 110,
              life: 0.4, maxLife: 0.4, color: "#eab308", size: 2.5
            });
          }
        }
      } else if (ent.state === "chime") {
        if (ent.timer >= 30) {
          ent.state = "cooldown";
          ent.timer = 0;
        }
      } else if (ent.state === "cooldown") {
        if (ent.timer >= 60) {
          ent.state = "patrol";
          ent.timer = 0;
        }
      }

      // Front-Arc Shield Ricochet (cos(theta) > 0.5) against player projectiles
      const projs = w.lasers || w.bullets || w.projectiles || [];
      projs.forEach(b => {
        if (!b || b.reflected) return;
        const bdx = b.x - ent.x, bdy = b.y - ent.y;
        if (Math.hypot(bdx, bdy) < ent.width + 10) {
          const toProjAngle = Math.atan2(bdy, bdx);
          const angleDiff = Math.abs(Math.atan2(Math.sin(toProjAngle - ent.facingAngle), Math.cos(toProjAngle - ent.facingAngle)));
          if (angleDiff < Math.PI * 0.33) {
            b.vx = -(b.vx || 0) * 1.3;
            b.vy = -(b.vy || 0) * 1.3;
            b.reflected = true;
            b.reflectedDamage = 28;
            w.cameraShake = Math.max(w.cameraShake || 0, 4);
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: b.x, y: b.y - 10, text: "PARRIED!", color: "#eab308", life: 0.8 });
          }
        }
      });
    });

    // 2. Shockwave Hazard Propagation & Dodge I-Frame Arbitration
    w.hazards = w.hazards.filter(h => {
      if (h.type !== "bell_shockwave") return true;
      h.r += h.growthPerSec * dt;
      if (!h.hitPlayer) {
        const pd = Math.hypot(p.x - h.x, p.y - h.y);
        if (Math.abs(pd - h.r) < 18) {
          if (isRolling) {
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: p.x, y: p.y - 18, text: "ROLL I-FRAME!", color: "#10b981", life: 0.6 });
            h.hitPlayer = true;
          } else if ((p.invuln || 0) <= 0) {
            p.health = Math.max(0, p.health - Math.ceil(h.dmg / 12));
            p.invuln = 0.65;
            p.hitStop = 0.12;
            w.cameraShake = Math.max(w.cameraShake || 0, 8);
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: p.x, y: p.y - 20, text: `STAGGER -${h.dmg}`, color: "#dc2626", life: 0.8 });
            h.hitPlayer = true;
          }
        }
      }
      return h.r < h.maxR;
    });

    // Handle ricochet impact on crypt pillars / masonry
    const projs = w.lasers || w.bullets || w.projectiles || [];
    projs.forEach(b => {
      if (b && b.reflected && w.pillars) {
        w.pillars.forEach(pil => {
          if (!pil.collapsed && Math.hypot(b.x - (pil.x + 16), b.y - (pil.y + 16)) < 26) {
            pil.hp = Math.max(0, (pil.hp || 80) - (b.reflectedDamage || 28));
            b.dead = true;
            w.cameraShake = Math.max(w.cameraShake || 0, 5);
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: pil.x, y: pil.y - 12, text: "MASONRY CRACK", color: "#f59e0b", life: 0.7 });
          }
        });
      }
    });

    // 3. Interactive Bronze Cathedral Censers: Pendulum Mechanics & Sacred Ash Dispensation
    w.censers.forEach(c => {
      c.angularAcc = (-0.004 * Math.sin(c.angle)) - (0.015 * c.angularVel);
      c.angularVel += c.angularAcc;
      c.angle += c.angularVel;
      c.ashTimer = (c.ashTimer || 0) + dt;

      if (Math.abs(c.angularVel) > 0.01 && c.ashTimer > 0.08) {
        c.ashTimer = 0;
        const cx = c.anchorX + Math.sin(c.angle) * c.length;
        const cy = c.anchorY + Math.cos(c.angle) * c.length;
        (w.particles || (w.particles = [])).push({
          x: cx + (Math.random() - 0.5) * 8, y: cy + (Math.random() - 0.5) * 8,
          vx: (Math.random() - 0.5) * 20, vy: (Math.random() - 0.5) * 14 + 18,
          life: 1.1, maxLife: 1.1, color: "#d1d5db", size: 4.5, isAsh: true
        });

        // Sacred Ash Blinds Lurking Fiends
        (w.enemies || []).concat(w.entities || []).forEach(foe => {
          if (foe.hp > 0 && Math.hypot(foe.x - cx, foe.y - cy) < 42) {
            foe.blindTimer = 180;
            if (Math.random() < 0.15) {
              (w.floatingTexts || (w.floatingTexts = [])).push({ x: foe.x, y: foe.y - 16, text: "BLINDED", color: "#9ca3af", life: 0.6 });
            }
          }
        });

        // Sacred Ash Ignites Oil Slicks
        w.hazards.forEach(hz => {
          if (hz.type === "oil_slick" && Math.hypot(hz.x - cx, hz.y - cy) < (hz.r || 32) + 20) {
            hz.type = "burning_slick";
            hz.dps = 14;
            hz.life = 8.0;
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: hz.x, y: hz.y - 10, text: "PURIFYING PYRE!", color: "#f97316", life: 0.8 });
          }
        });
      }
    });

    // Update Burning Slicks
    w.hazards.forEach(hz => {
      if (hz.type === "burning_slick") {
        hz.life = (hz.life || 6) - dt;
        if (Math.random() < 0.25) {
          (w.particles || (w.particles = [])).push({
            x: hz.x + (Math.random() - 0.5) * 28, y: hz.y + (Math.random() - 0.5) * 28,
            vx: (Math.random() - 0.5) * 18, vy: -Math.random() * 32 - 12,
            life: 0.5, maxLife: 0.5, color: "#ef4444", size: 3
          });
        }
        (w.enemies || []).concat(w.entities || []).forEach(foe => {
          if (foe.hp > 0 && Math.hypot(foe.x - hz.x, foe.y - hz.y) < 32) {
            foe.hp -= (hz.dps || 14) * dt;
          }
        });
      }
    });
    w.hazards = w.hazards.filter(hz => hz.type !== "burning_slick" || hz.life > 0);

    // 4. Diegetic Runic Glyph Detonation (Violet Fractures)
    w.glyphs.forEach(gl => {
      const pDist = Math.hypot(p.x - gl.x, p.y - gl.y);
      if (gl.state === "dormant" && pDist < gl.radius) {
        gl.state = "primed";
        gl.timer = 72;
      } else if (gl.state === "primed") {
        gl.timer -= 1;
        if (gl.timer <= 0) {
          gl.state = "erupted";
          w.cameraShake = Math.max(w.cameraShake || 0, 7);
          const pClose = Math.hypot(p.x - gl.x, p.y - gl.y) < 36;
          if (pClose && !isRolling && (p.invuln || 0) <= 0) {
            p.health = Math.max(0, p.health - 2);
            p.invuln = 0.7;
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: p.x, y: p.y - 22, text: "ELDRITCH SPIKE -38", color: "#a855f7", life: 0.9 });
          }
          for (let sp = 0; sp < 12; sp++) {
            const ang = (Math.PI * 2 * sp) / 12;
            (w.particles || (w.particles = [])).push({
              x: gl.x + Math.cos(ang) * 16, y: gl.y + Math.sin(ang) * 16,
              vx: Math.cos(ang) * 75, vy: Math.sin(ang) * 75 - 30,
              life: 0.55, maxLife: 0.55, color: "#c084fc", size: 3.5
            });
          }
        }
      }
    });
  },

  render: function(ctx, state, engine) {
    if (state.paused) return;
    const w = state.world;
    const t = (state.tick || 0);

    ctx.save();
    if (w.cameraShake > 0) {
      const s = w.cameraShake;
      ctx.translate((Math.random() - 0.5) * s, (Math.random() - 0.5) * s);
    }

    // 1. Render Runic Floor Glyphs & Branching Fractures
    w.glyphs.forEach(gl => {
      ctx.save();
      ctx.translate(gl.x, gl.y);
      if (gl.state === "dormant") {
        ctx.strokeStyle = "rgba(168, 85, 247, 0.28)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, 0, gl.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = "rgba(168, 85, 247, 0.08)";
        ctx.fill();
      } else if (gl.state === "primed") {
        const glow = Math.sin(gl.timer * 0.4) * 2 + 2;
        ctx.strokeStyle = "#a855f7";
        ctx.lineWidth = glow;
        ctx.shadowColor = "#c084fc";
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(0, 0, gl.radius, 0, Math.PI * 2);
        ctx.stroke();

        // Branching eldritch fissures
        ctx.beginPath();
        for (let a = 0; a < 6; a++) {
          const ang = (Math.PI * 2 * a) / 6 + Math.sin(t * 0.1 + a) * 0.2;
          ctx.moveTo(0, 0);
          ctx.lineTo(Math.cos(ang) * (gl.radius * 0.55), Math.sin(ang) * (gl.radius * 0.55));
          ctx.lineTo(Math.cos(ang + 0.3) * gl.radius, Math.sin(ang + 0.3) * gl.radius);
        }
        ctx.stroke();
      } else if (gl.state === "erupted") {
        ctx.fillStyle = "rgba(15, 10, 25, 0.85)";
        ctx.beginPath();
        ctx.arc(0, 0, gl.radius + 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "rgba(168, 85, 247, 0.4)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
      ctx.restore();
    });

    // 2. Render Suspended Bronze Cathedral Censers
    w.censers.forEach(c => {
      const cx = c.anchorX + Math.sin(c.angle) * c.length;
      const cy = c.anchorY + Math.cos(c.angle) * c.length;
      ctx.save();
      // Heavy iron chain suspension
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(c.anchorX, c.anchorY);
      ctx.lineTo(cx, cy);
      ctx.stroke();

      // Bronze censer body
      ctx.translate(cx, cy);
      ctx.rotate(c.angle);
      ctx.fillStyle = "#b45309";
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.moveTo(-12, -8);
      ctx.lineTo(12, -8);
      ctx.lineTo(8, 14);
      ctx.lineTo(-8, 14);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Censer burning embers & vents
      ctx.fillStyle = (Math.sin(t * 0.3) > 0) ? "#ef4444" : "#f59e0b";
      ctx.beginPath();
      ctx.arc(0, 2, 4.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    // 3. Render Bell-Warden Automaton & Expanding Funeral Shockwave
    w.entities.forEach(ent => {
      if (ent.type !== "bell_warden" || ent.hp <= 0) return;
      ctx.save();
      ctx.translate(ent.x, ent.y);

      // Heavy Iron Plate Automaton Body
      const bob = Math.sin(t * 0.12) * 2;
      ctx.fillStyle = "#1e293b";
      ctx.strokeStyle = "#64748b";
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.rect(-15, -18 + bob, 30, 36);
      ctx.fill();
      ctx.stroke();

      // Doom-Ochre Visor Slit
      ctx.fillStyle = (ent.state === "windup") ? "#dc2626" : "#eab308";
      ctx.fillRect(-7, -11 + bob, 14, 3.5);

      // Handheld Funeral Bell
      ctx.save();
      ctx.translate(14, 4 + bob);
      if (ent.state === "windup") ctx.rotate(Math.sin(t * 0.8) * 0.5 - 0.4);
      if (ent.state === "chime") ctx.rotate(0.6);
      ctx.fillStyle = "#d97706";
      ctx.strokeStyle = "#fef08a";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(-6, -8);
      ctx.lineTo(6, -8);
      ctx.lineTo(9, 10);
      ctx.lineTo(-9, 10);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#451a03";
      ctx.beginPath();
      ctx.arc(0, 10, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // Warden Health / Poise Pip Gauge (Diegetic)
      const pRatio = Math.max(0, ent.poise / ent.maxPoise);
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(-16, -26 + bob, 32, 4);
      ctx.fillStyle = "#eab308";
      ctx.fillRect(-16, -26 + bob, 32 * pRatio, 4);
      ctx.restore();
    });

    // Expanding Funeral Bell Shockwave Hazard
    w.hazards.forEach(hz => {
      if (hz.type === "bell_shockwave") {
        ctx.save();
        ctx.strokeStyle = "#fbbf24";
        ctx.lineWidth = 3.5;
        ctx.shadowColor = "#f59e0b";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(hz.x, hz.y, hz.r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }
    });

    ctx.restore();
    // Steady HUD Ribbon Guard
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
});
