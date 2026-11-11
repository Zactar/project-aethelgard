// Autonomous Plugin: RFC-20261111-A760D1 | Slalom gate generator with combo multiplier tracking.
window.StudioEngine.registerModule("SlalomGateSystem", {
  init: function(state, engine) {
    if (!state.slalomSystem) {
      state.slalomSystem = {
        lastSpawnWorldY: 0,
        nextPolarity: 0, // 0: Red (Left-favored), 1: Blue (Right-favored)
        prevPlayerX: (state.player &&
