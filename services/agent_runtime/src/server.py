from schemas.studio_contracts import SprintGoal
from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent
import websockets
from typing import Set, Any
import logging
import json
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("AethelgardServer")

DIRECTOR = StudioDirectorManagerAgent()
CONNECTED_CLIENTS: Set[Any] = set()

ACTIVE_GOALS = [
    SprintGoal(
        goal_id="GOAL-AUTONOMOUS-INIT",
        target_district="District_MarketSquare",
        primary_objective="Systemic Quests and Live Dynamic Broadcast",
        driving_ideas=["IDEA-SYS-01", "IDEA-LVL-01"],
        assigned_crews=["Systems_Architect",
                        "Narrative_Specialist", "Client_Architect"],
        success_criteria="Live hot-reload verified across browser client"
    )
]

SMART_OBJECT_RESPONSES = {
    "SmartObject.Mechanism.SluiceGate": {
        "speaker": "AQUEDUCT MECHANISM",
        "action": "OPERATE_SLUICE_GATE",
        "dialogue": "Heavy bronze gears groan as you crank the release valve. Subterranean floodwaters hiss and drain into the lower canals, advancing active quest objectives!"
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
    },
    "SmartObject.Container.SmugglerCache": {
        "speaker": "UNDERCROFT CACHE",
        "action": "LOOT_SMUGGLER_CHEST",
        "dialogue": "You pry open the false stone lining. Inside are smuggled flour bushels and untithed apothecary tinctures hidden beneath oiled sacking."
    },
    "SmartObject.Armory.WeaponRack": {
        "speaker": "GARRISON ARMORY",
        "action": "INSPECT_WEAPON_RACK",
        "dialogue": "Heavy iron halberds and riot pikes stand racked in rows, stamped with the Arch-Prelate's hawk insignia."
    },
    "SmartObject.Mechanism.CargoCrane": {
        "speaker": "DOCK CARGO CRANE",
        "action": "OPERATE_CARGO_WINCH",
        "dialogue": "The iron chain rattles as the hoist swings over the canal basin, ready to haul clandestine cargo sacks up from the water."
    },
    "SmartObject.Craft.AleCask": {
        "speaker": "HEARTH TAPROOM",
        "action": "POUR_COMMUNAL_ALE",
        "dialogue": "Spiced winter ale flows from the brass spigot. The patrons huddle near the peat hearth to whisper about the rising flour prices."
    }
}


async def broadcast_runtime_manifest(manifest_payload: dict):
    if not CONNECTED_CLIENTS:
        return
    message = json.dumps({
        "status": "LIVE_HOT_RELOAD",
        "game_runtime_manifest": manifest_payload
    })
    logger.info(
        f"Proactively broadcasting live update to {len(CONNECTED_CLIENTS)} client(s)...")
    await asyncio.gather(*[client.send(message) for client in CONNECTED_CLIENTS], return_exceptions=True)


async def handle_state_ipc(websocket: Any):
    client_addr = getattr(websocket, "remote_address", "unknown")
    CONNECTED_CLIENTS.add(websocket)
    logger.info(
        f"Client connected: {client_addr} (Pool: {len(CONNECTED_CLIENTS)})")
    try:
        async for message in websocket:
            payload = json.loads(message)
            msg_type = payload.get("type", "UNKNOWN")

            if msg_type in ("TELEMETRY_INGEST", "REQUEST_INITIAL_STATE"):
                district = payload.get("district_id", "District_MarketSquare")
                stress = payload.get("player_stress", 0.35)
                coords = tuple(payload.get(
                    "player_coords", [1400.0, 500.0, 0.0]))
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
                    "dialogue": result["raw_payload"]["spoken_dialogue"],
                    "target_npc": result["raw_payload"]["target_npc"],
                    "action": result["raw_payload"]["action"],
                    "game_runtime_manifest": result["raw_payload"]["game_runtime_manifest"]
                }
                await websocket.send(json.dumps(response))

            elif msg_type == "SMART_OBJECT_INTERACT":
                so_tag = payload.get("smart_object_tag", "")
                so_id = payload.get("smart_object_id", "")
                logger.info(f"Smart Object Interaction: {so_tag} ({so_id})")

                resp_data = SMART_OBJECT_RESPONSES.get(so_tag, {
                    "speaker": "WORLD OBJECT",
                    "action": "INTERACT_GENERIC",
                    "dialogue": f"You examine {so_id}."
                })

                response = {
                    "status": "PROCESSED",
                    "artifact_id": f"SO_EVENT_{so_id}",
                    "dialogue": resp_data["dialogue"],
                    "target_npc": resp_data["speaker"],
                    "action": resp_data["action"],
                    "advance_objective_tag": so_tag
                }
                await websocket.send(json.dumps(response))

            elif msg_type == "HOT_RELOAD_TRIGGER":
                await broadcast_runtime_manifest(payload.get("manifest", {}))

            elif msg_type == "HEARTBEAT":
                await websocket.send(json.dumps({"type": "PONG", "time": DIRECTOR.memory.world_time}))
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        pass
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        logger.info(
            f"Client disconnected: {client_addr} (Pool: {len(CONNECTED_CLIENTS)})")


async def main():
    server = await websockets.serve(handle_state_ipc, "0.0.0.0", 8765)
    logger.info(
        "Virtual Studio State & Broadcast Server live on ws://0.0.0.0:8765")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
