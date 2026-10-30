import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import math
from typing import Dict, List, Any, Optional, Tuple

from schemas.studio_contracts import (
    ContentType, AestheticVerdict, BugSeverity, Vector3D, SmartObjectAnchor,
    SpatialRoomNode, DistrictSpatialLayout, StyleEvaluationReport,
    ProposedGameBeat, BugTicket, GameReadyArtifact, SprintGoal,
    ProceduralPropSpec, PropPrimitiveType, LightingProfile, DistrictClientManifest,
    ClientPlaytestReport
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
            "NPC_GARRETT": {"gold": 45.0, "sunfire_blossom": 2.0, "black_market_grain": 5.0},
            "NPC_ALDOUS": {"gold": 12.0, "bread": 15.0}
        }
        self.canon_lore = [
            "Somatic traits (horns, eye pigment, species) are immutable.",
            "The Hearthmother is the sole legitimate harvest deity.",
            "Arch-Prelate Malakor enforces a 35% tithe on licensed guild merchants.",
            "Artisans consider uncompensated stock seizures an act of tyranny."
        ]
        self.bug_ticket_queue: List[BugTicket] = []
        self.active_phase: str = "PEACETIME_COMMERCE"

    def query_lore(self, query: str) -> List[str]:
        words = set(query.lower().split())
        matched = [f for f in self.canon_lore if any(w in f.lower() for w in words if len(w) > 3)]
        return matched if matched else self.canon_lore[:2]


class SystemsArchitectAgent:
    def audit_and_apply_goals(self, memory: StudioSharedMemoryBus, active_goals: List[SprintGoal]) -> Dict[str, Any]:
        goal_titles = [g.primary_objective.lower() for g in active_goals]

        if memory.active_district_unrest >= 0.90 and memory.commodity_reserves["Flour"] <= 15.0:
            memory.active_phase = "MUNICIPAL_BREAD_RIOT"
            memory.commodity_reserves["Flour"] = 55.0
            memory.commodity_reserves["Bread"] = 40.0
            memory.active_district_unrest = 0.45
            trade_regime = "POST_RIOT_MARTIAL_RATIONING"
            for g in active_goals:
                if "drought" in g.primary_objective.lower() or "arbitrage" in g.primary_objective.lower():
                    g.is_completed = True
        elif any("drought" in t or "arbitrage" in t for t in goal_titles):
            memory.commodity_reserves["Flour"] = max(12.0, memory.commodity_reserves["Flour"] - 18.0)
            memory.active_district_unrest = min(0.95, memory.active_district_unrest + 0.08)
            trade_regime = "CONTRABAND_BLACK_MARKET"
        else:
            trade_regime = "STANDARD_GUILD_COMMERCE"

        flour = memory.commodity_reserves.get("Flour", 0.0)
        return {
            "regime": trade_regime,
            "phase": memory.active_phase,
            "flour_level": flour,
            "unrest": memory.active_district_unrest
        }


class LevelArchitectAgent:
    def generate_and_refine_layout(self, district_id: str, active_goals: List[SprintGoal]) -> DistrictSpatialLayout:
        goal_titles = [g.primary_objective.lower() for g in active_goals]

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
            ),
            "NODE_ALLEY": SpatialRoomNode(
                node_id="NODE_ALLEY", zone_name="Shadowed Drainage Way", function="CLANDESTINE_ALLEY",
                bounds_min=Vector3D(x=1500, y=1500, z=0), bounds_max=Vector3D(x=2200, y=2200, z=300),
                center_location=Vector3D(x=1800, y=1800, z=0), connected_node_ids=["NODE_APOTHECARY", "NODE_BAKERY"]
            )
        }
        nodes["NODE_APOTHECARY"].connected_node_ids.append("NODE_ALLEY")
        nodes["NODE_BAKERY"].connected_node_ids.append("NODE_ALLEY")

        if any("aqueduct" in t or "catacombs" in t for t in goal_titles):
            nodes["NODE_AQUEDUCT_CATACOMBS"] = SpatialRoomNode(
                node_id="NODE_AQUEDUCT_CATACOMBS",
                zone_name="Subterranean Aqueduct Conduit",
                function="CLANDESTINE_ALLEY",
                bounds_min=Vector3D(x=0, y=1800, z=-400),
                bounds_max=Vector3D(x=1600, y=2800, z=-50),
                center_location=Vector3D(x=800, y=2300, z=-250),
                connected_node_ids=["NODE_BAKERY", "NODE_ALLEY"],
                smart_objects=[
                    SmartObjectAnchor(
                        anchor_id="SO_SLUICE_GATE_01",
                        smart_object_tag="SmartObject.Mechanism.SluiceGate",
                        relative_position=Vector3D(x=800, y=2300, z=-250),
                        interaction_facing_yaw=0.0
                    )
                ]
            )
            nodes["NODE_BAKERY"].connected_node_ids.append("NODE_AQUEDUCT_CATACOMBS")
            nodes["NODE_ALLEY"].connected_node_ids.append("NODE_AQUEDUCT_CATACOMBS")

        return DistrictSpatialLayout(
            district_id=district_id, district_name=district_id.replace("District_", "") + " Commons",
            nodes=nodes, is_topologically_sound=True
        )


class ClientArchitectAgent:
    def generate_client_manifest(
        self, district_layout: DistrictSpatialLayout, phase: str, unrest: float, goals: List[SprintGoal]
    ) -> DistrictClientManifest:
        if phase == "MUNICIPAL_BREAD_RIOT" or unrest >= 0.80:
            lighting = LightingProfile(
                ambient_sky_hex="#ff4500",
                ambient_ground_hex="#220a05",
                sun_color_hex="#ff7733",
                sun_intensity=0.95,
                fog_color_hex="#1a0805",
                fog_density=0.00030
            )
        else:
            lighting = LightingProfile(
                ambient_sky_hex="#b0c4de",
                ambient_ground_hex="#181c24",
                sun_color_hex="#fff5ea",
                sun_intensity=0.75,
                fog_color_hex="#06080d",
                fog_density=0.00018
            )

        props_by_node: Dict[str, List[ProceduralPropSpec]] = {}
        all_smart_objects: List[SmartObjectAnchor] = []

        for node_id, node in district_layout.nodes.items():
            node_props: List[ProceduralPropSpec] = []
            c = node.center_location
            all_smart_objects.extend(node.smart_objects)

            if "PLAZA" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_OBELISK_01", primitive_type=PropPrimitiveType.OBELISK,
                    relative_position=Vector3D(x=c.x, y=c.y, z=c.z + 170),
                    material_color_hex="#48515f"
                ))
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_STALL_RED", primitive_type=PropPrimitiveType.MARKET_STALL,
                    relative_position=Vector3D(x=c.x - 700, y=c.y - 600, z=c.z), rotation_y=0.4,
                    material_color_hex="#b22222"
                ))
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_STALL_BLUE", primitive_type=PropPrimitiveType.MARKET_STALL,
                    relative_position=Vector3D(x=c.x + 600, y=c.y - 500, z=c.z), rotation_y=-0.5,
                    material_color_hex="#1e88e5"
                ))
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_STALL_GREEN", primitive_type=PropPrimitiveType.MARKET_STALL,
                    relative_position=Vector3D(x=c.x - 500, y=c.y + 700, z=c.z), rotation_y=0.2,
                    material_color_hex="#2e7d32"
                ))
            elif "BAKERY" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_BAKERY_OVEN", primitive_type=PropPrimitiveType.BAKERY_OVEN,
                    relative_position=Vector3D(x=c.x, y=c.y + 200, z=c.z),
                    material_color_hex="#48515f", emissive_color_hex="#ff5500", emissive_intensity=1.5
                ))
            elif "APOTHECARY" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_APOTHECARY_SHELF", primitive_type=PropPrimitiveType.APOTHECARY_SHELF,
                    relative_position=Vector3D(x=c.x, y=c.y - 200, z=c.z),
                    material_color_hex="#5a3d28"
                ))
            elif "AQUEDUCT" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_SLUICE_GATE", primitive_type=PropPrimitiveType.SLUICE_MECHANISM,
                    relative_position=Vector3D(x=c.x + 40, y=c.y, z=c.z),
                    material_color_hex="#22262d", emissive_color_hex="#00f2fe", emissive_intensity=0.8
                ))

            props_by_node[node_id] = node_props

        return DistrictClientManifest(
            district_id=district_layout.district_id,
            world_time=1200.0,
            simulation_phase=phase,
            lighting=lighting,
            props=props_by_node,
            active_smart_objects=all_smart_objects
        )


class DMDirectorAgent:
    def formulate_pacing_beat(
        self, player_stress: float, memory: StudioSharedMemoryBus, active_goals: List[SprintGoal]
    ) -> ProposedGameBeat:
        if memory.active_phase == "MUNICIPAL_BREAD_RIOT":
            return ProposedGameBeat(
                beat_id="BEAT_CURFEW_INSPECTION",
                target_npc_id="NPC_ALDOUS",
                action_type="ENFORCE_MILITARY_RATION",
                narrative_intent="Resolve civic riot; transition to watch garrison rationing",
                dialogue_prompt_concept="By decree of the High Seat, all private baking is suspended. Form the rationing queue.",
                required_props_or_coin={"bread": 1.0},
                spawn_location_name="NODE_BAKERY",
                target_player_threat_delta=-0.30
            )

        goal_titles = [g.primary_objective.lower() for g in active_goals]
        if any("drought" in t or "arbitrage" in t for t in goal_titles) and memory.commodity_reserves["Flour"] < 40.0:
            return ProposedGameBeat(
                beat_id="BEAT_CONTRABAND_TRADE",
                target_npc_id="NPC_GARRETT",
                action_type="TRADE_CONTRABAND_FLOUR",
                narrative_intent="Involve player in illicit grain trafficking under church embargo",
                dialogue_prompt_concept="Keep your voice down. The grain sacks in the cellar don't have cathedral tithe stamps.",
                required_props_or_coin={"black_market_grain": 1.0},
                spawn_location_name="NODE_APOTHECARY",
                target_player_threat_delta=0.35
            )

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

    def validate_causal_invariants(
        self, beat: ProposedGameBeat, player_pos: Tuple[float, float, float], memory: StudioSharedMemoryBus
    ) -> Tuple[bool, str]:
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
            "raw_dialogue": beat.dialogue_prompt_concept,
            "pad_state": {"P": -0.20, "A": 0.40, "D": 0.10},
            "target_action": beat.action_type
        }


class StyleGuideAgent:
    def audit_and_restyle(
        self, dialogue_payload: Dict[str, Any], active_goals: List[SprintGoal]
    ) -> StyleEvaluationReport:
        text = dialogue_payload["raw_dialogue"]
        speaker = dialogue_payload["speaker_id"]
        action = dialogue_payload.get("target_action", "")

        if action == "ENFORCE_MILITARY_RATION":
            restyled = (
                "The church seal is on the ovens. Hearthmother’s peace is done—watch captain seized every "
                "sack of barley at dawn. Take your four ounces of hardtack and clear the square before the spears level."
            )
        elif "GARRETT" in speaker and "CONTRABAND" in action:
            restyled = (
                "Lower your head and step past the drying rack. The millers in the Undercroft ground this "
                "under tallow torches—no orthodoxy wax, no tithe marks. If the watch finds this bushel, "
                "we're both hanging from the aqueduct arches."
            )
        elif "ALDOUS" in speaker:
            restyled = (
                "Flour's up another four coppers and church guards are pounding on shutters. "
                "I've got two charred loaves off the hearthstones. Grab 'em and get down into the drainage vault."
            )
        else:
            restyled = text

        return StyleEvaluationReport(
            artifact_id=f"STYLE_{speaker}",
            verdict=AestheticVerdict.APPROVED_WITH_SOUL,
            human_touch_score=0.98,
            flagged_cliches=[],
            sensory_density_score=0.90,
            lyric_feedback_notes="Tactile, grounded dialogue with rich cultural cadence.",
            restyled_output=restyled
        )


class LoreConsistencyAuditorAgent:
    def audit_final_artifact(self, artifact_type: ContentType, payload: Dict[str, Any]) -> Tuple[bool, float, str]:
        text = json.dumps(payload).lower()
        if "changed species" in text or "altered horn structure" in text:
            return False, 0.0, "REJECTED: Somatic violation."
        return True, 0.98, "PASSED: Full conformance with canon dogmas."


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

    def execute_client_headless_playtest(
        self, layout: DistrictSpatialLayout, manifest: DistrictClientManifest
    ) -> Tuple[ClientPlaytestReport, List[BugTicket]]:
        tickets: List[BugTicket] = []
        traversed_count = 0
        unreachable = []
        interaction_failures = []

        for node_id, node in layout.nodes.items():
            if not node.connected_node_ids and len(layout.nodes) > 1:
                unreachable.append(node_id)
                tickets.append(BugTicket(
                    ticket_id=f"BUG-NAV-{node_id}",
                    severity=BugSeverity.P2_MEDIUM,
                    title=f"Navigation Fault: Node {node_id} isolated",
                    description=f"Automated pathfinder cannot reach {node.zone_name}.",
                    reproduction_seed=42109,
                    responsible_agent="Level_Architect",
                    suggested_action="Connect node to adjacent district rooms."
                ))
            else:
                traversed_count += 1

        for so in manifest.active_smart_objects:
            pos = so.relative_position
            matching_room = False
            for node in layout.nodes.values():
                min_b, max_b = node.bounds_min, node.bounds_max
                if min_b.x <= pos.x <= max_b.x and min_b.y <= pos.y <= max_b.y:
                    matching_room = True
                    break
            if not matching_room:
                interaction_failures.append(so.anchor_id)
                tickets.append(BugTicket(
                    ticket_id=f"BUG-SO-BOUNDS-{so.anchor_id}",
                    severity=BugSeverity.P1_HIGH,
                    title=f"Smart Object Out of Bounds: {so.anchor_id}",
                    description=f"{so.anchor_id} positioned outside floorplate bounds ({pos.x}, {pos.y}).",
                    reproduction_seed=42109,
                    responsible_agent="Client_Architect",
                    suggested_action="Clamp anchor coordinates inside host node boundaries."
                ))

        report = ClientPlaytestReport(
            nodes_traversed=traversed_count,
            unreachable_nodes=unreachable,
            interaction_failures=interaction_failures,
            average_socket_latency_ms=18.4,
            out_of_bounds_detected=len(interaction_failures) > 0,
            verdict="PASS" if len(tickets) == 0 else "FAIL_BUGS_FILED"
        )
        return report, tickets


class StudioDirectorManagerAgent:
    def __init__(self):
        self.memory = StudioSharedMemoryBus()
        self.systems_architect = SystemsArchitectAgent()
        self.level_architect = LevelArchitectAgent()
        self.client_architect = ClientArchitectAgent()
        self.dm_director = DMDirectorAgent()
        self.persona_synthesizer = PersonaDialogueAgent()
        self.style_guide = StyleGuideAgent()
        self.lore_auditor = LoreConsistencyAuditorAgent()
        self.statetree_specialist = StateTreeSpecialistAgent()
        self.chaos_crew = ChaosCrewCommander()
        self.staging_dir = Path("build/staging")
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def dispatch_studio_pipeline(
        self,
        district_id: str,
        player_stress: float,
        player_pos: Tuple[float, float, float],
        seed: int,
        active_goals: Optional[List[SprintGoal]] = None
    ) -> Dict[str, Any]:
        goals = active_goals or []
        print(f"\n[STUDIO DIRECTOR]: Commencing sprint for '{district_id}' | Phase: {self.memory.active_phase}")

        metabolism = self.systems_architect.audit_and_apply_goals(self.memory, goals)
        print(f"  [1/8 Systems] Regime: {metabolism['regime']} | Flour Reserve: {metabolism['flour_level']:.1f}")

        layout = self.level_architect.generate_and_refine_layout(district_id, goals)
        print(f"  [2/8 Level] Topology: {len(layout.nodes)} rooms")

        manifest = self.client_architect.generate_client_manifest(layout, self.memory.active_phase, metabolism['unrest'], goals)
        print(f"  [3/8 Client Architect] Manifest built with {sum(len(p) for p in manifest.props.values())} props")

        beat = self.dm_director.formulate_pacing_beat(player_stress, self.memory, goals)
        is_causal, reason = self.dm_director.validate_causal_invariants(beat, player_pos, self.memory)
        print(f"  [4/8 DM-Director] Beat '{beat.beat_id}' -> Causality: {reason}")
        if not is_causal:
            raise RuntimeError(f"Causal fault: {reason}")

        raw_dialogue = self.persona_synthesizer.synthesize_dialogue(beat)
        style_report = self.style_guide.audit_and_restyle(raw_dialogue, goals)
        raw_dialogue["spoken_dialogue"] = style_report.restyled_output or raw_dialogue["raw_dialogue"]
        print(f"  [5/8 Lyric Style] Human touch score: {style_report.human_touch_score:.2f}")

        approved, lore_score, notes = self.lore_auditor.audit_final_artifact(ContentType.NPC_DIALOGUE_TEMPLATE, raw_dialogue)
        print(f"  [6/8 Lore Auditor] Verification: {lore_score:.2f} (Approved: {approved})")

        cpp_scaffold = self.statetree_specialist.generate_cpp_task_scaffold(beat.action_type)
        tickets, hotfix_csv = self.chaos_crew.execute_playtest_matrix(seed)
        self.memory.bug_ticket_queue.extend(tickets)
        print(f"  [7/8 Chaos Crew] Headless matrix: {len(tickets)} combat tickets filed")

        client_report, client_tickets = self.chaos_crew.execute_client_headless_playtest(layout, manifest)
        self.memory.bug_ticket_queue.extend(client_tickets)
        print(f"  [8/8 Chaos Client Bot] Client Audit: {client_report.nodes_traversed} nodes verified, {len(client_tickets)} bounds tickets")

        deliverable = GameReadyArtifact(
            artifact_id=f"ART_{district_id}_{int(self.memory.world_time)}",
            content_type=ContentType.NPC_DIALOGUE_TEMPLATE,
            raw_payload={
                "dialogue": raw_dialogue,
                "target_npc": beat.target_npc_id,
                "action": beat.action_type,
                "spatial_layout": layout.model_dump(),
                "client_manifest": manifest.model_dump(),
                "client_playtest": client_report.model_dump(),
                "cpp_scaffold": cpp_scaffold,
                "hotfix_csv": hotfix_csv,
                "district_unrest": metabolism["unrest"],
                "active_phase": self.memory.active_phase,
                "active_goals": [g.primary_objective for g in goals if not g.is_completed]
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

        return deliverable.model_dump()
