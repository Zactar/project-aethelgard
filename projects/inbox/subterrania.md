# Subterranea: A Dig-Dug Metroidvania

A 2D subterranean exploration platformer combining classic destructible grid-tunnelling and pneumatic harpoon combat with non-linear Metroidvania world design and traversal ability gates.

## Core Gameplay Loop
1. **Destructible Tunnelling**: The player carves continuous tunnels through dirt, loam, and fragile strata on a discrete 2D subterranean grid, dynamically opening traversal routes and venting gas pockets.
2. **Pneumatic Harpoon & Pump Combat**: 
   - Press [F] to fire a directional pneumatic harpoon cable that tethers into subterranean fiends (Pookas and fire-breathing Fygars).
   - Repeatedly tap [F] to pump air into tethered targets, inflating them until they pop. Partially inflated enemies are immobilized and can be walked past safely.
3. **Kinetic Boulder Hazards**: Carving out dirt directly beneath stone boulders destabilizes them. After a 1-second rumble, boulders drop down shafts, crushing any enemies or players caught underneath.
4. **Non-Linear Metroidvania Exploration & Ability Gates**:
   - The subterranean crust is divided into distinct geological zones separated by impassable strata:
     - **Upper Loam & Old Mineshaft**: Starting sector with soft dirt and wooden supports.
     - **Dense Granite Strata**: Requires the *Pneumatic Jack-Drill* upgrade to carve.
     - **Magma Chambers**: Requires the *Thermal Plating* upgrade to prevent heat damage.
     - **Vertical Abyssal Faults**: Requires the *Pressurized Jump-Piston* (Double Jump) to scale.
5. **Base Camp & Energy Core**: Return ancient fossil relics and minerals to subterranean camp beacons to restore Hull Integrity and install permanent drill and suit modifications.

## Traversal Upgrades (Ability Gates)
- **Pneumatic Jack-Drill**: Enables digging through gray dense granite walls that block deeper biomes.
- **Pressurized Jump-Piston**: Expels compressed air downward, granting a double-jump to scale vertical mine shafts.
- **Overcharge Air Compressor**: Increases harpoon range and allows pumping stone boulders to launch them horizontally.
- **Thermal Heatsink Plating**: Grants immunity to volcanic vents and allows swimming across lava pools.

## Subterranea Bestiary
- **Burrower Pooka**: Blind crawler that patrols carved tunnels and phases through unmined dirt as an amorphous wisp when alerted.
- **Magma Fygar**: Winged subterranean lizard that pauses, turns red, and exhales horizontal jets of flame through carved open corridors.

## Controls
- **Arrow Keys / WASD**: Move and dig tunnels in 4 cardinal directions.
- **[F] / [J]**: Fire Pneumatic Harpoon / Pump tethered target.
- **[Space]**: Jump / Engage Jump-Piston (when unlocked).
- **[M]**: Toggle Subterranean Sector Map.
- **[R]**: Return to last activated Camp Beacon.

## Win/Loss Conditions
- **Hull Integrity (Hearts)**: Depleted by contact with enemies, flame jets, or falling boulders. Reaching 0 triggers respawn at the last activated Camp Beacon.
- **Objective**: Retrieve the 3 Ancient Core Prisms from the depths of the Granite, Magma, and Abyssal biomes to activate the Central Borehole Elevator.