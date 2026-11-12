// Cohesive Milestone Plugin: v0.9.0
// Cohesive Milestone Plugin: v0.9.0 (Ignitable Tar Fissures, Pyre-Vault Dash & Gothic Cinder-Gargoyle Perches)
window.StudioEngine.registerModule("Milestone_v0_9_0", {
  init: function(state, engine) {
    const w = state.world;
    const p = state.player;

    w.tarFissures = w.tarFissures || [
      { id: 'tf_1', x: 310, y: 260, radius: 44, ignited: false, flameTicks: 0, dps: 18, ash: false },
      { id: 'tf_2', x: 360, y: 290, radius: 40, ignited: false, flameTicks: 0, dps: 18, ash: false },
      { id: 'tf_3', x: 490, y: 360, radius: 46, ignited: false, flameTicks: 0, dps: 18, ash: false }
    ];

    w.gargoyles = w.gargoyles || [
      { x: 120, y: 80, angle: Math.PI * 0.35, heat: 0, state: 'DORMANT', timer: 0 },
      { x: 680, y: 80, angle: Math.PI * 0.65, heat: 0, state: 'DORMANT', timer: 0 },
      { x: 740, y: 340, angle: Math.PI, heat: 0, state: 'DORMANT', timer: 0 }
    ];

    w.projectiles = w.projectiles || w.lasers || [];
    w.particles = w.particles || [];
    w.floatingTexts = w.floatingTexts || [];

    p.pyreDashTimer = 0;
    p.prevActionKey = false;

    engine.on("PLAYER_ATTACK", (atk) => {
      if (!atk) return;
      const ax = p.x + Math.cos(p.facingAngle || 0) * 36;
      const ay = p.y + Math.sin(p.facingAngle || 0) * 36;
      w.tarFissures.forEach(f => {
        if (!f.ignited && !f.ash && Math.hypot(ax - f.x, ay - f.y) < f.radius + 20) {
          f.ignited = true;
          f.flameTicks = 360;
          (w.floatingTexts || (w.floatingTexts = [])).push({ x: f.x, y: f.y - 12, text: "TAR BLAZE!", color: "#f59e0b", life: 0.8 });
        }
      });
      w.gargoyles.forEach(g => {
        if (Math.hypot(ax - g.x, ay - g.y) < 68) {
          g.heat = Math.min(100, g.heat + 45);
          (w.particles || (w.particles = [])).push({ x: g.x, y: g.y, vx: (Math.random() - 0.5) * 40, vy: -30, life: 0.6, color: "#f97316" });
        }
      });
    });

    engine.on("EVENT_IGNITE_TAR", (target) => {
      w.tarFissures.forEach(f => {
        if (!f.ash && (!target || Math.hypot(target.x - f.x, target.y - f.y) < 70)) {
          f.ignited = true;
          f.flameTicks = 360;
        }
      });
    });
  },

  update: function(dt, state, engine) {
    if (state.paused || state.gameOver) return;
    const p = state.player;
    const w = state.world;
    const keys = state.keys || {};

    // 1. Systems: Tar Fissures (Viscous Drag, Blaze Propagation & Poise Burn)
    for (let i = w.tarFissures.length - 1; i >= 0; i--) {
      const f = w.tarFissures[i];
      if (f.ash) continue;
      const pd = Math.hypot(p.x - f.x, p.y - f.y);

      if (f.ignited) {
        f.flameTicks--;
        if (pd < f.radius) {
          p.health = Math.max(0, p.health - (f.dps * dt * 0.4));
          p.stress = Math.min(100, (p.stress || 0) + 12 * dt);
          w.cameraShake = Math.max(w.cameraShake || 0, 1.2);
        }
        (w.enemies || []).forEach(en => {
          if (Math.hypot(en.x - f.x, en.y - f.y) < f.radius + (en.width || 20) * 0.5) {
            en.hp = Math.max(0, en.hp - f.dps * dt);
            en.poise = Math.max(0, (en.poise || 40) - 30 * dt);
          }
        });

        // Chain ignite neighbors within 80px
        w.tarFissures.forEach(n => {
          if (!n.ignited && !n.ash && Math.hypot(n.x - f.x, n.y - f.y) < 80) {
            n.ignited = true;
            n.flameTicks = 360;
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: n.x, y: n.y - 10, text: "IGNITED!", color: "#ea580c", life: 0.6 });
          }
        });

        if (Math.random() < 0.4) {
          (w.particles || (w.particles = [])).push({
            x: f.x + (Math.random() - 0.5) * f.radius,
            y: f.y + (Math.random() - 0.5) * f.radius,
            vx: (Math.random() - 0.5) * 35,
            vy: -40 - Math.random() * 50,
            life: 0.5 + Math.random() * 0.3,
            color: Math.random() < 0.5 ? "#f97316" : "#dc2626"
          });
        }
        if (f.flameTicks <= 0) {
          f.ignited = false;
          f.ash = true;
        }
      } else if (pd < f.radius) {
        p.vx *= 0.6;
        p.vy *= 0.6;
      }
    }

    // 2. Gameplay: Pyre-Vault Dash Ability
    const actionPressed = keys.action && !p.prevActionKey;
    p.prevActionKey = !!keys.action;

    if (actionPressed && p.stamina >= 22 && (p.pyreDashTimer || 0) <= 0) {
      p.stamina = Math.max(0, p.stamina - 22);
      p.stamRegenDelay = 1.2;
      p.pyreDashTimer = 14;
      const angle = p.facingAngle || 0;
      const dirX = Math.cos(angle);
      const dirY = Math.sin(angle);
      p.vx = dirX * 310;
      p.vy = dirY * 310;
      w.cameraShake = Math.max(w.cameraShake || 0, 7);

      // Heel-stomp floor purging
      w.tarFissures.forEach(f => {
        if (Math.hypot(p.x - f.x, p.y - f.y) < 54) {
          f.ignited = false;
          f.ash = true;
          (w.floatingTexts || (w.floatingTexts = [])).push({ x: f.x, y: f.y, text: "PURGED", color: "#e2e8f0", life: 0.5 });
        }
      });

      // Directional 60-degree cinder cone projectile volley
      for (let c = -2; c <= 2; c++) {
        const cAngle = angle + (c * Math.PI) / 15;
        (w.projectiles || w.lasers).push({
          type: 'cinder',
          x: p.x + dirX * 12,
          y: p.y + dirY * 12,
          vx: Math.cos(cAngle) * 360,
          vy: Math.sin(cAngle) * 360,
          poiseDmg: 28,
          damage: 18,
          lifespan: 18,
          dirX: dirX,
          dirY: dirY
        });
      }
    }

    if (p.pyreDashTimer > 0) p.pyreDashTimer--;

    // Update cinder projectiles
    const projs = w.projectiles || w.lasers;
    for (let j = projs.length - 1; j >= 0; j--) {
      const pr = projs[j];
      if (pr.type === 'cinder') {
        pr.x += pr.vx * dt;
        pr.y += pr.vy * dt;
        pr.lifespan--;
        (w.enemies || []).forEach(en => {
          if (Math.hypot(pr.x - en.x, pr.y - en.y) < 26) {
            en.hp = Math.max(0, en.hp - pr.damage);
            en.poise = Math.max(0, (en.poise || 40) - pr.poiseDmg);
            en.vx = (en.vx || 0) + pr.dirX * 220;
            en.vy = (en.vy || 0) + pr.dirY * 220;
            pr.lifespan = 0;
            (w.floatingTexts || (w.floatingTexts = [])).push({ x: en.x, y: en.y - 14, text: "CRACK!", color: "#facc15", life: 0.45 });
          }
        });
        if (pr.lifespan <= 0) projs.splice(j, 1);
      }
    }

    // 3. Client & World: Gothic Cinder-Gargoyle Perches
    w.gargoyles.forEach(g => {
      if (g.state === 'DORMANT') {
        if (g.heat > 0) g.heat = Math.max(0, g.heat - 8 * dt);
        if (g.heat >= 100) {
          g.state = 'BREATHING';
          g.timer = 90;
        }
      } else if (g.state === 'BREATHING') {
        g.timer--;
        // Conical sweep hitbox
        const coneCos = Math.cos(Math.PI * 0.25);
        const checkSweep = (ent, isPlayer) => {
          const dx = ent.x - g.x, dy = ent.y - g.y;
          const dist = Math.hypot(dx, dy);
          if (dist > 18 && dist < 170) {
            const entAngle = Math.atan2(dy, dx);
            const dot = Math.cos(entAngle - g.angle);
            if (dot >= coneCos) {
              if (isPlayer) {
                p.health = Math.max(0, p.health - 12 * dt);
                p.stress = Math.min(100, (p.stress || 0) + 15 * dt);
              } else {
                ent.hp = Math.max(0, ent.hp - 18 * dt);
                ent.poise = Math.max(0, (ent.poise || 40) - 20 * dt);
              }
            }
          }
        };
        checkSweep(p, true);
        (w.enemies || []).forEach(en => checkSweep(en, false));

        if (g.timer <= 0) {
          g.state = 'DORMANT';
          g.heat = 0;
        }
      }
    });
  },

  render: function(ctx, state, engine) {
    const w = state.world;
    if (state.paused && !state.gameOver) return;

    ctx.save();
    if (w.cameraShake > 0) {
      const s = w.cameraShake;
      ctx.translate((Math.random() - 0.5) * s, (Math.random() - 0.5) * s);
    }

    // Render Tar Fissures
    w.tarFissures.forEach(f => {
      ctx.save();
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.radius, 0, Math.PI * 2);
      if (f.ash) {
        ctx.fillStyle = "#1e293b";
        ctx.fill();
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else if (f.ignited) {
        const radGrad = ctx.createRadialGradient(f.x, f.y, 4, f.x, f.y, f.radius * 1.15);
        radGrad.addColorStop(0, "#fef08a");
        radGrad.addColorStop(0.35, "#f97316");
        radGrad.addColorStop(0.75, "#b91c1c");
        radGrad.addColorStop(1, "rgba(24, 10, 10, 0.85)");
        ctx.fillStyle = radGrad;
        ctx.shadowColor = "#ea580c";
        ctx.shadowBlur = 18;
        ctx.fill();
      } else {
        ctx.fillStyle = "#09090b";
        ctx.fill();
        ctx.strokeStyle = "#3f3f46";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(f.x - 8, f.y - 6, f.radius * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = "#18181b";
        ctx.fill();
      }
      ctx.restore();
    });

    // Render Cinder Projectiles
    (w.projectiles || w.lasers || []).forEach(pr => {
      if (pr.type === 'cinder') {
        ctx.save();
        ctx.beginPath();
        ctx.arc(pr.x, pr.y, 3.5, 0, Math.PI * 2);
        ctx.fillStyle = "#fef08a";
        ctx.shadowColor = "#f97316";
        ctx.shadowBlur = 9;
        ctx.fill();
        ctx.restore();
      }
    });

    // Render Gargoyles & Conical Breath
    w.gargoyles.forEach(g => {
      ctx.save();
      ctx.translate(g.x, g.y);
      ctx.rotate(g.angle);

      // Low-poly stone relief bust
      ctx.fillStyle = "#1c1917";
      ctx.strokeStyle = "#44403c";
      ctx.lineWidth = 2;
      ctx.shadowColor = "#ea580c";
      ctx.shadowBlur = (g.heat || 0) * 0.35;

      ctx.beginPath();
      ctx.moveTo(-16, -14);
      ctx.lineTo(16, -14);
      ctx.lineTo(24, 0);
      ctx.lineTo(12, 16);
      ctx.lineTo(-12, 16);
      ctx.lineTo(-24, 0);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Gargoyle horns & glowing eyes
      ctx.fillStyle = g.heat > 50 || g.state === 'BREATHING' ? "#f59e0b" : "#78716c";
      ctx.fillRect(-8, -6, 4, 3);
      ctx.fillRect(4, -6, 4, 3);

      // Sweeping 45-degree Conical Ember Breath Field
      if (g.state === 'BREATHING') {
        ctx.restore();
        ctx.save();
        ctx.translate(g.x, g.y);
        ctx.rotate(g.angle);

        const coneGrad = ctx.createRadialGradient(0, 0, 10, 140, 0, 160);
        coneGrad.addColorStop(0, "rgba(254, 240, 138, 0.9)");
        coneGrad.addColorStop(0.3, "rgba(249, 115, 22, 0.7)");
        coneGrad.addColorStop(0.8, "rgba(185, 28, 28, 0.4)");
        coneGrad.addColorStop(1, "rgba(127, 29, 29, 0)");

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, 160, -Math.PI * 0.25, Math.PI * 0.25);
        ctx.closePath();
        ctx.fillStyle = coneGrad;
        ctx.shadowColor = "#f97316";
        ctx.shadowBlur = 24;
        ctx.fill();

        for (let k = 0; k < 6; k++) {
          const sparkDist = 20 + Math.random() * 130;
          const sparkAng = (Math.random() - 0.5) * (Math.PI * 0.45);
          ctx.fillStyle = Math.random() < 0.5 ? "#fde047" : "#ffedd5";
          ctx.fillRect(Math.cos(sparkAng) * sparkDist, Math.sin(sparkAng) * sparkDist, 3, 3);
        }
      }
      ctx.restore();
    });

    ctx.restore();
  }
});
