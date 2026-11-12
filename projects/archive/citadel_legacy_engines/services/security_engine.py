"""
services/agent_runtime/src/security_engine.py
Project Aethelgard: Physical Security Thresholds, Locks & Contraband Access Engine
"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.SecurityEngine")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


# --- TOPOLOGICAL SCHEMA DECLARATIONS ---
class LockState(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    BREACHED = "BREACHED"


class SecurityGate(BaseModel):
    gate_id: str
    name: str
    from_room: str
    to_room: str
    position: List[float]
    required_key: str
    allow_forged_permit: bool = True
    lock_state: LockState = LockState.LOCKED


class SecurityEngine:
    """
    Manages physical security thresholds and gate traversal verification.
    Prevents player traversal across corridor boundaries without valid tokens.
    """

    def __init__(self):
        self.gates: Dict[str, SecurityGate] = {
            "gate_undercroft_sluice": SecurityGate(
                gate_id="gate_undercroft_sluice",
                name="Old Undercroft Iron Portcullis",
                from_room="market_cross",
                to_room="undercroft_conduit",
                position=[0.0, 0.0, -15.0],
                required_key="undercroft_key",
                allow_forged_permit=True,
                lock_state=LockState.LOCKED
            ),
            "gate_garrison_bastion": SecurityGate(
                gate_id="gate_garrison_bastion",
                name="Citadel Garrison Security Gate",
                from_room="market_cross",
                to_room="district_sector_07",
                position=[0.0, 0.0, -38.0],
                required_key="garrison_permit",
                allow_forged_permit=True,
                lock_state=LockState.LOCKED
            )
        }

    def can_unlock_gate(self, gate_id: str, keyring: List[str], has_permit: bool = False) -> bool:
        gate = self.gates.get(gate_id)
        if not gate:
            return False
        if gate.lock_state != LockState.LOCKED:
            return True
        if gate.required_key in keyring:
            return True
        if gate.allow_forged_permit and has_permit:
            return True
        return False

    def unlock_gate(self, gate_id: str, keyring: List[str], has_permit: bool = False) -> Optional[SecurityGate]:
        if not self.can_unlock_gate(gate_id, keyring, has_permit):
            logger.warning(
                f"Access denied for {gate_id}. Missing required key or permit.")
            return None

        gate = self.gates[gate_id]
        gate.lock_state = LockState.UNLOCKED
        logger.info(
            f"[SECURITY] Gate '{gate.name}' ({gate.gate_id}) UNLOCKED.")
        return gate


if __name__ == "__main__":
    engine = SecurityEngine()
    test_keyring = ["undercroft_key"]
    unlocked = engine.unlock_gate(
        "gate_undercroft_sluice", test_keyring, has_permit=False)
    print(
        f"Gate Unlock Test Result: {unlocked.lock_state if unlocked else 'DENIED'}")
