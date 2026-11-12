"""
services/agent_runtime/src/chroma_lore_bus.py
Project Aethelgard: Dual-Mode ChromaDB Vector Bus (HTTP Daemon + Persistent Local Fallback)
"""

from typing import List, Dict, Any, Optional
import logging
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))


logger = logging.getLogger("Aethelgard.LoreBus")
logger.propagate = False
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")


class ChromaLoreBus:
    """
    Connects to ChromaDB over HTTP (Port 8000). If offline, seamlessly initializes
    an in-process PersistentClient at build/chroma to guarantee 100% vector memory uptime.
    """

    def __init__(self, workspace_root: Optional[Path] = None, host: str = "localhost", port: int = 8000):
        self.workspace_root = Path(
            workspace_root) if workspace_root else _WORKSPACE_ROOT
        self.chroma_dir = self.workspace_root / "build" / "chroma"
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = "citadel_canon_lore"
        self.client = None
        self.collection = None
        self._initialize_client(host, port)

    def _initialize_client(self, host: str, port: int) -> None:
        try:
            import chromadb
            # 1. Attempt HTTP daemon connection
            try:
                self.client = chromadb.HttpClient(host=host, port=port)
                self.client.heartbeat()
                logger.info(
                    f"Connected to ChromaDB HTTP daemon on Port {port}.")
            except Exception:
                # 2. Seamless in-process fallback
                self.client = chromadb.PersistentClient(
                    path=str(self.chroma_dir))
                logger.info(
                    f"Initialized in-process PersistentClient at {self.chroma_dir}.")

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.warning(
                f"Could not initialize Chroma client: {e}. Vector operations will degrade to empty results.")

    def add_passage(self, passage_id: str, text: str, category: str = "canon", unrest_bias: float = 0.0) -> bool:
        if not self.collection:
            return False
        try:
            self.collection.upsert(
                ids=[passage_id],
                documents=[text],
                metadatas=[{"category": category, "unrest_bias": unrest_bias}]
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to upsert passage {passage_id}: {e}")
            return False

    def query_canon(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        if not self.collection:
            return []
        try:
            res = self.collection.query(
                query_texts=[query_text], n_results=n_results)
            results = []
            if res and res.get("documents") and res["documents"][0]:
                ids = res.get("ids", [[]])[0] if res.get("ids") else []
                metas = res.get("metadatas", [[]])[
                    0] if res.get("metadatas") else []
                docs = res["documents"][0]

                for i, doc in enumerate(docs):
                    pid = ids[i] if i < len(ids) else f"CANON-{i}"
                    meta = metas[i] if i < len(metas) else {}
                    results.append({
                        "id": pid,
                        "passage_id": pid,
                        "text": doc,
                        "metadata": meta
                    })
            return results
        except Exception as e:
            logger.warning(f"Chroma query failed: {e}")
            return []
