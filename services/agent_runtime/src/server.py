import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import json
import logging
from typing import Any
import websockets

from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent
from schemas.studio_contracts import SprintGoal

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("AethelgardServer")

DIRECTOR = StudioDirectorManagerAgent()
ACTIVE_GOALS = [
    SprintGoal(
        goal_id="GOAL-INIT",
        target_district="District_MarketSquare",
        primary_objective="Vertical Aqueduct Catacombs with Dynamic Sluice Gates",
        driving_ideas=["IDEA-LVL-01"],
        assigned_crews=["Level_Architect"],
        success_criteria="Rendered in web client"
    )
]

SMART_OBJECT_RESPONSES = {
    "SmartObject.Mechanism.SluiceGate": {
        "speaker": "AQUEDUCT MECHANISM",
        "action": "OPERATE_SLUICE_GATE",
        "dialogue": "Heavy bronze gears groan as you crank the release valve. Subterranean floodwaters hiss and drain into the lower canals, clearing the dry walking path."
    },
    "SmartObject.Craft.BreadOven": {
        "speaker": "NPC_ALDOUS",
        "action": "INSPECT_COMMUNAL_OVEN",
        "dialogue": "Careful around the hearthstones—I've got embers banked under the ash. If the cathedral tithe collectors ask, this oven hasn't fired since yesterday."
    },
    "SmartObject.Merchant.ApothecaryCounter": {
        "speaker": "NPC_GARRETT",
        "action": "BROWSE_CONTRABAND_HERBS",
        "dialogue": "Keep your hands off the blue jars on the upper rack. That's powdered nightshade from the ridge, and the church watch would hang us both for looking at it."
    },
    "SmartObject.Civic.RallyPoint": {
        "speaker": "MARKET CROSS NOTICE",
        "action": "EXAMINE_PROCLAMATION",
        "dialogue": "A freshly stamped parchment from Arch-Prelate Malakor is posted here: 'All unauthorized milling or assembly after the sixth bell carries an immediate tithe penalty.'"
    }
}

async def handle_state_ipc(websocket: Any):
    client_addr = getattr(websocket, "remote_address", "unknown")
    logger.info(f"Client connected to State IPC: {client_addr}")
    try:
        async for message in websocket:
            payload = json.loads(message)
            msg_type = payload.get("type", "UNKNOWN")

            if msg_type == "SMART_OBJECT_INTERACT":
                so_tag = payload.get("smart_object_tag", "")
                so_id = payload.get("smart_object_id", "")
                logger.info(f"Smart Object Interaction triggered: {so_tag} ({so_id})")

                resp_data = SMART_OBJECT_RESPONSES.get(so_tag, {
                    "speaker": "WORLD OBJECT",
                    "action": "INTERACT_GENERIC",
                    "dialogue": f"You examine {so_id}. The surface is worn from years of continuous guild use."
                })

                response = {
                    "status": "PROCESSED",
                    "artifact_id": f"SO_EVENT_{so_id}",
                    "dialogue": resp_data["dialogue"],
                    "target_npc": resp_data["speaker"],
                    "action": resp_data["action"],
                    "district_unrest": DIRECTOR.memory.active_district_unrest,
                    "active_phase": DIRECTOR.memory.active_phase
                }
                await websocket.send(json.dumps(response))

            elif msg_type == "TELEMETRY_INGEST":
                district = payload.get("district_id", "District_MarketSquare")
                stress = payload.get("player_stress", 0.78)
                coords = tuple(payload.get("player_coords", [1400.0, 500.0, 0.0]))
                seed = payload.get("seed", 42109)

                result = DIRECTOR.dispatch_studio_pipeline(
                    district_id=district,
                    player_stress=stress,
                    player_pos=coords,
                    seed=seed,
                    active_goals=ACTIVE_GOALS
                )

                response = {
                    "status": "PROCESSED",
                    "artifact_id": result["artifact_id"],
                    "dialogue": result["raw_payload"]["dialogue"]["spoken_dialogue"],
                    "target_npc": result["raw_payload"]["target_npc"],
                    "action": result["raw_payload"]["action"],
                    "district_unrest": result["raw_payload"]["district_unrest"],
                    "active_phase": result["raw_payload"]["active_phase"],
                    "spatial_layout": result["raw_payload"]["spatial_layout"]
                }
                await websocket.send(json.dumps(response))

            elif msg_type == "HEARTBEAT":
                await websocket.send(json.dumps({"type": "PONG", "time": DIRECTOR.memory.world_time}))
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        logger.warning(f"Client disconnected: {client_addr}")
    except Exception as e:
        logger.error(f"Error handling IPC message: {e}", exc_info=True)

async def main():
    server = await websockets.serve(handle_state_ipc, "0.0.0.0", 8765)
    logger.info("Virtual Studio State Server live on ws://0.0.0.0:8765")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server halted by user.")
