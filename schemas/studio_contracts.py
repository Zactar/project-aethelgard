from enum import Enum
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class ContentType(str, Enum):
    STATETREE_TASK = "STATETREE_TASK"
    NPC_DIALOGUE_TEMPLATE = "NPC_DIALOGUE_TEMPLATE"
    SYSTEMIC_QUEST = "SYSTEMIC_QUEST"
    SPATIAL_LAYOUT = "SPATIAL_LAYOUT"
    BALANCE_HOTFIX = "BALANCE_HOTFIX"

class AestheticVerdict(str, Enum):
    APPROVED_WITH_SOUL = "APPROVED_WITH_SOUL"
    NEEDS_HUMAN_POLISH = "NEEDS_HUMAN_POLISH"
    REJECTED_GENERIC_SLOP = "REJECTED_GENERIC_SLOP"

class BugSeverity(str, Enum):
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"

class Vector3D(BaseModel):
    x: float
    y: float
    z: float

class SmartObjectAnchor(BaseModel):
    anchor_id: str
    smart_object_tag: str
    assigned_npc_id: Optional[str] = None
    relative_position: Vector3D
    interaction_facing_yaw: float

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

# ==============================================================================
# SPRINT CEREMONY & BRAINSTORMING DATA CONTRACTS
# ==============================================================================

class IdeaDiscipline(str, Enum):
    SYSTEMS_DESIGN = "SYSTEMS_DESIGN"
    LEVEL_ARCHITECTURE = "LEVEL_ARCHITECTURE"
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
