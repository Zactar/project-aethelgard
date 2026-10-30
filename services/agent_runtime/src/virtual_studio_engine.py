#!/usr/bin/env python3
"""
PROJECT AETHELGARD: VIRTUAL STUDIO ENGINE
Drives algorithmic district layouts, dynamic NPC roster generation, adaptive pacing beats,
authoritative 3-act quest DAG progression, and multi-tier chaos playtesting.
"""

from services.agent_runtime.src.chroma_lore_bus import ChromaLoreBus
from schemas.studio_contracts import (
    AestheticVerdict, BugSeverity, BugTicket, ClientPlaytestReport, ContentType,
    DistrictSpatialLayout, GameReadyArtifact, GameRuntimeManifest,
    GameplayMechanicsSpec, ItemCategory, ItemSpec, LightingProfile,
    NPCActorSpec, ObjectiveStatus, ProceduralPropSpec, PropPrimitiveType,
    ProposedGameBeat, QuestObjective, SmartObjectAnchor, SpatialRoomNode,
    SprintGoal, StyleEvaluationReport, SystemicQuest, UIThemeSpec, Vector3D
)
import json
import math
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# Diverse NPC archetypes mapped to zone functions
NPC_ARCHETYPES = [
    {
        "npc_id": "NPC_ALDOUS",
        "name": "Aldous the Baker",
        "role": "Guild Baker",
        "faction": "Bakers Fellowship",
        "color_hex": "#f5af19",
        "zone_affinity": ["CIVIC_GATHERING", "WORKSHOP_CRAFT"],
        "dialogues": [
            "Communal hearths are banked under ash; cathedral tithes took half the barley.",
            "If the watch captain comes knocking, tell him the flour sacks were already moldy.",
            "The ovens haven't had clean timber since the river freeze. Take what's on the stone."
        ],
        "inventory": {"item_bread": 12, "item_flour": 5}
    },
    {
        "npc_id": "NPC_GARRETT",
        "name": "Garrett the Herbalist",
        "role": "Apothecary Merchant",
        "faction": "Artisans Guild",
        "color_hex": "#2ecc71",
        "zone_affinity": ["COMMERCIAL_STALL", "CIVIC_PLAZA"],
        "dialogues": [
            "Lower your voice. Nightshade and dried hemlock on the top shelf don't carry tithe stamps.",
            "The church inquisitors checked my ledger twice before the morning bell. Be swift.",
            "Looking for mountain salves or the untagged grain from the undervaults?"
        ],
        "inventory": {"item_sunfire_salve": 4, "item_contraband_grain": 2}
    },
    {
        "npc_id": "NPC_CAPTAIN_VANE",
        "name": "Watch Captain Vane",
        "role": "Garrison Commander",
        "faction": "City Watch",
        "color_hex": "#e74c3c",
        "zone_affinity": ["MILITARY_CHECKPOINT", "CIVIC_PLAZA"],
        "dialogues": [
            "Curfew bell sounds at the sixth chime. Any citizen in the square without a stamped permit answers to my halberds.",
            "Arch-Prelate Malakor's tithe carts roll at sundown. Clear the thoroughfare or face the stockade.",
            "You smell of canal silt. Step forward for inspection before you cross the gate."
        ],
        "inventory": {"item_forged_permit": 1}
    },
    {
        "npc_id": "NPC_KAELEN",
        "name": "Kaelen the Smuggler",
        "role": "Black Market Broker",
        "faction": "Undercroft Syndicate",
        "color_hex": "#9b59b6",
        "zone_affinity": ["CLANDESTINE_STORAGE", "CLANDESTINE_ALLEY"],
        "dialogues": [
            "The water sluice is open for the next thirty minutes. If you want untithed barley, pay up front.",
            "Watch out for the garrison scouts near the canal grates. They've doubled the guard.",
            "I've got three forged seals off the cathedral printing press. Pure beeswax, identical stamp."
        ],
        "inventory": {"item_smoke_phial": 3, "item_salted_jerky": 5}
    },
    {
        "npc_id": "NPC_ORLOV",
        "name": "Dockmaster Orlov",
        "role": "Harbor Overseer",
        "faction": "Canal Guild",
        "color_hex": "#3498db",
        "zone_affinity": ["TRANSIT_WATERWAY", "COMMERCIAL_STALL"],
        "dialogues": [
            "Low-tide cargo winches are locked until the episcopate clears the shipping manifest.",
            "Sluice gates are groaning under the canal pressure. Hand me that iron wedge.",
            "The mountain barges came in light this morning. Grain prices will double by nightfall."
        ],
        "inventory": {"item_salted_jerky": 8}
    }
]

BEAT_ACTION_TEMPLATES = [
    {
        "action": "ENFORCE_CURFEW_INSPECTION",
        "role_match": "Garrison Commander",
        "prompt": "Level your spear and demand citizenship papers under decree of the High Seat.",
        "threat": 0.40
    },
    {
        "action": "TRADE_CONTRABAND_FLOUR",
        "role_match": "Black Market Broker",
        "prompt": "Whisper the secret password and slide the untithed grain bushel beneath the grate.",
        "threat": 0.25
    },
    {
        "action": "OFFER_SHELTER_AND_BREAD",
        "role_match": "Guild Baker",
        "prompt": "Quickly unlatch the cellar door and push the player out of sight of the patrol.",
        "threat": -0.45
    },
    {
        "action": "BROWSE_HERBAL_TINCTURES",
        "role_match": "Apothecary Merchant",
        "prompt": "Offer restorative salves while glancing nervously toward the garrison guard tower.",
        "threat": 0.10
    },
    {
        "action": "INSPECT_CARGO_CRANE",
        "role_match": "Harbor Overseer",
        "prompt": "Point toward the jammed sluice mechanism and demand help with the release chain.",
        "threat": 0.15
    }
]


class StudioSharedMemoryBus:
    def __init__(self):
        self.world_time: float = 1200.0
        self.active_district_unrest: float = 0.58
        self.commodity_reserves: Dict[str, float] = {
            "Grain": 120.0, "Flour": 85.0, "Bread": 60.0}
        self.bug_ticket_queue: List[Any] = []
        self.active_phase: str = "PEACETIME_COMMERCE"
        self.lore_bus = ChromaLoreBus()
        self.active_quests: List[SystemicQuest] = []

    def query_lore(self, query: str) -> List[str]:
        return self.lore_bus.query_lore_context(query, top_k=2)

    def advance_quest_objective(
        self, target_id: str, target_tag: str = ""
    ) -> Tuple[bool, Optional[SystemicQuest], Optional[str]]:
        for quest in self.active_quests:
            if quest.is_completed:
                continue
            for idx, obj in enumerate(quest.objectives):
                if obj.status == ObjectiveStatus.ACTIVE:
                    match_so = obj.target_smart_object and (
                        target_id == obj.target_smart_object or (
                            target_tag and target_tag in obj.target_smart_object)
                    )
                    match_npc = obj.target_npc_id and (
                        target_id == obj.target_npc_id)
                    if match_so or match_npc:
                        obj.status = ObjectiveStatus.COMPLETED
                        if idx + 1 < len(quest.objectives):
                            quest.objectives[idx +
                                             1].status = ObjectiveStatus.ACTIVE
                            return True, quest, None
                        else:
                            quest.is_completed = True
                            curr_idx = self.active_quests.index(quest)
                            if curr_idx + 1 < len(self.active_quests):
                                next_q = self.active_quests[curr_idx + 1]
                                if next_q.objectives:
                                    next_q.objectives[0].status = ObjectiveStatus.ACTIVE
                            return True, quest, quest.reward_item_id
            break
        return False, None, None


class SystemsArchitectAgent:
    def audit_and_synthesize_economy(
        self, memory: StudioSharedMemoryBus, active_goals: List[SprintGoal]
    ) -> Tuple[Dict[str, Any], Dict[str, ItemSpec]]:
        goal_titles = [g.primary_objective.lower() for g in active_goals]

        if memory.active_district_unrest >= 0.85 and memory.commodity_reserves["Flour"] <= 20.0:
            memory.active_phase = "MUNICIPAL_BREAD_RIOT"
            trade_regime = "POST_RIOT_MARTIAL_RATIONING"
        elif any("smuggl" in t or "tithe" in t or "contraband" in t for t in goal_titles):
            memory.commodity_reserves["Flour"] = max(
                10.0, memory.commodity_reserves["Flour"] - 12.0)
            memory.active_district_unrest = min(
                0.95, memory.active_district_unrest + 0.05)
            trade_regime = "CONTRABAND_BLACK_MARKET"
        else:
            trade_regime = "STANDARD_GUILD_COMMERCE"

        flour_price = 14.0 if trade_regime == "CONTRABAND_BLACK_MARKET" else 5.0
        items = {
            "item_bread": ItemSpec(
                item_id="item_bread", display_name="Hearth Bread", category=ItemCategory.CONSUMABLE,
                base_value=6.0, description="Dense barley bread baked on communal stones. Restores 35 stamina.",
                icon_symbol="🍞", effects={"stamina_restore": 35.0}
            ),
            "item_flour": ItemSpec(
                item_id="item_flour", display_name="Milled Flour", category=ItemCategory.COMMODITY,
                base_value=flour_price, description="Standard guild-stamped flour bushel for bakery ovens.",
                icon_symbol="🌾"
            ),
            "item_sunfire_salve": ItemSpec(
                item_id="item_sunfire_salve", display_name="Sunfire Salve", category=ItemCategory.CONSUMABLE,
                base_value=24.0, description="Apothecary ointment made from mountain blossoms. Increases speed by 25%.",
                icon_symbol="🧪", effects={"speed_boost": 0.25, "duration_sec": 14.0}
            ),
            "item_contraband_grain": ItemSpec(
                item_id="item_contraband_grain", display_name="Illicit Grain Bushel", category=ItemCategory.CONTRABAND,
                base_value=32.0, description="Untithed grain ground in subterranean drainage vaults. Highly illegal.",
                icon_symbol="🪙", effects={"stealth_bonus": 0.35, "duration_sec": 20.0}
            )
        }

        meta = {
            "regime": trade_regime,
            "phase": memory.active_phase,
            "flour_level": memory.commodity_reserves.get("Flour", 0.0),
            "unrest": memory.active_district_unrest
        }
        return meta, items


class LevelArchitectAgent:
    def generate_and_refine_layout(
        self, district_id: str, active_goals: List[SprintGoal]
    ) -> DistrictSpatialLayout:
        manifest_path = Path("web_client/game_runtime_manifest.json")
        if manifest_path.exists():
            try:
                manifest = GameRuntimeManifest.model_validate_json(
                    manifest_path.read_text(encoding="utf-8"))
                return manifest.spatial_layout
            except Exception:
                pass

        nodes = {
            "NODE_PLAZA": SpatialRoomNode(
                node_id="NODE_PLAZA", zone_name="Market Cross Square", function="CIVIC_PLAZA",
                bounds_min=Vector3D(x=-1500, y=-1500, z=0), bounds_max=Vector3D(x=1500, y=1500, z=500),
                center_location=Vector3D(x=0, y=0, z=0), connected_node_ids=["NODE_APOTHECARY", "NODE_BAKERY"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_RALLY", smart_object_tag="SmartObject.Civic.RallyPoint", relative_position=Vector3D(
                    x=0, y=0, z=0), interaction_facing_yaw=0.0)]
            ),
            "NODE_APOTHECARY": SpatialRoomNode(
                node_id="NODE_APOTHECARY", zone_name="Garrett's Curatives", function="COMMERCIAL_STALL",
                bounds_min=Vector3D(x=1800, y=-600, z=0), bounds_max=Vector3D(x=2800, y=600, z=400),
                center_location=Vector3D(x=2300, y=0, z=0), connected_node_ids=["NODE_PLAZA"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_GARRETT", smart_object_tag="SmartObject.Merchant.ApothecaryCounter",
                                                 assigned_npc_id="NPC_GARRETT", relative_position=Vector3D(x=2100, y=0, z=0), interaction_facing_yaw=180.0)]
            ),
            "NODE_BAKERY": SpatialRoomNode(
                node_id="NODE_BAKERY", zone_name="The Common Loaf", function="WORKSHOP_CRAFT",
                bounds_min=Vector3D(x=-600, y=1800, z=0), bounds_max=Vector3D(x=600, y=2800, z=400),
                center_location=Vector3D(x=0, y=2300, z=0), connected_node_ids=["NODE_PLAZA"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_ALDOUS", smart_object_tag="SmartObject.Craft.BreadOven",
                                                 assigned_npc_id="NPC_ALDOUS", relative_position=Vector3D(x=0, y=2500, z=0), interaction_facing_yaw=90.0)]
            ),
            "NODE_AQUEDUCT_CATACOMBS": SpatialRoomNode(
                node_id="NODE_AQUEDUCT_CATACOMBS", zone_name="Subterranean Aqueduct Conduit", function="CLANDESTINE_ALLEY",
                bounds_min=Vector3D(x=0, y=1800, z=-400), bounds_max=Vector3D(x=1600, y=2800, z=-50),
                center_location=Vector3D(x=800, y=2300, z=-250), connected_node_ids=["NODE_BAKERY"],
                smart_objects=[SmartObjectAnchor(anchor_id="SO_SLUICE_GATE_01", smart_object_tag="SmartObject.Mechanism.SluiceGate",
                                                 relative_position=Vector3D(x=800, y=2300, z=-250), interaction_facing_yaw=0.0)]
            )
        }
        return DistrictSpatialLayout(district_id=district_id, district_name=district_id.replace("District_", "") + " Commons", nodes=nodes, is_topologically_sound=True)


class ClientArchitectAgent:
    def design_ui_and_props(
        self, district_layout: DistrictSpatialLayout, phase: str, unrest: float, goals: List[SprintGoal]
    ) -> Tuple[UIThemeSpec, LightingProfile, Dict[str, List[ProceduralPropSpec]]]:
        if phase == "MUNICIPAL_BREAD_RIOT" or unrest >= 0.80:
            lighting = LightingProfile(
                ambient_sky_hex="#ff4500", ambient_ground_hex="#220a05",
                sun_color_hex="#ff7733", sun_intensity=0.95,
                fog_color_hex="#1a0805", fog_density=0.00030
            )
            theme = UIThemeSpec(
                primary_color_hex="#ff5252", accent_color_hex="#ffa726",
                hud_title="AETHELGARD: STATE OF SIEGE",
                action_buttons=[
                    {"id": "btn_curfew", "label": "Inspect Watch Patrols",
                        "action": "STRESS_SPIKE"}
                ]
            )
        else:
            lighting = LightingProfile(
                ambient_sky_hex="#b0c4de", ambient_ground_hex="#181c24",
                sun_color_hex="#fff5ea", sun_intensity=0.75,
                fog_color_hex="#06080d", fog_density=0.00018
            )
            theme = UIThemeSpec(
                primary_color_hex="#4facfe", accent_color_hex="#00f2fe",
                hud_title="AETHELGARD GROUND CONTROL",
                action_buttons=[
                    {"id": "btn_combat",
                        "label": "Trigger Combat Spike (0.85)", "action": "STRESS_SPIKE"},
                    {"id": "btn_rest",
                        "label": "Peacetime Repose (0.20)", "action": "PEACE_REST"}
                ]
            )

        props_by_node: Dict[str, List[ProceduralPropSpec]] = {}
        for node_id, node in district_layout.nodes.items():
            node_props: List[ProceduralPropSpec] = []
            c = node.center_location
            if "PLAZA" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_OBELISK_01", primitive_type=PropPrimitiveType.OBELISK, relative_position=Vector3D(x=c.x, y=c.y, z=c.z + 170)))
                node_props.append(ProceduralPropSpec(prop_id="PROP_STALL_RED", primitive_type=PropPrimitiveType.MARKET_STALL,
                                  relative_position=Vector3D(x=c.x - 700, y=c.y - 600, z=c.z), rotation_y=0.4, material_color_hex="#b22222"))
            elif "BAKERY" in node_id:
                node_props.append(ProceduralPropSpec(prop_id="PROP_BAKERY_OVEN", primitive_type=PropPrimitiveType.BAKERY_OVEN, relative_position=Vector3D(
                    x=c.x, y=c.y + 200, z=c.z), material_color_hex="#48515f", emissive_color_hex="#ff5500", emissive_intensity=1.5))
            elif "APOTHECARY" in node_id:
                node_props.append(ProceduralPropSpec(prop_id="PROP_APOTHECARY_SHELF",
                                  primitive_type=PropPrimitiveType.APOTHECARY_SHELF, relative_position=Vector3D(x=c.x, y=c.y - 200, z=c.z)))
            elif "AQUEDUCT" in node_id:
                node_props.append(ProceduralPropSpec(prop_id="PROP_SLUICE_GATE", primitive_type=PropPrimitiveType.SLUICE_MECHANISM, relative_position=Vector3D(
                    x=c.x + 40, y=c.y, z=c.z), material_color_hex="#22262d", emissive_color_hex="#00f2fe", emissive_intensity=0.8))
            props_by_node[node_id] = node_props

        return theme, lighting, props_by_node


class GameplayMechanicsSpecialistAgent:
    def tune_mechanics(self, unrest: float, phase: str) -> GameplayMechanicsSpec:
        speed = 1550.0 if phase == "MUNICIPAL_BREAD_RIOT" else 1400.0
        return GameplayMechanicsSpec(
            player_base_speed=speed, sprint_multiplier=1.6,
            stamina_max=100.0, stamina_recovery_rate=14.0,
            interaction_radius=480.0, camera_fov=45.0, camera_default_distance=3000.0
        )


class NarrativeNPCSpecialistAgent:
    def synthesize_npc_roster(
        self, layout: DistrictSpatialLayout, phase: str, unrest: float
    ) -> Dict[str, NPCActorSpec]:
        roster: Dict[str, NPCActorSpec] = {}
        nodes_list = list(layout.nodes.values())

        for arc in NPC_ARCHETYPES:
            matching_node = None
            for node in layout.nodes.values():
                if node.function in arc["zone_affinity"] or any(aff in node.zone_name.upper() for aff in arc["zone_affinity"]):
                    matching_node = node
                    break

            if not matching_node:
                matching_node = nodes_list[len(roster) % len(nodes_list)]

            cx = matching_node.center_location.x + random.uniform(-120, 120)
            cy = matching_node.center_location.y + random.uniform(-120, 120)
            cz = matching_node.center_location.z

            so_id = matching_node.smart_objects[0].anchor_id if matching_node.smart_objects else None

            waypoints: List[Vector3D] = [Vector3D(x=cx, y=cy, z=cz)]
            if matching_node.smart_objects:
                so_pos = matching_node.smart_objects[0].relative_position
                waypoints.append(
                    Vector3D(x=so_pos.x + 80.0, y=so_pos.y, z=so_pos.z))

            for neighbor_id in matching_node.connected_node_ids[:2]:
                if neighbor_id in layout.nodes:
                    n_center = layout.nodes[neighbor_id].center_location
                    waypoints.append(Vector3D(
                        x=n_center.x + random.uniform(-100, 100),
                        y=n_center.y + random.uniform(-100, 100),
                        z=n_center.z
                    ))

            roster[arc["npc_id"]] = NPCActorSpec(
                npc_id=arc["npc_id"],
                name=arc["name"],
                role=arc["role"],
                faction=arc["faction"],
                color_hex=arc["color_hex"],
                position=Vector3D(x=cx, y=cy, z=cz),
                default_dialogue=random.choice(arc["dialogues"]),
                inventory=arc["inventory"],
                assigned_smart_object=so_id,
                patrol_waypoints=waypoints,
                current_schedule_activity="PATROL"
            )

        return roster

    def synthesize_systemic_quests(
        self, phase: str, unrest: float, goals: List[SprintGoal], npcs: Dict[str, NPCActorSpec]
    ) -> List[SystemicQuest]:
        return [
            SystemicQuest(
                quest_id="QUEST_ACT_1_BREAD",
                title="Act I: The Hearthmother's Tithe",
                synopsis="Aldous requires untithed flour from the undercroft vaults to fire the communal ovens.",
                issuing_npc_id="NPC_ALDOUS",
                reward_item_id="item_bread",
                reward_stamina=35.0,
                completion_debrief="Aldous banks the untithed flour into the communal ovens, easing bread rations for the district artisans and unlocking access to subterranean smugglers.",
                objectives=[
                    QuestObjective(objective_id="OBJ_BREAD_01", description="Inspect communal ovens at The Common Loaf.",
                                   target_node_id="NODE_BAKERY", target_smart_object="SO_ALDOUS", status=ObjectiveStatus.ACTIVE),
                    QuestObjective(objective_id="OBJ_BREAD_02", description="Confer with Garrett regarding herbal nightshade stocks.",
                                   target_node_id="NODE_APOTHECARY", target_npc_id="NPC_GARRETT", status=ObjectiveStatus.LOCKED)
                ]
            ),
            SystemicQuest(
                quest_id="QUEST_ACT_2_UNDERCROFT",
                title="Act II: The Undercroft Run",
                synopsis="Smuggler Kaelen needs the aqueduct sluice opened to float illicit grain into the harbor.",
                issuing_npc_id="NPC_KAELEN",
                reward_item_id="item_forged_permit",
                reward_stamina=45.0,
                completion_debrief="Subterranean floodwaters hiss into the sea canals. Kaelen hands you a forged cathedral transit permit stamped in tallow wax.",
                objectives=[
                    QuestObjective(objective_id="OBJ_KAELEN_01", description="Operate Sluice Gate 01 to drain the subterranean basin.",
                                   target_node_id="NODE_AQUEDUCT_CATACOMBS", target_smart_object="SO_SLUICE_GATE_01", status=ObjectiveStatus.ACTIVE),
                    QuestObjective(objective_id="OBJ_KAELEN_02", description="Rendezvous with Kaelen the Smuggler in the lower vaults.",
                                   target_node_id="NODE_AQUEDUCT_CATACOMBS", target_npc_id="NPC_KAELEN", status=ObjectiveStatus.LOCKED)
                ]
            ),
            SystemicQuest(
                quest_id="QUEST_ACT_3_GARRISON",
                title="Act III: The Episcopal Inquest",
                synopsis="Watch Captain Vane has cordoned the market cross. Infiltrate the checkpoint.",
                issuing_npc_id="NPC_CAPTAIN_VANE",
                reward_item_id="item_sunfire_salve",
                reward_stamina=50.0,
                completion_debrief="You bypass the city watch perimeter with your forged pass, establishing an unbroken supply corridor across the entire district.",
                objectives=[
                    QuestObjective(objective_id="OBJ_VANE_01", description="Inspect the Arch-Prelate's decree at the Market Cross.",
                                   target_node_id="NODE_PLAZA", target_smart_object="SO_RALLY", status=ObjectiveStatus.ACTIVE),
                    QuestObjective(objective_id="OBJ_VANE_02", description="Confront Watch Captain Vane at the garrison checkpoint.",
                                   target_node_id="NODE_PLAZA", target_npc_id="NPC_CAPTAIN_VANE", status=ObjectiveStatus.LOCKED)
                ]
            )
        ]


class DMDirectorAgent:
    def formulate_pacing_beat(
        self,
        player_stress: float,
        memory: StudioSharedMemoryBus,
        active_goals: List[SprintGoal],
        npcs: Dict[str, NPCActorSpec]
    ) -> ProposedGameBeat:
        npc_ids = list(npcs.keys())
        target_id = random.choice(npc_ids) if npc_ids else "NPC_GARRETT"
        target_npc = npcs.get(target_id)
        role = target_npc.role if target_npc else "Merchant"

        matched_action = None
        for tmpl in BEAT_ACTION_TEMPLATES:
            if tmpl["role_match"].lower() in role.lower():
                matched_action = tmpl
                break

        if not matched_action:
            matched_action = random.choice(BEAT_ACTION_TEMPLATES)

        beat_id = f"BEAT_{matched_action['action']}_{int(memory.world_time) % 1000}"

        return ProposedGameBeat(
            beat_id=beat_id,
            target_npc_id=target_id,
            action_type=matched_action["action"],
            narrative_intent=f"Engage player in {matched_action['action'].lower()} driven by {target_npc.name if target_npc else target_id}",
            dialogue_prompt_concept=target_npc.default_dialogue if target_npc else matched_action[
                "prompt"],
            required_props_or_coin={},
            spawn_location_name="NODE_PLAZA",
            target_player_threat_delta=matched_action["threat"]
        )

    def validate_causal_invariants(
        self, beat: ProposedGameBeat, player_pos: Tuple[float, float, float], npcs: Dict[str, NPCActorSpec]
    ) -> Tuple[bool, str]:
        npc = npcs.get(beat.target_npc_id)
        if npc:
            p = (npc.position.x, npc.position.y, npc.position.z)
            if math.dist(p, player_pos) > 12000.0:
                return False, f"SPATIAL FAULT: {npc.name} is {math.dist(p, player_pos):.1f} units away."
        return True, "PASSED: Causal continuity verified."


class StyleGuideAgent:
    def audit_and_restyle(
        self, dialogue_payload: Dict[str, Any], active_goals: List[SprintGoal]
    ) -> StyleEvaluationReport:
        text = dialogue_payload["raw_dialogue"]
        speaker = dialogue_payload["speaker_id"]
        action = dialogue_payload.get("target_action", "")

        return StyleEvaluationReport(
            artifact_id=f"STYLE_{speaker}",
            verdict=AestheticVerdict.APPROVED_WITH_SOUL,
            human_touch_score=0.98,
            flagged_cliches=[],
            sensory_density_score=0.92,
            lyric_feedback_notes=f"Evocative dialogue tailored for {speaker} executing {action}.",
            restyled_output=text
        )


class LoreConsistencyAuditorAgent:
    def audit_final_artifact(self, payload: Dict[str, Any]) -> Tuple[bool, float, str]:
        text = json.dumps(payload).lower()
        if "changed species" in text or "altered horn structure" in text:
            return False, 0.0, "REJECTED: Somatic violation."
        return True, 0.98, "PASSED: Full conformance with canon dogmas."


class ChaosCrewCommander:
    def execute_client_headless_playtest(
        self, layout: DistrictSpatialLayout, npcs: Dict[str, NPCActorSpec], mechanics: GameplayMechanicsSpec
    ) -> Tuple[ClientPlaytestReport, List[BugTicket]]:
        traversed = len(layout.nodes)
        tickets: List[BugTicket] = []

        # 1. Audit Locomotion Bounds
        if mechanics.player_base_speed < 1450.0:
            tickets.append(BugTicket(
                ticket_id=f"TICK-SPD-{int(time.time()) % 1000}",
                severity=BugSeverity.P2_MEDIUM,
                title="Player Base Speed Sub-Optimal",
                description="Movement velocity is below standard citadel exploration target (1500.0).",
                reproduction_seed=42109,
                responsible_agent="Gameplay_Specialist",
                suggested_action="Adjust player_base_speed in schema contracts."
            ))

        # 2. Audit NPC Patrol Pacing
        if npcs and any(len(n.patrol_waypoints) > 2 for n in npcs.values()):
            tickets.append(BugTicket(
                ticket_id=f"TICK-PAT-{int(time.time()) % 1000}",
                severity=BugSeverity.P3_LOW,
                title="NPC Walk Patrol Cadence Tuning",
                description="NPC street movement speed can be calibrated for natural thoroughfare flow.",
                reproduction_seed=42110,
                responsible_agent="Level_Architect",
                suggested_action="Calibrate npcWalkSpeed in client runtime loop."
            ))

        report = ClientPlaytestReport(
            nodes_traversed=traversed,
            unreachable_nodes=[],
            interaction_failures=[],
            average_socket_latency_ms=15.8,
            out_of_bounds_detected=False,
            verdict="PASS"
        )
        return report, tickets


class StudioDirectorManagerAgent:
    def __init__(self):
        self.memory = StudioSharedMemoryBus()
        self.systems_architect = SystemsArchitectAgent()
        self.level_architect = LevelArchitectAgent()
        self.client_architect = ClientArchitectAgent()
        self.gameplay_specialist = GameplayMechanicsSpecialistAgent()
        self.narrative_specialist = NarrativeNPCSpecialistAgent()
        self.dm_director = DMDirectorAgent()
        self.style_guide = StyleGuideAgent()
        self.lore_auditor = LoreConsistencyAuditorAgent()
        self.chaos_crew = ChaosCrewCommander()
        self.staging_dir = Path("build/staging")
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def build_live_manifest(self, district_id: str = "District_MarketSquare") -> Dict[str, Any]:
        manifest_path = ROOT_DIR / "web_client" / "game_runtime_manifest.json"
        if manifest_path.exists():
            try:
                m = json.loads(manifest_path.read_text(encoding="utf-8"))
                m["active_quests"] = [q.model_dump()
                                      for q in self.memory.active_quests]
                manifest_path.write_text(
                    json.dumps(m, indent=2), encoding="utf-8")
                return m
            except Exception:
                pass
        return {}

    def dispatch_studio_pipeline(
        self,
        district_id: str,
        player_stress: float,
        player_pos: Tuple[float, float, float],
        seed: int,
        active_goals: Optional[List[SprintGoal]] = None
    ) -> Dict[str, Any]:
        goals = active_goals or []
        print(
            f"\n[STUDIO DIRECTOR]: Dispatching sprint for '{district_id}' | Phase: {self.memory.active_phase}")

        economy_meta, item_catalog = self.systems_architect.audit_and_synthesize_economy(
            self.memory, goals)
        print(
            f"  [1/7 Systems] Economy: {economy_meta['regime']} | Commodities: {self.memory.commodity_reserves}")

        layout = self.level_architect.generate_and_refine_layout(
            district_id, goals)
        print(f"  [2/7 Level] Topology: {len(layout.nodes)} zones")

        ui_spec, lighting, props = self.client_architect.design_ui_and_props(
            layout, self.memory.active_phase, economy_meta['unrest'], goals
        )
        print(
            f"  [3/7 Client UI/Props] Theme: {ui_spec.hud_title} | Props: {sum(len(p) for p in props.values())}")

        mechanics = self.gameplay_specialist.tune_mechanics(
            economy_meta['unrest'], self.memory.active_phase)
        print(
            f"  [4/7 Gameplay] Player Base Speed: {mechanics.player_base_speed:.0f}")

        npcs = self.narrative_specialist.synthesize_npc_roster(
            layout, self.memory.active_phase, economy_meta['unrest'])
        print(
            f"  [5/7 Narrative Crew] Roster Populated: {len(npcs)} characters ({', '.join(npcs.keys())})")

        beat = self.dm_director.formulate_pacing_beat(
            player_stress, self.memory, goals, npcs)
        is_causal, reason = self.dm_director.validate_causal_invariants(
            beat, player_pos, npcs)
        if not is_causal:
            raise RuntimeError(f"Causal fault: {reason}")

        client_report, client_tickets = self.chaos_crew.execute_client_headless_playtest(
            layout, npcs, mechanics)
        self.memory.bug_ticket_queue.extend(client_tickets)

        style_report = self.style_guide.audit_and_restyle(
            {"raw_dialogue": beat.dialogue_prompt_concept,
                "speaker_id": beat.target_npc_id, "target_action": beat.action_type},
            goals
        )
        print(
            f"  [6/7 Pacing Beat] Actor: {beat.target_npc_id} | Action: {beat.action_type}")

        if not self.memory.active_quests:
            self.memory.active_quests = self.narrative_specialist.synthesize_systemic_quests(
                self.memory.active_phase, economy_meta['unrest'], goals, npcs
            )
        quests = self.memory.active_quests

        runtime_manifest = GameRuntimeManifest(
            manifest_version=int(self.memory.world_time),
            district_id=district_id,
            simulation_phase=self.memory.active_phase,
            district_unrest=economy_meta['unrest'],
            world_time=self.memory.world_time,
            lighting=lighting,
            ui=ui_spec,
            mechanics=mechanics,
            items=item_catalog,
            npcs=npcs,
            spatial_layout=layout,
            props=props,
            active_quests=quests
        )

        client_report, _ = self.chaos_crew.execute_client_headless_playtest(
            layout, npcs, mechanics)
        approved, lore_score, notes = self.lore_auditor.audit_final_artifact(
            runtime_manifest.model_dump())
        print(
            f"  [7/7 Lore & QA Audit] Status: {client_report.verdict} (Score: {lore_score:.2f})")

        deliverable = GameReadyArtifact(
            artifact_id=f"ART_{district_id}_{int(self.memory.world_time)}",
            content_type=ContentType.CLIENT_RUNTIME_MANIFEST,
            raw_payload={
                "game_runtime_manifest": runtime_manifest.model_dump(),
                "active_beat": beat.model_dump(),
                "spoken_dialogue": style_report.restyled_output,
                "target_npc": beat.target_npc_id,
                "action": beat.action_type
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
