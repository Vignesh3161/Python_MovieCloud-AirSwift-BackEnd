from pydantic import BaseModel, EmailStr
from typing import Optional

# For Registration (role required)
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str  # superadmin, dispatcher, medical_staff

# For Login (role optional)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Response model
class UserOut(BaseModel):
    id: Optional[str]
    email: EmailStr
    role: str
