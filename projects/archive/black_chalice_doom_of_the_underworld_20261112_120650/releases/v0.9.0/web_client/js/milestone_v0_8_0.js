// Cohesive Milestone Plugin: v0.8.0
// Cohesive Milestone Plugin: v0.8.0 (Floor-Grit & Sunder Dynamics, Lodestone Pylons & Necrotic Bell-Warden Resonance)
window.StudioEngine.registerModule("Milestone_v0_8_0", {
  init: function(state, engine) {
    const w = state.world;
    const p = state.player;
    w.floorDecals = w.floorDecals || [];
    w.pylons = w.pylons || [
      { x: 260, y: 220, radius: 28, polarity: 1, charge: 1.0, empCooldown: 0 },
      { x: 540, y: 390, radius: 28, polarity: -1, charge: 1.0, empCooldown: 0 }
    ];
    w.oilSlicks = w.oilSlicks || [
      { x: 380, y: 300, radius: 36, ignited: false, flameTimer: 0 }
    ];
    w.tiles = w.tiles || [
      { x: 190, y: 150, type: 'brittle_wall', hp: 30 },
      { x: 610, y: 460, type: 'brittle_wall', hp: 30 }
    ];
    w.hazards = w.hazards || [];
    w.enemies = w.enemies || [];
    w.particles = w.particles || [];
    w.bloodPools = w.bloodPools || [
      { x: 420, y: 330, radius: 32 }
    ];

    if (!w.enemies.some(e => e.type === "bell_warden")) {
      (w.enemies || (w.enemies = [])).push({
        type: 'bell_warden', ironClad: true, x: 480, y: 280, vx: 0, vy: 0,
        width: 32, height: 38, mass: 450, poise: 80, poiseMax: 80, resonance: 0,
        hp: 180, maxHp: 180, facingAngle: Math.PI, clapperOffset: 0
      });
    }

    p.footstepSoot = p.footstepSoot || { stepsRemaining: 0, bloodHue: '#991b1b', lastStepDist: 0 };

    engine.on("PLAYER_ATTACK", (atk) => {
      w.enemies.forEach(en => {
        if (en.type === 'bell_warden') {
          const d = Math.hypot(p.x - en.x, p.y - en.y);
          if (d < (p.weaponReach || 44) + 24) {
            const dmg = p.weaponDamage || 25;
            en.poise -= dmg * 0.75;
            en.hp = Math.max(0, en.hp - dmg);
            const impAngle = Math.atan2(en.y - p.y, en.x - p.x);
            en.vx += Math.cos(impAngle) * 60;
            en.vy += Math.sin(impAngle) * 60;
            w.cameraShake = Math.max(w.cameraShake || 0, 5);

            if (en.poise <= 0) {
              en.poise = en.poiseMax;
              en.resonance = (en.resonance || 0) + 1;
              (w.hazards || (w.hazards = [])).push({
                type: 'harmonic_wave', x: en.x, y: en.y, radius: 24,
                maxRadius: 190, speed: 320, angle: impAngle, life: 1.0
              });
              w.cameraShake = Math.max(w.cameraShake || 0, 11);
              for (let i = 0; i < 7; i++) {
                if (w.floorDecals.length < 256) {
                  (w.floorDecals || (w.floorDecals = [])).push({
                    x: en.x + (Math.random() - 0.5) * 40, y: en.y + (Math.random() - 0.5) * 40,
                    angle: impAngle + (Math.random() - 0.5) * 0.9, length: 14 + Math.random() * 22,
                    color: '#1c1917', alpha: 1.0, type: 'splinter'
                  });
                }
              }
            }
          }
        }
      });
    });
  },

  update: function(dt, state, engine) {
    if (state.paused || state.gameOver) return;
    const w = state.world;
    const p = state.player;
    const t = state.tick || 0;

    // Decals Culling & Fading
    for (let i = w.floorDecals.length - 1; i >= 0; i--) {
      const dec = w.floorDecals[i];
      if (dec.type === 'footprint') {
        dec.alpha -= dt / 12;
        if (dec.alpha <= 0) w.floorDecals.splice(i, 1);
      }
    }

    // Footstep & Blood Soot Mechanics
    const pDist = Math.hypot(p.vx, p.vy) * dt;
    p.footstepSoot.lastStepDist = (p.footstepSoot.lastStepDist || 0) + pDist;
    w.bloodPools.forEach(bp => {
      if (Math.hypot(p.x - bp.x, p.y - bp.y) < bp.radius) {
        p.footstepSoot.stepsRemaining = 6;
        p.footstepSoot.bloodHue = '#991b1b';
      }
    });

    if (p.footstepSoot.stepsRemaining > 0 && p.footstepSoot.lastStepDist > 20) {
      p.footstepSoot.lastStepDist = 0;
      p.footstepSoot.stepsRemaining--;
      if (w.floorDecals.length < 256) {
        (w.floorDecals || (w.floorDecals = [])).push({
          x: p.x + (Math.random() - 0.5) * 6, y: p.y + (Math.random() - 0.5) * 6,
          angle: p.facingAngle || 0, length: 7, color: p.footstepSoot.bloodHue,
          alpha: 0.9, type: 'footprint'
        });
      }
    }

    // Interactive Lodestone Pylons & Shield Rebound
    const isDashing = (p.dashTimer > 0) || (p.isRolling === true);
    w.pylons.forEach(pyl => {
      pyl.charge = Math.min(1.0, pyl.charge + dt * 0.25);
      const ironEntities = [...w.enemies.filter(e => e.ironClad || e.type === 'bell_warden')];
      ironEntities.forEach(ent => {
        const dx = pyl.x - ent.x, dy = pyl.y - ent.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist <= 220) {
          const force = (4200 * pyl.charge * pyl.polarity) / Math.max(dist, 32);
          ent.vx += (dx / dist) * force * dt;
          ent.vy += (dy / dist) * force * dt;
        }
      });

      // Deflect Iron Projectiles
      (w.projectiles || w.lasers || []).forEach(proj => {
        const pdx = pyl.x - proj.x, pdy = pyl.y - proj.y;
        const pdist = Math.hypot(pdx, pdy) || 1;
        if (pdist < 180) {
          const targetAngle = Math.atan2(pdy, pdx);
          proj.angle = (proj.angle || 0) + (targetAngle - (proj.angle || 0)) * (dt * 3.5);
          proj.vx = Math.cos(proj.angle) * (proj.speed || 240);
          proj.vy = Math.sin(proj.angle) * (proj.speed || 240);
        }
      });

      // Shield Rebound EMP Arc
      const pDistToPyl = Math.hypot(p.x - pyl.x, p.y - pyl.y);
      if (isDashing && pDistToPyl <= pyl.radius + 18 && pyl.charge >= 0.7 && p.stamina >= 25) {
        p.stamina = Math.max(0, p.stamina - 25);
        pyl.charge = 0;
        w.cameraShake = Math.max(w.cameraShake || 0, 14);
        (w.hazards || (w.hazards = [])).push({ type: 'emp_ring', x: pyl.x, y: pyl.y, radius: pyl.radius, maxRadius: 170, life: 0.45 });
        w.enemies.forEach(en => {
          const edx = en.x - pyl.x, edy = en.y - pyl.y;
          const edist = Math.hypot(edx, edy) || 1;
          if (edist <= 170) {
            const recoilVel = 400;
            en.vx += (edx / edist) * recoilVel;
            en.vy += (edy / edist) * recoilVel;
            en.poise = Math.max(0, (en.poise || 40) - 40);
            en.hp = Math.max(0, en.hp - 20);
          }
        });
      }
    });

    // Diegetic Necrotic Bell-Warden Logic & Harmonic Waves
    w.enemies.forEach(en => {
      if (en.type === 'bell_warden') {
        en.clapperOffset = Math.sin(t * 0.35 + (en.resonance || 0) * 1.5) * (4 + (en.resonance || 0) * 3);
        const dx = p.x - en.x, dy = p.y - en.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist > 50 && dist < 320) {
          en.vx += (dx / dist) * 28 * dt;
          en.vy += (dy / dist) * 28 * dt;
        }
        en.x += en.vx * dt; en.y += en.vy * dt;
        en.vx *= 0.88; en.vy *= 0.88;
      }
    });

    // Harmonic Shockwaves Propagation
    for (let i = w.hazards.length - 1; i >= 0; i--) {
      const h = w.hazards[i];
      if (h.type === 'harmonic_wave') {
        h.radius += h.speed * dt;
        h.life -= dt * (h.speed / h.maxRadius);
        w.tiles.forEach(tl => {
          if (tl.type === 'brittle_wall' && Math.hypot(tl.x - h.x, tl.y - h.y) <= h.radius + 16) {
            tl.type = 'rubble';
            w.cameraShake = Math.max(w.cameraShake || 0, 7);
            for (let k = 0; k < 6; k++) {
              if (w.floorDecals.length < 256) {
                (w.floorDecals || (w.floorDecals = [])).push({
                  x: tl.x + (Math.random() - 0.5) * 20, y: tl.y + (Math.random() - 0.5) * 20,
                  angle: Math.random() * Math.PI * 2, length: 12 + Math.random() * 14,
                  color: '#44403c', alpha: 1.0, type: 'splinter'
                });
              }
            }
          }
        });
        w.oilSlicks.forEach(sl => {
          if (!sl.ignited && Math.hypot(sl.x - h.x, sl.y - h.y) <= h.radius + sl.radius) {
            sl.ignited = true;
            sl.flameTimer = 7.0;
          }
        });
        if (h.radius >= h.maxRadius || h.life <= 0) w.hazards.splice(i, 1);
      } else if (h.type === 'emp_ring') {
        h.radius += 280 * dt;
        h.life -= dt * 1.8;
        if (h.life <= 0) w.hazards.splice(i, 1);
      }
    }

    // Oil Slick Burning & Ignition Particle Loop
    w.oilSlicks.forEach(sl => {
      if (sl.ignited) {
        sl.flameTimer -= dt;
        if (Math.random() < 0.35) {
          (w.particles || (w.particles = [])).push({
            x: sl.x + (Math.random() - 0.5) * sl.radius, y: sl.y + (Math.random() - 0.5) * sl.radius,
            vx: (Math.random() - 0.5) * 16, vy: -35 - Math.random() * 25,
            life: 0.6, maxLife: 0.6, color: '#f59e0b', size: 3
          });
        }
        if (sl.flameTimer <= 0) sl.ignited = false;
      }
    });
  },

  render: function(ctx, state, engine) {
    const w = state.world;
    const p = state.player;
    const t = state.tick || 0;
    const shakeMag = w.cameraShake || 0;
    const tremorX = Math.sin(t * 0.45) * shakeMag;

    ctx.save();
    // Chiaroscuro Decals & Sunder Splinters
    w.floorDecals.forEach(dec => {
      ctx.save();
      ctx.globalAlpha = Math.max(0, dec.alpha || 1.0);
      ctx.strokeStyle = dec.color;
      ctx.fillStyle = dec.color;
      ctx.lineWidth = dec.type === 'footprint' ? 3.5 : 1.8;
      ctx.beginPath();
      const lx = Math.cos(dec.angle) * dec.length;
      const ly = Math.sin(dec.angle) * dec.length;
      ctx.moveTo(dec.x - lx * 0.5, dec.y - ly * 0.5);
      ctx.lineTo(dec.x + lx * 0.5, dec.y + ly * 0.5);
      ctx.stroke();
      ctx.restore();
    });

    // Render Blood Pools & Oil Slicks
    w.bloodPools.forEach(bp => {
      ctx.save();
      ctx.fillStyle = 'rgba(153, 27, 27, 0.45)';
      ctx.beginPath();
      ctx.ellipse(bp.x, bp.y, bp.radius, bp.radius * 0.65, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    w.oilSlicks.forEach(sl => {
      ctx.save();
      ctx.fillStyle = sl.ignited ? 'rgba(234, 88, 12, 0.6)' : 'rgba(17, 24, 39, 0.8)';
      ctx.beginPath();
      ctx.ellipse(sl.x, sl.y, sl.radius, sl.radius * 0.6, 0.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = sl.ignited ? '#fbbf24' : '#374151';
      ctx.stroke();
      ctx.restore();
    });

    // Render Brittle Walls / Rubble
    w.tiles.forEach(tl => {
      ctx.save();
      if (tl.type === 'brittle_wall') {
        ctx.fillStyle = '#292524';
        ctx.strokeStyle = '#78716c';
        ctx.fillRect(tl.x - 14, tl.y - 14, 28, 28);
        ctx.strokeRect(tl.x - 14, tl.y - 14, 28, 28);
        ctx.beginPath();
        ctx.moveTo(tl.x - 10, tl.y - 10); ctx.lineTo(tl.x + 2, tl.y); ctx.lineTo(tl.x + 8, tl.y + 10);
        ctx.stroke();
      } else {
        ctx.fillStyle = '#1c1917';
        for (let j = 0; j < 4; j++) {
          ctx.fillRect(tl.x - 12 + (j % 2) * 12, tl.y - 10 + Math.floor(j / 2) * 10, 8, 7);
        }
      }
      ctx.restore();
    });

    // Directional Seismic Torch Drop-Shadows
    const torchRange = p.torchRadius || 240;
    const distToTorch = Math.hypot(p.x - 400, p.y - 300) || 1;
    const shadowStretch = Math.min(2.2, (torchRange / distToTorch) * 0.85);

    // Render Lodestone Pylons (Faceted 2.5D Monoliths)
    w.pylons.forEach(pyl => {
      ctx.save();
      // Drop-Shadow skewed by tremor offset
      ctx.fillStyle = 'rgba(4, 3, 7, 0.65)';
      ctx.beginPath();
      ctx.ellipse(pyl.x + tremorX * 1.5, pyl.y + pyl.radius * 0.5, pyl.radius * shadowStretch, pyl.radius * 0.45, 0, 0, Math.PI * 2);
      ctx.fill();

      // Pylon Core Base
      const glow = pyl.polarity > 0 ? '#38bdf8' : '#c084fc';
      ctx.fillStyle = '#1e1b4b';
      ctx.strokeStyle = glow;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(pyl.x, pyl.y, pyl.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Pulsing Lodestone Magnetic Rings
      ctx.beginPath();
      ctx.strokeStyle = `rgba(${pyl.polarity > 0 ? '56, 189, 248' : '192, 132, 252'}, ${pyl.charge * 0.7})`;
      ctx.arc(pyl.x, pyl.y, pyl.radius + Math.sin(t * 0.1) * 8 + 6, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    });

    // Render Enemies & Bell-Wardens Diegetically
    w.enemies.forEach(en => {
      if (en.type === 'bell_warden') {
        ctx.save();
        ctx.translate(en.x, en.y);
        // Shadow
        ctx.fillStyle = 'rgba(5, 3, 9, 0.7)';
        ctx.beginPath();
        ctx.ellipse(tremorX, en.height * 0.45, en.width * 0.65, 8, 0, 0, Math.PI * 2);
        ctx.fill();

        // Heavy Bronze Bell Body (Articulated Silhouette)
        ctx.fillStyle = '#78350f';
        ctx.strokeStyle = en.resonance > 0 ? '#facc15' : '#451a03';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(-en.width * 0.35, -en.height * 0.5);
        ctx.lineTo(en.width * 0.35, -en.height * 0.5);
        ctx.quadraticCurveTo(en.width * 0.6, 0, en.width * 0.55, en.height * 0.35);
        ctx.lineTo(-en.width * 0.55, en.height * 0.35);
        ctx.quadraticCurveTo(-en.width * 0.6, 0, -en.width * 0.35, -en.height * 0.5);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Vibrating Internal Clapper
        ctx.fillStyle = '#d97706';
        ctx.beginPath();
        ctx.arc(en.clapperOffset || 0, en.height * 0.38, 6.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Glowing Rune Eye of the Warden
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(0, -6, 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    });

    // Render Concussive EMP & Harmonic Shockwave Rings
    w.hazards.forEach(h => {
      if (h.type === 'harmonic_wave') {
        ctx.save();
        ctx.strokeStyle = `rgba(250, 204, 21, ${h.life})`;
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.arc(h.x, h.y, h.radius, h.angle - 0.7, h.angle + 0.7);
        ctx.stroke();
        ctx.restore();
      } else if (h.type === 'emp_ring') {
        ctx.save();
        ctx.strokeStyle = `rgba(56, 189, 248, ${h.life * 2})`;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(h.x, h.y, h.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }
    });

    ctx.restore();
  }
});
