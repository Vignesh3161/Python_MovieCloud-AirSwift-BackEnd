from fastapi import FastAPI
from routes.auth_routes import auth_router
from routes.flight_routes import flight_router
from routes.ambulance_routes import ambulance_router
from routes.aircraft_routes import aircraft_router 
from routes.schedule_routes import schedule_router # ✅ added

app = FastAPI(title="Air Ambulance Backend")

app.include_router(auth_router, prefix="/api/auth")
app.include_router(flight_router, prefix="/api/flight")
app.include_router(ambulance_router, prefix="/api/ambulance")
app.include_router(aircraft_router, prefix="/api/aircraft")
app.include_router(schedule_router, prefix="/api/schedule") # ✅ added

@app.get("/")
async def root():
    return {"message": "Air Ambulance Backend Running"}
