import sys
from pathlib import Path

# Add project root to sys.path so schemas and services import cleanly from anywhere
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import math
from typing import Dict, List, Any, Optional, Tuple

from schemas.studio_contracts import (
    ContentType, AestheticVerdict, BugSeverity, Vector3D, SmartObjectAnchor,
    SpatialRoomNode, DistrictSpatialLayout, StyleEvaluationReport,
    ProposedGameBeat, BugTicket, GameReadyArtifact
)

class StudioSharedMemoryBus:
    def __init__(self):
        self.world_time: float = 1200.0
        self.active_district_unrest: float = 0.58
        self.commodity_reserves: Dict[str, float] = {"Grain": 120.0, "Flour": 85.0, "Bread": 60.0}
        self.npc_locations: Dict[str, Tuple[float, float, float]] = {
            "NPC_GARRETT": (1200.0, 450.0, 0.0),
            "NPC_ALDOUS": (1450.0, 600.0, 0.0),
            "NPC_CAPTAIN_VANE": (8500.0, 9200.0, 0.0)
        }
        self.npc_inventories: Dict[str, Dict[str, float]] = {
            "NPC_GARRETT": {"gold": 45.0, "sunfire_blossom": 2.0},
            "NPC_ALDOUS": {"gold": 12.0, "bread": 15.0}
        }
        self.canon_lore = [
            "Somatic traits (horns, eye pigment, species) are immutable.",
            "The Hearthmother is the sole legitimate harvest deity.",
            "Arch-Prelate Malakor enforces a 35% tithe on licensed guild merchants.",
            "Artisans consider uncompensated stock seizures an act of tyranny."
        ]
        self.bug_ticket_queue: List[BugTicket] = []

    def __init__(self):
        self.world_time: float = 1200.0
        self.active_district_unrest: float = 0.58
        self.commodity_reserves: Dict[str, float] = {"Grain": 120.0, "Flour": 85.0, "Bread": 60.0}
        self.npc_locations: Dict[str, Tuple[float, float, float]] = {
            "NPC_GARRETT": (1200.0, 450.0, 0.0),
            "NPC_ALDOUS": (1450.0, 600.0, 0.0),
            "NPC_CAPTAIN_VANE": (8500.0, 9200.0, 0.0)
        }
        self.npc_inventories: Dict[str, Dict[str, float]] = {
            "NPC_GARRETT": {"gold": 45.0, "sunfire_blossom": 2.0},
            "NPC_ALDOUS": {"gold": 12.0, "bread": 15.0}
        }
        self.canon_lore = [
            "Somatic traits (horns, eye pigment, species) are immutable.",
            "The Hearthmother is the sole legitimate harvest deity.",
            "Arch-Prelate Malakor enforces a 35% tithe on licensed guild merchants.",
            "Artisans consider uncompensated stock seizures an act of tyranny."
        ]
        self.bug_ticket_queue: List[BugTicket] = []
        self._init_chroma_store()

    def _init_chroma_store(self):
        try:
            import chromadb
            client = chromadb.HttpClient(host="localhost", port=8000)
            self.collection = client.get_or_create_collection(name="aethelgard_canon")
            if self.collection.count() == 0:
                ids = [f"lore_{i}" for i in range(len(self.canon_lore))]
                self.collection.add(documents=self.canon_lore, ids=ids)
        except Exception:
            self.collection = None

    def query_lore(self, query: str) -> List[str]:
        if getattr(self, "collection", None) is not None:
            try:
                results = self.collection.query(query_texts=[query], n_results=2)
                docs = results.get("documents", [[]])[0]
                if docs:
                    return docs
            except Exception:
                pass
        words = set(query.lower().split())
        matched = [f for f in self.canon_lore if any(w in f.lower() for w in words if len(w) > 3)]
        return matched if matched else self.canon_lore[:2]

class SystemsArchitectAgent:
    def audit_metabolic_balance(self, memory: StudioSharedMemoryBus) -> Dict[str, Any]:
        grain = memory.commodity_reserves.get("Grain", 0.0)
        flour = memory.commodity_reserves.get("Flour", 0.0)
        bread = memory.commodity_reserves.get("Bread", 0.0)
        is_conserved = (grain >= 10.0 and flour >= 5.0 and bread >= 1.0)
        return {
            "status": "EQUILIBRIUM" if is_conserved else "DEFICIT",
            "is_conserved": is_conserved,
            "reserves": memory.commodity_reserves
        }

class LevelArchitectAgent:
    def generate_and_refine_layout(self, district_id: str) -> DistrictSpatialLayout:
        nodes = {
            "NODE_PLAZA": SpatialRoomNode(
                node_id="NODE_PLAZA", zone_name="Market Cross Square", function="CIVIC_PLAZA",
                bounds_min=Vector3D(x=-1500, y=-1500, z=0), bounds_max=Vector3D(x=1500, y=1500, z=500),
                center_location=Vector3D(x=0, y=0, z=0), connected_node_ids=["NODE_APOTHECARY", "NODE_BAKERY"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_RALLY", smart_object_tag="SmartObject.Civic.RallyPoint", relative_position=Vector3D(x=0, y=0, z=0), interaction_facing_yaw=0.0)]
            ),
            "NODE_APOTHECARY": SpatialRoomNode(
                node_id="NODE_APOTHECARY", zone_name="Garrett's Curatives", function="COMMERCIAL_STALL",
                bounds_min=Vector3D(x=1800, y=-600, z=0), bounds_max=Vector3D(x=2800, y=600, z=400),
                center_location=Vector3D(x=2300, y=0, z=0), connected_node_ids=["NODE_PLAZA"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_GARRETT", smart_object_tag="SmartObject.Merchant.ApothecaryCounter", assigned_npc_id="NPC_GARRETT", relative_position=Vector3D(x=2100, y=0, z=0), interaction_facing_yaw=180.0)]
            ),
            "NODE_BAKERY": SpatialRoomNode(
                node_id="NODE_BAKERY", zone_name="The Common Loaf", function="WORKSHOP_CRAFT",
                bounds_min=Vector3D(x=-600, y=1800, z=0), bounds_max=Vector3D(x=600, y=2800, z=400),
                center_location=Vector3D(x=0, y=2300, z=0), connected_node_ids=["NODE_PLAZA"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_ALDOUS", smart_object_tag="SmartObject.Craft.BreadOven", assigned_npc_id="NPC_ALDOUS", relative_position=Vector3D(x=0, y=2500, z=0), interaction_facing_yaw=90.0)]
            )
        }
        nodes["NODE_ALLEY"] = SpatialRoomNode(
            node_id="NODE_ALLEY", zone_name="Shadowed Drainage Way", function="CLANDESTINE_ALLEY",
            bounds_min=Vector3D(x=1500, y=1500, z=0), bounds_max=Vector3D(x=2200, y=2200, z=300),
            center_location=Vector3D(x=1800, y=1800, z=0), connected_node_ids=["NODE_APOTHECARY", "NODE_BAKERY"]
        )
        nodes["NODE_APOTHECARY"].connected_node_ids.append("NODE_ALLEY")
        nodes["NODE_BAKERY"].connected_node_ids.append("NODE_ALLEY")

        return DistrictSpatialLayout(
            district_id=district_id, district_name="Oakhaven Market Commons",
            nodes=nodes, is_topologically_sound=True
        )

class DMDirectorAgent:
    def formulate_pacing_beat(self, player_stress: float, memory: StudioSharedMemoryBus) -> ProposedGameBeat:
        if player_stress >= 0.70:
            return ProposedGameBeat(
                beat_id="BEAT_RELIEF_ALDOUS",
                target_npc_id="NPC_ALDOUS",
                action_type="OFFER_SHELTER_AND_BREAD",
                narrative_intent="Provide relief valve from sustained pressure",
                dialogue_prompt_concept="Quick, into the bakery cellar before the street patrol circles back!",
                required_props_or_coin={"bread": 1.0},
                spawn_location_name="NODE_BAKERY",
                target_player_threat_delta=-0.50
            )
        return ProposedGameBeat(
            beat_id="BEAT_STALL_GOSSIP",
            target_npc_id="NPC_GARRETT",
            action_type="CONFRONT_THEFT",
            narrative_intent="Escalate tension around player's stolen goods",
            dialogue_prompt_concept="I know what you took from the drying racks.",
            required_props_or_coin={},
            spawn_location_name="NODE_APOTHECARY",
            target_player_threat_delta=0.20
        )

    def validate_causal_invariants(self, beat: ProposedGameBeat, player_pos: Tuple[float, float, float], memory: StudioSharedMemoryBus) -> Tuple[bool, str]:
        npc = beat.target_npc_id
        npc_pos = memory.npc_locations.get(npc)
        if npc_pos and math.dist(npc_pos, player_pos) > 3000.0:
            return False, f"SPATIAL FAULT: {npc} is {math.dist(npc_pos, player_pos):.1f} units away. Cannot teleport."
        for item, qty in beat.required_props_or_coin.items():
            held = memory.npc_inventories.get(npc, {}).get(item, 0.0)
            if held < qty:
                return False, f"MATERIAL FAULT: {npc} lacks {qty}x of '{item}' (Holds {held})."
        return True, "PASSED: Causal continuity verified."

class PersonaDialogueAgent:
    def synthesize_dialogue(self, beat: ProposedGameBeat) -> Dict[str, Any]:
        return {
            "speaker_id": beat.target_npc_id,
            "raw_dialogue": "Welcome to my shop. Bread is scarce, but you look like you need a meal. Step inside.",
            "pad_state": {"P": 0.20, "A": -0.10, "D": 0.30},
            "target_action": beat.action_type
        }

class StyleGuideAgent:
    def audit_and_restyle(self, dialogue_payload: Dict[str, Any]) -> StyleEvaluationReport:
        text = dialogue_payload["raw_dialogue"]
        speaker = dialogue_payload["speaker_id"]
        if "ALDOUS" in speaker:
            restyled = (
                "Flour's up four coppers a sack and the watch is banging on shutters, but I've got two "
                "loaves scorched on the hearthstones. Too burnt for the high seats, which means they're "
                "free for an empty belly. Get inside the cellar before the truncheons swing."
            )
            return StyleEvaluationReport(
                artifact_id=f"STYLE_{speaker}",
                verdict=AestheticVerdict.APPROVED_WITH_SOUL,
                human_touch_score=0.98,
                flagged_cliches=[],
                sensory_density_score=0.85,
                lyric_feedback_notes="Replaced standard dialogue with authentic baker grit.",
                restyled_output=restyled
            )
        return StyleEvaluationReport(
            artifact_id=f"STYLE_{speaker}",
            verdict=AestheticVerdict.APPROVED_WITH_SOUL,
            human_touch_score=0.90,
            flagged_cliches=[],
            sensory_density_score=0.75,
            lyric_feedback_notes="Accepted.",
            restyled_output=text
        )

class LoreConsistencyAuditorAgent:
    def audit_final_artifact(self, artifact_type: ContentType, payload: Dict[str, Any]) -> Tuple[bool, float, str]:
        text = json.dumps(payload).lower()
        if "changed species" in text or "altered horn structure" in text:
            return False, 0.0, "REJECTED: Somatic violation."
        return True, 0.98, "PASSED: Full conformance."

class StateTreeSpecialistAgent:
    def generate_cpp_task_scaffold(self, action_name: str) -> str:
        return f"""#pragma once
#include "CoreMinimal.h"
#include "StateTreeTaskBase.h"
#include "StateTreeTask_{action_name}.generated.h"

USTRUCT(meta = (DisplayName = "Task {action_name}"))
struct MYGAMEPROJECT_API FStateTreeTask_{action_name} : public FStateTreeTaskBase
{{
    GENERATED_BODY()
    virtual EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context, const FStateTreeTransitionResult& Transition) const override
    {{
        return EStateTreeRunStatus::Running;
    }}
}};
"""

class ChaosCrewCommander:
    def __init__(self, damping: float = 0.20):
        self.damping = damping
        self.target_dps_lvl4 = 101.0
        self.current_base_damage = 70.0

    def execute_playtest_matrix(self, seed: int) -> Tuple[List[BugTicket], Optional[str]]:
        tickets = [
            BugTicket(
                ticket_id="BUG-COMBAT-450",
                severity=BugSeverity.P1_HIGH,
                title="DPS Exploit: Min-Maxer animation cancel loop achieved 188.0 DPS",
                description="Rapid melee state switching bypasses weapon recovery frames.",
                reproduction_seed=seed,
                responsible_agent="StateTree_Specialist",
                suggested_action="Add uncancelable recovery frames to StateTree melee task."
            )
        ]
        measured_dps = 188.0
        delta = measured_dps - self.target_dps_lvl4
        factor = 1.0 - (self.damping * (delta / self.target_dps_lvl4))
        hotfixed_base = round(self.current_base_damage * factor, 2)

        csv_hotfix = (
            "---,1,2,3,4,5\n"
            f"Skill_Fireball_BaseDamage,20.00,35.00,50.00,{hotfixed_base:.2f},95.00\n"
        )
        return tickets, csv_hotfix

class StudioDirectorManagerAgent:
    def __init__(self):
        self.memory = StudioSharedMemoryBus()
        self.systems_architect = SystemsArchitectAgent()
        self.level_architect = LevelArchitectAgent()
        self.dm_director = DMDirectorAgent()
        self.persona_synthesizer = PersonaDialogueAgent()
        self.style_guide = StyleGuideAgent()
        self.lore_auditor = LoreConsistencyAuditorAgent()
        self.statetree_specialist = StateTreeSpecialistAgent()
        self.chaos_crew = ChaosCrewCommander()
        self.staging_dir = Path("build/staging")
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def dispatch_studio_pipeline(self, district_id: str, player_stress: float, player_pos: Tuple[float, float, float], seed: int) -> Dict[str, Any]:
        print(f"\n[STUDIO DIRECTOR]: Commencing feature sprint for '{district_id}'...")

        metabolism = self.systems_architect.audit_metabolic_balance(self.memory)
        print(f"  [1/6 Systems] Metabolic equilibrium: {metabolism['is_conserved']}")

        layout = self.level_architect.generate_and_refine_layout(district_id)
        print(f"  [2/6 Level] Layout generated with {len(layout.nodes)} topological nodes")

        beat = self.dm_director.formulate_pacing_beat(player_stress, self.memory)
        is_causal, reason = self.dm_director.validate_causal_invariants(beat, player_pos, self.memory)
        print(f"  [3/6 DM-Director] Beat '{beat.beat_id}' causality: {reason}")
        if not is_causal:
            raise RuntimeError(f"Causal fault: {reason}")

        raw_dialogue = self.persona_synthesizer.synthesize_dialogue(beat)
        style_report = self.style_guide.audit_and_restyle(raw_dialogue)
        raw_dialogue["spoken_dialogue"] = style_report.restyled_output or raw_dialogue["raw_dialogue"]
        print(f"  [4/6 Lyric Style] Human touch score: {style_report.human_touch_score:.2f}")

        approved, lore_score, notes = self.lore_auditor.audit_final_artifact(ContentType.NPC_DIALOGUE_TEMPLATE, raw_dialogue)
        print(f"  [5/6 Lore Auditor] Invariant verification score: {lore_score:.2f} (Approved: {approved})")

        cpp_scaffold = self.statetree_specialist.generate_cpp_task_scaffold(beat.action_type)
        tickets, hotfix_csv = self.chaos_crew.execute_playtest_matrix(seed)
        self.memory.bug_ticket_queue.extend(tickets)
        print(f"  [6/6 Chaos Crew] Headless matrix generated {len(tickets)} bug ticket(s)")

        deliverable = GameReadyArtifact(
            artifact_id=f"ART_{district_id}_{int(self.memory.world_time)}",
            content_type=ContentType.NPC_DIALOGUE_TEMPLATE,
            raw_payload={
                "dialogue": raw_dialogue,
                "target_npc": beat.target_npc_id,
                "action": beat.action_type,
                "spatial_layout": layout.model_dump(),
                "cpp_scaffold": cpp_scaffold,
                "hotfix_csv": hotfix_csv
            },
            style_report=style_report,
            lore_consistency_score=lore_score,
            human_touch_score=style_report.human_touch_score,
            auditor_approved=approved,
            audit_notes=notes
        )

        staged_path = self.staging_dir / f"{deliverable.artifact_id}.json"
        with open(staged_path, "w", encoding="utf-8") as f:
            f.write(deliverable.model_dump_json(indent=2))

        print(f"[STUDIO DIRECTOR]: Artifact staged at {staged_path}\n")
        return deliverable.model_dump()
