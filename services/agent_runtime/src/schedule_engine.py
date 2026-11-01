"""
services/agent_runtime/src/schedule_engine.py
Project Aethelgard: StateTree NPC Schedule & Daily Citizen Routine Engine
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class CitizenActivity(str, Enum):
    WORK = "WORK"
    DWELL = "DWELL"
    WORSHIP = "WORSHIP"
    SLEEP = "SLEEP"
    CURFEW_FLEE = "CURFEW_FLEE"

class ScheduleSlot(BaseModel):
    start_hour: int
    end_hour: int
    activity: CitizenActivity
    location_node: str
    dialogue_context: str

class NPCSchedule(BaseModel):
    npc_id: str
    name: str
    routine: List[ScheduleSlot]

class ScheduleEngine:
    def __init__(self):
        self.schedules = {
            "hearthmother_elspeth": NPCSchedule(
                npc_id="hearthmother_elspeth",
                name="Hearthmother Elspeth",
                routine=[
                    ScheduleSlot(start_hour=6, end_hour=18, activity=CitizenActivity.WORK, location_node="common_loaf_bakery", dialogue_context="Baking the morning grain tithes."),
                    ScheduleSlot(start_hour=18, end_hour=21, activity=CitizenActivity.DWELL, location_node="market_cross", dialogue_context="Resting at the square well before curfew."),
                    ScheduleSlot(start_hour=21, end_hour=6, activity=CitizenActivity.CURFEW_FLEE, location_node="common_loaf_bakery", dialogue_context="Doors barricaded for twilight curfew.")
                ]
            ),
            "garrett_apothecary": NPCSchedule(
                npc_id="garrett_apothecary",
                name="Garrett the Apothecary",
                routine=[
                    ScheduleSlot(start_hour=8, end_hour=17, activity=CitizenActivity.WORK, location_node="garrett_curatives", dialogue_context="Distilling mountain salves."),
                    ScheduleSlot(start_hour=17, end_hour=20, activity=CitizenActivity.WORSHIP, location_node="market_cross", dialogue_context="Lighting votives at the street shrine."),
                    ScheduleSlot(start_hour=20, end_hour=8, activity=CitizenActivity.SLEEP, location_node="garrett_curatives", dialogue_context="Asleep behind locked shutters.")
                ]
            )
        }

    def get_current_activity(self, npc_id: str, current_hour: int = 14) -> Optional[ScheduleSlot]:
        sched = self.schedules.get(npc_id)
        if not sched:
            return None
        for slot in sched.routine:
            if slot.start_hour <= slot.end_hour:
                if slot.start_hour <= current_hour < slot.end_hour:
                    return slot
            else:
                if current_hour >= slot.start_hour or current_hour < slot.end_hour:
                    return slot
        return sched.routine[0]
