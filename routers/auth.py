# routers/auth.py
# Registration and login endpoints

from fastapi import APIRouter, HTTPException
from bson import ObjectId

from database import users_col
from models.schemas import UserRegister, UserLogin, TokenResponse, UserOut
from middleware.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister):
    # Check email not already taken
    if await users_col.find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="Email already registered.")

    if await users_col.find_one({"username": body.username}):
        raise HTTPException(status_code=409, detail="Username already taken.")

    user_doc = {
        "username": body.username,
        "email": body.email,
        "password": hash_password(body.password),
    }

    result = await users_col.insert_one(user_doc)
    token = create_access_token(str(result.inserted_id))

    return {"access_token": token}


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = await users_col.find_one({"email": body.email})

    # Intentionally vague error — don't reveal which field is wrong
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(str(user["_id"]))
    return {"access_token": token}


@router.get("/me", response_model=UserOut)
async def get_me(user=__import__("fastapi").Depends(__import__("middleware.auth", fromlist=["get_current_user"]).get_current_user)):
    return UserOut(id=str(user["_id"]), username=user["username"], email=user["email"])
