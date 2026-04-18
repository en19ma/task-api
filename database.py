# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.task_manager

users_col = db.users
tasks_col = db.tasks
