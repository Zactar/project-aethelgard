"""
services/agent_runtime/src/systemic_economy_generator.py
Project Aethelgard: Dynamic Commodity Price Bidding & Contraband Exchange
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List
from enum import Enum
import logging
import json
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.Economy")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


# --- TOPOLOGICAL SCHEMA DECLARATION ORDER (INC-20261027-SYS-04 Safe) ---
class CommodityType(str, Enum):
    HEARTH_BREAD = "HEARTH_BREAD"
    SUNFIRE_SALVE = "SUNFIRE_SALVE"
    FORGED_PERMIT = "FORGED_PERMIT"
    AQUEDUCT_SILVER = "AQUEDUCT_SILVER"


class MarketSentiment(str, Enum):
    STABLE = "STABLE"
    INFLATIONARY = "INFLATIONARY"
    RESTRICTED = "RESTRICTED"
    BLACK_MARKET = "BLACK_MARKET"


class CommodityQuote(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    commodity: CommodityType
    base_price: float
    current_bid: float
    current_ask: float
    market_sentiment: MarketSentiment
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SystemicEconomyGenerator:
    """
    Simulates real-time market pressure and contraband markups across Citadel districts.
    """

    def __init__(self, workspace_root: Path = _WORKSPACE_ROOT):
        self.workspace_root = workspace_root
        self.state_file = self.workspace_root / \
            "build" / "staging" / "economy_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.commodities = self._init_commodities()

    def _init_commodities(self) -> Dict[str, CommodityQuote]:
        return {
            CommodityType.HEARTH_BREAD.value: CommodityQuote(
                commodity=CommodityType.HEARTH_BREAD,
                base_price=5.0,
                current_bid=5.0,
                current_ask=5.5,
                market_sentiment=MarketSentiment.STABLE
            ),
            CommodityType.SUNFIRE_SALVE.value: CommodityQuote(
                commodity=CommodityType.SUNFIRE_SALVE,
                base_price=25.0,
                current_bid=24.0,
                current_ask=26.5,
                market_sentiment=MarketSentiment.STABLE
            ),
            CommodityType.FORGED_PERMIT.value: CommodityQuote(
                commodity=CommodityType.FORGED_PERMIT,
                base_price=50.0,
                current_bid=65.0,
                current_ask=75.0,
                market_sentiment=MarketSentiment.BLACK_MARKET
            ),
            CommodityType.AQUEDUCT_SILVER.value: CommodityQuote(
                commodity=CommodityType.AQUEDUCT_SILVER,
                base_price=100.0,
                current_bid=110.0,
                current_ask=120.0,
                market_sentiment=MarketSentiment.RESTRICTED
            )
        }

    def simulate_economic_tick(self, unrest_level: float = 0.5, curfew_active: bool = True) -> Dict[str, Any]:
        """Calculates price shifts based on unrest and curfew conditions."""
        for quote in self.commodities.values():
            if quote.commodity == CommodityType.HEARTH_BREAD.value:
                markup = 1.0 + (unrest_level * 0.4)
                quote.current_bid = round(quote.base_price * markup, 2)
                quote.current_ask = round(quote.current_bid * 1.1, 2)
                quote.market_sentiment = MarketSentiment.INFLATIONARY if unrest_level > 0.4 else MarketSentiment.STABLE

            elif quote.commodity == CommodityType.FORGED_PERMIT.value:
                curfew_multiplier = 1.6 if curfew_active else 1.0
                quote.current_bid = round(
                    quote.base_price * curfew_multiplier * (1.0 + unrest_level), 2)
                quote.current_ask = round(quote.current_bid * 1.15, 2)
                quote.market_sentiment = MarketSentiment.BLACK_MARKET

            quote.last_updated = datetime.utcnow()

        self._save_state()
        return {k: v.model_dump(mode="json") for k, v in self.commodities.items()}

    def _save_state(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            payload = {k: v.model_dump(mode="json")
                       for k, v in self.commodities.items()}
            json.dump(payload, f, indent=2)


if __name__ == "__main__":
    econ = SystemicEconomyGenerator()
    results = econ.simulate_economic_tick(
        unrest_level=0.75, curfew_active=True)
    print("\n--- CITADEL COMMODITY EXCHANGE TICK ---")
    for data in results.values():
        print(f"[{data['commodity']:<16}] Bid: {data['current_bid']:>6.2f} | Ask: {data['current_ask']:>6.2f} | {data['market_sentiment']}")
