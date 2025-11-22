# models/schedule.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ETAInfo(BaseModel):
    eta_utc: Optional[datetime] = None     # computed ETA in UTC
    estimated_duration_minutes: Optional[int] = None
    last_updated: Optional[datetime] = None

class ScheduleBase(BaseModel):
    flight_request_id: str
    scheduled_by: Optional[str] = None            # email or user id who scheduled
    scheduled_at: Optional[datetime] = None       # when it was scheduled (UTC)
    departure_time_utc: Optional[datetime] = None
    arrival_time_utc: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    assigned_crew: List[str] = Field(default_factory=list)

class ScheduleCreate(ScheduleBase):
    # minimal required fields are flight_request_id and departure/arrival or duration
    pass

class ScheduleOut(ScheduleBase):
    id: Optional[str]
    status: str                                      # Scheduled, En Route, In Transit, Completed, Cancelled
    eta: Optional[ETAInfo] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UpdateETA(BaseModel):
    eta_utc: datetime
    estimated_duration_minutes: Optional[int] = None

class UpdateStatus(BaseModel):
    status: str
    note: Optional[str] = None

class AssignCrew(BaseModel):
    crew: List[str]
