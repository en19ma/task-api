# main.py — Task Management API

from fastapi import FastAPI
from database import users_col, tasks_col
from routers import auth, tasks as task_router

app = FastAPI(
    title="Task Management API",
    description="A production-style task manager with auth, filtering, pagination, and stats.",
    version="1.0.0"
)

@app.on_event("startup")
async def create_indexes():
    # Speed up common queries
    await users_col.create_index("email", unique=True)
    await users_col.create_index("username", unique=True)
    await tasks_col.create_index("owner_id")
    await tasks_col.create_index([("owner_id", 1), ("status", 1)])
    await tasks_col.create_index([("owner_id", 1), ("priority", 1)])
    await tasks_col.create_index([("owner_id", 1), ("due_date", 1)])
    print("✅ Indexes created")

app.include_router(auth.router)
app.include_router(task_router.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
