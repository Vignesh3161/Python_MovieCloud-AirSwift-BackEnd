from fastapi import APIRouter, HTTPException
from models.user import UserRegister, UserLogin
from database import db
from utils import hash_password, verify_password, create_access_token


auth_router = APIRouter()

# Registration (role required)
@auth_router.post("/register")
async def register(user: UserRegister):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    await db.users.insert_one(user_dict)
    return {"message": "User registered successfully"}

# Login (role NOT required)
@auth_router.post("/login")
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"email": db_user["email"], "role": db_user["role"]})
    return {"access_token": token}
