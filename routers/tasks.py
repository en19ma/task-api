# routers/tasks.py
# Full CRUD for tasks with filtering, sorting, and pagination

from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from datetime import datetime
from typing import Optional
import math

from database import tasks_col
from models.schemas import TaskCreate, TaskUpdate, TaskOut, TaskList, Priority, Status
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def task_to_out(doc: dict) -> TaskOut:
    """Convert a raw MongoDB document to a TaskOut schema."""
    return TaskOut(
        id=str(doc["_id"]),
        title=doc["title"],
        description=doc.get("description"),
        priority=doc["priority"],
        status=doc["status"],
        due_date=doc.get("due_date"),
        tags=doc.get("tags", []),
        owner_id=str(doc["owner_id"]),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


# ─── CREATE a task ────────────────────────────────────────────
@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(body: TaskCreate, user=Depends(get_current_user)):
    now = datetime.utcnow()
    doc = {
        **body.model_dump(),
        "owner_id": ObjectId(user["_id"]),  # Link task to the logged-in user
        "created_at": now,
        "updated_at": now,
    }
    result = await tasks_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return task_to_out(doc)


# ─── GET all tasks (with filtering, sorting, pagination) ──────
@router.get("/", response_model=TaskList)
async def get_tasks(
    user=Depends(get_current_user),
    # Filtering options — all optional
    status: Optional[Status] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    # Sorting
    sort_by: str = Query("created_at", description="Field to sort by"),
    order: str = Query("desc", description="asc or desc"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page"),
):
    # Always filter by the logged-in user — users only see their own tasks
    query = {"owner_id": ObjectId(user["_id"])}

    # Add optional filters
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if tag:
        query["tags"] = tag  # MongoDB matches if array contains this value
    if search:
        # Case-insensitive text search across title and description
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    sort_direction = -1 if order == "desc" else 1
    skip = (page - 1) * page_size

    # Run count and fetch in parallel would be ideal; keeping it simple here
    total = await tasks_col.count_documents(query)
    cursor = tasks_col.find(query).sort(sort_by, sort_direction).skip(skip).limit(page_size)
    docs = await cursor.to_list(length=page_size)

    return TaskList(
        tasks=[task_to_out(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


# ─── GET a single task ────────────────────────────────────────
@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, user=Depends(get_current_user)):
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await tasks_col.find_one({"_id": oid, "owner_id": ObjectId(user["_id"])})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task_to_out(doc)


# ─── UPDATE a task (PATCH — partial update) ───────────────────
@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, body: TaskUpdate, user=Depends(get_current_user)):
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    # Only update fields that were actually provided
    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    updates["updated_at"] = datetime.utcnow()

    result = await tasks_col.find_one_and_update(
        {"_id": oid, "owner_id": ObjectId(user["_id"])},
        {"$set": updates},
        return_document=True,  # Return the updated document
    )

    if not result:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task_to_out(result)


# ─── DELETE a task ────────────────────────────────────────────
@router.delete("/{task_id}", status_code=200)
async def delete_task(task_id: str, user=Depends(get_current_user)):
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    result = await tasks_col.delete_one({"_id": oid, "owner_id": ObjectId(user["_id"])})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found.")

    return {"message": "Task deleted."}


# ─── GET task stats summary ───────────────────────────────────
@router.get("/stats/summary")
async def get_stats(user=Depends(get_current_user)):
    """Returns a summary: how many tasks per status and per priority."""
    owner_id = ObjectId(user["_id"])

    pipeline = [
        {"$match": {"owner_id": owner_id}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "todo": {"$sum": {"$cond": [{"$eq": ["$status", "todo"]}, 1, 0]}},
                "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
                "done": {"$sum": {"$cond": [{"$eq": ["$status", "done"]}, 1, 0]}},
                "high_priority": {"$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}},
                "overdue": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$ne": ["$status", "done"]},
                                {"$lt": ["$due_date", datetime.utcnow()]},
                                {"$ne": ["$due_date", None]},
                            ]},
                            1, 0
                        ]
                    }
                },
            }
        },
    ]

    result = await tasks_col.aggregate(pipeline).to_list(1)
    if not result:
        return {"total": 0, "todo": 0, "in_progress": 0, "done": 0, "high_priority": 0, "overdue": 0}

    data = result[0]
    data.pop("_id", None)
    return data
