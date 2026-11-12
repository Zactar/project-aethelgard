// Cohesive Milestone Plugin: v0.1.0
window.StudioEngine.registerModule("Milestone_v0_1_0", {
  init: function(state) {
    state.running = true;
    state.paused = false;
    state.world = state.world || {};
    state.keys = state.keys || {};
    state.world.rooms = [];
    state.world.currentRoom = { x: 1, y: 1 };
    state.world.particles = [];
    state.world.floatingTexts = [];
    state.world.cameraShake = 0;
    state.world.enemies = [];
    state.world.braziers = [];
    state.world.bonePiles = [];
    state.world.depth = 1;

    for (let ry = 0; ry < 3; ry++) {
      state.world.rooms[ry] = [];
      for (let rx = 0; rx < 3; rx++) {
        state.world.rooms[ry][rx] = {
          cleared: false,
          enemies: [
            { type: 'skel', x: 260 + (rx * 70) % 280, y: 200 + (ry * 60) % 180, hp: 45, maxHp: 45, vx: 0, vy: 0, poise: 20, timer: 0 },
            { type: 'slime', x: 500 - (ry * 60) % 240, y: 320 - (rx * 50) % 140, hp: 30, maxHp: 30, vx: 0, vy: 0, poise: 10, timer: 0 }
          ],
          bones: [
            { x: 160 + (rx * 120) % 480, y: 160 + (ry * 90) % 220, hp: 1, gold: 6 + rx * 2 }
          ]
        };
      }
    }

    state.player = {
      x: 400, y: 260, vx: 0, vy: 0, width: 22, height: 26, facingAngle: 0,
      health: 5, maxHealth: 5, stamina: 100, maxStamina: 100, stamRegenDelay: 0,
      torchLevel: 1.0, gold: 0, dashTimer: 0, attackTimer: 0, hitStop: 0, speed: 175
    };
    this.audioCtx = null;
    this.loadRoom(state, 1, 1);
  },

  playTone: function(freq, type, dur, gain) {
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!this.audioCtx && AC) this.audioCtx = new AC();
      if (!this.audioCtx) return;
      var o = this.audioCtx.createOscillator(), g = this.audioCtx.createGain();
      o.type = type || 'sine';
      o.frequency.setValueAtTime(Math.min(freq, 640), this.audioCtx.currentTime);
      g.gain.setValueAtTime(gain || 0.05, this.audioCtx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + dur);
      o.connect(g); g.connect(this.audioCtx.destination);
      o.start(); o.stop(this.audioCtx.currentTime + dur);
    } catch (e) {}
  },

  loadRoom: function(state, rx, ry) {
    state.world.currentRoom = { x: rx, y: ry };
    var r = state.world.rooms[ry][rx];
    state.world.enemies = r.cleared ? [] : r.enemies.map(function(e) { return Object.assign({}, e); });
    state.world.bonePiles = r.bones.map(function(b) { return Object.assign({}, b); });
    state.world.braziers = [
      { x: 120, y: 100, flame: 1 }, { x: 680, y: 100, flame: 1 },
      { x: 120, y: 400, flame: 1 }, { x: 680, y: 400, flame: 1 }
    ];
  },

  update: function(dt, state) {
    if (state.paused) return;
    var p = state.player, k = state.keys || {};
    if (p.hitStop > 0) { p.hitStop -= dt; return; }

    var dx = (k.right ? 1 : 0) - (k.left ? 1 : 0);
    var dy = (k.down ? 1 : 0) - (k.up ? 1 : 0);
    if ((dx !== 0 || dy !== 0) && p.attackTimer <= 0) {
      p.facingAngle = Math.atan2(dy, dx);
    }

    if (p.dashTimer > 0) {
      p.dashTimer -= dt;
    } else if ((k.action) && p.stamina >= 25 && (dx !== 0 || dy !== 0)) {
      p.dashTimer = 0.3;
      p.stamina -= 25;
      p.stamRegenDelay = 0.6;
      this.playTone(220, 'triangle', 0.25, 0.05);
    }

    if (k.jump && p.attackTimer <= 0 && p.dashTimer <= 0 && p.stamina >= 20) {
      p.attackTimer = 0.24;
      p.stamina -= 20;
      p.stamRegenDelay = 0.65;
      this.playTone(130, 'sawtooth', 0.2, 0.06);
    }

    var moveSpd = p.dashTimer > 0 ? p.speed * 2.1 : (p.attackTimer > 0 ? 0 : p.speed);
    var len = Math.hypot(dx, dy);
    var curVx = len > 0 ? (dx / len) * moveSpd : 0;
    var curVy = len > 0 ? (dy / len) * moveSpd : 0;

    var nX = p.x + curVx * dt, nY = p.y + curVy * dt;
    var minX = 48, maxX = 752, minY = 64, maxY = 456;
    var isDoorX = p.x > 360 && p.x < 440, isDoorY = p.y > 220 && p.y < 300;

    if (!isDoorY) { nX = Math.max(minX, Math.min(maxX, nX)); }
    if (!isDoorX) { nY = Math.max(minY, Math.min(maxY, nY)); }
    p.x = nX; p.y = nY;

    var cr = state.world.currentRoom;
    if (p.x < 24 && cr.x > 0) { this.loadRoom(state, cr.x - 1, cr.y); p.x = 760; }
    else if (p.x > 776 && cr.x < 2) { this.loadRoom(state, cr.x + 1, cr.y); p.x = 40; }
    else if (p.y < 48 && cr.y > 0) { this.loadRoom(state, cr.x, cr.y - 1); p.y = 448; }
    else if (p.y > 472 && cr.y < 2) { this.loadRoom(state, cr.x, cr.y + 1); p.y = 70; }

    if (p.stamRegenDelay > 0) p.stamRegenDelay -= dt;
    else p.stamina = Math.min(p.maxStamina, p.stamina + 22 * dt);
    p.torchLevel = Math.max(0.35, p.torchLevel - 0.0018 * dt);

    if (p.attackTimer > 0) {
      p.attackTimer -= dt;
      var slashX = p.x + Math.cos(p.facingAngle) * 36;
      var slashY = p.y + Math.sin(p.facingAngle) * 36;
      for (var bi = state.world.bonePiles.length - 1; bi >= 0; bi--) {
        var bp = state.world.bonePiles[bi];
        if (Math.hypot(bp.x - slashX, bp.y - slashY) < 42) {
          p.gold += bp.gold;
          state.world.bonePiles.splice(bi, 1);
          (state.world.floatingTexts || (state.world.floatingTexts = [])).push({ text: "+" + bp.gold + "G", x: bp.x, y: bp.y, life: 0.6 });
          this.playTone(480, 'sine', 0.15, 0.04);
        }
      }
      state.world.enemies.forEach(function(e) {
        if (e.hp > 0 && Math.hypot(e.x - slashX, e.y - slashY) < 48) {
          e.hp -= 25;
          e.vx = Math.cos(p.facingAngle) * 220;
          e.vy = Math.sin(p.facingAngle) * 220;
          p.hitStop = 0.08;
          state.world.cameraShake = 5;
          for (var s = 0; s < 6; s++) {
            (state.world.particles || (state.world.particles = [])).push({ x: e.x, y: e.y, vx: (Math.random() - 0.5) * 140, vy: (Math.random() - 0.5) * 140, life: 0.4, col: '#dc2626' });
          }
        }
      });
    }

    state.world.enemies.forEach(function(e) {
      if (e.hp <= 0) return;
      var edx = p.x - e.x, edy = p.y - e.y, dist = Math.hypot(edx, edy);
      var eSpd = e.type === 'skel' ? 75 : 45;
      if (dist < 260 && dist > 18) {
        e.x += (edx / dist) * eSpd * dt;
        e.y += (edy / dist) * eSpd * dt;
      }
      e.x += e.vx * dt; e.y += e.vy * dt;
      e.vx *= 0.82; e.vy *= 0.82;
      if (p.dashTimer <= 0 && dist < 22) {
        p.health = Math.max(0, p.health - 1);
        p.dashTimer = 0.4;
        state.world.cameraShake = 8;
      }
    });

    for (var pi = state.world.particles.length - 1; pi >= 0; pi--) {
      var pt = state.world.particles[pi];
      pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.life -= dt;
      if (pt.life <= 0) state.world.particles.splice(pi, 1);
    }
    for (var ti = state.world.floatingTexts.length - 1; ti >= 0; ti--) {
      var ft = state.world.floatingTexts[ti];
      ft.y -= 25 * dt; ft.life -= dt;
      if (ft.life <= 0) state.world.floatingTexts.splice(ti, 1);
    }
  },

  render: function(ctx, state) {
    ctx.save();
    if (state.world.cameraShake > 0) {
      ctx.translate((Math.random() - 0.5) * state.world.cameraShake, (Math.random() - 0.5) * state.world.cameraShake);
      state.world.cameraShake = Math.max(0, state.world.cameraShake - 0.35);
    }

    ctx.fillStyle = '#08060c';
    ctx.fillRect(0, 0, 800, 600);

    ctx.strokeStyle = '#1d1728';
    ctx.lineWidth = 1;
    for (var gx = 40; gx < 760; gx += 40) {
      for (var gy = 40; gy < 480; gy += 40) {
        ctx.strokeRect(gx, gy, 40, 40);
      }
    }

    ctx.fillStyle = '#181124';
    ctx.fillRect(0, 36, 800, 24); ctx.fillRect(0, 464, 800, 36);
    ctx.fillRect(0, 36, 40, 464); ctx.fillRect(760, 36, 40, 464);

    var cr = state.world.currentRoom;
    ctx.fillStyle = '#2d1b4e';
    if (cr.y > 0) ctx.fillRect(360, 36, 80, 24);
    if (cr.y < 2) ctx.fillRect(360, 464, 80, 24);
    if (cr.x > 0) ctx.fillRect(0, 220, 40, 80);
    if (cr.x < 2) ctx.fillRect(760, 220, 40, 80);

    state.world.braziers.forEach(function(b) {
      ctx.fillStyle = '#3a2e39';
      ctx.fillRect(b.x - 8, b.y - 8, 16, 16);
      ctx.fillStyle = '#f59e0b';
      ctx.beginPath(); ctx.arc(b.x, b.y - 4, 6 + Math.sin(Date.now() * 0.01) * 2, 0, Math.PI * 2); ctx.fill();
    });

    state.world.bonePiles.forEach(function(bp) {
      ctx.fillStyle = '#e2e8f0';
      ctx.fillRect(bp.x - 10, bp.y - 6, 20, 12);
      ctx.fillStyle = '#94a3b8';
      ctx.fillRect(bp.x - 6, bp.y - 10, 12, 6);
    });

    state.world.particles.forEach(function(pt) {
      ctx.fillStyle = pt.col;
      ctx.fillRect(pt.x, pt.y, 4, 4);
    });

    var p = state.player;
    ctx.fillStyle = p.dashTimer > 0 ? '#93c5fd' : '#f59e0b';
    ctx.fillRect(p.x - 11, p.y - 13, p.width, p.height);
    ctx.strokeStyle = '#07050a';
    ctx.strokeRect(p.x - 11, p.y - 13, p.width, p.height);

    if (p.attackTimer > 0) {
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 38, p.facingAngle - 0.7, p.facingAngle + 0.7);
      ctx.stroke();
    }

    state.world.enemies.forEach(function(e) {
      if (e.hp <= 0) return;
      ctx.fillStyle = e.type === 'skel' ? '#e2e8f0' : '#10b981';
      ctx.fillRect(e.x - 12, e.y - 12, 24, 24);
      ctx.fillStyle = '#dc2626';
      ctx.fillRect(e.x - 12, e.y - 18, (e.hp / e.maxHp) * 24, 3);
    });

    var lightGrad = ctx.createRadialGradient(p.x, p.y, 20, p.x, p.y, (140 + Math.sin(Date.now() * 0.008) * 8) * p.torchLevel);
    lightGrad.addColorStop(0, 'rgba(0,0,0,0)');
    lightGrad.addColorStop(0.7, 'rgba(5,3,8,0.4)');
    lightGrad.addColorStop(1, 'rgba(5,3,8,0.92)');
    ctx.fillStyle = lightGrad;
    ctx.fillRect(0, 36, 800, 564);

    state.world.floatingTexts.forEach(function(ft) {
      ctx.fillStyle = '#eab308';
      ctx.font = '12px monospace';
      ctx.fillText(ft.text, ft.x, ft.y);
    });

    ctx.fillStyle = '#07050a';
    ctx.fillRect(0, 0, 800, 36);
    ctx.strokeStyle = '#312e81';
    ctx.strokeRect(0, 0, 800, 36);

    for (var h = 0; h < p.maxHealth; h++) {
      ctx.fillStyle = h < p.health ? '#dc2626' : '#374151';
      ctx.fillRect(16 + h * 18, 11, 14, 14);
    }

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(120, 12, 110, 12);
    ctx.fillStyle = '#10b981';
    ctx.fillRect(120, 12, (p.stamina / p.maxStamina) * 110, 12);

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(245, 12, 90, 12);
    ctx.fillStyle = '#f59e0b';
    ctx.fillRect(245, 12, p.torchLevel * 90, 12);

    ctx.fillStyle = '#f8fafc';
    ctx.font = '13px monospace';
    ctx.fillText("GOLD:" + p.gold, 360, 21);
    ctx.fillText("ROOM:[" + cr.x + "," + cr.y + "]", 470, 21);
    ctx.fillText("DEPTH:" + state.world.depth, 590, 21);
    ctx.fillText("[SPC]ATK [SHF]ROLL", 680, 21);
    ctx.restore();
  }
});
