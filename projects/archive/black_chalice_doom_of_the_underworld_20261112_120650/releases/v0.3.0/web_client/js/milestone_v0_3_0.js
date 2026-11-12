// Cohesive Milestone Plugin: v0.3.0
// Cohesive Milestone Plugin: v0.3.0 (Diablo-style Procedural Loot, Ultima Underworld Physics, & 68-BPM Stoner-Doom Audio DSP)
window.StudioEngine.registerModule("Milestone_v0_3_0", {
  init: function(state, engine) {
    state.world.droppedLoot = state.world.droppedLoot || [];
    state.world.interactives = state.world.interactives || [];
    state.world.projectiles = state.world.projectiles || state.world.lasers || [];
    state.player.equipment = state.player.equipment || { weapon: null };
    state.player.attackArcRadius = state.player.attackArcRadius || 48;
    state.player.attackArcColor = state.player.attackArcColor || "#eab308";
    this.prevAction = false;
    this.spawnDefaults(state);
    this.initAudio(state);

    engine.on("SPAWN_LOOT", (data) => this.spawnLoot(state, data.x, data.y, data.tier));
    engine.on("ELITE_KILLED", (data) => this.spawnLoot(state, data.x, data.y, data.tier || 'doom'));
    engine.on("CHEST_OPENED", (data) => this.spawnLoot(state, data.x, data.y, data.tier || 'occult'));
  },

  spawnDefaults: function(state) {
    const w = state.world;
    if (w.interactives.length === 0) {
      (w.interactives || (w.interactives = [])).push(
        { type: 'brazier', x: 260, y: 260, vx: 0, vy: 0, radius: 18, burning: true },
        { type: 'oil', x: 380, y: 260, vx: 0, vy: 0, radius: 34, burning: false, timer: 0 },
        { type: 'plate', x: 500, y: 340, vx: 0, vy: 0, radius: 16, triggered: false },
        { type: 'cauldron', x: 400, y: 160, vx: 0, vy: 0, radius: 22, brewed: false }
      );
      this.spawnLoot(state, 320, 360, 'verdigris');
      this.spawnLoot(state, 460, 360, 'doom');
    }
  },

  initAudio: function(state) {
    if (state.audio && state.audio.ctx) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      const ctx = new AC();
      const master = ctx.createGain();
      master.gain.value = 0.22;
      master.connect(ctx.destination);

      const fCurve = new Float32Array(256);
      for (let i = 0; i < 256; i++) {
        const x = (i * 2) / 256 - 1;
        fCurve[i] = ((Math.PI + 4) * x) / (Math.PI + 4 * Math.abs(x));
      }
      const fuzz = ctx.createWaveShaper();
      fuzz.curve = fCurve; fuzz.oversample = '4x';

      const lpf = ctx.createBiquadFilter();
      lpf.type = 'lowpass'; lpf.frequency.value = 280;

      fuzz.connect(lpf);
      lpf.connect(master);

      state.audio = { ctx, master, fuzz, lpf, nextStep: 0, stepIdx: 0, riff: [65.41, 65.41, 77.78, 73.42, 65.41, 98.0, 92.5, 77.78] };
    } catch (e) {}
  },

  playStepDSP: function(state) {
    const a = state.audio;
    if (!a || !a.ctx || a.ctx.state !== 'running') return;
    const t = a.ctx.currentTime;
    const osc = a.ctx.createOscillator();
    const sub = a.ctx.createOscillator();
    const g = a.ctx.createGain();
    const freq = a.riff[a.stepIdx % a.riff.length];

    osc.type = 'sawtooth'; osc.frequency.setValueAtTime(freq, t);
    sub.type = 'square'; sub.frequency.setValueAtTime(freq * 0.5, t);

    g.gain.setValueAtTime(0.3, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.42);

    osc.connect(g); sub.connect(g);
    g.connect(a.fuzz);
    osc.start(t); sub.start(t);
    osc.stop(t + 0.44); sub.stop(t + 0.44);

    if (a.stepIdx % 4 === 0) {
      const bOsc = a.ctx.createOscillator();
      const bG = a.ctx.createGain();
      bOsc.frequency.setValueAtTime(110, t);
      bOsc.frequency.exponentialRampToValueAtTime(32, t + 0.25);
      bG.gain.setValueAtTime(0.5, t);
      bG.gain.exponentialRampToValueAtTime(0.001, t + 0.28);
      bOsc.connect(bG); bG.connect(a.master);
      bOsc.start(t); bOsc.stop(t + 0.3);
    }
    a.stepIdx = (a.stepIdx + 1) % 8;
  },

  playChime: function(state) {
    const a = state.audio;
    if (!a || !a.ctx) return;
    const t = a.ctx.currentTime;
    const o = a.ctx.createOscillator();
    const g = a.ctx.createGain();
    o.type = 'triangle';
    o.frequency.setValueAtTime(640, t);
    o.frequency.exponentialRampToValueAtTime(440, t + 0.35);
    g.gain.setValueAtTime(0.06, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + 0.35);
    o.connect(g); g.connect(a.master);
    o.start(t); o.stop(t + 0.36);
  },

  spawnLoot: function(state, x, y, forcedTier) {
    const tiers = {
      iron: { name: 'Rusty Iron', color: '#9ca3af', scale: 0.9, dmg: 1.0 },
      verdigris: { name: 'Runic Verdigris', color: '#10b981', scale: 1.15, dmg: 1.35, elem: 'acid' },
      occult: { name: 'Occult Purple', color: '#a855f7', scale: 1.3, dmg: 1.6, elem: 'electric' },
      doom: { name: 'Doom-Forged Gold', color: '#eab308', scale: 1.45, dmg: 1.9, elem: 'fire' },
      blood: { name: 'Blood-Cursed Crimson', color: '#dc2626', scale: 1.6, dmg: 2.3, elem: 'blood' }
    };
    const affixes = [
      { name: "of the Electric Wizard", elem: 'electric', dmgMult: 1.35, color: '#38bdf8' },
      { name: "Vampiric", elem: 'blood', dmgMult: 1.25, color: '#ef4444' },
      { name: "Vorpal", elem: 'doom', dmgMult: 1.5, color: '#f59e0b' },
      { name: "Acid-Drenched", elem: 'acid', dmgMult: 1.2, color: '#22c55e' }
    ];
    const tierKeys = Object.keys(tiers);
    const tierKey = forcedTier || tierKeys[Math.floor(Math.random() * tierKeys.length)];
    const base = tiers[tierKey];
    const affix = affixes[Math.floor(Math.random() * affixes.length)];
    const finalDmg = Math.round((state.player.weaponDamage || 25) * base.dmg * affix.dmgMult);

    const item = {
      id: Math.random().toString(36).substr(2, 6),
      name: `${base.name} Cleaver ${affix.name}`,
      tier: tierKey,
      color: affix.color || base.color,
      arcScale: base.scale,
      damage: finalDmg,
      element: affix.elem || base.elem || 'none'
    };

    (state.world.droppedLoot || (state.world.droppedLoot = [])).push({
      id: item.id, x, y, tier: tierKey, color: item.color,
      beamH: 0, beamMax: 64, itemData: item
    });
    this.playChime(state);
  },

  update: function(dt, state) {
    if (state.paused) return;
    const p = state.player;
    const w = state.world;
    const actionPressed = state.keys.action && !this.prevAction;

    // Web Audio Sequencer (68-BPM ~0.441s step)
    if (state.audio && state.audio.ctx) {
      if (state.audio.ctx.state === 'suspended' && (state.keys.jump || state.keys.action)) state.audio.ctx.resume();
      if (state.audio.ctx.currentTime >= state.audio.nextStep) {
        this.playStepDSP(state);
        state.audio.nextStep = state.audio.ctx.currentTime + 0.441;
      }
    }

    // Dropped Loot update & Pickup
    let nearestLoot = null;
    let minD = 40;
    for (let i = w.droppedLoot.length - 1; i >= 0; i--) {
      const l = w.droppedLoot[i];
      l.beamH = Math.min(l.beamMax, l.beamH + dt * 140);
      const d = Math.hypot(p.x - l.x, p.y - l.y);
      if (d < minD) { minD = d; nearestLoot = l; }
      if (d < 30 && actionPressed) {
        p.equipment.weapon = l.itemData;
        p.attackArcRadius = 48 * l.itemData.arcScale;
        p.attackArcColor = l.itemData.color;
        p.weaponDamage = l.itemData.damage;
        (w.floatingTexts || (w.floatingTexts = [])).push({ text: `EQUIPPED: ${l.itemData.name}`, x: p.x - 40, y: p.y - 30, timer: 1.2, color: l.itemData.color });
        w.droppedLoot.splice(i, 1);
        this.playChime(state);
      }
    }

    // Interactives Physics & Logic
    for (let i = 0; i < w.interactives.length; i++) {
      const obj = w.interactives[i];
      if (obj.type === 'brazier') {
        const d = Math.hypot(p.x - obj.x, p.y - obj.y);
        if (d < 34 && actionPressed) {
          const ang = p.facingAngle !== undefined ? p.facingAngle : Math.atan2(p.vy, p.vx);
          obj.vx = Math.cos(ang) * 340;
          obj.vy = Math.sin(ang) * 340;
          w.cameraShake = Math.max(w.cameraShake, 6);
        }
        obj.x += obj.vx * dt; obj.y += obj.vy * dt;
        obj.vx *= 0.88; obj.vy *= 0.88;

        for (let j = 0; j < w.interactives.length; j++) {
          const oil = w.interactives[j];
          if (oil.type === 'oil' && !oil.burning && Math.hypot(obj.x - oil.x, obj.y - oil.y) < 32) {
            oil.burning = true; oil.timer = 8.0;
            (w.floatingTexts || (w.floatingTexts = [])).push({ text: "OIL INFERNO!", x: oil.x - 24, y: oil.y - 12, timer: 1.0, color: "#f97316" });
          }
        }
      } else if (obj.type === 'oil') {
        if (obj.burning) {
          obj.timer -= dt;
          if (Math.hypot(p.x - obj.x, p.y - obj.y) < obj.radius && (!p.invuln || p.invuln <= 0)) {
            p.health = Math.max(0, p.health - dt * 2.5);
            w.cameraShake = Math.max(w.cameraShake, 3);
          }
          if (obj.timer <= 0) obj.burning = false;
        }
      } else if (obj.type === 'plate') {
        const d = Math.hypot(p.x - obj.x, p.y - obj.y);
        if (d < obj.radius && !obj.triggered) {
          obj.triggered = true;
          const angle = Math.atan2(p.y - obj.y, p.x - obj.x);
          (w.projectiles || (w.projectiles = [])).push({
            x: obj.x, y: obj.y, vx: Math.cos(angle) * 220, vy: Math.sin(angle) * 220,
            radius: 5, color: '#eab308', damage: 1, timer: 2.0
          });
          (w.floatingTexts || (w.floatingTexts = [])).push({ text: "TRAP SPRUNG!", x: obj.x - 20, y: obj.y - 14, timer: 0.8, color: "#ef4444" });
        } else if (d >= obj.radius + 8) {
          obj.triggered = false;
        }
      } else if (obj.type === 'cauldron') {
        if (Math.hypot(p.x - obj.x, p.y - obj.y) < obj.radius + 14 && actionPressed && !obj.brewed) {
          obj.brewed = true;
          p.health = Math.min(p.maxHealth, p.health + 2);
          p.torchLevel = Math.min(100, (p.torchLevel || 80) + 30);
          (w.floatingTexts || (w.floatingTexts = [])).push({ text: "ELIXIR RESTORED HP & FLAME", x: obj.x - 45, y: obj.y - 20, timer: 1.3, color: "#10b981" });
        }
      }
    }

    this.prevAction = !!state.keys.action;
  },

  render: function(ctx, state) {
    if (state.paused) return;
    const p = state.player;
    const w = state.world;

    ctx.save();
    // Environmental Interactives
    for (let i = 0; i < w.interactives.length; i++) {
      const o = w.interactives[i];
      ctx.beginPath();
      if (o.type === 'oil') {
        ctx.fillStyle = o.burning ? 'rgba(239, 68, 68, 0.75)' : '#17141f';
        ctx.arc(o.x, o.y, o.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = o.burning ? '#f59e0b' : '#332940';
        ctx.lineWidth = 2; ctx.stroke();
      } else if (o.type === 'brazier') {
        ctx.fillStyle = '#27272a';
        ctx.arc(o.x, o.y, o.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath(); ctx.arc(o.x, o.y, 8, 0, Math.PI * 2); ctx.fill();
      } else if (o.type === 'plate') {
        ctx.fillStyle = o.triggered ? '#dc2626' : '#52525b';
        ctx.fillRect(o.x - 12, o.y - 12, 24, 24);
        ctx.strokeStyle = '#27272a'; ctx.strokeRect(o.x - 12, o.y - 12, 24, 24);
      } else if (o.type === 'cauldron') {
        ctx.fillStyle = '#18181b';
        ctx.arc(o.x, o.y, o.radius, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = o.brewed ? '#3f3f46' : '#10b981';
        ctx.beginPath(); ctx.arc(o.x, o.y, o.radius - 6, 0, Math.PI * 2); ctx.fill();
      }
    }

    // Dropped Loot Beams & Icons
    let inspected = null;
    for (let i = 0; i < w.droppedLoot.length; i++) {
      const l = w.droppedLoot[i];
      const grad = ctx.createLinearGradient(l.x, l.y, l.x, l.y - l.beamH);
      grad.addColorStop(0, l.color);
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.fillRect(l.x - 4, l.y - l.beamH, 8, l.beamH);

      ctx.fillStyle = l.color;
      ctx.beginPath(); ctx.arc(l.x, l.y, 6, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();

      if (Math.hypot(p.x - l.x, p.y - l.y) < 40) inspected = l;
    }

    // Diegetic Tooltip Comparison Card (kept below y: 36 status ribbon)
    if (inspected) {
      const item = inspected.itemData;
      const curDmg = p.weaponDamage || 25;
      const delta = item.damage - curDmg;
      const cardW = 150, cardH = 50;
      const cx = Math.max(10, Math.min(640, inspected.x - cardW * 0.5));
      const cy = Math.max(42, inspected.y - 62);

      ctx.fillStyle = 'rgba(15, 12, 20, 0.92)';
      ctx.fillRect(cx, cy, cardW, cardH);
      ctx.strokeStyle = inspected.color;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(cx, cy, cardW, cardH);

      ctx.font = '10px monospace';
      ctx.fillStyle = inspected.color;
      ctx.fillText(item.name.slice(0, 22), cx + 6, cy + 14);

      ctx.fillStyle = '#d1d5db';
      ctx.fillText(`DMG: ${item.damage} (${delta >= 0 ? '+' : ''}${delta})`, cx + 6, cy + 28);
      ctx.fillStyle = '#eab308';
      ctx.fillText(`[SHIFT/E] EQUIP LOOT`, cx + 6, cy + 42);
    }

    ctx.restore();
  }
});
