// Cohesive Milestone Plugin: v0.5.0 (Grand Arbiter Coronation Modal, Constellation Starfield & Master Ledger)
window.StudioEngine.registerModule("Milestone_v0_5_0", {
  init: function(state, engine) {
    this.verdictOpen = false;
    this.lastVerdictBout = 0;
    this.stars = [];
    for (let i = 0; i < 36; i++) {
      // Place constellation stars in the left/right astral margins outside the 360x360 matrix
      const side = (i % 2 === 0) ? (25 + Math.random() * 170) : (605 + Math.random() * 170);
      this.stars.push({
        x: side,
        y: 60 + Math.random() * 480,
        r: 1.2 + (i % 3) * 0.7,
        phase: Math.random() * Math.PI * 2
      });
    }

    this.ledger = [
      { name: "HYPATIA // PRIME GEOMETER", score: 6400, rank: "S-RANK" },
      { name: "ARCHIMEDES // TRIAD SAGE", score: 4800, rank: "A-RANK" },
      { name: "PYTHAGORAS // NEXUS LORD", score: 3200, rank: "B-RANK" },
      { name: "EUCLID // AXIOM KEEPER", score: 1800, rank: "C-RANK" }
    ];

    this.axioms = {
      CENTER: "AXIOM OF THE NEXUS: 'He who commands the central convergence bends all eight vectors to his will.'",
      CORNER: "AXIOM OF THE FOUR PILLARS: 'Strike from the outer vertices; a dual-vector fork cannot be parried.'",
      ATTRITION: "AXIOM OF EQUILIBRIUM: 'Against an infallible oracle, patience turns deadlock into revelation.'"
    };
    this.activeAxiom = this.axioms.CENTER;

    engine.on("BOUT_CONCLUDED", () => {
      const lat = state.world && state.world.lattice;
      if (!lat) return;
      // Trigger Series Coronation Verdict when a contender reaches 3 wins OR after 5 completed bouts!
      const totalFinished = lat.playerWins + lat.arbiterWins + lat.deadlocks;
      if ((lat.playerWins >= 3 || lat.arbiterWins >= 3 || totalFinished >= 5) && this.lastVerdictBout !== totalFinished) {
        this.lastVerdictBout = totalFinished;
        setTimeout(() => {
          this.openVerdict(state);
        }, 950);
      }
    });

    engine.on("KEYDOWN", (ev) => {
      if (!this.verdictOpen) return;
      if (ev.code === "Space" || ev.code === "Enter") {
        this.startNewSeries(state, engine, false);
      } else if (ev.code === "KeyC") {
        this.startNewSeries(state, engine, true);
      }
    });

    engine.on("POINTER_DOWN", () => {
      if (this.verdictOpen) {
        this.startNewSeries(state, engine, false);
      }
    });
  },

  openVerdict: function(state) {
    const lat = state.world.lattice;
    this.verdictOpen = true;
    state.paused = true;
    state.modal = "VERDICT";

    const sc = Math.floor(state.score || 0);
    const rank = lat.playerWins > lat.arbiterWins
      ? (sc >= 4000 ? "S-RANK // GRAND GEOMETER" : "A-RANK // TRIAD SOVEREIGN")
      : (lat.playerWins === lat.arbiterWins ? "B-RANK // EQUILIBRIUM KEEPER" : "C-RANK // ASTRAL INITIATE");

    if (lat.board[4] === "X") this.activeAxiom = this.axioms.CENTER;
    else if (lat.deadlocks >= 2) this.activeAxiom = this.axioms.ATTRITION;
    else this.activeAxiom = this.axioms.CORNER;

    this.lastSummary = {
      rank: rank,
      score: sc,
      w: lat.playerWins,
      d: lat.deadlocks,
      l: lat.arbiterWins
    };

    this.ledger = this.ledger.filter(r => !r.name.startsWith("YOU"));
    this.ledger.push({ name: "YOU (INITIATOR)", score: sc, rank: rank.split(" ")[0] });
    this.ledger.sort((a, b) => b.score - a.score);
    this.ledger = this.ledger.slice(0, 5);
  },

  startNewSeries: function(state, engine, openConfig) {
    const lat = state.world.lattice;
    this.verdictOpen = false;
    lat.playerWins = 0;
    lat.arbiterWins = 0;
    lat.deadlocks = 0;
    lat.bout = 0;
    this.lastVerdictBout = 0;
    state.score = 0;

    const m1 = engine.modules["Milestone_v0_1_0"];
    const m2 = engine.modules["Milestone_v0_2_0"];
    if (openConfig && m2) {
      m2.configOpen = true;
      state.paused = true;
      state.modal = "CONFIG";
    } else {
      state.paused = false;
      state.modal = null;
      if (m1) m1.resetBout(state, engine);
    }
  },

  update: function(dt, state) {
    if (this.verdictOpen) {
      state.paused = true;
    }
  },

  render: function(ctx, state) {
    const lat = state.world && state.world.lattice;
    if (!lat) return;
    const pal = lat.palettes[lat.paletteIdx] || lat.palettes[0];

    // 1. Render Astral Observatory Constellation Starfield in Left & Right Wings
    const t = performance.now() * 0.002;
    ctx.save();
    for (let i = 0; i < this.stars.length; i++) {
      const s = this.stars[i];
      const alpha = 0.35 + Math.sin(t + s.phase) * 0.25;
      ctx.fillStyle = `rgba(226, 232, 240, ${alpha})`;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    }

    // Link constellation stars into glowing zodiac geometries based on Bouts played!
    const links = Math.min(this.stars.length - 2, (lat.playerWins * 4) + (lat.deadlocks * 2) + 4);
    ctx.strokeStyle = pal.xCol;
    ctx.globalAlpha = 0.22;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < links; i += 2) {
      ctx.moveTo(this.stars[i].x, this.stars[i].y);
      ctx.lineTo(this.stars[i + 2].x, this.stars[i + 2].y);
    }
    ctx.stroke();
    ctx.restore();

    // 2. Render Grand Arbiter Series Verdict Modal if Open
    if (this.verdictOpen && this.lastSummary) {
      const sum = this.lastSummary;
      ctx.save();
      ctx.globalAlpha = 1.0;
      ctx.fillStyle = 'rgba(6, 9, 18, 0.96)';
      ctx.fillRect(0, 36, 800, 564);
      ctx.fillStyle = "#080c17";
      ctx.fillRect(140, 82, 520, 440);
      ctx.strokeStyle = pal.xCol;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(140, 82, 520, 440);

      ctx.textAlign = "center";
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 20px monospace";
      ctx.fillText("// GRAND ARBITER SERIES VERDICT //", 400, 122);

      ctx.fillStyle = pal.xCol;
      ctx.font = "bold 15px monospace";
      ctx.fillText(sum.rank, 400, 152);

      ctx.fillStyle = "#cbd5e1";
      ctx.font = "13px monospace";
      ctx.fillText(`SERIES RECORD: ${sum.w}W - ${sum.d}D - ${sum.l}L   |   TOTAL SCORE: ${sum.score}`, 400, 180);

      ctx.fillStyle = pal.oCol;
      ctx.font = "bold 13px monospace";
      ctx.fillText("--- OBSERVATORY GRANDMASTER LEDGER ---", 400, 218);

      ctx.font = "12px monospace";
      for (let i = 0; i < this.ledger.length; i++) {
        const row = this.ledger[i];
        const ry = 246 + i * 24;
        ctx.fillStyle = row.name.startsWith("YOU") ? "#10b981" : "#94a3b8";
        ctx.textAlign = "left";
        ctx.fillText(`${i + 1}. ${row.name}`, 185, ry);
        ctx.textAlign = "right";
        ctx.fillText(`${row.rank}  //  ${row.score} PTS`, 615, ry);
      }

      ctx.textAlign = "center";
      ctx.fillStyle = "#fde68a";
      ctx.font = "italic 10.5px monospace";
      ctx.fillText(this.activeAxiom, 400, 392);

      ctx.fillStyle = "#10b981";
      ctx.font = "bold 13px monospace";
      ctx.fillText("[SPACE / CLICK] COMMENCE NEW CHAMPIONSHIP SERIES", 400, 442);
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 12px monospace";
      ctx.fillText("[PRESS C] RECONFIGURE LATTICE ARCHITECTURE", 400, 472);
      ctx.restore();
    }
  }
});
