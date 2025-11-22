from fastapi import APIRouter, HTTPException, Header, Depends
from database import db
from models.flight_request import FlightRequest
from utils import decode_token
from bson import ObjectId
from datetime import datetime

flight_router = APIRouter()


# ============================
# AUTH MIDDLEWARE
# ============================
def get_current_user(token: str = Header(...)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# ============================
# CREATE FLIGHT REQUEST
# ============================
@flight_router.post("/create-flight-request")
async def create_flight_request(request: FlightRequest, current_user: dict = Depends(get_current_user)):

    # Combine date + time into MongoDB safe datetime
    combined_dt = datetime.combine(request.flight_date, request.flight_time)

    request_dict = request.dict()
    request_dict["status"] = "Pending"
    request_dict["flight_datetime"] = combined_dt  # <-- MongoDB-safe field

    # Remove original fields (optional, but recommended)
    del request_dict["flight_date"]
    del request_dict["flight_time"]

    # Insert into DB
    result = await db.flight_requests.insert_one(request_dict)

    return {
        "id": str(result.inserted_id),
        "message": "Flight request created",
        "flight_datetime": combined_dt.isoformat()
    }


# ============================
# APPROVE / DISPATCH FLIGHT REQUEST
# ============================
@flight_router.put("/approve-flight-request/{request_id}")
async def approve_flight_request(request_id: str, current_user: dict = Depends(get_current_user)):

    # Role validation
    if current_user["role"] not in ["superadmin", "dispatcher"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate request ID format
    if not ObjectId.is_valid(request_id):
        raise HTTPException(status_code=400, detail="Invalid request ID")

    # Check if request exists
    flight_request = await db.flight_requests.find_one({"_id": ObjectId(request_id)})
    if not flight_request:
        raise HTTPException(status_code=404, detail="Flight request not found")

    # Only allow approval of pending requests
    if flight_request.get("status") != "Pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    # Update status to APPROVED
    await db.flight_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": "Approved",
            "approved_by": current_user["email"],
            "approved_at": datetime.utcnow()
        }}
    )

    return {"message": "Flight request approved successfully"}


# ============================
# LIST FLIGHT REQUESTS
# ============================
@flight_router.get("/list-flight-requests")
async def list_flight_requests():
    requests = []
    async for fr in db.flight_requests.find():
        fr["id"] = str(fr["_id"])
        del fr["_id"]
        requests.append(fr)
    return requests
