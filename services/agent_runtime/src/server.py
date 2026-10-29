import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import json
import logging
from typing import Any
import websockets

from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("AethelgardServer")

DIRECTOR = StudioDirectorManagerAgent()

async def handle_state_ipc(websocket: Any):
    client_addr = getattr(websocket, "remote_address", "unknown")
    logger.info(f"Client connected to State IPC: {client_addr}")
    try:
        async for message in websocket:
            payload = json.loads(message)
            msg_type = payload.get("type", "UNKNOWN")

            if msg_type == "TELEMETRY_INGEST":
                district = payload.get("district_id", "District_MarketSquare")
                stress = payload.get("player_stress", 0.78)
                coords = tuple(payload.get("player_coords", [1400.0, 500.0, 0.0]))
                seed = payload.get("seed", 42109)

                result = DIRECTOR.dispatch_studio_pipeline(
                    district_id=district,
                    player_stress=stress,
                    player_pos=coords,
                    seed=seed
                )

                response = {
                    "status": "PROCESSED",
                    "artifact_id": result["artifact_id"],
                    "dialogue": result["raw_payload"]["dialogue"]["spoken_dialogue"],
                    "target_npc": result["raw_payload"]["target_npc"],
                    "action": result["raw_payload"]["action"]
                }
                await websocket.send(json.dumps(response))

            elif msg_type == "HEARTBEAT":
                await websocket.send(json.dumps({"type": "PONG", "time": DIRECTOR.memory.world_time}))
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        logger.warning(f"Client abruptly disconnected: {client_addr}")
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
