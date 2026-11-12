// Cohesive Milestone Plugin: v0.3.0
// Cohesive Milestone Plugin: v0.3.0
window.StudioEngine.registerModule("Milestone_v0_3_0", {
  init: function(state, engine) {
    state.audio = state.audio || {
      ctx: null, step: 0, nextStepTime: 0, bpm: 128, noiseBuf: null,
      kickGain: null, bassGain: null, snareGain: null, leadGain: null, masterGain: null
    };
    state.player.mods = state.player.mods || [];
    state.player.ricochetCount = state.player.ricochetCount || 0;
    state.player.chainLightning = state.player.chainLightning || false;
    state.player.orbitalSaws = state.player.orbitalSaws || 0;
    state.player.afterburnerNova = state.player.afterburnerNova || false;
    state.world.sawAngle = 0;
    state.world.lightningArcs = [];
    state.world.waveIndex = state.world.waveIndex || 1;
    state.world.waveActive = state.world.waveActive !== undefined ? state.world.waveActive : true;
    state.world.waveTransition = 0;
    state.modal = null;
    this.prevDraftKeys = {};

    this.MOD_CATALOG = [
      { id: 'ricochet_prism', title: 'RICOCHET PRISM', color: '#00f3ff', desc: 'Lasers bounce off screen boundaries +2 times', icon: [0x18,0x24,0x42,0x81,0x42,0x24,0x18,0x00], apply: p => { p.ricochetCount = (p.ricochetCount || 0) + 2; } },
      { id: 'chain_lightning', title: 'CHAIN LIGHTNING', color: '#39ff14', desc: 'Shatters arc high-voltage arcs to adjacent targets', icon: [0x08,0x1c,0x3e,0x0c,0x18,0x30,0x10,0x00], apply: p => { p.chainLightning = true; } },
      { id: 'orbital_saws', title: 'ORBITAL SAWS', color: '#ffea00', desc: 'Dual kinetic neon plasma blades shred proximity threats', icon: [0x3c,0x42,0x81,0xa5,0xa5,0x81,0x42,0x3c], apply: p => { p.orbitalSaws = (p.orbitalSaws || 0) + 1; } },
      { id: 'afterburner_nova', title: 'AFTERBURNER NOVA', color: '#ff007f', desc: 'High thruster burns vent explosive plasma shockwaves', icon: [0x18,0x3c,0x7e,0xff,0xdb,0x99,0x18,0x00], apply: p => { p.afterburnerNova = true; } }
    ];
  },

  ensureAudio: function(state) {
    const a = state.audio;
    if (!a.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return false;
      a.ctx = new AC();
      a.masterGain = a.ctx.createGain();
      a.masterGain.gain.setValueAtTime(0.135, a.ctx.currentTime);
      a.masterGain.connect(a.ctx.destination);
      const bLen = Math.floor(a.ctx.sampleRate * 0.2);
      a.noiseBuf = a.ctx.createBuffer(1, bLen, a.ctx.sampleRate);
      const out = a.noiseBuf.getChannelData(0);
      for (let i = 0; i < bLen; i++) out[i] = Math.random() * 2 - 1;
      a.nextStepTime = a.ctx.currentTime + 0.05;
    }
    if (a.ctx.state === 'suspended') a.ctx.resume();
    return true;
  },

  stepAudio: function(state) {
    if (!this.ensureAudio(state)) return;
    const a = state.audio, t = a.ctx.currentTime, stepDur = 60 / (a.bpm * 4);
    while (a.nextStepTime < t + 0.1) {
      const st = a.nextStepTime, s = a.step;
      if (s % 4 === 0) {
        state.world.beatPulse = 1.0;
        const osc = a.ctx.createOscillator(), g = a.ctx.createGain();
        osc.frequency.setValueAtTime(140, st);
        osc.frequency.exponentialRampToValueAtTime(35, st + 0.09);
        g.gain.setValueAtTime(0.158, st);
        g.gain.exponentialRampToValueAtTime(0.001, st + 0.12);
        osc.connect(g); g.connect(a.masterGain);
        osc.start(st); osc.stop(st + 0.12);
      }
      if (s % 8 === 4 && a.noiseBuf) {
        const src = a.ctx.createBufferSource(), f = a.ctx.createBiquadFilter(), g = a.ctx.createGain();
        src.buffer = a.noiseBuf; f.type = 'bandpass'; f.frequency.setValueAtTime(624, st); f.Q.value = 2.0;
        g.gain.setValueAtTime(0.113, st); g.gain.exponentialRampToValueAtTime(0.001, st + 0.11);
        src.connect(f); f.connect(g); g.connect(a.masterGain);
        src.start(st); src.stop(st + 0.11);
      }
      const bassFreqs = [55.0, 65.4, 73.4, 82.4, 73.4, 65.4, 55.0, 98.0];
      const bOsc = a.ctx.createOscillator(), bFilt = a.ctx.createBiquadFilter(), bG = a.ctx.createGain();
      bOsc.type = 'sawtooth';
      bOsc.frequency.setValueAtTime(bassFreqs[s % bassFreqs.length], st);
      bFilt.type = 'lowpass';
      bFilt.frequency.setValueAtTime(320 + Math.min(600, (state.stats?.combo || 1) * 80), st);
      bG.gain.setValueAtTime(0.081, st);
      bG.gain.exponentialRampToValueAtTime(0.001, st + stepDur * 0.9);
      bOsc.connect(bFilt); bFilt.connect(bG); bG.connect(a.masterGain);
      bOsc.start(st); bOsc.stop(st + stepDur * 0.9);

      if ((state.stats?.combo || 1) >= 2) {
        const lFreqs = [293.66, 349.23, 392.0, 440.0, 523.25, 587.33];
        const lOsc = a.ctx.createOscillator(), lG = a.ctx.createGain();
        lOsc.type = 'square';
        lOsc.frequency.setValueAtTime(lFreqs[(s * 3) % lFreqs.length], st);
        const lVol = Math.min(0.12, (state.stats.combo - 1) * 0.03);
        lG.gain.setValueAtTime(lVol, st);
        lG.gain.exponentialRampToValueAtTime(0.001, st + 0.08);
        lOsc.connect(lG); lG.connect(a.masterGain);
        lOsc.start(st); lOsc.stop(st + 0.08);
      }
      a.step = (a.step + 1) % 16;
      a.nextStepTime += stepDur;
    }
  },

  playLaserSFX: function(state, freq, decay) {
    if (!this.ensureAudio(state)) return;
    const a = state.audio, t = a.ctx.currentTime, osc = a.ctx.createOscillator(), g = a.ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(freq || 900, t);
    osc.frequency.exponentialRampToValueAtTime(140, t + (decay || 0.14));
    g.gain.setValueAtTime(0.068, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + (decay || 0.14));
    osc.connect(g); g.connect(a.masterGain);
    osc.start(t); osc.stop(t + (decay || 0.14));
  },

  playShatterSFX: function(state, impact) {
    if (!this.ensureAudio(state) || !state.audio.noiseBuf) return;
    const a = state.audio, t = a.ctx.currentTime, src = a.ctx.createBufferSource(), f = a.ctx.createBiquadFilter(), g = a.ctx.createGain();
    src.buffer = a.noiseBuf; f.type = 'bandpass';
    f.frequency.setValueAtTime(600 + (impact || 1) * 400, t);
    g.gain.setValueAtTime(Math.min(0.35, 0.15 + (impact || 1) * 0.08), t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
    src.connect(f); f.connect(g); g.connect(a.masterGain);
    src.start(t); src.stop(t + 0.16);
  },

  openDraft: function(state) {
    const pool = [...this.MOD_CATALOG].sort(() => Math.random() - 0.5);
    state.modal = { type: 'DRAFT', animTime: 0, selected: 0, cards: pool.slice(0, 3) };
    state.paused = true;
  },

  update: function(dt, state, engine) {
    if (!state.running) return;
    if (state.keys?.action || state.keys?.up || state.pointer?.clicked) this.ensureAudio(state);
    this.stepAudio(state);

    state.world.beatPulse = Math.max(0, (state.world.beatPulse || 0) - dt * 3.5);

    if (state.modal && state.modal.type === 'DRAFT') {
      state.modal.animTime += dt;
      const k = state.keys || {}, m = state.modal;
      if (k.left && !this.prevDraftKeys.left) m.selected = (m.selected + 2) % 3;
      if (k.right && !this.prevDraftKeys.right) m.selected = (m.selected + 1) % 3;
      let pick = -1;
      if (k.digit1 && !this.prevDraftKeys.digit1) pick = 0;
      if (k.digit2 && !this.prevDraftKeys.digit2) pick = 1;
      if (k.digit3 && !this.prevDraftKeys.digit3) pick = 2;
      if ((k.action || k.jump) && !this.prevDraftKeys.action) pick = m.selected;

      if (state.pointer?.clicked) {
        for (let i = 0; i < 3; i++) {
          const cx = 200 + i * 200, cy = 300;
          if (Math.abs(state.pointer.x - cx) < 85 && Math.abs(state.pointer.y - cy) < 130) pick = i;
        }
      }
      if (pick >= 0 && pick < m.cards.length) {
        const chosen = m.cards[pick];
        (state.player.mods || (state.player.mods = [])).push(chosen.id);
        chosen.apply(state.player);
        this.playLaserSFX(state, 1200, 0.25);
        state.modal = null;
        state.paused = false;
        state.world.waveIndex = (state.world.waveIndex || 1) + 1;
        state.world.waveTransition = 1.0;
        state.world.waveActive = true;
      }
      this.prevDraftKeys = { ...k, action: k.action || k.jump };
      return;
    }
    this.prevDraftKeys = { ...(state.keys || {}) };

    if (!state.paused) {
      const p = state.player, w = state.world;
      w.sawAngle = (w.sawAngle || 0) + dt * 6.0;

      if (p.orbitalSaws > 0) {
        const sawCount = p.orbitalSaws * 2;
        for (let s = 0; s < sawCount; s++) {
          const ang = w.sawAngle + (s / sawCount) * Math.PI * 2;
          const sx = p.x + Math.cos(ang) * 58, sy = p.y + Math.sin(ang) * 58;
          (w.asteroids || []).forEach(ast => {
            if (Math.hypot(ast.x - sx, ast.y - sy) < ast.r + 12) {
              ast.hp -= dt * 4;
              (w.particles || (w.particles = [])).push({ x: sx, y: sy, vx: (Math.random() - 0.5) * 160, vy: (Math.random() - 0.5) * 160, life: 0.15, maxLife: 0.15, color: '#ffea00', size: 3 });
              if (Math.random() < 0.2) this.playShatterSFX(state, 1);
            }
          });
        }
      }

      if (p.ricochetCount > 0 && w.lasers) {
        w.lasers.forEach(l => {
          l.bounces = l.bounces || 0;
          if (l.bounces < p.ricochetCount) {
            if (l.x < 4 || l.x > 796) { l.vx *= -1; l.bounces++; this.playLaserSFX(state, 800, 0.05); }
            if (l.y < 36 || l.y > 596) { l.vy *= -1; l.bounces++; this.playLaserSFX(state, 800, 0.05); }
          }
        });
      }

      if (p.afterburnerNova && state.keys?.up && Math.random() < 0.25) {
        const rad = p.angle + Math.PI + (Math.random() - 0.5) * 0.4;
        (w.particles || (w.particles = [])).push({ x: p.x, y: p.y, vx: Math.cos(rad) * 220, vy: Math.sin(rad) * 220, life: 0.35, maxLife: 0.35, color: '#ff007f', size: 5 });
      }

      for (let i = (w.lightningArcs || []).length - 1; i >= 0; i--) {
        w.lightningArcs[i].life -= dt;
        if (w.lightningArcs[i].life <= 0) w.lightningArcs.splice(i, 1);
      }

      if (w.waveTransition > 0) {
        w.waveTransition -= dt;
        if (w.waveTransition <= 0 && (!w.asteroids || w.asteroids.length === 0)) {
          const count = 3 + state.world.waveIndex * 2;
          for (let i = 0; i < count; i++) {
            const ex = Math.random() < 0.5 ? Math.random() * 180 : 620 + Math.random() * 180;
            (w.asteroids || (w.asteroids = [])).push(window.StudioEngine?.modules?.Milestone_v0_1_0?.spawnAsteroid
              ? window.StudioEngine.modules.Milestone_v0_1_0.spawnAsteroid(Math.random() < 0.5 ? 3 : 2, ex, Math.random() * 500 + 50)
              : { tier: 3, x: ex, y: Math.random() * 500 + 50, r: 38, vx: (Math.random() - 0.5) * 60, vy: (Math.random() - 0.5) * 60, pts: [], hp: 3, color: '#ff007f' });
          }
        }
      } else if (w.waveActive && (!w.asteroids || w.asteroids.length === 0)) {
        w.waveActive = false;
        this.openDraft(state);
      }
    }
  },

  render: function(ctx, state) {
    ctx.save();
    const bp = state.world?.beatPulse || 0, w = state.world;

    ctx.save();
    ctx.strokeStyle = '#ff007f';
    ctx.globalAlpha = 0.08 + 0.2 * bp;
    ctx.lineWidth = 1.0 + 2.5 * bp;
    ctx.beginPath();
    for (let x = 0; x <= 800; x += 50) { ctx.moveTo(x, 34); ctx.lineTo(x, 600); }
    for (let y = 34; y <= 600; y += 50) { ctx.moveTo(0, y); ctx.lineTo(800, y); }
    ctx.stroke();
    ctx.restore();

    if (w?.stars) {
      ctx.save();
      for (const s of w.stars) {
        ctx.fillStyle = s.c;
        ctx.shadowColor = s.c;
        ctx.shadowBlur = 4 * bp;
        const rad = Math.max(0.5, s.s * (1.0 + 0.4 * bp));
        ctx.fillRect(s.x - rad, s.y - rad, rad * 2, rad * 2);
      }
      ctx.restore();
    }

    if (w?.lightningArcs) {
      ctx.save();
      ctx.strokeStyle = '#39ff14'; ctx.shadowColor = '#39ff14'; ctx.shadowBlur = 10; ctx.lineWidth = 2;
      for (const arc of w.lightningArcs) {
        ctx.beginPath(); ctx.moveTo(arc.x1, arc.y1);
        ctx.lineTo((arc.x1 + arc.x2) / 2 + (Math.random() - 0.5) * 20, (arc.y1 + arc.y2) / 2 + (Math.random() - 0.5) * 20);
        ctx.lineTo(arc.x2, arc.y2); ctx.stroke();
      }
      ctx.restore();
    }

    const p = state.player;
    if (p && p.orbitalSaws > 0) {
      ctx.save();
      const count = p.orbitalSaws * 2;
      for (let s = 0; s < count; s++) {
        const ang = (w?.sawAngle || 0) + (s / count) * Math.PI * 2;
        const sx = p.x + Math.cos(ang) * 58, sy = p.y + Math.sin(ang) * 58;
        ctx.translate(sx, sy); ctx.rotate(w?.sawAngle * 3);
        ctx.fillStyle = '#ffea00'; ctx.shadowColor = '#ffea00'; ctx.shadowBlur = 12;
        ctx.beginPath();
        for (let b = 0; b < 6; b++) {
          const ba = (b / 6) * Math.PI * 2, r = b % 2 === 0 ? 12 : 5;
          ctx.lineTo(Math.cos(ba) * r, Math.sin(ba) * r);
        }
        ctx.closePath(); ctx.fill();
        ctx.setTransform(1,0,0,1,0,0);
      }
      ctx.restore();
    }

    if (state.modal && state.modal.type === 'DRAFT') {
      const m = state.modal;
      ctx.fillStyle = 'rgba(5, 2, 13, 0.88)';
      ctx.fillRect(0, 0, 800, 600);
      ctx.textAlign = 'center'; ctx.font = '900 24px monospace'; ctx.fillStyle = '#00f3ff';
      ctx.shadowColor = '#00f3ff'; ctx.shadowBlur = 14;
      ctx.fillText('// HYPER-MOD SYNTHESIS UNIT //', 400, 110);
      ctx.font = '12px monospace'; ctx.fillStyle = '#ffea00'; ctx.shadowBlur = 6;
      ctx.fillText('SELECT ONE MODIFIER TO ENHANCE SHIP CORE [1] [2] [3]', 400, 138);

      for (let i = 0; i < m.cards.length; i++) {
        const card = m.cards[i], isSel = m.selected === i;
        const cx = 200 + i * 200, cy = 330;
        const scale = isSel ? 1.05 + 0.04 * Math.sin(m.animTime * 8) : 1.0;
        ctx.save();
        ctx.translate(cx, cy); ctx.scale(scale, scale);
        ctx.fillStyle = '#0a0518'; ctx.strokeStyle = card.color;
        ctx.lineWidth = isSel ? 3.5 : 1.5;
        ctx.shadowColor = card.color; ctx.shadowBlur = isSel ? 20 : 6;
        ctx.fillRect(-85, -140, 170, 280);
        ctx.strokeRect(-85, -140, 170, 280);

        ctx.fillStyle = card.color;
        for (let row = 0; row < 8; row++) {
          for (let col = 0; col < 8; col++) {
            if ((card.icon[row] >> (7 - col)) & 1) ctx.fillRect(-32 + col * 8, -100 + row * 8, 7, 7);
          }
        }
        ctx.font = '900 13px monospace'; ctx.fillText(card.title, 0, -10);
        ctx.font = '11px monospace'; ctx.fillStyle = '#ffffff'; ctx.shadowBlur = 0;
        const words = card.desc.split(' ');
        let line = '', ly = 24;
        for (const word of words) {
          if ((line + word).length > 18) { ctx.fillText(line, 0, ly); line = word + ' '; ly += 16; }
          else line += word + ' ';
        }
        ctx.fillText(line, 0, ly);
        ctx.fillStyle = isSel ? card.color : '#555'; ctx.font = '900 14px monospace';
        ctx.fillText(`[ KEY ${i + 1} ]`, 0, 115);
        ctx.restore();
      }
    }
    ctx.restore();
  }
});
