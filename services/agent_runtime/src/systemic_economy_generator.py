#!/usr/bin/env python3
"""
PROJECT AETHELGARD: SYSTEMIC LEONTIEF ECONOMIC SYNTHESIZER
Generates procedural item contracts, base values, and buff durations from active district reserves.
"""

import math
import random
from typing import Dict, List, Tuple

from schemas.studio_contracts import ItemCategory, ItemSpec

ITEM_SYMBOLS = {
    ItemCategory.CONSUMABLE: ["🧪", "🍞", "🥩", "🍶", "🌿"],
    ItemCategory.CONTRABAND: ["📜", "🪙", "🗝️", "💎", "⚖️"],
    ItemCategory.COMMODITY:  ["🌾", "🪵", "🧱", "🧵", "🛢️"],
    ItemCategory.TOOL:       ["🔧", "🪓", "🧭", "🔨", "🔦"]
}


class SystemicEconomyGenerator:
    """Generates novel items with dynamically computed values and gameplay buff durations."""

    def synthesize_item(
        self,
        reserves: Dict[str, float],
        unrest: float,
        world_time: float,
        lore_snippet: str
    ) -> ItemSpec:
        """Derives a new item specification from current economic scarcity."""
        flour = reserves.get("Flour", 60.0)
        grain = reserves.get("Grain", 100.0)

        # Determine item category based on unrest and scarcity
        if unrest >= 0.70 or flour < 30.0:
            category = random.choice(
                [ItemCategory.CONTRABAND, ItemCategory.CONSUMABLE])
        else:
            category = random.choice(
                [ItemCategory.CONSUMABLE, ItemCategory.COMMODITY, ItemCategory.TOOL])

        # Scarcity multiplier formula: S = 1.0 + (unrest * 1.4) + (100 / max(15, flour)) * 0.2
        scarcity_factor = 1.0 + (unrest * 1.4) + \
            ((100.0 / max(15.0, flour)) * 0.25)

        unique_idx = int(world_time) % 10000

        if category == ItemCategory.CONTRABAND:
            names = ["Smuggler Flour Draft", "Forged Cathedral Seal",
                     "Undercroft Tithe Coin", "Clandestine Barley Deed"]
            name = f"{random.choice(names)} #{unique_idx}"
            base_value = round(min(220.0, 24.0 * scarcity_factor), 1)
            desc = f"Untithed district contraband. Formulated under unrest level {unrest:.2f}."
            effects = {"stealth_bonus": round(
                min(0.70, 0.25 * scarcity_factor), 2), "duration_sec": 18.0}

        elif category == ItemCategory.CONSUMABLE:
            names = ["Hearthstone Hardtack", "Apothecary Vigor Draught",
                     "Barley Porridge Ration", "Spiced Mountain Salve"]
            name = f"{random.choice(names)} #{unique_idx}"
            base_value = round(min(120.0, 10.0 * scarcity_factor), 1)
            desc = f"Nutritive ration baked in civic ovens. Restores stamina."
            effects = {"stamina_restore": round(
                min(80.0, 30.0 * scarcity_factor), 1), "speed_boost": 0.20, "duration_sec": 14.0}

        elif category == ItemCategory.COMMODITY:
            names = ["Coarse Hearth Barley", "Refined Mill Flour",
                     "Smelted Bronze Rivet", "Canal Packing Twine"]
            name = f"{random.choice(names)} #{unique_idx}"
            base_value = round(min(80.0, 6.0 * scarcity_factor), 1)
            desc = f"Standard guild trade commodity subject to episcopal verification."
            effects = {}

        else:
            names = ["Lock-Turn Wedge", "Canal Sounding Rod",
                     "Miller Pry-Chisel", "Catacomb Flint Striker"]
            name = f"{random.choice(names)} #{unique_idx}"
            base_value = round(min(150.0, 16.0 * scarcity_factor), 1)
            desc = f"Utilitarian workshop tool used across district transit passages."
            effects = {"interaction_speed": 0.30}

        icon = random.choice(ITEM_SYMBOLS[category])
        item_id = f"item_proc_{category.value.lower()}_{unique_idx}"

        return ItemSpec(
            item_id=item_id,
            display_name=name,
            category=category,
            base_value=base_value,
            description=f"{desc} Lore anchor: {lore_snippet[:60]}...",
            icon_symbol=icon,
            stack_limit=20,
            effects=effects
        )
