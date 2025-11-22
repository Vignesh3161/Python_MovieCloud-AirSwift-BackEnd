from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

class FlightRequest(BaseModel):
    requester: str
    from_location: dict
    from_hospital: str
    from_address: str
    to_location: dict
    to_hospital: str
    to_address: str
    flight_date: date       # <-- KEEP THIS
    flight_time: time       # <-- KEEP THIS
    route: str
    medical_staff: List[str]
    medicalEquipmentOnboard: str
    status: Optional[str] = "Pending"
    special_instructions : Optional[str] = None