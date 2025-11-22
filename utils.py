from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Header, UploadFile
from bson import ObjectId
import os
from dotenv import load_dotenv
import shutil
import uuid

# Load environment variables
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 160

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ------------------------------------------
# JWT TOKEN FUNCTIONS
# ------------------------------------------
def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    """Create JWT Access Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ------------------------------------------
# PASSWORD FUNCTIONS
# ------------------------------------------
def hash_password(password: str) -> str:
    """Hash the given password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


# ------------------------------------------
# FASTAPI TOKEN VERIFICATION DEPENDENCY
# ------------------------------------------
async def verify_token(token: str = Header(...)):
    """Verify token for protected routes"""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# ------------------------------------------
# FILE UPLOAD FUNCTION
# ------------------------------------------
def save_uploaded_file(upload_file: UploadFile, folder: str = "uploads"):
    """Save uploaded file and return file path"""
    os.makedirs(folder, exist_ok=True)  # Ensure folder exists

    # Create unique filename
    ext = upload_file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(folder, new_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path


# ------------------------------------------
# OBJECTID SERIALIZER (FULL RECURSIVE)
# ------------------------------------------
def serialize_doc(doc):
    """Recursively convert MongoDB ObjectIds to strings."""
    if not doc:
        return doc

    # If list → process each item
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]

    # If dict → convert values
    if isinstance(doc, dict):
        new_doc = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                new_doc[key] = str(value)
            elif isinstance(value, (dict, list)):
                new_doc[key] = serialize_doc(value)
            else:
                new_doc[key] = value
        return new_doc

    return doc
