"""
services/agent_runtime/src/server.py
Project Aethelgard: WebSocket IPC Server (Port 8765) with Curfew Line-of-Sight & Stealth
"""

from services.agent_runtime.src.systemic_economy_generator import SystemicEconomyGenerator
import websockets
from typing import Dict, Any, List
import math
import logging
import json
import asyncio
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.Server")
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")

# Port 8765 WebSocket Bridge
HOST = "0.0.0.0"
PORT = 8765

CONNECTED_CLIENTS = set()
economy_engine = SystemicEconomyGenerator()

# Runtime Watchman Patrol State
WATCHMEN_PATROLS = [
    {
        "id": "watchman_01",
        "name": "Inquest Sentinel Bronn",
        "position": [18.0, 0.0, -12.0],
        "forward": [0.0, 0.0, 1.0],  # Normalized direction
        "view_distance": 14.0,
        "fov_degrees": 70.0,
        "is_interactive": True,
        "interaction_layer": "InteractionLayer.INTERACTIVE",
        "bribe_cost": 25.0
    }
]


def check_line_of_sight(watchman: Dict[str, Any], player_pos: List[float]) -> Dict[str, Any]:
    """Calculates radial field-of-view cone interception."""
    wx, wz = watchman["position"][0], watchman["position"][2]
    px, pz = player_pos[0], player_pos[2]

    dx = px - wx
    dz = pz - wz
    dist = math.sqrt(dx * dx + dz * dz)

    if dist > watchman["view_distance"]:
        return {"detected": False, "distance": dist, "alert_level": 0.0}

    # Normalize vector to player
    ndx, ndz = dx / (dist or 1e-5), dz / (dist or 1e-5)
    fx, fz = watchman["forward"][0], watchman["forward"][2]

    # Dot product for angle
    dot = ndx * fx + ndz * fz
    dot = max(-1.0, min(1.0, dot))
    angle = math.degrees(math.acos(dot))

    if angle <= (watchman["fov_degrees"] / 2.0):
        alert = 1.0 - (dist / watchman["view_distance"])
        return {"detected": True, "distance": dist, "alert_level": round(alert, 2)}

    return {"detected": False, "distance": dist, "alert_level": 0.0}


async def handle_client(websocket):
    CONNECTED_CLIENTS.add(websocket)
    logger.info(f"Client connected: {websocket.remote_address}")
    try:
        # Broadcast initial market and watchman data
        market_quotes = economy_engine.simulate_economic_tick(
            unrest_level=0.6, curfew_active=True)
        await websocket.send(json.dumps({
            "type": "WORLD_STATE_INIT",
            "curfew_active": True,
            "market_quotes": market_quotes,
            "watchmen": WATCHMEN_PATROLS
        }))

        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "PLAYER_TELEMETRY":
                player_pos = data.get("position", [0, 0, 0])
                stealth_alerts = []
                for wm in WATCHMEN_PATROLS:
                    los = check_line_of_sight(wm, player_pos)
                    if los["detected"]:
                        stealth_alerts.append({
                            "watchman_id": wm["id"],
                            "alert_level": los["alert_level"]
                        })

                await websocket.send(json.dumps({
                    "type": "STEALTH_STATUS",
                    "in_curfew_sight": len(stealth_alerts) > 0,
                    "alerts": stealth_alerts
                }))

            elif msg_type == "INTERACT_BRIBE":
                # Validate interaction layer masking
                watchman_id = data.get("target_id")
                wm = next(
                    (w for w in WATCHMEN_PATROLS if w["id"] == watchman_id), None)
                if wm and wm.get("interaction_layer") == "InteractionLayer.INTERACTIVE":
                    await websocket.send(json.dumps({
                        "type": "BRIBE_RESOLVED",
                        "success": True,
                        "watchman_id": watchman_id,
                        "message": f"{wm['name']} accepts the silver and looks the other way."
                    }))

    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected.")
    finally:
        CONNECTED_CLIENTS.remove(websocket)


async def main():
    logger.info(f"Starting Aethelgard WebSocket Server on ws://{HOST}:{PORT}")
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
