from pydantic import BaseModel, Field
from typing import Optional, List

class MaintenanceRecord(BaseModel):
    date: str
    details: str

class Ambulance(BaseModel):
    id: Optional[str]
    name: str
    type: str
    capacity: int
    maintenance_records: List[MaintenanceRecord] = Field(default_factory=list)
    available: bool = True
    last_maintenance_date: Optional[str] = None
