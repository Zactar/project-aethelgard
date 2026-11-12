# TRINITAS // THE NINEFOLD LATTICE

**Genre:** Minimalist Geometric Tactical Duel & Abstract Spatial Strategy
**Engine Type:** CANVAS_2D

## 1. Executive Vision & Aesthetic Direction
*TRINITAS // THE NINEFOLD LATTICE* is a sleek, high-tension abstract strategy duel set inside an obsidian-and-gold astral observatory (`#070913`). Two minds compete for geometric dominance across a sacred Ninefold Matrix. Every placement resonates with tactile audio-visual "JUICE": glowing laser-etched dividers, smooth stroke-drawn sigil animations, magnetic hover reticles, harmonic crystal chimes, and a blazing energy beam that locks across the winning collinear triad.

## 2. Formal Topological Ruleset (Core Game Loop)
1. **The Ninefold Matrix (The Arena):** The playfield centers on a bounded, equilateral square lattice (`360x360px`, centered at `x: 400, y: 310`) partitioned by two vertical and two horizontal glowing dividers into **nine discrete, contiguous spatial sectors** arranged in three horizontal ranks and three vertical files.
2. **Alternating Contender Phases:** Two contenders—the **Initiator (Player)** and the **Synthetic Arbiter (AI Opponent)**—alternate discrete turns. At the start of a bout, all nine sectors are vacant.
3. **Permanent Sector Inscription:** On a contender's active turn, they select exactly one vacant sector (via Mouse Click or `WASD`/`Arrows` + `SPACE`) to permanently inscribe their faction's geometric sigil for the remainder of the bout:
   - **First Contender Sigil (Crimson/Cyan):** *The Intersecting Diagonal Blades* (two symmetrical diagonal vectors crossing through the sector's center).
   - **Second Contender Sigil (Gold/Violet):** *The Concentric Meridian Ring* (a luminous closed circular orbit inscribed within the sector).
4. **Collinear Triad Victory & Equilibrium Deadlock:**
   - Immediately after each inscription, the engine inspects all **eight canonical collinear vectors** of the matrix (the three horizontal ranks, the three vertical files, and the two corner-to-corner main diagonals).
   - **Triad Alignment (Victory):** If any single collinear vector of three sectors is occupied exclusively by the same contender's sigil, a **Harmonic Triad** is achieved! A high-energy laser beam locks through the centers of the three aligned sectors, the winner's score increments, and the bout concludes.
   - **Equilibrium Deadlock (Draw):** If all nine sectors are inscribed without any collinear triad of three matching sigils, the bout concludes in an **Equilibrium Deadlock**, flashing the lattice in amber before resetting for the next bout.

## 3. UI/UX & Architectural Laws (Mandatory Studio Invariants)
- **Single Top Status Ribbon (`y: 0..36`):** Displays `INITIATOR WINS`, `DEADLOCKS`, `ARBITER WINS`, `STREAK`, and `ACTIVE TURN` in one clean top bar. Zero floating stat boxes cluttering the canvas.
- **Dual Input Ergonomics:** Full support for both Mouse Hover + Left-Click AND Keyboard Cursor (`WASD` / `Arrow Keys` to move a glowing selection frame across the 3 ranks and 3 files, plus `SPACE` / `ENTER` to inscribe).

## 4. Production Roadmap & Milestone Deliverables

### Milestone v0.1.0: The Ninefold Matrix, Alternating Turn Protocol & Collinear Triad Arbiter
- **[Level]** Centered 9-sector orthogonal lattice (`three ranks by three files`) rendered with glowing architectural dividers, sector coordinate mapping, and dual Mouse-Click + Keyboard (`WASD`/`Arrows` + `SPACE`) sector selection.
- **[Gameplay]** Alternating turn state machine (`PLAYER_TURN` -> `AI_THINKING` -> `ROUND_OVER`), immutable sector claiming, evaluation of all 8 collinear triads (3 ranks, 3 files, 2 diagonals) plus 9-sector Equilibrium Deadlock detection, and instant `[SPACE]` / Click bout reset.
- **[Aesthetics]** Animated geometric sigil drawing (*Intersecting Diagonal Blades* vs. *Concentric Meridian Ring*), radial particle bursts upon inscription, and a blazing harmonic laser beam connecting the 3 aligned sectors on victory.

### Milestone v0.2.0: Contender Sigil Customization, Minimax Oracle AI & Threat Telemetry
- **[UI_UX]** Pre-series Contender Configuration Modal allowing the player to choose their Geometric Crest palette, select who claims the opening turn (`Initiator First` vs `Arbiter First` vs `Alternating`), and select the Arbiter's cognitive tier (*Tier I: Opportunist*, *Tier II: Tactical Blocker*, *Tier III: Perfect Minimax Oracle*).
- **[Systems]** Three-tier Synthetic Arbiter AI: Tier I claims random/adjacent sectors; Tier II detects and blocks any collinear vector where the opponent holds 2 of 3 sectors; Tier III executes full recursive Minimax lookahead (prioritizing immediate winning triads, blocking opponent threats, seizing the central nexus or corner anchors, and setting up dual-vector forks).
- **[Aesthetics]** Translucent ghost-sigil hover preview inside vacant sectors and subtle pulsing threat-threads along any rank, file, or diagonal where a contender holds 2 of 3 sectors.

### Milestone v0.3.0: Pentatonic Crystal Audio Synthesizer, Championship Series & Blitz Clock
- **[Client]** Centralized Web Audio API harmonic synthesizer: 9 distinct pentatonic crystal chime frequencies mapped to the 9 matrix sectors, deep sub-bass lock thuds on placement, triumphant chord fanfare on Triad Victory, and a suspended chord resolve on Equilibrium Deadlock.
- **[Systems]** Best-of-5 Championship Series & Streak Multiplier system tracking Tactical Forks, Center-Nexus Control, and Flawless Series Sweeps inside the top status ribbon.
- **[Gameplay]** Optional 5.0-second Blitz Turn Timer integrated diegetically into the outer frame of the Ninefold Matrix (pulsing faster during the final 2 seconds and awarding speed-placement score bonuses).

### Milestone v0.4.0: Ephemeral Decay Mutator & Quantum Swap Protocol
- **[Gameplay]** Optional "Ephemeral Protocol" mutator toggle (`[KeyM]` or pre-match toggle): each contender may only maintain at most 3 active sigils on the lattice at once—when a contender inscribes their 4th sigil, their oldest sigil on the lattice dissolves back into a vacant sector, making Equilibrium Deadlocks impossible!
- **[Aesthetics]** Shimmering half-life decay indicators and disintegration particle motes on whichever sigil is queued to vanish next under Ephemeral Protocol.
- **[UI_UX]** Diegetic turn-order age pips (`1`, `2`, `3`) subtly etched into the corner of each occupied sector so both contenders can read the decay queue at a glance.

### Milestone v0.5.0: Grand Arbiter Coronation, Match Replay & Master Ledger
- **[UI_UX]** End-of-Series Grand Arbiter Verdict Modal displaying Series Outcome, Strategic Rating (`S-RANK: GRAND GEOMETER` to `C-RANK: INITIATE`), Win/Deadlock/Loss breakdown, Top-5 Observatory Ledger, and `[SPACE]` New Series / `[C]` Reconfigure Protocol.
- **[Aesthetics]** Constellation background starfield that links won bouts into glowing zodiac geometries behind the lattice, plus a slow-motion harmonic shatter finale when a Championship Series is clinched.
- **[Narrative]** Concise, atmospheric philosophical axioms from the Observatory Arbiter inscribed along the bottom border of the Verdict Modal reflecting the player's tactical style (Corner Dominance, Center Control, or Fork Mastery).
