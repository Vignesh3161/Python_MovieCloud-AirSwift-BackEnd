# routes/schedule_routes.py
from fastapi import APIRouter, HTTPException, Depends, Header
from database import db, scheduling_collection
from models.schedule import ScheduleCreate, ScheduleOut, UpdateETA, UpdateStatus, AssignCrew
from utils import verify_token, decode_token
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List

schedule_router = APIRouter()

# Allowed status transitions (small state-machine)
VALID_TRANSITIONS = {
    "Scheduled": ["Dispatched", "Cancelled"],
    "Dispatched": ["In-Transit", "Cancelled"],
    "In-Transit": ["Completed"],
    "Completed": [],
    "Cancelled": []
}

def objid(val: str):
    try:
        return ObjectId(val)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

# Helper to fetch flight request
async def get_flight_request_or_404(fr_id: str):
    fr = await db.flight_requests.find_one({"_id": objid(fr_id)})
    if not fr:
        raise HTTPException(status_code=404, detail="Flight request not found")
    return fr

# Helper to fetch schedule
async def get_schedule_or_404(sched_id: str):
    sched = await db.schedules.find_one({"_id": objid(sched_id)})
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sched

# Compute ETA helper (simple): if departure + duration => arrival and ETA
def compute_eta(departure: datetime, duration_minutes: int):
    eta = departure + timedelta(minutes=duration_minutes)
    return eta

# Create schedule (requires dispatcher or superadmin)
@schedule_router.post("/create-schedule", response_model=dict)
async def create_schedule(schedule: ScheduleCreate, token_data: dict = Depends(verify_token)):
    payload = token_data
    if payload["role"] not in ["superadmin", "dispatcher"]:
        raise HTTPException(status_code=403, detail="Not authorized to create schedule")

    # ensure flight request exists
    fr = await get_flight_request_or_404(schedule.flight_request_id)

    # build schedule document
    now = datetime.utcnow()
    sched_doc = schedule.dict()
    sched_doc.update({
        "status": "Scheduled",
        "created_at": now,
        "updated_at": now,
        "scheduled_by": payload.get("email"),
        # eta subdoc - computed if departure_time and duration provided
        "eta": None
    })

    # compute ETA if departure_time_utc and estimated_duration_minutes are present
    if sched_doc.get("departure_time_utc") and sched_doc.get("estimated_duration_minutes"):
        eta_dt = compute_eta(sched_doc["departure_time_utc"], sched_doc["estimated_duration_minutes"])
        sched_doc["eta"] = {
            "eta_utc": eta_dt,
            "estimated_duration_minutes": sched_doc["estimated_duration_minutes"],
            "last_updated": now
        }

    result = await db.schedules.insert_one(sched_doc)

    # Update flight_request status to "Scheduled"
    await db.flight_requests.update_one({"_id": objid(schedule.flight_request_id)}, {"$set": {"status": "Scheduled"}})

    return {"id": str(result.inserted_id), "message": "Schedule created"}

# List schedules (optionally filter by flight_request_id or status)
@schedule_router.get("/list-schedules")
async def list_schedules(flight_request_id: str = None, status: str = None) -> List[dict]:
    query = {}
    if flight_request_id:
        # allow plain id string
        query["flight_request_id"] = flight_request_id
    if status:
        query["status"] = status

    schedules = []
    async for s in db.schedules.find(query):
        s["id"] = str(s["_id"])
        del s["_id"]
        schedules.append(s)
    return schedules

# Get schedule by id
@schedule_router.get("/{schedule_id}")
async def get_schedule(schedule_id: str):
    s = await get_schedule_or_404(schedule_id)
    s["id"] = str(s["_id"])
    del s["_id"]
    return s

# Update ETA (dispatcher/superadmin)
@schedule_router.put("/update-eta/{schedule_id}")
async def update_eta(schedule_id: str, payload: UpdateETA, token_data: dict = Depends(verify_token)):
    user = token_data
    if user["role"] not in ["superadmin", "dispatcher"]:
        raise HTTPException(status_code=403, detail="Not authorized to update ETA")

    sched = await get_schedule_or_404(schedule_id)

    now = datetime.utcnow()
    eta_doc = {
        "eta_utc": payload.eta_utc,
        "estimated_duration_minutes": payload.estimated_duration_minutes if payload.estimated_duration_minutes is not None else sched.get("estimated_duration_minutes"),
        "last_updated": now
    }

    await db.schedules.update_one({"_id": objid(schedule_id)}, {"$set": {"eta": eta_doc, "updated_at": now}})

    return {"message": "ETA updated", "eta": eta_doc}

# Update status with validation

@schedule_router.put("/update-status/{schedule_id}")
async def update_schedule_status(schedule_id: str, body: dict, auth=Depends(verify_token)):

    new_status = body["status"]

    # FIX: MUST AWAIT
    schedule = await scheduling_collection.find_one({"_id": ObjectId(schedule_id)})

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    current_status = schedule["status"]

    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {current_status} to {new_status}"
        )

    now = datetime.utcnow()

    # FIX: MUST AWAIT
    await scheduling_collection.update_one(
        {"_id": ObjectId(schedule_id)},
        {
            "$set": {"status": new_status, "updated_at": now},
            "$push": {"status_flow": {"status": new_status, "time": now}}
        }
    )

    return {"success": True, "message": f"Status updated → {new_status}"}


# Assign crew
@schedule_router.put("/assign-crew/{schedule_id}")
async def assign_crew(schedule_id: str, body: AssignCrew, token_data: dict = Depends(verify_token)):
    user = token_data
    if user["role"] not in ["superadmin", "dispatcher"]:
        raise HTTPException(status_code=403, detail="Not authorized to assign crew")

    sched = await get_schedule_or_404(schedule_id)
    now = datetime.utcnow()
    await db.schedules.update_one({"_id": objid(schedule_id)}, {"$set": {"assigned_crew": body.crew, "updated_at": now}})
    return {"message": "Crew assigned", "assigned_crew": body.crew}

# Cancel schedule
@schedule_router.put("/cancel/{schedule_id}")
async def cancel_schedule(schedule_id: str, token_data: dict = Depends(verify_token)):
    user = token_data
    if user["role"] not in ["superadmin", "dispatcher"]:
        raise HTTPException(status_code=403, detail="Not authorized to cancel schedule")

    sched = await get_schedule_or_404(schedule_id)
    current_status = sched.get("status", "Scheduled")

    if current_status == "Completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed schedule")

    now = datetime.utcnow()
    await db.schedules.update_one({"_id": objid(schedule_id)}, {"$set": {"status": "Cancelled", "updated_at": now}})
    # Sync flight_request
    fr_id = sched.get("flight_request_id")
    if fr_id:
        await db.flight_requests.update_one({"_id": objid(fr_id)}, {"$set": {"status": "Cancelled"}})

    return {"message": "Schedule cancelled"}
