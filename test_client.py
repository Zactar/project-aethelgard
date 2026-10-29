import asyncio
import json
import websockets

async def run_test():
    uri = "ws://localhost:8765"
    print(f"[TEST CLIENT]: Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            payload = {
                "type": "TELEMETRY_INGEST",
                "district_id": "District_MarketSquare",
                "player_stress": 0.82,
                "player_coords": [1400.0, 500.0, 0.0],
                "seed": 42109
            }
            print(f"[TEST CLIENT]: Dispatched high-stress player telemetry frame.")
            await ws.send(json.dumps(payload))

            response = await ws.recv()
            data = json.loads(response)
            print("\n" + "=" * 60)
            print("         RECEIVED VIRTUAL STUDIO PIPELINE RESPONSE         ")
            print("=" * 60)
            print(f"Status       : {data['status']}")
            print(f"Artifact ID  : {data['artifact_id']}")
            print(f"Target NPC   : {data['target_npc']}")
            print(f"State Action : {data['action']}")
            print(f"Dialogue     :\n  \"{data['dialogue']}\"")
            print("=" * 60 + "\n")
    except Exception as e:
        print(f"[TEST CLIENT ERROR]: Could not connect or exchange data: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
