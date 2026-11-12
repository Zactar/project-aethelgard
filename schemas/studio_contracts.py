"""
schemas/studio_contracts.py
Project Aethelgard: 100% Game-Agnostic Multi-Agent Virtual Studio Contracts.
Zero game-specific schemas; defines only universal studio governance & roadmap models.
"""

import time
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DisciplineType(str, Enum):
    SYSTEMS = "Systems"
    GAMEPLAY = "Gameplay"
    CLIENT = "Client"
    LEVEL = "Level"
    NARRATIVE = "Narrative"
    AESTHETICS = "Aesthetics"
    UI_UX = "UI_UX"
    CHAOS_QA = "Chaos QA"


class MilestoneStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATING = "VALIDATING"
    SHIPPED = "SHIPPED"


class DeliverableStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"


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


class ReviewVote(str, Enum):
    APPROVE = "APPROVE"
    VETO = "VETO"
    ABSTAIN = "ABSTAIN"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FeatureChangeRequest(BaseModel):
    rfc_id: str
    title: str
    description: str
    submitted_by: str
    change_type: RFCChangeType = RFCChangeType.ADJUST_MECHANICS
    payload_diff: Dict[str, Any] = Field(default_factory=dict)
    status: RFCStatus = RFCStatus.PENDING_REVIEW
    created_at: float = Field(default_factory=lambda: float(time.time()))


class DeliverableItem(BaseModel):
    deliverable_id: str
    discipline: DisciplineType
    title: str
    target_subsystem: str = "web_client/index.html"
    status: DeliverableStatus = DeliverableStatus.PENDING
    verified_artifact: Optional[str] = None


class StudioMilestone(BaseModel):
    version: str
    codename: str
    theme: str = "Core Milestone"
    status: MilestoneStatus = MilestoneStatus.PLANNED
    completion_percentage: float = 0.0
    deliverables: List[DeliverableItem] = Field(default_factory=list)
    completed_at: Optional[datetime] = None


class StudioRoadmapState(BaseModel):
    active_version: str = "v0.1.0"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    milestones: List[StudioMilestone] = Field(default_factory=list)


class DisciplineBallot(BaseModel):
    discipline: DisciplineType
    vote: ReviewVote
    rationale: str


class ReviewQuorumResult(BaseModel):
    rfc_id: str
    approved: bool
    ballots: List[DisciplineBallot] = Field(default_factory=list)


class PostMortemRecord(BaseModel):
    incident_id: str
    milestone: str
    discipline: str
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    summary: str
    mitigation: str
