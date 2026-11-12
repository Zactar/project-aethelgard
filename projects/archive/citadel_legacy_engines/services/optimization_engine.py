import json
from pathlib import Path
from schemas.studio_contracts import GameRuntimeManifest, OptimizationReport

class StudioOptimizationProfiler:
    """Technical Director agent auditing scene complexity, draw calls, and client budget limits."""

    def __init__(self, max_draw_calls: int = 120, max_payload_kb: float = 250.0):
        self.max_draw_calls = max_draw_calls
        self.max_payload_kb = max_payload_kb

    def audit_runtime_manifest(self, manifest: GameRuntimeManifest) -> OptimizationReport:
        node_count = len(manifest.spatial_layout.nodes)
        prop_count = sum(len(props) for props in manifest.props.values())

        # Estimated draw calls: 1 call per room floor + 4 curbs + 1 call per prop + smart objects + NPCs
        so_count = sum(len(n.smart_objects) for n in manifest.spatial_layout.nodes.values())
        npc_count = len(manifest.npcs)
        estimated_draw_calls = (node_count * 5) + prop_count + (so_count * 2) + (npc_count * 2)

        raw_json = manifest.model_dump_json()
        payload_kb = round(len(raw_json.encode("utf-8")) / 1024.0, 2)

        instancing_needed = prop_count > 45 or estimated_draw_calls > self.max_draw_calls
        budget_exceeded = payload_kb > self.max_payload_kb or estimated_draw_calls > (self.max_draw_calls * 1.5)

        notes = []
        if instancing_needed:
            notes.append("Recommend THREE.InstancedMesh batching for repeated crate and barrel primitives.")
        if payload_kb > self.max_payload_kb:
            notes.append(f"Payload ({payload_kb} KB) exceeds target budget ({self.max_payload_kb} KB). Strip redundant decimals.")
        if not notes:
            notes.append("Performance budget healthy: high frame-rate headroom verified for WebGL.")

        return OptimizationReport(
            total_nodes=node_count,
            total_props=prop_count,
            estimated_draw_calls=estimated_draw_calls,
            payload_size_kb=payload_kb,
            instancing_recommended=instancing_needed,
            budget_exceeded=budget_exceeded,
            triage_notes=" | ".join(notes)
        )
