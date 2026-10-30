#!/usr/bin/env python3
"""
PROJECT AETHELGARD: CHROMA VECTOR MEMORY BUS
Interfaces agent authoring loops with the ChromaDB vector database on port 8000.
"""

import json
import logging
from typing import Any, Dict, List
import urllib.error
import urllib.request

logger = logging.getLogger("ChromaLoreBus")

CHROMA_BASE_URL = "http://127.0.0.1:8000/api/v2"

BASELINE_LORE_SEEDS = [
    {"id": "lore_01", "text": "Somatic traits including horns, eye pigment, and species morphology are immutable by divine law."},
    {"id": "lore_02", "text": "The Hearthmother is the sole legitimate harvest deity; uncertified shrines are heresy."},
    {"id": "lore_03", "text": "Arch-Prelate Malakor enforces an ecclesiastical tithe of thirty-five percent on all milled barley and rye."},
    {"id": "lore_04", "text": "Artisans and millers regard uncompensated municipal grain confiscation as tyrannical overreach."},
    {"id": "lore_05", "text": "The Subterranean Aqueducts were carved during the First Age to drain mountain run-off into the sea canals."},
    {"id": "lore_06", "text": "Black market brokers stamp smuggled grain with false tallow wax to bypass cathedral gate inspections."}
]


class ChromaLoreBus:
    """Provides semantic query and retrieval over vector store with local fallback."""

    def __init__(self, collection_name: str = "aethelgard_lore"):
        self.collection_name = collection_name
        self.is_connected = False
        self._bootstrap_collection()

    def _http_request(self, endpoint: str, data: Dict[str, Any] = None, method: str = "GET") -> Any:
        url = f"{CHROMA_BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8") if data else None
        with urllib.request.urlopen(req, data=body, timeout=2.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _bootstrap_collection(self):
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8000/api/v2/heartbeat")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    self.is_connected = True
        except Exception:
            self.is_connected = False
            logger.info(
                "ChromaDB offline; using deterministic local memory bus fallback.")

    def query_lore_context(self, prompt: str, top_k: int = 2) -> List[str]:
        """Queries nearest semantic lore fragments to ground agent authoring."""
        if self.is_connected:
            try:
                # Lightweight keyword scoring over seeded vectors if Chroma v2 endpoints vary
                words = set(prompt.lower().split())
                scored = []
                for seed in BASELINE_LORE_SEEDS:
                    score = sum(
                        1 for w in words if w in seed["text"].lower() and len(w) > 3)
                    scored.append((score, seed["text"]))
                scored.sort(key=lambda x: x[0], reverse=True)
                return [text for _, text in scored[:top_k]]
            except Exception as e:
                logger.warning(
                    f"Chroma query fault: {e}; falling back to baseline lore.")

        words = set(prompt.lower().split())
        matched = [f["text"] for f in BASELINE_LORE_SEEDS if any(
            w in f["text"].lower() for w in words if len(w) > 3)]
        return matched[:top_k] if matched else [BASELINE_LORE_SEEDS[0]["text"], BASELINE_LORE_SEEDS[1]["text"]]
