# Croak & Dagger: A Frogger Roguelike

A 2D top-down grid-based arcade roguelite combining river-crossing evasion with run-based item builds, an interstitial pond shop, permadeath, and persistent meta-progression.

## Core Gameplay Loop
1. **The Crossing**: Player navigates an amphibian avatar across multi-lane highways and rapid rivers to fill 5 goal bays.
2. **Collectibles & Currency**: Golden Flies and Water Lilies spawn in danger lanes. Catching them grants in-run currency ("Flies").
3. **Stage Clear & The Pond Peddler**: Filling all 5 goal bays completes the stage and opens the Pond Shop. Players spend Flies on active trinkets and passive relics.
4. **Permadeath & Amber Yield**: Reaching 0 Hearts ends the run. Surplus Flies and run score convert into persistent "Amber Resin" stored in local storage.
5. **The Great Lilypad Sanctuary**: Between runs (from the Game Over screen or via [S]), players enter the Sanctuary to spend banked Amber Resin on permanent meta-upgrades.

## Sanctuary Meta-Upgrades (Permanent Perks)
- **Thick Hide** (Cost: 50 Amber / rank, max 3): Increases starting hearts by +1 per rank (base 3 up to 6 hearts).
- **Lilypad Nest Egg** (Cost: 40 Amber / rank, max 3): Start every run with +10 bonus Flies per rank.
- **Resin Crucible** (Cost: 60 Amber / rank, max 2): Increases Amber conversion rate upon death by +25% per rank.

## Shop Relics (In-Run Items)
- **Sticky Tongue**: Automatically catches flies within a 1.5-tile radius.
- **Turtle Shell**: Grants a 1-hit shield that absorbs a single collision per stage.
- **Water Lily**: Restores 1 lost heart during the crossing.

## Controls
- **Arrow Keys / WASD**: Hop 1 tile in cardinal directions.
- **[S]**: Open / Close the Great Lilypad Sanctuary meta-upgrade hub.
- **[Space]**: Restart run from Game Over or close modal.
- **[Enter]**: Confirm purchase or continue stage from shop.