"""
services/agent_runtime/src/crafting_engine.py
Project Aethelgard: Physical Workstation Recipe & Closed-Loop Transformation Engine
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.CraftingEngine")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


# --- TOPOLOGICAL SCHEMA DECLARATIONS ---
class WorkstationType(str, Enum):
    GRAIN_MILL = "GRAIN_MILL"
    BAKERY_OVEN = "BAKERY_OVEN"
    APOTHECARY_ALEMBIC = "APOTHECARY_ALEMBIC"


class RecipeItem(BaseModel):
    item_id: str
    quantity: int = 1


class CraftingRecipe(BaseModel):
    recipe_id: str
    name: str
    workstation: WorkstationType
    duration_seconds: float = 2.0
    inputs: List[RecipeItem]
    outputs: List[RecipeItem]


class CraftingEngine:
    """
    Manages physical workstation conversions without abstract menu spawning:
    - Grain Mill: 2 Unblended Grain -> 1 Milled Flour
    - Bakery Oven: 1 Milled Flour -> 1 Hearth Bread
    - Apothecary Alembic: 2 Mountain Herbs -> 1 Sunfire Salve
    """

    def __init__(self):
        self.recipes: Dict[str, CraftingRecipe] = {
            "mill_grain": CraftingRecipe(
                recipe_id="mill_grain",
                name="Mill Unblended Flour",
                workstation=WorkstationType.GRAIN_MILL,
                duration_seconds=2.5,
                inputs=[RecipeItem(item_id="grain", quantity=2)],
                outputs=[RecipeItem(item_id="flour", quantity=1)]
            ),
            "bake_bread": CraftingRecipe(
                recipe_id="bake_bread",
                name="Bake Hearth Loaf",
                workstation=WorkstationType.BAKERY_OVEN,
                duration_seconds=2.0,
                inputs=[RecipeItem(item_id="flour", quantity=1)],
                outputs=[RecipeItem(item_id="bread", quantity=1)]
            ),
            "brew_salve": CraftingRecipe(
                recipe_id="brew_salve",
                name="Brew Sunfire Salve",
                workstation=WorkstationType.APOTHECARY_ALEMBIC,
                duration_seconds=2.0,
                inputs=[RecipeItem(item_id="herbs", quantity=2)],
                outputs=[RecipeItem(item_id="salve", quantity=1)]
            )
        }

    def can_craft(self, recipe_id: str, inventory: Dict[str, int]) -> bool:
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return False
        return all(inventory.get(item.item_id, 0) >= item.quantity for item in recipe.inputs)

    def execute_craft(self, recipe_id: str, inventory: Dict[str, int]) -> Optional[Dict[str, int]]:
        if not self.can_craft(recipe_id, inventory):
            return None

        recipe = self.recipes[recipe_id]
        updated = dict(inventory)

        # Deduct inputs
        for inp in recipe.inputs:
            updated[inp.item_id] -= inp.quantity

        # Grant outputs
        for out in recipe.outputs:
            updated[out.item_id] = updated.get(out.item_id, 0) + out.quantity

        logger.info(
            f"Crafted '{recipe.name}' at {recipe.workstation.value}. Updated inventory: {updated}")
        return updated


if __name__ == "__main__":
    engine = CraftingEngine()
    test_inv = {"flour": 2, "bread": 1}
    success = engine.execute_craft("bake_bread", test_inv)
    print(f"Craft Test Result: {success}")
