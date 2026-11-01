"""
services/agent_runtime/src/stealth_engine.py
Project Aethelgard: Authoritative Light Metering & Shadow Concealment Engine
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Tuple
import logging
import math
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.StealthEngine")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class LightSource(BaseModel):
    source_id: str
    position: Tuple[float, float, float]
    radius: float = 12.0
    intensity: float = 1.4


class StealthState(BaseModel):
    is_crouching: bool = False
    # 0.0 (pitch black) to 1.0 (fully illuminated)
    raw_light_exposure: float = 0.0
    concealment_factor: float = 1.0  # Multiplier on guard vision range
    in_shadow_hideaway: bool = False


class StealthEngine:
    """
    Evaluates player light exposure from static torch sconces and calculates
    dynamic detection envelopes for patrolling sentinels.
    """

    def __init__(self):
        self.light_sources: List[LightSource] = [
            LightSource(source_id="market_torch_nw",
                        position=(-11.2, 2.0, -11.2), radius=14.0),
            LightSource(source_id="market_torch_se",
                        position=(11.2, 2.0, 11.2), radius=14.0),
            LightSource(source_id="bakery_hearth_oven",
                        position=(24.0, 1.0, -3.5), radius=10.0),
            LightSource(source_id="apothecary_alembic",
                        position=(-24.0, 1.2, -4.5), radius=8.0),
            LightSource(source_id="aqueduct_lantern",
                        position=(26.0, -3.0, -25.0), radius=12.0),
        ]

    def evaluate_player_exposure(
        self,
        player_pos: Tuple[float, float, float],
        is_crouching: bool = False
    ) -> StealthState:
        px, py, pz = player_pos
        total_lux = 0.0

        for light in self.light_sources:
            lx, ly, lz = light.position
            dist = math.sqrt((px - lx) ** 2 + (py - ly) ** 2 + (pz - lz) ** 2)
            if dist < light.radius:
                # Quadratic inverse falloff simulation
                falloff = (1.0 - (dist / light.radius)) ** 2
                total_lux += falloff * light.intensity

        clamped_exposure = min(max(total_lux, 0.05), 1.0)
        in_shadow = clamped_exposure < 0.25

        # Crouching in darkness dramatically reduces detection profile
        if is_crouching and in_shadow:
            concealment = 0.20  # Guards must be within 20% range to spot player
        elif is_crouching:
            concealment = 0.55
        elif in_shadow:
            concealment = 0.45
        else:
            concealment = 1.0

        return StealthState(
            is_crouching=is_crouching,
            raw_light_exposure=round(clamped_exposure, 3),
            concealment_factor=round(concealment, 3),
            in_shadow_hideaway=in_shadow
        )


if __name__ == "__main__":
    engine = StealthEngine()
    test_standing = engine.evaluate_player_exposure(
        (0.0, 0.0, 0.0), is_crouching=False)
    test_crouching = engine.evaluate_player_exposure(
        (0.0, 0.0, 0.0), is_crouching=True)
    print(
        f"Center Square (Standing): Exposure={test_standing.raw_light_exposure} | Concealment={test_standing.concealment_factor}")
    print(
        f"Center Square (Crouched): Exposure={test_crouching.raw_light_exposure} | Concealment={test_crouching.concealment_factor}")
