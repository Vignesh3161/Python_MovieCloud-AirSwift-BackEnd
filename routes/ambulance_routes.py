from fastapi import APIRouter, HTTPException, Header, Depends
from database import db
from models.ambulance import Ambulance, MaintenanceRecord
from utils import decode_token
from bson import ObjectId
from datetime import datetime

ambulance_router = APIRouter()

def get_current_user(token: str = Header(...)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

@ambulance_router.post("/create-ambulance")
async def create_ambulance(ambulance: Ambulance, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.ambulances.insert_one(ambulance.dict())
    return {"id": str(result.inserted_id), "message": "Ambulance added"}

@ambulance_router.put("/add-maintenance/{ambulance_id}")
async def add_maintenance(ambulance_id: str, record: MaintenanceRecord, current_user: dict = Depends(get_current_user)):
    ambulance = await db.ambulances.find_one({"_id": ObjectId(ambulance_id)})
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    
    record_dict = record.dict()
    record_dict["date"] = datetime.utcnow().isoformat()
    await db.ambulances.update_one(
        {"_id": ObjectId(ambulance_id)},
        {
            "$push": {"maintenance_records": record_dict},
            "$set": {"last_maintenance_date": record_dict["date"], "available": True}
        }
    )
    return {"message": "Maintenance record added"}

@ambulance_router.get("/available-ambulances")
async def available_ambulances():
    ambulances = []
    async for amb in db.ambulances.find({"available": True}):
        amb["id"] = str(amb["_id"])
        del amb["_id"]
        ambulances.append(amb)
    return ambulances
