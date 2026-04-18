# middleware/auth.py
# JWT creation and verification for FastAPI using python-jose

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bson import ObjectId
import os

from database import users_col

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Bcrypt context for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    FastAPI dependency — inject this into any route that needs auth.
    Usage: async def my_route(user=Depends(get_current_user))
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise credentials_exception

    return user
