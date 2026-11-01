from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ==============================================================================
# ENUM DEFINITIONS (TOPOLOGICALLY ORDERED BEFORE USAGE)
# ==============================================================================


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


class BiomeType(str, Enum):
    CIVIC_MARKET = "CIVIC_MARKET"
    SUBTERRANEAN_UNDERCROFT = "SUBTERRANEAN_UNDERCROFT"
    CATHEDRAL_HEIGHTS = "CATHEDRAL_HEIGHTS"
    LOW_DOCKS = "LOW_DOCKS"


class MilestoneStatus(str, Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATION = "VALIDATION"
    SHIPPED = "SHIPPED"


class SoundCategory(str, Enum):
    UI_CLICK = "UI_CLICK"
    FOOTSTEP = "FOOTSTEP"
    INTERACTION_MECHANISM = "INTERACTION_MECHANISM"
    BUFF_CONSUMED = "BUFF_CONSUMED"
    AMBIENT_ZONE = "AMBIENT_ZONE"


class AnimationState(str, Enum):
    IDLE = "IDLE"
    WALK = "WALK"
    INTERACT = "INTERACT"
    COMBAT = "COMBAT"


class PropPrimitiveType(str, Enum):
    BOX = "BOX"
    CYLINDER = "CYLINDER"
    TORUS = "TORUS"
    OBELISK = "OBELISK"
    MARKET_STALL = "MARKET_STALL"
    BAKERY_OVEN = "BAKERY_OVEN"
    APOTHECARY_SHELF = "APOTHECARY_SHELF"
    SLUICE_MECHANISM = "SLUICE_MECHANISM"


class ItemCategory(str, Enum):
    COMMODITY = "COMMODITY"
    CONSUMABLE = "CONSUMABLE"
    CONTRABAND = "CONTRABAND"
    TOOL = "TOOL"


class ObjectiveStatus(str, Enum):
    LOCKED = "LOCKED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RFCChangeType(str, Enum):
    NEW_ITEM = "NEW_ITEM"
    MODIFY_ITEM = "MODIFY_ITEM"
    NEW_ROOM_NODE = "NEW_ROOM_NODE"
    NEW_SMART_OBJECT = "NEW_SMART_OBJECT"
    ADJUST_MECHANICS = "ADJUST_MECHANICS"
    UPDATE_UI_THEME = "UPDATE_UI_THEME"
    NEW_QUEST = "NEW_QUEST"


class RFCStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPLOYED = "DEPLOYED"


class IdeaDiscipline(str, Enum):
    SYSTEMS_DESIGN = "SYSTEMS_DESIGN"
    LEVEL_ARCHITECTURE = "LEVEL_ARCHITECTURE"
    GAMEPLAY_MECHANICS = "GAMEPLAY_MECHANICS"
    UI_UX_DESIGN = "UI_UX_DESIGN"
    NARRATIVE_LORE = "NARRATIVE_LORE"
    AESTHETIC_STYLE = "AESTHETIC_STYLE"
    QA_COMBAT_BALANCE = "QA_COMBAT_BALANCE"

# ==============================================================================
# SPATIAL & PRIMITIVE MODELS
# ==============================================================================


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


class SpatialSoundCue(BaseModel):
    cue_id: str
    category: SoundCategory
    base_frequency: float = 440.0
    duration_sec: float = 0.25
    gain: float = 0.5
    position: Optional[Vector3D] = None
    spatial_radius: float = 1200.0

# ==============================================================================
# GAMEPLAY, ITEM, & ACTOR MODELS
# ==============================================================================


class ItemSpec(BaseModel):
    item_id: str
    display_name: str
    category: ItemCategory
    base_value: float
    description: str
    icon_symbol: str = "📦"
    stack_limit: int = 20
    effects: Dict[str, float] = Field(default_factory=dict)


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
    current_animation_state: AnimationState = AnimationState.IDLE
    dialogue_sound_frequency: float = 320.0
    patrol_waypoints: List[Vector3D] = Field(default_factory=list)
    current_schedule_activity: str = "PATROL"


class UIThemeSpec(BaseModel):
    primary_color_hex: str = "#4facfe"
    accent_color_hex: str = "#00f2fe"
    background_alpha: float = 0.94
    hud_title: str = "AETHELGARD RUNTIME CLIENT"
    show_minimap: bool = True
    show_inventory: bool = True
    action_buttons: List[Dict[str, Any]] = Field(default_factory=list)


class GameplayMechanicsSpec(BaseModel):
    player_base_speed: float = 1500.0
    sprint_multiplier: float = 1.6
    stamina_max: float = 100.0
    stamina_recovery_rate: float = 15.0
    interaction_radius: float = 480.0
    camera_fov: float = 45.0
    camera_default_distance: float = 3000.0

# ==============================================================================
# QUESTS & UNIFIED RUNTIME MANIFEST
# ==============================================================================


class QuestObjective(BaseModel):
    objective_id: str
    description: str
    target_node_id: str
    target_smart_object: Optional[str] = None
    target_npc_id: Optional[str] = None
    required_item_id: Optional[str] = None
    status: ObjectiveStatus = ObjectiveStatus.ACTIVE


class SystemicQuest(BaseModel):
    quest_id: str
    title: str
    synopsis: str
    issuing_npc_id: str
    reward_item_id: Optional[str] = None
    reward_stamina: float = 0.0
    objectives: List[QuestObjective] = Field(default_factory=list)
    is_completed: bool = False
    completion_debrief: str = ""


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
    active_quests: List[SystemicQuest] = Field(default_factory=list)


# ==============================================================================
# RETROSPECTIVE MEMORY & POST-MORTEM SCHEMAS
# ==============================================================================


class IncidentSeverity(str, Enum):
    """Categorization of failure impact across engine, client, and runtime."""
    LOW = "LOW"             # Telemetry blips, cosmetic warnings, minor draw-call budget creep
    MEDIUM = "MEDIUM"       # Balance anomalies, soft-locks, state desync, quest state loop
    HIGH = "HIGH"           # Functional failure, collision entrapment, raycast hijacking
    CRITICAL = "CRITICAL"   # Engine crash, AST parse failure, topological break, server halt


class DisciplineType(str, Enum):
    """Virtual studio disciplines with role-specific agency."""
    SYSTEMS = "Systems"
    LEVEL = "Level"
    NARRATIVE = "Narrative"
    GAMEPLAY = "Gameplay"
    CLIENT = "Client"
    CHAOS_QA = "Chaos QA"


class PostMortemRecord(BaseModel):
    """Deterministic post-mortem event schema for retrospective tracking."""
    incident_id: str = Field(...,
                             description="Unique slug: e.g. INC-20261028-LVL-01")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    milestone_tag: str = Field(...,
                               description="Target release milestone (e.g., v0.4.0, v0.5.0)")
    discipline: DisciplineType = Field(
        ..., description="Responsible or affected studio discipline")
    severity: IncidentSeverity = Field(...,
                                       description="Severity level of the incident")
    summary: str = Field(...,
                         description="Concise description of the failure event")
    root_cause: str = Field(
        ..., description="Underlying architectural, topological, or code failure")
    symptoms: List[str] = Field(
        default_factory=list, description="Observed error logs or telemetry signatures")
    mitigation_applied: str = Field(
        ..., description="Remediation, patch, or self-healing rollback applied")
    prevention_rule: str = Field(
        ..., description="Negative constraint rule injected into future agent prompts")
    affected_files: List[str] = Field(
        default_factory=list, description="Files modified or broken by this regression")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary telemetry or engine coordinates")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DisciplineCompetency(BaseModel):
    """Historical reliability metrics calculated across release milestones."""
    discipline: DisciplineType
    total_proposals: int = Field(default=0)
    accepted_rfcs: int = Field(default=0)
    regressions_caused: int = Field(default=0)
    clean_streak: int = Field(
        default=0, description="Consecutive deployments without a regression")
    active_friction_notes: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ==============================================================================
# AUDIT, LORE, & QA CONTRACTS
# ==============================================================================


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


class ClientPlaytestReport(BaseModel):
    nodes_traversed: int
    unreachable_nodes: List[str]
    interaction_failures: List[str]
    average_socket_latency_ms: float
    out_of_bounds_detected: bool
    verdict: str

# ==============================================================================
# RFC, MILESTONE, & OPTIMIZATION CONTRACTS
# ==============================================================================


class AgentReviewVote(BaseModel):
    agent_id: str
    approved: bool
    score: float = Field(ge=0.0, le=1.0)
    comments: str
    flagged_risks: List[str] = Field(default_factory=list)


class FeatureChangeRequest(BaseModel):
    rfc_id: str
    title: str
    description: str
    submitted_by: str
    change_type: RFCChangeType
    payload_diff: Dict[str, Any]
    status: RFCStatus = RFCStatus.PENDING_REVIEW
    review_votes: List[AgentReviewVote] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    resolved_at: Optional[float] = None


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


class StudioEpic(BaseModel):
    epic_id: str
    title: str
    target_biome: BiomeType
    primary_deliverable: str
    assigned_crews: List[str]
    is_completed: bool = False


class StudioMilestone(BaseModel):
    milestone_id: str
    version_tag: str
    theme: str
    target_phase: str
    epics: List[StudioEpic] = Field(default_factory=list)
    status: MilestoneStatus = MilestoneStatus.PLANNING
    release_notes: List[str] = Field(default_factory=list)


class OptimizationReport(BaseModel):
    total_nodes: int
    total_props: int
    estimated_draw_calls: int
    payload_size_kb: float
    instancing_recommended: bool
    budget_exceeded: bool
    triage_notes: str


# ==============================================================================
# REVIEW BOARD QUORUM SCHEMAS
# ==============================================================================

class ReviewVote(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    REJECT = "REJECT"


class DisciplineBallot(BaseModel):
    reviewer: DisciplineType
    vote: ReviewVote
    critique: str
    friction_points: List[str] = Field(default_factory=list)
    veto: bool = Field(
        default=False, description="Hard block preventing RFC approval")

    class Config:
        use_enum_values = True


class ReviewQuorumResult(BaseModel):
    rfc_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(...,
                        description="APPROVED, REJECTED, or REVISION_REQUIRED")
    quorum_reached: bool
    total_votes: int
    approvals: int
    rejections: int
    vetoes_cast: int
    ballots: List[DisciplineBallot]
    synthesis_summary: str
    actionable_directives: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==============================================================================
# ROADMAP & MILESTONE EVOLUTION SCHEMAS
# ==============================================================================


class MilestoneStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATING = "VALIDATING"
    SHIPPED = "SHIPPED"


class DeliverableStatus(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    VERIFIED = "VERIFIED"


class MilestoneDeliverable(BaseModel):
    deliverable_id: str
    discipline: DisciplineType
    title: str
    target_subsystem: str
    acceptance_criteria: List[str]
    status: DeliverableStatus = DeliverableStatus.PENDING
    verified_artifact: Optional[str] = None

    class Config:
        use_enum_values = True


class StudioMilestone(BaseModel):
    version: str
    codename: str
    theme: str
    status: MilestoneStatus = MilestoneStatus.PLANNED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    deliverables: List[MilestoneDeliverable] = Field(default_factory=list)
    completion_percentage: float = 0.0

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StudioRoadmapState(BaseModel):
    active_version: str
    milestones: List[StudioMilestone]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
