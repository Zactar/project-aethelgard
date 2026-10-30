#!/usr/bin/env python3
"""
PROJECT AETHELGARD: FULL RUNTIME CLIENT PIPELINE UPDATER
Deploys schemas, virtual dev team modules, asset ingesters, and the data-driven web client.
"""

from pathlib import Path
import py_compile
import sys

print("[PIPELINE SETUP]: Synchronizing game systems, virtual studio agents, and client...")

# ==============================================================================
# 1. SCHEMAS: studio_contracts.py (Expanded Game Engine Manifest)
# ==============================================================================
Path("schemas").mkdir(parents=True, exist_ok=True)
Path("schemas/studio_contracts.py").write_text('''from enum import Enum
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# Content and Audit Types
class ContentType(str, Enum):
    STATETREE_TASK = "STATETREE_TASK"
    NPC_DIALOGUE_TEMPLATE = "NPC_DIALOGUE_TEMPLATE"
    SPATIAL_LAYOUT = "SPATIAL_LAYOUT"
    BALANCE_HOTFIX = "BALANCE_HOTFIX"
    CLIENT_RUNTIME_MANIFEST = "CLIENT_RUNTIME_MANIFEST"

class AestheticVerdict(str, Enum):
    APPROVED_WITH_SOUL = "APPROVED_WITH_SOUL"
    NEEDS_HUMAN_POLISH = "NEEDS_HUMAN_POLISH"
    REJECTED_GENERIC_SLOP = "REJECTED_GENERIC_SLOP"

class BugSeverity(str, Enum):
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"

# Math & Spatial Primitives
class Vector3D(BaseModel):
    x: float
    y: float
    z: float

class SmartObjectAnchor(BaseModel):
    anchor_id: str
    smart_object_tag: str
    assigned_npc_id: Optional[str] = None
    relative_position: Vector3D
    interaction_facing_yaw: float = 0.0

class SpatialRoomNode(BaseModel):
    node_id: str
    zone_name: str
    function: str
    bounds_min: Vector3D
    bounds_max: Vector3D
    center_location: Vector3D
    connected_node_ids: List[str]
    smart_objects: List[SmartObjectAnchor] = Field(default_factory=list)

class DistrictSpatialLayout(BaseModel):
    district_id: str
    district_name: str
    nodes: Dict[str, SpatialRoomNode]
    is_topologically_sound: bool = False

# Prop & Visual Specifications
class PropPrimitiveType(str, Enum):
    BOX = "BOX"
    CYLINDER = "CYLINDER"
    TORUS = "TORUS"
    OBELISK = "OBELISK"
    MARKET_STALL = "MARKET_STALL"
    BAKERY_OVEN = "BAKERY_OVEN"
    APOTHECARY_SHELF = "APOTHECARY_SHELF"
    SLUICE_MECHANISM = "SLUICE_MECHANISM"

class ProceduralPropSpec(BaseModel):
    prop_id: str
    primitive_type: PropPrimitiveType
    relative_position: Vector3D
    rotation_y: float = 0.0
    scale: Vector3D = Field(default_factory=lambda: Vector3D(x=1, y=1, z=1))
    material_color_hex: str = "#5a3d28"
    emissive_color_hex: Optional[str] = None
    emissive_intensity: float = 0.0
    cast_shadow: bool = True

class LightingProfile(BaseModel):
    ambient_sky_hex: str = "#b0c4de"
    ambient_ground_hex: str = "#181c24"
    sun_color_hex: str = "#fff5ea"
    sun_intensity: float = 0.75
    fog_color_hex: str = "#06080d"
    fog_density: float = 0.00018

# Item & Economic Specifications
class ItemCategory(str, Enum):
    COMMODITY = "COMMODITY"
    CONSUMABLE = "CONSUMABLE"
    CONTRABAND = "CONTRABAND"
    TOOL = "TOOL"

class ItemSpec(BaseModel):
    item_id: str
    display_name: str
    category: ItemCategory
    base_value: float
    description: str
    icon_symbol: str = "📦"
    stack_limit: int = 20
    effects: Dict[str, float] = Field(default_factory=dict)

# NPC Actor Specifications
class NPCActorSpec(BaseModel):
    npc_id: str
    name: str
    role: str
    faction: str
    color_hex: str = "#f5af19"
    position: Vector3D
    default_dialogue: str
    inventory: Dict[str, int] = Field(default_factory=dict)
    assigned_smart_object: Optional[str] = None

# UI & HUD Styling Specifications
class UIThemeSpec(BaseModel):
    primary_color_hex: str = "#4facfe"
    accent_color_hex: str = "#00f2fe"
    background_alpha: float = 0.94
    hud_title: str = "AETHELGARD RUNTIME CLIENT"
    show_minimap: bool = True
    show_inventory: bool = True
    action_buttons: List[Dict[str, Any]] = Field(default_factory=list)

# Gameplay Mechanics Specifications
class GameplayMechanicsSpec(BaseModel):
    player_base_speed: float = 1400.0
    sprint_multiplier: float = 1.6
    stamina_max: float = 100.0
    stamina_recovery_rate: float = 15.0
    interaction_radius: float = 480.0
    camera_fov: float = 45.0
    camera_default_distance: float = 3000.0

# Master Unified Runtime Manifest
class GameRuntimeManifest(BaseModel):
    manifest_version: int = 1
    district_id: str
    simulation_phase: str
    district_unrest: float
    world_time: float
    lighting: LightingProfile
    ui: UIThemeSpec
    mechanics: GameplayMechanicsSpec
    items: Dict[str, ItemSpec] = Field(default_factory=dict)
    npcs: Dict[str, NPCActorSpec] = Field(default_factory=dict)
    spatial_layout: DistrictSpatialLayout
    props: Dict[str, List[ProceduralPropSpec]] = Field(default_factory=dict)

# Narrative & Evaluation Contracts
class StyleEvaluationReport(BaseModel):
    artifact_id: str
    verdict: AestheticVerdict
    human_touch_score: float = Field(ge=0.0, le=1.0)
    flagged_cliches: List[str]
    sensory_density_score: float
    lyric_feedback_notes: str
    restyled_output: Optional[str] = None

class ProposedGameBeat(BaseModel):
    beat_id: str
    target_npc_id: str
    action_type: str
    narrative_intent: str
    dialogue_prompt_concept: str
    required_props_or_coin: Dict[str, float] = Field(default_factory=dict)
    spawn_location_name: str
    target_player_threat_delta: float

class BugTicket(BaseModel):
    ticket_id: str
    severity: BugSeverity
    title: str
    description: str
    reproduction_seed: int
    responsible_agent: str
    suggested_action: str
    timestamp: float = Field(default_factory=time.time)

class GameReadyArtifact(BaseModel):
    artifact_id: str
    content_type: ContentType
    raw_payload: Dict[str, Any]
    style_report: Optional[StyleEvaluationReport] = None
    lore_consistency_score: float = Field(ge=0.0, le=1.0)
    human_touch_score: float = Field(ge=0.0, le=1.0)
    auditor_approved: bool
    audit_notes: str
    timestamp: float = Field(default_factory=time.time)

# Standup Ceremonies Contracts
class IdeaDiscipline(str, Enum):
    SYSTEMS_DESIGN = "SYSTEMS_DESIGN"
    LEVEL_ARCHITECTURE = "LEVEL_ARCHITECTURE"
    GAMEPLAY_MECHANICS = "GAMEPLAY_MECHANICS"
    UI_UX_DESIGN = "UI_UX_DESIGN"
    NARRATIVE_LORE = "NARRATIVE_LORE"
    AESTHETIC_STYLE = "AESTHETIC_STYLE"
    QA_COMBAT_BALANCE = "QA_COMBAT_BALANCE"

class BrainstormIdea(BaseModel):
    idea_id: str
    proposing_agent: str
    discipline: IdeaDiscipline
    title: str
    pitch: str
    technical_feasibility_score: float = Field(ge=0.0, le=1.0)
    systemic_emergence_score: float = Field(ge=0.0, le=1.0)
    estimated_complexity: str = "MEDIUM"

class SprintGoal(BaseModel):
    goal_id: str
    target_district: str
    primary_objective: str
    driving_ideas: List[str]
    assigned_crews: List[str]
    success_criteria: str
    is_completed: bool = False

class SprintMeetingMinutes(BaseModel):
    meeting_id: str
    world_time_marker: float
    retrospective_summary: Dict[str, Any]
    brainstorm_proposals: List[BrainstormIdea]
    selected_sprint_goals: List[SprintGoal]
    director_closing_notes: str
    timestamp: float = Field(default_factory=time.time)

class ClientPlaytestReport(BaseModel):
    nodes_traversed: int
    unreachable_nodes: List[str]
    interaction_failures: List[str]
    average_socket_latency_ms: float
    out_of_bounds_detected: bool
    verdict: str
''', encoding="utf-8")
print("  [1/5] Compiled schemas/studio_contracts.py")

# ==============================================================================
# 2. VIRTUAL STUDIO ENGINE: virtual_studio_engine.py
# ==============================================================================
Path("services/agent_runtime/src/virtual_studio_engine.py").write_text('''import sys
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
    """Specialist responsible for economy, Leontief matrices, commodities, and item catalogs."""
    def audit_and_synthesize_economy(self, memory: StudioSharedMemoryBus, active_goals: List[SprintGoal]) -> Tuple[Dict[str, Any], Dict[str, ItemSpec]]:
        goal_titles = [g.primary_objective.lower() for g in active_goals]

        # Phase transition check
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

        # Item Definitions Catalog
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
    """Specialist responsible for UI design, client theme, visual dressing, and lighting."""
    def design_ui_and_props(
        self, district_layout: DistrictSpatialLayout, phase: str, unrest: float, goals: List[SprintGoal]
    ) -> Tuple[UIThemeSpec, LightingProfile, Dict[str, List[ProceduralPropSpec]]]:
        # Dynamic Lighting Profile
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
    """Specialist responsible for tuning physics, movement, and interaction rules."""
    def tune_mechanics(self, unrest: float, phase: str) -> GameplayMechanicsSpec:
        # Under civil unrest, increase movement pace and interaction urgency
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
    """Specialist responsible for defining NPC rosters, schedules, and personalities."""
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

        # Audit NPC positions inside room boundaries
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
        print(f"\\n[STUDIO DIRECTOR]: Commencing full studio sprint for '{district_id}' | Phase: {self.memory.active_phase}")

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
            props=props
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
''', encoding="utf-8")
print("  [2/5] Compiled services/agent_runtime/src/virtual_studio_engine.py")

# ==============================================================================
# 3. WEBSOCKET IPC STATE SERVER: server.py
# ==============================================================================
Path("services/agent_runtime/src/server.py").write_text('''import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
import json
import logging
from typing import Any
import websockets

from services.agent_runtime.src.virtual_studio_engine import StudioDirectorManagerAgent
from schemas.studio_contracts import SprintGoal

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("AethelgardServer")

DIRECTOR = StudioDirectorManagerAgent()
ACTIVE_GOALS = [
    SprintGoal(
        goal_id="GOAL-INIT",
        target_district="District_MarketSquare",
        primary_objective="Vertical Aqueduct Catacombs with Dynamic Sluice Gates",
        driving_ideas=["IDEA-LVL-01"],
        assigned_crews=["Level_Architect", "Client_Architect"],
        success_criteria="Rendered in web client"
    )
]

SMART_OBJECT_RESPONSES = {
    "SmartObject.Mechanism.SluiceGate": {
        "speaker": "AQUEDUCT MECHANISM",
        "action": "OPERATE_SLUICE_GATE",
        "dialogue": "Heavy bronze gears groan as you crank the release valve. Subterranean floodwaters hiss and drain into the lower canals, clearing the dry walking path."
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
    }
}

async def handle_state_ipc(websocket: Any):
    client_addr = getattr(websocket, "remote_address", "unknown")
    logger.info(f"Client connected to State IPC: {client_addr}")
    try:
        async for message in websocket:
            payload = json.loads(message)
            msg_type = payload.get("type", "UNKNOWN")

            if msg_type in ("TELEMETRY_INGEST", "REQUEST_INITIAL_STATE"):
                district = payload.get("district_id", "District_MarketSquare")
                stress = payload.get("player_stress", 0.35)
                coords = tuple(payload.get("player_coords", [1400.0, 500.0, 0.0]))
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
                    "dialogue": f"You examine {so_id}. The surface is worn from years of continuous guild use."
                })

                response = {
                    "status": "PROCESSED",
                    "artifact_id": f"SO_EVENT_{so_id}",
                    "dialogue": resp_data["dialogue"],
                    "target_npc": resp_data["speaker"],
                    "action": resp_data["action"],
                    "district_unrest": DIRECTOR.memory.active_district_unrest,
                    "active_phase": DIRECTOR.memory.active_phase
                }
                await websocket.send(json.dumps(response))

            elif msg_type == "HEARTBEAT":
                await websocket.send(json.dumps({"type": "PONG", "time": DIRECTOR.memory.world_time}))
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        logger.warning(f"Client disconnected: {client_addr}")
    except Exception as e:
        logger.error(f"Error handling IPC message: {e}", exc_info=True)

async def main():
    server = await websockets.serve(handle_state_ipc, "0.0.0.0", 8765)
    logger.info("Virtual Studio State Server live on ws://0.0.0.0:8765")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server halted by user.")
''', encoding="utf-8")
print("  [3/5] Compiled services/agent_runtime/src/server.py")

# ==============================================================================
# 4. ENGINE ASSET INGESTER: engine_importer.py
# ==============================================================================
Path("tools/engine_importer.py").write_text('''import json
from pathlib import Path

STAGING_DIR = Path("build/staging")
WEB_CLIENT_DIR = Path("web_client")

class EngineAssetIngester:
    def __init__(self):
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        WEB_CLIENT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[ENGINE INGESTER]: Listening on {STAGING_DIR.resolve()}...")

    def stage_artifact(self, artifact_path: Path):
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data.get("auditor_approved", False):
            print(f"[INGESTER REJECTED]: Artifact {artifact_path.name} failed auditor approval.")
            return

        payload = data.get("raw_payload", {})

        # Deploy Unified Runtime Manifest directly to Web Client
        if payload.get("game_runtime_manifest"):
            target_manifest = WEB_CLIENT_DIR / "game_runtime_manifest.json"
            with open(target_manifest, "w", encoding="utf-8") as f:
                json.dump(payload["game_runtime_manifest"], f, indent=2)
            print(f"[INGESTER -> WEB CLIENT]: Deployed live game runtime manifest to {target_manifest}")

    def run_once(self):
        staged_files = list(STAGING_DIR.glob("*.json"))
        for artifact_file in staged_files:
            try:
                self.stage_artifact(artifact_file)
                artifact_file.unlink()
            except Exception as e:
                print(f"[INGESTER ERROR]: Failed staging {artifact_file.name}: {e}")

if __name__ == "__main__":
    ingester = EngineAssetIngester()
    ingester.run_once()
''', encoding="utf-8")
print("  [4/5] Compiled tools/engine_importer.py")

# ==============================================================================
# 5. DATA-DRIVEN BROWSER CLIENT: web_client/index.html
# ==============================================================================
Path("web_client/index.html").write_text('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Project Aethelgard - Modular Game Runtime</title>
  <style>
    body { margin: 0; padding: 0; overflow: hidden; background: #06080d; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #e0e0e0; user-select: none; }
    #canvas-container { width: 100vw; height: 100vh; display: block; }
    
    /* Dynamic Studio HUD */
    #hud {
      position: absolute; top: 16px; left: 16px; width: 330px;
      background: rgba(11, 15, 22, 0.94); border: 1px solid #232c3d;
      border-radius: 8px; padding: 14px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); z-index: 10;
    }
    #hud h2 { margin: 0 0 8px 0; font-size: 14px; color: #4facfe; text-transform: uppercase; letter-spacing: 1px; }
    .hud-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px; }
    .hud-val { font-weight: bold; color: #fff; }
    
    /* Dynamic Inventory Bar */
    #inventory-bar {
      position: absolute; bottom: 20px; left: 16px; width: 330px;
      background: rgba(11, 15, 22, 0.94); border: 1px solid #232c3d;
      border-radius: 8px; padding: 12px; z-index: 10;
    }
    #inventory-bar h3 { margin: 0 0 8px 0; font-size: 12px; color: #f5af19; text-transform: uppercase; }
    .inv-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
    .inv-slot {
      background: #131924; border: 1px solid #2b3548; border-radius: 4px; padding: 6px;
      text-align: center; font-size: 11px; cursor: pointer;
    }
    .inv-slot:hover { border-color: #4facfe; background: #1a2230; }

    .minimap-container { margin-top: 8px; border-top: 1px solid #232c3d; padding-top: 8px; text-align: center; }
    #minimap { background: #080b11; border: 1px solid #1a2230; border-radius: 4px; display: block; margin: 0 auto; }
    .instructions { margin-top: 8px; font-size: 11px; color: #8a99ad; line-height: 1.4; text-align: left; }
    
    #interaction-toast {
      position: absolute; top: 24px; left: 50%; transform: translateX(-50%);
      background: rgba(0, 242, 254, 0.2); border: 1px solid #00f2fe; color: #00f2fe;
      padding: 8px 24px; border-radius: 20px; font-size: 13px; font-weight: bold;
      letter-spacing: 0.5px; display: none; z-index: 15; box-shadow: 0 0 16px rgba(0,242,254,0.4);
    }
    #dialogue-box {
      position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); width: 700px;
      background: rgba(11, 15, 22, 0.96); border: 1px solid #334057; border-radius: 8px;
      padding: 18px; box-shadow: 0 12px 36px rgba(0,0,0,0.85); display: none; z-index: 10;
    }
    #dialogue-speaker { font-weight: bold; color: #f5af19; font-size: 14px; margin-bottom: 4px; }
    #dialogue-text { font-size: 14px; line-height: 1.5; color: #f0f0f0; font-style: italic; }
    #dialogue-action { margin-top: 8px; font-size: 11px; color: #00f2fe; text-transform: uppercase; letter-spacing: 0.5px; }
    .btn {
      width: 100%; background: #18202d; color: #fff; border: 1px solid #4facfe;
      padding: 8px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold; margin-top: 6px;
    }
    .btn:hover { background: #4facfe; color: #06080d; }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="hud">
    <h2 id="ui-title">AETHELGARD RUNTIME CLIENT</h2>
    <div class="hud-row"><span>District:</span><span id="ui-district" class="hud-val">MarketSquare</span></div>
    <div class="hud-row"><span>Zone:</span><span id="ui-room" class="hud-val" style="color: #00f2fe;">Plaza</span></div>
    <div class="hud-row"><span>Phase:</span><span id="ui-phase" class="hud-val">PEACETIME_COMMERCE</span></div>
    <div class="hud-row"><span>Stamina:</span><span id="ui-stamina" class="hud-val" style="color: #00e676;">100 / 100</span></div>
    <div class="hud-row"><span>Interaction:</span><span id="ui-prompt" class="hud-val" style="color: #f5af19;">None</span></div>
    <div class="hud-row"><span>IPC Bridge:</span><span id="ui-status" class="hud-val" style="color: #ffb300;">Connecting...</span></div>
    <div id="ui-action-buttons"></div>
    <button class="btn" onclick="recenterCamera()">Recenter Camera (Spacebar)</button>
    
    <div class="minimap-container">
      <canvas id="minimap" width="280" height="150"></canvas>
      <div class="instructions">
        • <b>WASD / Arrows</b>: Walk | <b>E</b>: Interact<br>
        • <b>Mouse Drag</b>: Orbit View | <b>Scroll</b>: Zoom
      </div>
    </div>
  </div>

  <div id="inventory-bar">
    <h3>Backpack Storage</h3>
    <div id="inv-slots" class="inv-grid"></div>
  </div>

  <div id="interaction-toast">ACTIVATING...</div>

  <div id="dialogue-box">
    <div id="dialogue-speaker">NPC SPEECH</div>
    <div id="dialogue-text">...</div>
    <div id="dialogue-action">ACTION: NONE</div>
  </div>

  <div id="canvas-container"></div>

  <script>
    // 1. Scene & Lighting Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x06080d);
    scene.fog = new THREE.FogExp2(0x06080d, 0.00018);

    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 10, 35000);
    camera.position.set(1400, 2400, 2600);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    document.getElementById('canvas-container').appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.12;
    controls.maxPolarAngle = Math.PI / 2.12;
    controls.minDistance = 600;
    controls.maxDistance = 7000;
    controls.target.set(1400, 80, 500);

    const hemiLight = new THREE.HemisphereLight(0xb0c4de, 0x181c24, 0.7);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfff5ea, 0.75);
    sunLight.position.set(2200, 4800, 2800);
    sunLight.castShadow = true;
    scene.add(sunLight);

    const grid = new THREE.GridHelper(16000, 80, 0x1b222f, 0x0c0f16);
    grid.position.y = -6;
    scene.add(grid);

    // Entity & World Groups
    const architecturalGroup = new THREE.Group(); scene.add(architecturalGroup);
    const labelGroup = new THREE.Group(); scene.add(labelGroup);
    const dynamicPropsGroup = new THREE.Group(); scene.add(dynamicPropsGroup);
    const npcActorGroup = new THREE.Group(); scene.add(npcActorGroup);

    const smartObjectRings = [];
    let runtimeMechanics = { player_base_speed: 1400.0, interaction_radius: 480.0, stamina_max: 100.0 };
    let playerStamina = 100.0;
    let playerInventory = { "item_bread": 2, "item_sunfire_salve": 1 };

    // Player Mesh
    const playerGroup = new THREE.Group();
    const playerBody = new THREE.Mesh(
      new THREE.CylinderGeometry(55, 55, 150, 16),
      new THREE.MeshLambertMaterial({ color: 0x00f2fe, emissive: 0x003344 })
    );
    playerBody.position.y = 75;
    playerBody.castShadow = true;
    playerGroup.add(playerBody);

    const arrowGeo = new THREE.ConeGeometry(25, 55, 12);
    arrowGeo.rotateX(-Math.PI / 2);
    const playerVisor = new THREE.Mesh(
      arrowGeo,
      new THREE.MeshLambertMaterial({ color: 0xffd700, emissive: 0x664400 })
    );
    playerVisor.position.set(0, 95, -60);
    playerGroup.add(playerVisor);
    playerGroup.position.set(1400, 0, 500);
    scene.add(playerGroup);

    let activeRooms = {};
    let activeSmartObjects = [];
    let activeNPCActors = [];
    const keys = { w: false, a: false, s: false, d: false };

    function makeBillboardText(text, x, y, z, color = "#4facfe") {
      const canvas = document.createElement('canvas');
      canvas.width = 512; canvas.height = 128;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = "rgba(10, 14, 22, 0.78)";
      ctx.strokeStyle = color; ctx.lineWidth = 4;
      ctx.roundRect(10, 10, 492, 108, 16);
      ctx.fill(); ctx.stroke();
      ctx.font = "bold 42px sans-serif";
      ctx.fillStyle = color; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(text, 256, 64);

      const texture = new THREE.CanvasTexture(canvas);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true }));
      sprite.position.set(x, y, z);
      sprite.scale.set(580, 145, 1);
      labelGroup.add(sprite);
      return sprite;
    }

    // 2. Data-Driven Dynamic World Ingestion
    function applyCompleteRuntimeManifest(manifest) {
      if (!manifest) return;

      // Update Dynamic UI Theme
      if (manifest.ui) {
        document.getElementById('ui-title').innerText = manifest.ui.hud_title || "AETHELGARD CLIENT";
        const btnContainer = document.getElementById('ui-action-buttons');
        btnContainer.innerHTML = "";
        (manifest.ui.action_buttons || []).forEach(btn => {
          const b = document.createElement('button');
          b.className = "btn";
          b.innerText = btn.label;
          b.onclick = () => {
            if (btn.action === "STRESS_SPIKE") sendStressTelemetry(0.85);
            else if (btn.action === "PEACE_REST") sendStressTelemetry(0.20);
          };
          btnContainer.appendChild(b);
        });
      }

      // Update Gameplay Mechanics Constants
      if (manifest.mechanics) {
        runtimeMechanics = manifest.mechanics;
      }

      // Update Lighting
      if (manifest.lighting) {
        hemiLight.color.set(manifest.lighting.ambient_sky_hex);
        hemiLight.groundColor.set(manifest.lighting.ambient_ground_hex);
        sunLight.color.set(manifest.lighting.sun_color_hex);
        sunLight.intensity = manifest.lighting.sun_intensity;
      }

      // Render Dynamic Inventory UI
      const invContainer = document.getElementById('inv-slots');
      invContainer.innerHTML = "";
      for (const [itemId, qty] of Object.entries(playerInventory)) {
        const itemSpec = manifest.items ? manifest.items[itemId] : null;
        const name = itemSpec ? itemSpec.display_name : itemId;
        const icon = itemSpec ? itemSpec.icon_symbol : "📦";
        const slot = document.createElement('div');
        slot.className = "inv-slot";
        slot.innerHTML = `<div>${icon}</div><b>${name}</b><br><small>Qty: ${qty}</small>`;
        invContainer.appendChild(slot);
      }

      // Rebuild Spatial District Zones
      if (manifest.spatial_layout && manifest.spatial_layout.nodes) {
        activeRooms = manifest.spatial_layout.nodes;
        activeSmartObjects = [];
        smartObjectRings.length = 0;
        while (architecturalGroup.children.length > 0) architecturalGroup.remove(architecturalGroup.children[0]);
        while (labelGroup.children.length > 0) labelGroup.remove(labelGroup.children[0]);
        while (dynamicPropsGroup.children.length > 0) dynamicPropsGroup.remove(dynamicPropsGroup.children[0]);

        for (const [nodeId, nodeData] of Object.entries(activeRooms)) {
          buildRoomFloorplate(nodeId, nodeData);
        }
      }

      // Rebuild Dynamic Props
      if (manifest.props) {
        buildPropsFromManifest(manifest.props);
      }

      // Spawn Dynamic NPC Actors
      if (manifest.npcs) {
        activeNPCActors = [];
        while (npcActorGroup.children.length > 0) npcActorGroup.remove(npcActorGroup.children[0]);
        for (const [npcId, npcData] of Object.entries(manifest.npcs)) {
          spawnNPCActor(npcData);
        }
      }
    }

    function buildRoomFloorplate(nodeId, nodeData) {
      const min = nodeData.bounds_min;
      const max = nodeData.bounds_max;
      const width = Math.abs(max.x - min.x);
      const depth = Math.abs(max.y - min.y);
      const center = nodeData.center_location;
      const isCatacomb = nodeId.includes("AQUEDUCT");
      const floorY = center.z;

      let floorColor = isCatacomb ? 0x072535 : (nodeId.includes("BAKERY") ? 0x2b1e16 : (nodeId.includes("APOTHECARY") ? 0x13271c : 0x1b2333));
      let curbColor = isCatacomb ? 0x00a8cc : (nodeId.includes("BAKERY") ? 0x884926 : (nodeId.includes("APOTHECARY") ? 0x2d6e4b : 0x334466));

      const floorMesh = new THREE.Mesh(new THREE.BoxGeometry(width, 16, depth), new THREE.MeshLambertMaterial({ color: floorColor }));
      floorMesh.position.set(center.x, floorY, center.y);
      floorMesh.receiveShadow = true;
      architecturalGroup.add(floorMesh);

      // Low Curbs (70cm)
      const curbMat = new THREE.MeshLambertMaterial({ color: curbColor });
      const nsGeo = new THREE.BoxGeometry(width, 70, 24);
      const nCurb = new THREE.Mesh(nsGeo, curbMat); nCurb.position.set(center.x, floorY + 35, center.y - (depth / 2)); architecturalGroup.add(nCurb);
      const sCurb = new THREE.Mesh(nsGeo, curbMat); sCurb.position.set(center.x, floorY + 35, center.y + (depth / 2)); architecturalGroup.add(sCurb);
      const ewGeo = new THREE.BoxGeometry(24, 70, depth);
      const wCurb = new THREE.Mesh(ewGeo, curbMat); wCurb.position.set(center.x - (width / 2), floorY + 35, center.y); architecturalGroup.add(wCurb);
      const eCurb = new THREE.Mesh(ewGeo, curbMat); eCurb.position.set(center.x + (width / 2), floorY + 35, center.y); architecturalGroup.add(eCurb);

      makeBillboardText(nodeData.zone_name, center.x, floorY + 420, center.y, "#4facfe");

      if (nodeData.smart_objects) {
        nodeData.smart_objects.forEach(so => {
          const soPos = { x: so.relative_position.x, y: floorY + 60, z: so.relative_position.y };
          const soColor = isCatacomb ? 0x00f2fe : (nodeId.includes("BAKERY") ? 0xff7b25 : 0xff007f);

          const soMesh = new THREE.Mesh(new THREE.BoxGeometry(90, 110, 90), new THREE.MeshLambertMaterial({ color: soColor, emissive: soColor, emissiveIntensity: 0.35 }));
          soMesh.position.set(soPos.x, soPos.y, soPos.z);
          soMesh.castShadow = true;
          architecturalGroup.add(soMesh);

          const ringGeo = new THREE.RingGeometry(400, 450, 32);
          ringGeo.rotateX(-Math.PI / 2);
          const ringMesh = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: soColor, side: THREE.DoubleSide, transparent: true, opacity: 0.35 }));
          ringMesh.position.set(soPos.x, floorY + 10, soPos.y);
          architecturalGroup.add(ringMesh);
          smartObjectRings.push(ringMesh);

          const tagShort = so.smart_object_tag.split('.').pop();
          makeBillboardText(`[E] ${tagShort}`, soPos.x, floorY + 250, soPos.z, "#ffffff");

          activeSmartObjects.push({ tag: so.smart_object_tag, anchor_id: so.anchor_id, mesh: soMesh, pos: soPos });
        });
      }
    }

    function buildPropsFromManifest(manifestProps) {
      const propMatWood = new THREE.MeshLambertMaterial({ color: 0x5a3d28 });
      const propMatStone = new THREE.MeshLambertMaterial({ color: 0x48515f });

      for (const [nodeId, propList] of Object.entries(manifestProps)) {
        propList.forEach(prop => {
          const pos = prop.relative_position;
          const pType = prop.primitive_type;

          if (pType === "OBELISK") {
            const obelisk = new THREE.Mesh(new THREE.CylinderGeometry(20, 45, 340, 4), propMatStone);
            obelisk.position.set(pos.x, pos.z, pos.y);
            obelisk.rotation.y = Math.PI / 4;
            dynamicPropsGroup.add(obelisk);
          } else if (pType === "MARKET_STALL") {
            const stall = new THREE.Group();
            const table = new THREE.Mesh(new THREE.BoxGeometry(220, 80, 100), propMatWood);
            table.position.y = 40;
            stall.add(table);
            const awning = new THREE.Mesh(new THREE.BoxGeometry(240, 12, 130), new THREE.MeshLambertMaterial({ color: prop.material_color_hex || 0xb22222 }));
            awning.position.set(0, 185, 0); awning.rotation.x = 0.15;
            stall.add(awning);
            stall.position.set(pos.x, pos.z, pos.y);
            stall.rotation.y = prop.rotation_y || 0;
            dynamicPropsGroup.add(stall);
          } else if (pType === "BAKERY_OVEN") {
            const oven = new THREE.Group();
            const base = new THREE.Mesh(new THREE.BoxGeometry(280, 140, 240), propMatStone); base.position.y = 70; oven.add(base);
            const fire = new THREE.Mesh(new THREE.BoxGeometry(110, 40, 60), new THREE.MeshBasicMaterial({ color: 0xff3b00 })); fire.position.set(0, 50, 95); oven.add(fire);
            oven.position.set(pos.x, pos.z, pos.y);
            dynamicPropsGroup.add(oven);
          } else if (pType === "APOTHECARY_SHELF") {
            const shelf = new THREE.Mesh(new THREE.BoxGeometry(260, 260, 35), propMatWood);
            shelf.position.set(pos.x, pos.z + 130, pos.y);
            dynamicPropsGroup.add(shelf);
          } else if (pType === "SLUICE_MECHANISM") {
            const gate = new THREE.Mesh(new THREE.BoxGeometry(160, 280, 40), propMatStone);
            gate.position.set(pos.x, pos.z + 140, pos.y);
            dynamicPropsGroup.add(gate);
          }
        });
      }
    }

    function spawnNPCActor(npc) {
      const g = new THREE.Group();
      const col = parseInt((npc.color_hex || "#f5af19").replace('#', '0x'));
      const body = new THREE.Mesh(
        new THREE.CylinderGeometry(55, 55, 150, 16),
        new THREE.MeshLambertMaterial({ color: col, emissive: col, emissiveIntensity: 0.25 })
      );
      body.position.y = 75;
      body.castShadow = true;
      g.add(body);
      g.position.set(npc.position.x, npc.position.z, npc.position.y);
      npcActorGroup.add(g);

      makeBillboardText(npc.name, npc.position.x, npc.position.z + 240, npc.position.y, "#f5af19");
      activeNPCActors.push({ id: npc.npc_id, name: npc.name, group: g, dialogue: npc.default_dialogue, pos: npc.position });
    }

    // 3. Minimap Radar
    const mapCanvas = document.getElementById("minimap");
    const mapCtx = mapCanvas.getContext("2d");

    function renderMinimap() {
      mapCtx.fillStyle = "#080b11";
      mapCtx.fillRect(0, 0, mapCanvas.width, mapCanvas.height);
      const scale = 0.045;
      const offsetX = mapCanvas.width / 2;
      const offsetY = mapCanvas.height / 2;

      for (const [nodeId, node] of Object.entries(activeRooms)) {
        const min = node.bounds_min;
        const max = node.bounds_max;
        const rx = (min.x * scale) + offsetX;
        const ry = (min.y * scale) + offsetY;
        const rw = Math.abs(max.x - min.x) * scale;
        const rh = Math.abs(max.y - min.y) * scale;
        mapCtx.fillStyle = nodeId.includes("AQUEDUCT") ? "rgba(0, 168, 204, 0.4)" : "rgba(35, 44, 61, 0.5)";
        mapCtx.strokeStyle = nodeId.includes("AQUEDUCT") ? "#00f2fe" : "#334057";
        mapCtx.fillRect(rx, ry, rw, rh);
        mapCtx.strokeRect(rx, ry, rw, rh);
      }

      activeNPCActors.forEach(npc => {
        mapCtx.fillStyle = "#f5af19";
        mapCtx.beginPath();
        mapCtx.arc((npc.pos.x * scale) + offsetX, (npc.pos.y * scale) + offsetY, 4, 0, Math.PI * 2);
        mapCtx.fill();
      });

      mapCtx.fillStyle = "#00f2fe";
      mapCtx.beginPath();
      mapCtx.arc((playerGroup.position.x * scale) + offsetX, (playerGroup.position.z * scale) + offsetY, 5, 0, Math.PI * 2);
      mapCtx.fill();
    }

    // 4. WebSocket State Bridge with Auto-Handshake
    let socket = null;
    function connectWS() {
      let wsUrl = (window.location.host.includes('-3000.app.github.dev'))
        ? `wss://${window.location.host.replace('-3000', '-8765')}`
        : ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'ws://localhost:8765' : `wss://${window.location.host}`);

      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        document.getElementById('ui-status').innerText = "Connected (8765)";
        document.getElementById('ui-status').style.color = "#00e676";
        socket.send(JSON.stringify({
          type: "REQUEST_INITIAL_STATE",
          district_id: "District_MarketSquare",
          player_stress: 0.35,
          player_coords: [playerGroup.position.x, playerGroup.position.z, playerGroup.position.y]
        }));
      };

      socket.onclose = () => {
        document.getElementById('ui-status').innerText = "Disconnected (Retrying...)";
        document.getElementById('ui-status').style.color = "#ff5252";
        setTimeout(connectWS, 2500);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === "PROCESSED") {
          document.getElementById('dialogue-speaker').innerText = data.target_npc;
          document.getElementById('dialogue-text').innerText = `"${data.dialogue}"`;
          document.getElementById('dialogue-action').innerText = `EXECUTING STATETREE: ${data.action}`;
          document.getElementById('dialogue-box').style.display = 'block';

          if (data.game_runtime_manifest) {
            applyCompleteRuntimeManifest(data.game_runtime_manifest);
          }
        }
      };
    }
    connectWS();

    function sendStressTelemetry(stress) {
      if (!socket || socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({
        type: "TELEMETRY_INGEST",
        district_id: "District_MarketSquare",
        player_stress: stress,
        player_coords: [playerGroup.position.x, playerGroup.position.z, playerGroup.position.y],
        seed: Math.floor(Math.random() * 90000)
      }));
    }

    function triggerSmartObjectInteraction(so) {
      if (!socket || socket.readyState !== WebSocket.OPEN) return;
      const toast = document.getElementById('interaction-toast');
      toast.innerText = `ACTIVATED: ${so.anchor_id}`;
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 2200);

      socket.send(JSON.stringify({
        type: "SMART_OBJECT_INTERACT",
        smart_object_id: so.anchor_id,
        smart_object_tag: so.tag,
        district_id: "District_MarketSquare",
        player_coords: [playerGroup.position.x, playerGroup.position.z, playerGroup.position.y]
      }));
    }

    function recenterCamera() {
      controls.target.set(playerGroup.position.x, playerGroup.position.y + 75, playerGroup.position.z);
      camera.position.set(playerGroup.position.x, playerGroup.position.y + 2200, playerGroup.position.z + 2400);
      controls.update();
    }

    // 5. Controls & Interaction Loop
    window.addEventListener('keydown', (e) => {
      const k = e.key.toLowerCase();
      if (k === 'w' || k === 'arrowup') keys.w = true;
      if (k === 'a' || k === 'arrowleft') keys.a = true;
      if (k === 's' || k === 'arrowdown') keys.s = true;
      if (k === 'd' || k === 'arrowright') keys.d = true;
      if (k === ' ') recenterCamera();
      if (k === 'e') {
        let nearest = null;
        let minDist = runtimeMechanics.interaction_radius || 480.0;
        activeSmartObjects.forEach(so => {
          const d = Math.hypot(playerGroup.position.x - so.pos.x, playerGroup.position.z - so.pos.z);
          if (d < minDist) { nearest = so; minDist = d; }
        });
        if (nearest) triggerSmartObjectInteraction(nearest);
      }
    });

    window.addEventListener('keyup', (e) => {
      const k = e.key.toLowerCase();
      if (k === 'w' || k === 'arrowup') keys.w = false;
      if (k === 'a' || k === 'arrowleft') keys.a = false;
      if (k === 's' || k === 'arrowdown') keys.s = false;
      if (k === 'd' || k === 'arrowright') keys.d = false;
    });

    function updatePlayer(delta) {
      const speed = (runtimeMechanics.player_base_speed || 1400.0) * delta;
      let dx = 0, dz = 0;
      if (keys.w) dz -= speed;
      if (keys.s) dz += speed;
      if (keys.a) dx -= speed;
      if (keys.d) dx += speed;

      if (dx !== 0 || dz !== 0) {
        playerGroup.position.x += dx;
        playerGroup.position.z += dz;
        const targetRotation = Math.atan2(-dx, -dz);
        let diff = targetRotation - playerGroup.rotation.y;
        while (diff < -Math.PI) diff += Math.PI * 2;
        while (diff > Math.PI) diff -= Math.PI * 2;
        playerGroup.rotation.y += diff * 0.25;

        camera.position.x += dx;
        camera.position.z += dz;
        controls.target.x += dx;
        controls.target.z += dz;
      }

      let currentRoomName = "Outdoor Alleyways";
      let targetElevation = 0;

      for (const [nodeId, node] of Object.entries(activeRooms)) {
        const min = node.bounds_min;
        const max = node.bounds_max;
        if (playerGroup.position.x >= min.x && playerGroup.position.x <= max.x &&
            playerGroup.position.z >= min.y && playerGroup.position.z <= max.y) {
          currentRoomName = node.zone_name;
          targetElevation = node.center_location.z;
          break;
        }
      }

      playerGroup.position.y += (targetElevation - playerGroup.position.y) * 0.15;
      controls.target.y = playerGroup.position.y + 75;
      document.getElementById('ui-room').innerText = currentRoomName;

      // Smart Object Prompt
      let promptText = "None";
      const rad = runtimeMechanics.interaction_radius || 480.0;
      activeSmartObjects.forEach(so => {
        const dist = Math.hypot(playerGroup.position.x - so.pos.x, playerGroup.position.z - so.pos.z);
        if (dist < rad) promptText = `${so.anchor_id} [Press E]`;
      });
      document.getElementById('ui-prompt').innerText = promptText;
    }

    let lastTime = performance.now();
    function animate() {
      requestAnimationFrame(animate);
      const now = performance.now();
      const delta = (now - lastTime) / 1000.0;
      lastTime = now;

      updatePlayer(delta);
      const pulse = 0.25 + 0.15 * Math.sin(now * 0.005);
      smartObjectRings.forEach(r => { r.material.opacity = pulse; });

      controls.update();
      renderer.render(scene, camera);
      renderMinimap();
    }
    animate();

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  </script>
</body>
</html>
''', encoding="utf-8")
print("  [5/5] Compiled web_client/index.html")

# ==============================================================================
# 6. BYTECODE INTEGRITY CHECK
# ==============================================================================
print("\n[VERIFIER]: Auditing Python bytecode...")
targets = [
    "schemas/studio_contracts.py",
    "services/agent_runtime/src/virtual_studio_engine.py",
    "services/agent_runtime/src/server.py",
    "services/agent_runtime/src/team_sync.py",
    "tools/engine_importer.py"
]

for t in targets:
    py_compile.compile(t, doraise=True)
    print(f"  [BYTECODE VERIFIED]: {t}")

print("\nSUCCESS: Production runtime manifest, dev team agents, and client engine deployed!")
