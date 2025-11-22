# models/aircraft.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# ------------------ ObjectId Support for Pydantic v2 ------------------ #
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        schema.update(type="string")
        return schema


# ------------------ Maintenance Record Schema ------------------ #
class MaintenanceRecord(BaseModel):
    date: datetime
    details: str
    cost: Optional[float] = None


# ------------------ Aircraft Model (MongoDB Document) ------------------ #
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ------------------ Maintenance Record ------------------ #
class MaintenanceRecord(BaseModel):
    date: datetime
    details: str


# ------------------ Aircraft Model (Matches Your JSON) ------------------ #
class Aircraft(BaseModel):
    id: Optional[str] = Field(default=None)   # Example: "AA03"

    aircraft_type: str                        # "Helicopter"
    registration: str                         # "VT-ABC"
    airline_operator: str                     # "Air Ambulance India"

    range_km: int                              # 550
    speed_kmh: int                             # 300
    max_payload_kg: int                        # 540

    cabin_configuration: str                  # "2 medical seats, 2 stretcher"
    base_location: str                        # "Coimbatore Airport"
    medical_equipment_onboard: str            # "Ventilator, Oxygen Cylinder"

    available: bool = True

    last_maintenance_date: Optional[datetime] = None
    
    image_url: Optional[str] = None

    maintenance_records: List[MaintenanceRecord] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    



# ------------------ Create Aircraft Schema ------------------ #
class CreateAircraft(BaseModel):
    id: str 
    aircraft_type: str
    registration: str
    airline_operator: str

    range_km: int
    speed_kmh: int
    max_payload_kg: int

    cabin_configuration: str
    base_location: str
    medical_equipment_onboard: str

    available: bool = True


# ------------------ Update Aircraft Schema ------------------ #
class UpdateAircraft(BaseModel):
    aircraft_type: Optional[str] = None
    registration: Optional[str] = None
    airline_operator: Optional[str] = None

    range_km: Optional[int] = None
    speed_kmh: Optional[int] = None
    max_payload_kg: Optional[int] = None

    cabin_configuration: Optional[str] = None
    base_location: Optional[str] = None
    medical_equipment_onboard: Optional[str] = None

    available: Optional[bool] = None
    last_maintenance_date: Optional[datetime] = None

    maintenance_records: Optional[List[MaintenanceRecord]] = None


# ------------------ Add Single Maintenance Record Schema ------------------ #


class AddMaintenance(BaseModel):
    maintenance_type: str
    description: Optional[str] = None
    last_maintenance_date: datetime
    next_due_date: Optional[datetime] = None
    status: str = "scheduled"   # scheduled | in-progress | completed
    technician: Optional[str] = None
# ------------------ Update Maintenance Status Schema ------------------ #
    
class UpdateMaintenanceStatus(BaseModel):
    status: str = Field(..., description="scheduled | in-progress | completed")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed"
            }
        }
    }




    
