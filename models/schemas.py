# models/schemas.py
# All Pydantic schemas for request/response validation

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


# ─── Auth Schemas ─────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    username: str
    email: str


# ─── Task Schemas ─────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Priority = Priority.medium
    status: Status = Status.todo
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Build authentication system",
                "description": "Implement JWT login and registration",
                "priority": "high",
                "status": "in_progress",
                "due_date": "2025-08-01T12:00:00",
                "tags": ["backend", "auth"]
            }
        }

class TaskUpdate(BaseModel):
    # All fields optional — only update what's provided (PATCH behaviour)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None

class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    due_date: Optional[datetime]
    tags: List[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime

class TaskList(BaseModel):
    tasks: List[TaskOut]
    total: int
    page: int
    page_size: int
    total_pages: int
