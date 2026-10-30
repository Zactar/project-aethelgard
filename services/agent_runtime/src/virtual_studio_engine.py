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
    ProceduralPropSpec, PropPrimitiveType, LightingProfile,
    ItemSpec, ItemCategory, NPCActorSpec, UIThemeSpec, GameplayMechanicsSpec,
    SystemicQuest, QuestObjective, ObjectiveStatus,
    GameRuntimeManifest, ClientPlaytestReport
)

class StudioSharedMemoryBus:
    def __init__(self):
        self.world_time: float = 1200.0
        self.active_district_unrest: float = 0.58
        self.commodity_reserves: Dict[str, float] = {"Grain": 120.0, "Flour": 85.0, "Bread": 60.0}
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
    def audit_and_synthesize_economy(self, memory: StudioSharedMemoryBus, active_goals: List[SprintGoal]) -> Tuple[Dict[str, Any], Dict[str, ItemSpec]]:
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

        flour_price = 12.0 if trade_regime == "CONTRABAND_BLACK_MARKET" else 4.0
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
                icon_symbol="🧪", effects={"speed_boost": 0.25}
            ),
            "item_contraband_grain": ItemSpec(
                item_id="item_contraband_grain", display_name="Illicit Grain Bushel", category=ItemCategory.CONTRABAND,
                base_value=32.0, description="Untithed grain ground in subterranean drainage vaults. Highly illegal.",
                icon_symbol="🪙"
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
    def design_ui_and_props(
        self, district_layout: DistrictSpatialLayout, phase: str, unrest: float, goals: List[SprintGoal]
    ) -> Tuple[UIThemeSpec, LightingProfile, Dict[str, List[ProceduralPropSpec]]]:
        if phase == "MUNICIPAL_BREAD_RIOT" or unrest >= 0.80:
            lighting = LightingProfile(
                ambient_sky_hex="#ff4500",
                ambient_ground_hex="#220a05",
                sun_color_hex="#ff7733",
                sun_intensity=0.95,
                fog_color_hex="#1a0805",
                fog_density=0.00030
            )
            theme = UIThemeSpec(
                primary_color_hex="#ff5252",
                accent_color_hex="#ffa726",
                hud_title="AETHELGARD: STATE OF SIEGE",
                action_buttons=[
                    {"id": "btn_ration", "label": "Inspect Bread Ration", "action": "INSPECT_RATION"},
                    {"id": "btn_curfew", "label": "Check Guard Patrols", "action": "CHECK_PATROLS"}
                ]
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
            theme = UIThemeSpec(
                primary_color_hex="#4facfe",
                accent_color_hex="#00f2fe",
                hud_title="AETHELGARD GROUND CONTROL",
                action_buttons=[
                    {"id": "btn_combat", "label": "Trigger Combat Spike (0.85)", "action": "STRESS_SPIKE"},
                    {"id": "btn_rest", "label": "Peacetime Repose (0.20)", "action": "PEACE_REST"}
                ]
            )

        props_by_node: Dict[str, List[ProceduralPropSpec]] = {}
        for node_id, node in district_layout.nodes.items():
            node_props: List[ProceduralPropSpec] = []
            c = node.center_location
            if "PLAZA" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_OBELISK_01", primitive_type=PropPrimitiveType.OBELISK,
                    relative_position=Vector3D(x=c.x, y=c.y, z=c.z + 170)
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
            elif "BAKERY" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_BAKERY_OVEN", primitive_type=PropPrimitiveType.BAKERY_OVEN,
                    relative_position=Vector3D(x=c.x, y=c.y + 200, z=c.z),
                    material_color_hex="#48515f", emissive_color_hex="#ff5500", emissive_intensity=1.5
                ))
            elif "APOTHECARY" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_APOTHECARY_SHELF", primitive_type=PropPrimitiveType.APOTHECARY_SHELF,
                    relative_position=Vector3D(x=c.x, y=c.y - 200, z=c.z)
                ))
            elif "AQUEDUCT" in node_id:
                node_props.append(ProceduralPropSpec(
                    prop_id="PROP_SLUICE_GATE", primitive_type=PropPrimitiveType.SLUICE_MECHANISM,
                    relative_position=Vector3D(x=c.x + 40, y=c.y, z=c.z),
                    material_color_hex="#22262d", emissive_color_hex="#00f2fe", emissive_intensity=0.8
                ))
            props_by_node[node_id] = node_props

        return theme, lighting, props_by_node


class GameplayMechanicsSpecialistAgent:
    def tune_mechanics(self, unrest: float, phase: str) -> GameplayMechanicsSpec:
        speed = 1550.0 if phase == "MUNICIPAL_BREAD_RIOT" else 1400.0
        return GameplayMechanicsSpec(
            player_base_speed=speed,
            sprint_multiplier=1.6,
            stamina_max=100.0,
            stamina_recovery_rate=14.0,
            interaction_radius=480.0,
            camera_fov=45.0,
            camera_default_distance=3000.0
        )


class NarrativeNPCSpecialistAgent:
    def synthesize_systemic_quests(self, phase: str, unrest: float, goals: List[SprintGoal]) -> List[SystemicQuest]:
        if phase == "MUNICIPAL_BREAD_RIOT" or unrest >= 0.80:
            return [
                SystemicQuest(
                    quest_id="QUEST_RIOT_RELIEF",
                    title="Clandestine Granary Relief",
                    synopsis="Bypass the City Watch curfew to unlock Aldous's emergency cellar stores.",
                    issuing_npc_id="NPC_ALDOUS",
                    reward_item_id="item_bread",
                    reward_stamina=40.0,
                    objectives=[
                        QuestObjective(
                            objective_id="OBJ_01_TALK_ALDOUS",
                            description="Confer with Aldous outside The Common Loaf.",
                            target_node_id="NODE_BAKERY",
                            target_npc_id="NPC_ALDOUS",
                            status=ObjectiveStatus.COMPLETED
                        ),
                        QuestObjective(
                            objective_id="OBJ_02_DRAIN_SLUICE",
                            description="Operate Sluice Gate 01 in the aqueduct catacombs to lower drainage water.",
                            target_node_id="NODE_AQUEDUCT_CATACOMBS",
                            target_smart_object="SO_SLUICE_GATE_01",
                            status=ObjectiveStatus.ACTIVE
                        ),
                        QuestObjective(
                            objective_id="OBJ_03_RETRIEVE_FLOUR",
                            description="Trade contraband herbs with Garrett for grain reserves.",
                            target_node_id="NODE_APOTHECARY",
                            target_npc_id="NPC_GARRETT",
                            target_smart_object="SO_GARRETT",
                            status=ObjectiveStatus.LOCKED
                        )
                    ]
                )
            ]
        else:
            return [
                SystemicQuest(
                    quest_id="QUEST_GUILD_COMMERCE",
                    title="The Tithe Evasion Network",
                    synopsis="Establish a discrete conduit between the apothecaries and subterranean water vaults.",
                    issuing_npc_id="NPC_GARRETT",
                    reward_item_id="item_sunfire_salve",
                    reward_stamina=25.0,
                    objectives=[
                        QuestObjective(
                            objective_id="OBJ_COMMERCE_01",
                            description="Inspect the Market Cross Rally Notice.",
                            target_node_id="NODE_PLAZA",
                            target_smart_object="SO_RALLY",
                            status=ObjectiveStatus.ACTIVE
                        ),
                        QuestObjective(
                            objective_id="OBJ_COMMERCE_02",
                            description="Report Arch-Prelate Malakor's tithe rate back to Garrett.",
                            target_node_id="NODE_APOTHECARY",
                            target_npc_id="NPC_GARRETT",
                            target_smart_object="SO_GARRETT",
                            status=ObjectiveStatus.LOCKED
                        )
                    ]
                )
            ]

    def synthesize_npc_roster(self, phase: str, unrest: float) -> Dict[str, NPCActorSpec]:
        return {
            "NPC_ALDOUS": NPCActorSpec(
                npc_id="NPC_ALDOUS",
                name="Aldous the Baker",
                role="Guild Baker",
                faction="Baker's Guild",
                color_hex="#f5af19",
                position=Vector3D(x=0.0, y=2300.0, z=0.0),
                default_dialogue="Communal ovens are fired down. Tithes took half the grain this morning.",
                inventory={"item_bread": 12, "item_flour": 5},
                assigned_smart_object="SO_ALDOUS"
            ),
            "NPC_GARRETT": NPCActorSpec(
                npc_id="NPC_GARRETT",
                name="Garrett the Herbalist",
                role="Apothecary Merchant",
                faction="Artisans Fellowship",
                color_hex="#2ecc71",
                position=Vector3D(x=2300.0, y=0.0, z=0.0),
                default_dialogue="Keep your voice low. Nightshade and dried hemlock on the top shelf.",
                inventory={"item_sunfire_salve": 4, "item_contraband_grain": 2},
                assigned_smart_object="SO_GARRETT"
            )
        }


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
        self, beat: ProposedGameBeat, player_pos: Tuple[float, float, float], npcs: Dict[str, NPCActorSpec]
    ) -> Tuple[bool, str]:
        npc = npcs.get(beat.target_npc_id)
        if npc:
            p = (npc.position.x, npc.position.y, npc.position.z)
            if math.dist(p, player_pos) > 4000.0:
                return False, f"SPATIAL FAULT: {npc.name} is {math.dist(p, player_pos):.1f} units away. Cannot teleport."
        return True, "PASSED: Causal continuity verified."


class StyleGuideAgent:
    def audit_and_restyle(self, dialogue_payload: Dict[str, Any], active_goals: List[SprintGoal]) -> StyleEvaluationReport:
        text = dialogue_payload["raw_dialogue"]
        speaker = dialogue_payload["speaker_id"]
        action = dialogue_payload.get("target_action", "")

        if action == "ENFORCE_MILITARY_RATION":
            restyled = "The church seal is on the ovens. Hearthmother’s peace is done—watch captain seized every sack of barley at dawn. Take your hardtack and clear the square."
        elif "GARRETT" in speaker and "CONTRABAND" in action:
            restyled = "Lower your head and step past the rack. The millers in the Undercroft ground this under tallow torches. If the watch finds this bushel, we're both hanging."
        elif "ALDOUS" in speaker:
            restyled = "Flour's up another four coppers and church guards are pounding on shutters. Grab two charred loaves off the hearthstones and get into the drainage vault."
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
    def audit_final_artifact(self, payload: Dict[str, Any]) -> Tuple[bool, float, str]:
        text = json.dumps(payload).lower()
        if "changed species" in text or "altered horn structure" in text:
            return False, 0.0, "REJECTED: Somatic violation."
        return True, 0.98, "PASSED: Full conformance with canon dogmas."


class ChaosCrewCommander:
    def execute_client_headless_playtest(
        self, layout: DistrictSpatialLayout, npcs: Dict[str, NPCActorSpec], mechanics: GameplayMechanicsSpec
    ) -> Tuple[ClientPlaytestReport, List[BugTicket]]:
        tickets: List[BugTicket] = []
        traversed = len(layout.nodes)

        for npc in npcs.values():
            inside = False
            for node in layout.nodes.values():
                bmin, bmax = node.bounds_min, node.bounds_max
                if bmin.x <= npc.position.x <= bmax.x and bmin.y <= npc.position.y <= bmax.y:
                    inside = True
                    break
            if not inside:
                tickets.append(BugTicket(
                    ticket_id=f"BUG-NPC-OOB-{npc.npc_id}",
                    severity=BugSeverity.P1_HIGH,
                    title=f"NPC Out of Bounds: {npc.name}",
                    description=f"{npc.name} spawned outside walkable floorplate bounds.",
                    reproduction_seed=42109,
                    responsible_agent="Narrative_Specialist",
                    suggested_action="Clamp NPC coordinates inside assigned zone."
                ))

        report = ClientPlaytestReport(
            nodes_traversed=traversed,
            unreachable_nodes=[],
            interaction_failures=[],
            average_socket_latency_ms=16.2,
            out_of_bounds_detected=len(tickets) > 0,
            verdict="PASS" if len(tickets) == 0 else "FAIL_BUGS_FILED"
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

    def dispatch_studio_pipeline(
        self,
        district_id: str,
        player_stress: float,
        player_pos: Tuple[float, float, float],
        seed: int,
        active_goals: Optional[List[SprintGoal]] = None
    ) -> Dict[str, Any]:
        goals = active_goals or []
        print(f"\n[STUDIO DIRECTOR]: Commencing full studio sprint for '{district_id}' | Phase: {self.memory.active_phase}")

        # 1. Systems & Economy
        economy_meta, item_catalog = self.systems_architect.audit_and_synthesize_economy(self.memory, goals)
        print(f"  [1/7 Systems] Economy: {economy_meta['regime']} | Items: {len(item_catalog)} defined")

        # 2. Level Spatial Topology
        layout = self.level_architect.generate_and_refine_layout(district_id, goals)
        print(f"  [2/7 Level] Topology: {len(layout.nodes)} zones")

        # 3. Client UI & Visual Props
        ui_spec, lighting, props = self.client_architect.design_ui_and_props(
            layout, self.memory.active_phase, economy_meta['unrest'], goals
        )
        print(f"  [3/7 Client UI/Props] UI Theme: {ui_spec.hud_title} | Props: {sum(len(p) for p in props.values())}")

        # 4. Gameplay Mechanics Tuning
        mechanics = self.gameplay_specialist.tune_mechanics(economy_meta['unrest'], self.memory.active_phase)
        print(f"  [4/7 Gameplay Specialist] Move speed: {mechanics.player_base_speed:.0f} | Radius: {mechanics.interaction_radius:.0f}")

        # 5. Narrative Actors & Pacing Beat
        npcs = self.narrative_specialist.synthesize_npc_roster(self.memory.active_phase, economy_meta['unrest'])
        beat = self.dm_director.formulate_pacing_beat(player_stress, self.memory, goals)
        is_causal, reason = self.dm_director.validate_causal_invariants(beat, player_pos, npcs)
        if not is_causal:
            raise RuntimeError(f"Causal fault: {reason}")

        style_report = self.style_guide.audit_and_restyle(
            {"raw_dialogue": beat.dialogue_prompt_concept, "speaker_id": beat.target_npc_id, "target_action": beat.action_type},
            goals
        )
        print(f"  [5/7 Narrative & Lyric] Beat: '{beat.beat_id}' | Soul: {style_report.human_touch_score:.2f}")

        # 5b. Synthesize Systemic Quest DAGs
        quests = self.narrative_specialist.synthesize_systemic_quests(self.memory.active_phase, economy_meta['unrest'], goals)

        # 6. Assemble Unified Runtime Manifest
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

        # 7. Chaos Crew Headless Client & Logic Playtest
        client_report, client_tickets = self.chaos_crew.execute_client_headless_playtest(layout, npcs, mechanics)
        self.memory.bug_ticket_queue.extend(client_tickets)
        print(f"  [6/7 Chaos Crew] Headless Playtest: {client_report.verdict} ({len(client_tickets)} bugs)")

        approved, lore_score, notes = self.lore_auditor.audit_final_artifact(runtime_manifest.model_dump())
        print(f"  [7/7 Lore Auditor] Canon conformity: {lore_score:.2f} (Approved: {approved})")

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
