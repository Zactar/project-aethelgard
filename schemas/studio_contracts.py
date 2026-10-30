from enum import Enum
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
