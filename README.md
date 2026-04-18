# ✅ Task Management API

A production-style REST API for managing personal tasks, built with **Python**, **FastAPI**, and **MongoDB**.

## What This Demonstrates
- Full **JWT authentication** — each user only sees their own tasks
- **PATCH semantics** — partial updates, only changes what you send
- **Filtering** by status, priority, tag, and free-text search
- **Sorting** by any field, ascending or descending
- **Pagination** with total count and total pages
- **MongoDB aggregation pipeline** for stats summary
- Compound indexes for efficient multi-field queries
- Clean router/schema separation (production-grade structure)

## Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/api/auth/register` | None | Register |
| POST | `/api/auth/login` | None | Login |
| GET | `/api/auth/me` | Bearer | My profile |
| POST | `/api/tasks/` | Bearer | Create task |
| GET | `/api/tasks/` | Bearer | List tasks (filter/sort/paginate) |
| GET | `/api/tasks/{id}` | Bearer | Get one task |
| PATCH | `/api/tasks/{id}` | Bearer | Update task (partial) |
| DELETE | `/api/tasks/{id}` | Bearer | Delete task |
| GET | `/api/tasks/stats/summary` | Bearer | Task stats |

## Query Parameters for GET /api/tasks/

| Param | Type | Example | Description |
|-------|------|---------|-------------|
| `status` | string | `todo` | Filter by status (todo/in_progress/done) |
| `priority` | string | `high` | Filter by priority (low/medium/high) |
| `tag` | string | `backend` | Filter by tag |
| `search` | string | `auth` | Search title/description |
| `sort_by` | string | `due_date` | Field to sort by |
| `order` | string | `asc` | Sort direction |
| `page` | int | `2` | Page number |
| `page_size` | int | `20` | Results per page (max 100) |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for the Swagger UI.

## Example: Create a Task

```http
POST /api/tasks/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Build auth system",
  "priority": "high",
  "status": "in_progress",
  "due_date": "2025-08-01T12:00:00",
  "tags": ["backend", "auth"]
}
```

## Example: Filtered + Paginated Query
```
GET /api/tasks/?status=todo&priority=high&search=auth&sort_by=due_date&order=asc&page=1&page_size=10
```

## Folder Structure
```
4-task-api/
├── main.py              # App entry point + startup
├── database.py          # MongoDB connection
├── models/
│   └── schemas.py       # All Pydantic schemas + enums
├── middleware/
│   └── auth.py          # JWT + password hashing + auth dependency
├── routers/
│   ├── auth.py          # Register, login, me
│   └── tasks.py         # Full CRUD + stats
├── requirements.txt
└── .env.example
```
