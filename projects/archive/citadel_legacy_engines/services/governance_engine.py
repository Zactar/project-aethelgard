"""
services/agent_runtime/src/governance_engine.py
Project Aethelgard: Faction Dynamics, Edicts, & Political Regime Transitions
"""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel

class RegimeType(str, Enum):
    CITADEL_THEOCRACY = "CITADEL_THEOCRACY"
    MERCHANT_OLIGARCHY = "MERCHANT_OLIGARCHY"
    POPULAR_COMMUNE = "POPULAR_COMMUNE"
    MARTIAL_COLLAPSE = "MARTIAL_COLLAPSE"

class CivicEdict(str, Enum):
    NIGHT_CURFEW = "NIGHT_CURFEW"
    GRAIN_REQUISITION = "GRAIN_REQUISITION"
    FREE_COMMERCE = "FREE_COMMERCE"
    SANCTUARY_PROTECTION = "SANCTUARY_PROTECTION"

class Faction(BaseModel):
    name: str
    influence: float = 0.25
    approval: float = 0.50
    demands: List[str] = []

class GovernanceEngine:
    def __init__(self):
        self.active_regime = RegimeType.CITADEL_THEOCRACY
        self.active_edicts = [CivicEdict.NIGHT_CURFEW, CivicEdict.GRAIN_REQUISITION]
        self.citadel_legitimacy: float = 0.70
        self.citadel_treasury: float = 450.0

        self.factions = {
            "CLERISY": Faction(name="High Clerisy", influence=0.35, approval=0.85, demands=["Enforce Curfew", "Collect Tithes"]),
            "GUILDS": Faction(name="Merchant Guilds", influence=0.25, approval=0.40, demands=["Repeal Curfew", "Lower Tariffs"]),
            "COMMONS": Faction(name="Warrens Laborers", influence=0.25, approval=0.30, demands=["Abolish Grain Requisition", "Open Bakeries"]),
            "WATCH": Faction(name="City Watch Garrisons", influence=0.15, approval=0.65, demands=["Guaranteed Silver Wages", "Rations"])
        }

    def evaluate_political_phase(self, civil_unrest: float, guard_loyalty: float) -> RegimeType:
        if guard_loyalty < 0.25 and civil_unrest > 0.60:
            if self.active_regime != RegimeType.MARTIAL_COLLAPSE:
                self.active_regime = RegimeType.MARTIAL_COLLAPSE
                self.active_edicts = []
                return self.active_regime

        if self.factions["COMMONS"].approval > 0.75 and civil_unrest > 0.70 and self.citadel_legitimacy < 0.25:
            if self.active_regime != RegimeType.POPULAR_COMMUNE:
                self.active_regime = RegimeType.POPULAR_COMMUNE
                self.active_edicts = [CivicEdict.SANCTUARY_PROTECTION, CivicEdict.FREE_COMMERCE]
                return self.active_regime

        if self.citadel_treasury < 50.0 and self.factions["GUILDS"].influence > 0.40:
            if self.active_regime != RegimeType.MERCHANT_OLIGARCHY:
                self.active_regime = RegimeType.MERCHANT_OLIGARCHY
                self.active_edicts = [CivicEdict.FREE_COMMERCE]
                return self.active_regime

        return self.active_regime

    def toggle_edict(self, edict: CivicEdict, enable: bool) -> None:
        if enable and edict not in self.active_edicts:
            self.active_edicts.append(edict)
        elif not enable and edict in self.active_edicts:
            self.active_edicts.remove(edict)
