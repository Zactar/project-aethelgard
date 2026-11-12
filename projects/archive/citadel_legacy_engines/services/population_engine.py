"""
services/agent_runtime/src/population_engine.py
Project Aethelgard: Sociological Simulation, Citizen Drives & Collective Unrest
Inspired by Rimworld and Dwarf Fortress psychological need architectures.
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


logger = logging.getLogger("Aethelgard.PopulationEngine")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class SocialClass(str, Enum):
    CLERISY = "CLERISY"
    GUILD_MASTER = "GUILD_MASTER"
    CRAFTSMAN = "CRAFTSMAN"
    WATCH_SENTINEL = "WATCH_SENTINEL"
    LOWER_LABORER = "LOWER_LABORER"
    CONTRABAND_PARIAH = "CONTRABAND_PARIAH"


class MentalState(str, Enum):
    CONTENT = "CONTENT"
    DISCONTENT = "DISCONTENT"
    AGITATED = "AGITATED"
    REBELLIOUS = "REBELLIOUS"
    BROKEN = "BROKEN"


class CitizenNeeds(BaseModel):
    nourishment: float = 1.0     # 0.0 (starving) to 1.0 (satiated)
    rest: float = 1.0            # 0.0 (exhausted) to 1.0 (rested)
    spiritual_solace: float = 0.8  # 0.0 (despair) to 1.0 (devout)
    civic_security: float = 0.7  # 0.0 (terror/siege) to 1.0 (safe)


class CitizenActor(BaseModel):
    citizen_id: str
    name: str
    social_class: SocialClass
    needs: CitizenNeeds = Field(default_factory=CitizenNeeds)
    grievances: List[str] = Field(default_factory=list)
    morale: float = 0.8
    loyalty_to_citadel: float = 0.75
    mental_state: MentalState = MentalState.CONTENT

    def evaluate_mental_state(self) -> MentalState:
        # Weighted drive evaluation
        stress = (
            (1.0 - self.needs.nourishment) * 0.40 +
            (1.0 - self.needs.rest) * 0.20 +
            (1.0 - self.needs.spiritual_solace) * 0.20 +
            (1.0 - self.needs.civic_security) * 0.20
        )
        self.morale = max(0.0, min(1.0, 1.0 - stress))

        if self.morale > 0.65:
            self.mental_state = MentalState.CONTENT
        elif self.morale > 0.45:
            self.mental_state = MentalState.DISCONTENT
        elif self.morale > 0.25:
            self.mental_state = MentalState.AGITATED
        elif self.loyalty_to_citadel < 0.30:
            self.mental_state = MentalState.REBELLIOUS
        else:
            self.mental_state = MentalState.BROKEN

        return self.mental_state


class PopulationEngine:
    """Simulates the collective demographic ecosystem and emergence of civil unrest."""

    def __init__(self):
        self.citizens: Dict[str, CitizenActor] = {
            "hearthmother_elspeth": CitizenActor(
                citizen_id="hearthmother_elspeth",
                name="Hearthmother Elspeth",
                social_class=SocialClass.CRAFTSMAN,
                loyalty_to_citadel=0.60
            ),
            "garrett_apothecary": CitizenActor(
                citizen_id="garrett_apothecary",
                name="Garrett the Apothecary",
                social_class=SocialClass.GUILD_MASTER,
                loyalty_to_citadel=0.45
            ),
            "watchman_bronn": CitizenActor(
                citizen_id="watchman_bronn",
                name="Inquest Sentinel Bronn",
                social_class=SocialClass.WATCH_SENTINEL,
                loyalty_to_citadel=0.70
            )
        }

    def simulate_hour_tick(self, food_available: bool, curfew_active: bool, wage_paid: bool) -> Dict[str, Any]:
        total_morale = 0.0
        rebellious_count = 0

        for c in self.citizens.values():
            # Food dynamics
            if not food_available:
                c.needs.nourishment = max(0.0, c.needs.nourishment - 0.15)
                if "Starvation" not in c.grievances:
                    c.grievances.append("Starvation")
            else:
                c.needs.nourishment = min(1.0, c.needs.nourishment + 0.10)
                if "Starvation" in c.grievances:
                    c.grievances.remove("Starvation")

            # Guard wage and loyalty dynamics
            if c.social_class == SocialClass.WATCH_SENTINEL and not wage_paid:
                c.loyalty_to_citadel = max(0.0, c.loyalty_to_citadel - 0.25)
                if "Unpaid Wages" not in c.grievances:
                    c.grievances.append("Unpaid Wages")

            # Curfew fatigue
            if curfew_active:
                c.needs.civic_security = max(
                    0.0, c.needs.civic_security - 0.05)

            c.evaluate_mental_state()
            total_morale += c.morale
            if c.mental_state == MentalState.REBELLIOUS:
                rebellious_count += 1

        avg_morale = total_morale / len(self.citizens)
        civil_unrest = 1.0 - avg_morale

        logger.info(
            f"[PopulationTick] Avg Morale: {avg_morale:.2f} | Unrest: {civil_unrest:.2f} | Rebels: {rebellious_count}")
        return {
            "average_morale": round(avg_morale, 3),
            "civil_unrest": round(civil_unrest, 3),
            "rebellious_citizens": rebellious_count,
            "guard_loyalty": self.citizens["watchman_bronn"].loyalty_to_citadel
        }


if __name__ == "__main__":
    sim = PopulationEngine()
    # Simulate a 3-hour grain embargo and missed guard payroll
    for h in range(1, 4):
        print(f"--- Hour {h}: Food Embargo & Missed Wages ---")
        res = sim.simulate_hour_tick(
            food_available=False, curfew_active=True, wage_paid=False)
        print(f"Result: {res}")
