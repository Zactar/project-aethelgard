// Cohesive Milestone Plugin: v0.3.0 (Pentatonic Crystal Audio Synthesizer, Championship Series & Blitz Clock)
window.StudioEngine.registerModule("Milestone_v0_3_0", {
  init: function(state, engine) {
    this.audioCtx = null;
    // 9 Pentatonic Crystal Frequencies (C4, D4, E4, G4, A4, C5, D5, E5, G5)
    this.pentatonic = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99];

    const unlock = () => {
      if (!this.audioCtx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (AC) this.audioCtx = new AC();
      } else if (this.audioCtx.state === "suspended") {
        this.audioCtx.resume();
      }
    };
    window.addEventListener("keydown", unlock);
    window.addEventListener("mousedown", unlock);

    engine.on("SECTOR_INSCRIBED", (ev) => {
      const freq = this.pentatonic[ev.index % 9] * (ev.symbol === "O" ? 0.75 : 1.0);
      this.playChime(freq, 0.28, "sine", 0.10);
      this.playChime(freq * 0.5, 0.16, "triangle", 0.08);
    });

    engine.on("BOUT_CONCLUDED", (ev) => {
      if (ev.winner === "X") {
        [523.25, 659.25, 783.99, 1046.50].forEach((f, idx) => {
          setTimeout(() => this.playChime(f, 0.35, "triangle", 0.11), idx * 70);
        });
      } else if (ev.winner === "O") {
        [392.00, 349.23, 311.13, 261.63].forEach((f, idx) => {
          setTimeout(() => this.playChime(f, 0.35, "sawtooth", 0.07), idx * 80);
        });
      } else {
        this.playChime(440.0, 0.4, "sine", 0.08);
      }
    });

    // Toggle Blitz Clock anytime with [KeyT]
    engine.on("KEYDOWN", (ev) => {
      const lat = state.world && state.world.lattice;
      if (lat && ev.code === "KeyT" && !state.paused) {
        lat.blitzEnabled = !lat.blitzEnabled;
        lat.turnTimer = lat.maxTurnTimer;
      }
    });
  },

  playChime: function(freq, dur, type, gainVal) {
    if (!this.audioCtx || this.audioCtx.state !== "running") return;
    const now = this.audioCtx.currentTime;
    const osc = this.audioCtx.createOscillator();
    const g = this.audioCtx.createGain();
    osc.type = type || "sine";
    osc.frequency.setValueAtTime(freq, now);
    g.gain.setValueAtTime(gainVal || 0.08, now);
    g.gain.exponentialRampToValueAtTime(0.001, now + dur);
    osc.connect(g);
    g.connect(this.audioCtx.destination);
    osc.start(now);
    osc.stop(now + dur + 0.02);
  },

  update: function(dt, state) {
    if (!state.running || state.paused || state.modal) return;
    const lat = state.world && state.world.lattice;
    if (!lat || !lat.blitzEnabled) return;

    // Blitz Clock ONLY ticks during active PLAYER_TURN and never forfeits a winning trap!
    // If the 12s speed-bonus timer reaches 0, it simply zeroes the speed-bonus multiplier for that turn.
    if (lat.phase === "PLAYER_TURN") {
      lat.turnTimer = Math.max(0, lat.turnTimer - dt);
    }
  },

  render: function(ctx, state) {
    const lat = state.world && state.world.lattice;
    if (!lat || state.paused || state.modal) return;

    // Render Diegetic Blitz Speed-Bonus Perimeter Gauge around the Ninefold Matrix
    if (lat.blitzEnabled && lat.phase === "PLAYER_TURN") {
      const ratio = Math.max(0, lat.turnTimer / (lat.maxTurnTimer || 12));
      ctx.save();
      ctx.strokeStyle = ratio > 0.3 ? "#38bdf8" : "#f43f5e";
      ctx.lineWidth = 3;
      const gx = 212, gy = 122, w = 376 * ratio;
      ctx.beginPath();
      ctx.moveTo(gx, gy);
      ctx.lineTo(gx + w, gy);
      ctx.stroke();
      ctx.restore();
    }
  }
});
