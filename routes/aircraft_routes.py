from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from models.aircraft import Aircraft, MaintenanceRecord, UpdateMaintenanceStatus, AddMaintenance
from database import db
from utils import verify_token, serialize_doc

aircraft_router = APIRouter()


# ---------------------------------------------------------
# 1️⃣ CREATE AIRCRAFT (SuperAdmin Only)
# ---------------------------------------------------------
@aircraft_router.post("/create-aircraft")
async def create_aircraft(aircraft: Aircraft, token_data: dict = Depends(verify_token)):
    if token_data["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can create aircraft")

    aircraft_dict = aircraft.dict()
    aircraft_dict.pop("id", None)  # Remove optional id field

    result = await db.aircrafts.insert_one(aircraft_dict)

    return {"id": str(result.inserted_id), "message": "Aircraft added successfully"}



# ---------------------------------------------------------
# 2️⃣ ADD MAINTENANCE RECORD (SuperAdmin Only)
# ---------------------------------------------------------
@aircraft_router.post("/add-maintenance/{aircraft_id}")
async def add_maintenance(
    aircraft_id: str,       # path parameter
    data: AddMaintenance,   # JSON body
    token_data: dict = Depends(verify_token)
):
    if token_data["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can add maintenance")

    maintenance_record = {
        "_id": ObjectId(),
        "maintenance_type": data.maintenance_type,
        "description": data.description,
        "last_maintenance_date": data.last_maintenance_date,
        "next_due_date": data.next_due_date,
        "status": data.status,
        "technician": data.technician
    }

    update_result = await db.aircrafts.update_one(
        {"_id": ObjectId(aircraft_id)},
        {
            "$push": {"maintenance_records": maintenance_record},
            "$set": {
                "last_maintenance_date": data.last_maintenance_date,
                "available": False
            }
        }
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    return {
        "message": "Maintenance added & aircraft marked unavailable",
        "record_id": str(maintenance_record["_id"])
    }

# ---------------------------------------------------------

@aircraft_router.put("/update-maintenance-status/{aircraft_id}/{record_id}")
async def update_maintenance_status(
    aircraft_id: str,
    record_id: str,
    data: UpdateMaintenanceStatus,
    token_data: dict = Depends(verify_token)
):
    if token_data["role"] != ["superadmin", "technician"]:
        raise HTTPException(status_code=403, detail="Only superadmin can update maintenance status")

    update_result = await db.aircrafts.update_one(
        {
            "_id": ObjectId(aircraft_id),
            "maintenance_records._id": ObjectId(record_id)
        },
        {
            "$set": {
                "maintenance_records.$.status": data.status
            }
        }
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Aircraft or maintenance record not found")

    return {"message": f"Maintenance record status updated to {data.status}"}




# 4️⃣ MARK AIRCRAFT AS AVAILABLE
# ---------------------------------------------------------
@aircraft_router.put("/aircraft/{aircraft_id}/available")
async def mark_aircraft_available(aircraft_id: str, token_data: dict = Depends(verify_token)):
    if token_data["role"] not in ["superadmin", "dispatcher"]:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.aircrafts.update_one(
        {"_id": ObjectId(aircraft_id)},
        {"$set": {"available": True}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    return {"message": "Aircraft is now available"}
# ---------------------------------------------------------



@aircraft_router.get("/available-aircrafts")
async def list_available_aircrafts():
    aircrafts = []
    async for ac in db.aircrafts.find({"available": True}):
        aircrafts.append(serialize_doc(ac))
    return aircrafts

@aircraft_router.get("/list-aircrafts")
async def list_all_aircrafts():
    aircrafts = []
    async for ac in db.aircrafts.find():
        aircrafts.append(serialize_doc(ac))
    return aircrafts
# ---------------------------------------------------------

@aircraft_router.delete("/delete/{aircraft_id}")
async def delete_aircraft(aircraft_id: str, token_data: dict = Depends(verify_token)):

    # Only superadmin can delete
    if token_data["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can delete aircraft")

    # Validate ObjectId format
    if not ObjectId.is_valid(aircraft_id):
        raise HTTPException(status_code=400, detail="Invalid aircraft ID format")

    # Delete aircraft
    result = await db.aircrafts.delete_one({"_id": ObjectId(aircraft_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    return {"message": "Aircraft deleted successfully"}

# ---------------------------------------------------------

# @aircraft_router.post("/aircraft/upload-image/{aircraft_id}")
# async def upload_aircraft_image(
#     aircraft_id: str,
#     file: UploadFile,
#     token_data: dict = Depends(verify_token)
# ):

#     if token_data["role"] != "superadmin":
#         raise HTTPException(status_code=403, detail="Only superadmin can upload")

#     file_path = save_uploaded_file(file, folder="aircraft_uploads")

#     await db.aircrafts.update_one(
#         {"_id": ObjectId(aircraft_id)},
#         {"$set": {"image_url": file_path}}
#     )

#     return {"message": "Image uploaded successfully", "path": file_path}


