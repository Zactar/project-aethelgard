#!/usr/bin/env python3
"""
tools/seed_lore_bus.py
Project Aethelgard: Seed ChromaLoreBus with Citadel Canon & District Tensions
"""

from services.agent_runtime.src.chroma_lore_bus import ChromaLoreBus
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


CITADEL_CANON = [
    {
        "id": "CANON_DISTRICT_MARKET",
        "content": "Market Cross Square is the commercial belly of the upper citadel. The Common Loaf bakery and Garrett's Curatives anchor public commerce, but rising bread tithes levied by the Episcopal Inquest have spurred talk of worker strikes.",
        "metadata": {"district": "Market Cross Square", "theme": "commerce_and_unrest", "danger_level": 1}
    },
    {
        "id": "CANON_DISTRICT_UNDERCROFT",
        "content": "The Undercroft Ossuaries and Aqueduct Conduits lie beneath the street curbs. The subterranean canal is used by shadow runners to bypass the city watch, smuggling unblessed hearth grain and forged travel permits past the curfew.",
        "metadata": {"district": "Old Undercroft", "theme": "contraband_and_stealth", "danger_level": 3}
    },
    {
        "id": "CANON_FACTION_CLERISY",
        "content": "The High Clerisy enforces the Hearthmother's Tithe with strict legalism. Their inquisitors patrol the stone thoroughfares after twilight bells, confiscating unregistered alchemy and checking merchant ledgers.",
        "metadata": {"district": "Cathedral Heights", "theme": "authority_and_curfew", "danger_level": 2}
    },
    {
        "id": "CANON_FACTION_BAKERS_GUILD",
        "content": "The Bakers Guild controls grain distribution from the Common Loaf. They face supply shortages due to banditry along the south turnpike, causing price spikes in daily rations and brewing resentment against garrison guards.",
        "metadata": {"district": "Market Cross Square", "theme": "economy_and_supplies", "danger_level": 1}
    },
    {
        "id": "CANON_SYSTEM_CURFEW",
        "content": "Citadel curfew commences when the high chimes strike eight. Any citizen caught outside market boundaries without an inscribed Sunfire lantern or an authentic Clerisy seal is subject to immediate questioning.",
        "metadata": {"district": "Citadel", "theme": "curfew_mechanics", "danger_level": 2}
    }
]


def seed():
    print("[*] Seeding ChromaLoreBus with Citadel Canon...")
    lore_bus = ChromaLoreBus(workspace_root=WORKSPACE_ROOT)

    if not lore_bus.collection:
        print(
            "[!] Unable to reach ChromaDB collection. Ensure Chroma daemon is running on Port 8000.")
        return

    for entry in CITADEL_CANON:
        lore_bus.index_canon_document(
            doc_id=entry["id"],
            content=entry["content"],
            metadata=entry["metadata"]
        )

    print(
        f"[✓] Successfully seeded {len(CITADEL_CANON)} canonical entries into ChromaDB.")

    # Verification query
    test_query = "smuggling and curfew evasion in the aqueducts"
    results = lore_bus.query_canon(test_query, n_results=2)
    print(f"\n[+] Verification Query: '{test_query}'")
    for r in results:
        print(f" - [{r['metadata'].get('district')}] {r['text']}")


if __name__ == "__main__":
    seed()
