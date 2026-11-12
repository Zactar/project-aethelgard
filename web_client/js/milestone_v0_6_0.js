// Cohesive Milestone Plugin: v0.6.0
// Cohesive Milestone Plugin: v0.6.0 (Kinetic Overcharge, Astra-Singularity Core & Diegetic Crucible Bloom)
window.StudioEngine.registerModule("Milestone_v0_6_0", {
  init: function(state, engine) {
    const w = (state.world = state.world || {});
    w.particles = w.particles || [];
    w.shake = w.shake || 0;
    w.time = w.time || 0;
    w.contestedLines = w.contestedLines || [];
    w.shockwaves = [];
    w.embers = [];

    // Spatial Sectors & Dividers
    w.sectors = Array.from({ length: 9 }, (_, i) => ({
      id: i,
      x: 280 + (i % 3) * 120,
      y: 190 + Math.floor(i / 3) * 120,
      fractureLevel: 0,
      overcharged: false
    }));

    // Graviton Singularity Core
    w.singularity = {
      active: true,
      x: 400,
      y: 310,
      targetX: 400,
      targetY: 310,
      pulsePhase: 0,
      strength: 1.0,
      eventHorizonRadius: 42
    };

    // Initialize 36 ambient astral embers inside lattice basin
    for (let i = 0; i < 36; i++) {
      (w.embers || (w.embers = [])).push({
        x: 240 + Math.random() * 320,
        y: 150 + Math.random() * 320,
        vx: (Math.random() - 0.5) * 18,
        vy: (Math.random() - 0.5) * 18,
        rad: 1.2 + Math.random() * 2.2,
        hue: Math.random() > 0.5 ? 45 : 190,
        alpha: 0.3 + Math.random() * 0.5
      });
    }

    // Active Placement Mechanic: Inscription Hook
    engine.on("SECTOR_INSCRIBED", (ev) => {
      const idx = ev.index;
      const sec = w.sectors[idx];
      if (!sec) return;

      const breath = Math.sin(w.singularity.pulsePhase);
      const isOvercharge = breath >= 0.82;

      if (isOvercharge) {
        sec.overcharged = true;
        w.shake = Math.max(w.shake, 8.5);

        // Emit 24 Kinetic Shockwave Fragments
        for (let k = 0; k < 24; k++) {
          const theta = (k / 24) * Math.PI * 2 + (Math.random() - 0.5) * 0.15;
          const spd = 300 + Math.random() * 40;
          (w.particles || (w.particles = [])).push({
            x: sec.x,
            y: sec.y,
            vx: Math.cos(theta) * spd,
            vy: Math.sin(theta) * spd,
            life: 0.45,
            maxLife: 0.45,
            color: "#ffdf55",
            size: 3.5
          });
        }
        (w.shockwaves || (w.shockwaves = [])).push({ x: sec.x, y: sec.y, rad: 8, maxRad: 170, life: 0.45, maxLife: 0.45 });

        // Fracture neighbor borders & displace ambient embers
        const row = Math.floor(idx / 3), col = idx % 3;
        w.sectors.forEach((adj, aIdx) => {
          const aR = Math.floor(aIdx / 3), aC = aIdx % 3;
          if (Math.abs(row - aR) + Math.abs(col - aC) === 1) {
            adj.fractureLevel = Math.min(3, adj.fractureLevel + 1);
          }
        });

        w.embers.forEach((em) => {
          const edx = em.x - sec.x, edy = em.y - sec.y;
          const edist = Math.hypot(edx, edy) || 1;
          if (edist < 140) {
            const push = Math.max(0, 110 - edist) * 1.8;
            em.x += (edx / edist) * push;
            em.y += (edy / edist) * push;
          }
        });
      }
    });
  },

  update: function(dt, state) {
    const w = state.world;
    if (!w || !w.singularity) return;
    w.time = (w.time || 0) + dt;

    // Singularity Graviton Pulse
    const sing = w.singularity;
    sing.pulsePhase = (sing.pulsePhase + dt * 2.4) % (Math.PI * 2);
    w.breathWindow = Math.sin(sing.pulsePhase);

    // Contested Triad Corridor Detection
    const lat = w.lattice;
    w.contestedLines = [];
    if (lat && lat.board) {
      const triads = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
      triads.forEach((t) => {
        const s0 = lat.board[t[0]], s1 = lat.board[t[1]], s2 = lat.board[t[2]];
        const syms = [s0, s1, s2].filter(Boolean);
        if (syms.length === 2 && syms[0] === syms[1]) {
          (w.contestedLines || (w.contestedLines = [])).push(t);
        }
      });
    }

    // Graviton Pull on Visual Pointer Cursor
    const ptr = state.pointer;
    if (ptr && sing.active) {
      const dx = sing.x - ptr.x, dy = sing.y - ptr.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 260 && dist > 8) {
        const pull = (sing.strength * 480 / (dist + 40)) * dt;
        ptr.x += (dx / dist) * pull;
        ptr.y += (dy / dist) * pull;
      }
    }

    // Singularity Velocity Gravitational Bending on Particles & Embers
    const G = 14000;
    (w.particles || []).forEach((p) => {
      const pdx = sing.x - p.x, pdy = sing.y - p.y;
      const pdist = Math.max(12, Math.hypot(pdx, pdy));
      const acc = Math.min(400, G / Math.pow(pdist, 1.5));
      p.vx = (p.vx || 0) + (pdx / pdist) * acc * dt;
      p.vy = (p.vy || 0) + (pdy / pdist) * acc * dt;
    });

    w.embers.forEach((em) => {
      const edx = sing.x - em.x, edy = sing.y - em.y;
      const edist = Math.max(20, Math.hypot(edx, edy));
      const pull = Math.min(65, 4200 / (edist * edist));
      em.vx += (edx / edist) * pull * dt + (Math.random() - 0.5) * 4 * dt;
      em.vy += (edy / edist) * pull * dt + (Math.random() - 0.5) * 4 * dt;
      em.vx *= 0.98;
      em.vy *= 0.98;
      em.x += em.vx * dt;
      em.y += em.vy * dt;
      if (em.x < 220 || em.x > 580) em.vx *= -1;
      if (em.y < 130 || em.y > 490) em.vy *= -1;
    });

    // Update Expanding Kinetic Shockwaves
    for (let i = w.shockwaves.length - 1; i >= 0; i--) {
      const sw = w.shockwaves[i];
      sw.life -= dt;
      sw.rad += (sw.maxRad - sw.rad) * (dt * 12);
      if (sw.life <= 0) w.shockwaves.splice(i, 1);
    }

    if (w.shake > 0) w.shake = Math.max(0, w.shake - dt * 24);
  },

  render: function(ctx, state) {
    const w = state.world;
    if (!w || !w.singularity) return;
    const t = w.time || 0;
    const sing = w.singularity;

    ctx.save();
    // Context-Aware Screen Shake bounded to World Render Pass
    if (w.shake > 0) {
      const sx = (Math.random() - 0.5) * w.shake * 1.5;
      const sy = (Math.random() - 0.5) * w.shake * 1.5;
      ctx.translate(sx, sy);
    }

    // 1. Diegetic Radiant Crucible Bloom over Contested Corridors
    if (w.contestedLines && w.contestedLines.length > 0) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      w.contestedLines.forEach((triad, lIdx) => {
        const p0 = w.sectors[triad[0]], p2 = w.sectors[triad[2]];
        const cx = (p0.x + p2.x) * 0.5, cy = (p0.y + p2.y) * 0.5;
        const pulse = 0.85 + Math.sin(t * 6 + lIdx) * 0.15;
        const grad = ctx.createRadialGradient(cx, cy, 14, cx, cy, 130 * pulse);
        grad.addColorStop(0, "rgba(255, 190, 40, 0.24)");
        grad.addColorStop(0.55, "rgba(255, 110, 20, 0.08)");
        grad.addColorStop(1, "rgba(7, 9, 19, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx, cy, 130 * pulse, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    }

    // 2. Ambient Astral Embers
    ctx.save();
    w.embers.forEach((em) => {
      ctx.fillStyle = em.hue === 45 ? `rgba(250, 204, 21, ${em.alpha})` : `rgba(0, 243, 255, ${em.alpha})`;
      ctx.beginPath();
      ctx.arc(em.x, em.y, em.rad, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.restore();

    // 3. Astra-Singularity Graviton Core
    ctx.save();
    const breath = 0.5 + 0.5 * Math.sin(sing.pulsePhase);
    const coreRad = sing.eventHorizonRadius + breath * 9;
    const singGrad = ctx.createRadialGradient(sing.x, sing.y, 4, sing.x, sing.y, coreRad * 1.6);
    singGrad.addColorStop(0, "rgba(255, 255, 255, 0.95)");
    singGrad.addColorStop(0.35, "rgba(0, 243, 255, 0.45)");
    singGrad.addColorStop(0.7, "rgba(250, 204, 21, 0.18)");
    singGrad.addColorStop(1, "rgba(7, 9, 19, 0)");
    ctx.fillStyle = singGrad;
    ctx.beginPath();
    ctx.arc(sing.x, sing.y, coreRad * 1.6, 0, Math.PI * 2);
    ctx.fill();

    // Pulse Wave Rings
    ctx.strokeStyle = `rgba(0, 243, 255, ${0.15 + breath * 0.35})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(sing.x, sing.y, coreRad, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // 4. Diegetic Stress Fractures along Partition Borders
    ctx.save();
    w.sectors.forEach((sec) => {
      if (sec.fractureLevel > 0) {
        ctx.strokeStyle = sec.fractureLevel >= 3 ? "rgba(255, 220, 100, 0.85)" : "rgba(0, 243, 255, 0.65)";
        ctx.lineWidth = 1.2 + sec.fractureLevel * 0.7;
        const fDist = sec.fractureLevel * 2.8;
        ctx.beginPath();
        for (let a = 0; a < 4; a++) {
          const ang = (a * Math.PI) / 2;
          const x0 = sec.x + Math.cos(ang) * 22, y0 = sec.y + Math.sin(ang) * 22;
          const x1 = x0 + Math.cos(ang) * (26 + fDist);
          const y1 = y0 + Math.sin(ang) * (26 + fDist);
          const mx = (x0 + x1) * 0.5 + Math.sin(sec.id + a) * fDist;
          const my = (y0 + y1) * 0.5 + Math.cos(sec.id + a) * fDist;
          ctx.moveTo(x0, y0);
          ctx.lineTo(mx, my);
          ctx.lineTo(x1, y1);
        }
        ctx.stroke();
      }
    });
    ctx.restore();

    // 5. Kinetic Shockwave Rings Pass
    if (w.shockwaves.length > 0) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      w.shockwaves.forEach((sw) => {
        const ratio = Math.max(0, sw.life / sw.maxLife);
        ctx.strokeStyle = `rgba(255, 230, 120, ${ratio * 0.9})`;
        ctx.lineWidth = ratio * 6;
        ctx.beginPath();
        ctx.arc(sw.x, sw.y, sw.rad, 0, Math.PI * 2);
        ctx.stroke();
      });
      ctx.restore();
    }

    ctx.restore();
  }
});
