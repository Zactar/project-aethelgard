// Cohesive Milestone Plugin: v0.1.0
// Glissade: Descent of the Yeti - Core Baseline Module (v0.1.0)
// High-contrast 90s Shareware Downhill Skiing Roguelike

(function() {
  'use strict';

  // Fallback Microkernel initialization if running standalone
  if (!window.StudioEngine) {
    window.StudioEngine = {
      state: {},
      modules: {},
      events: {},
      registerModule: function(name, mod) {
        this.modules[name] = mod;
      },
      on: function(event, handler) {
        if (!this.events[event]) this.events[event] = [];
        this.events[event].push(handler);
      },
      emit: function(event, payload) {
        if (!this.events[event]) return;
        var handlers = this.events[event];
        for (var i = 0; i < handlers.length; i++) {
          handlers[i](payload, this.state);
        }
      }
    };
  }

  // --- BITMASKS & CONSTANTS ---
  var STATE_BITS = {
    SKIING: 0x01,
    TUCK: 0x02,
    AIRBORNE: 0x04,
    WIPEOUT_MAJOR: 0x08,
    WIPEOUT_RECOVERY: 0x10,
    INVULNERABLE: 0x20
  };

  var CANVAS_W = 800;
  var CANVAS_H = 600;
  var PISTE_LEFT = 40;
  var PISTE_RIGHT = 760;
  var CHUNK_HEIGHT = 1200;
  var FIXED_DT = 1.0 / 60.0;
  var LOOKAHEAD_SEC = 0.35;
  var CAMERA_LERP = 0.12;

  // Kinematic parameters
  var GRAVITY_DOWNHILL = 320.0; // Base downhill acceleration (px/s^2)
  var JUMP_GRAVITY = 640.0;     // Air gravity (px/s^2)
  var JUMP_IMPULSE = 280.0;     // Upward impulse
  var CARVE_FORCE = 440.0;
  var BASE_TERMINAL_VY = 480.0;
  var TUCK_TERMINAL_VY = 650.0;
  var DRAG_CRUISE = 0.45;
  var DRAG_TUCK = 0.18;
  var CARVE_BRAKE_FACTOR = 0.35;
  var SNOWPLOW_BRAKE = 520.0;

  // PRNG: SplitMix32 implementation
  function SplitMix32(seed) {
    var state = seed | 0;
    return function() {
      state = (state + 0x9E3779B9) | 0;
      var z = state;
      z = Math.imul(z ^ (z >>> 16), 0x21f0aaad);
      z = Math.imul(z ^ (z >>> 15), 0x735a2d97);
      return ((z ^ (z >>> 15)) >>> 0) / 4294967296.0;
    };
  }

  function hashChunk(seed, chunkY) {
    var h = (seed ^ Math.imul(chunkY, 0x85EBCA6B)) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 0xC2B2AE35);
    return (h ^ (h >>> 16)) >>> 0;
  }

  // Pre-allocated HUD and Camera Singletons
  var CAMERA = {
    x: 400,
    y: 300,
    targetY: 300
  };

  var HUD_DATA = {
    speedKmH: new Float64Array(1),
    distanceM: new Float64Array(1),
    wipeouts: new Int32Array(1),
    maxWipeouts: 3,
    flashTimer: 0.0,
    redlineTimer: 0.0
  };

  // Pre-cached CRT Scanlines and Bitmap Font
  var offscreenCRT = null;
  var offscreenFont = null;

  function initOffscreenAssets() {
    if (offscreenCRT && offscreenFont) return;

    // Scanline canvas (2x2 repeating)
    offscreenCRT = document.createElement('canvas');
    offscreenCRT.width = 4;
    offscreenCRT.height = 4;
    var cCtx = offscreenCRT.getContext('2d');
    if (cCtx) {
      cCtx.fillStyle = 'rgba(16, 24, 32, 0.28)';
      cCtx.fillRect(0, 0, 4, 2);
      cCtx.fillStyle = 'rgba(0, 0, 0, 0.0)';
      cCtx.fillRect(0, 2, 4, 2);
    }

    // 16x16 Monospace Bitmap Font
    // Glyphs: 0-9, K, M, /, H, :, -, P, L, A, Y, E, R, S, P, D, W, I, N, G, O, !
    offscreenFont = document.createElement('canvas');
    offscreenFont.width = 256;
    offscreenFont.height = 32;
    var fCtx = offscreenFont.getContext('2d');
    if (fCtx) {
      fCtx.imageSmoothingEnabled = false;
      fCtx.fillStyle = '#05111B';
      fCtx.fillRect(0, 0, 256, 32);
      fCtx.font = 'bold 14px monospace';
      fCtx.textBaseline = 'top';
      fCtx.textAlign = 'center';
      
      var glyphs =
