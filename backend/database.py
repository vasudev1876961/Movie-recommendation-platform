import logging
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

logger = logging.getLogger("uvicorn.error")

client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.database_name]

# Helper to access collections easily
users_collection = db["users"]
watchlist_collection = db["watchlists"]

async def check_db_connection():
    try:
        # Ping the server to check connectivity
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB server.")
        return True
    except Exception as e:
        logger.warning(f"CRITICAL: Failed to connect to MongoDB at {settings.mongodb_url}. Ensure MongoDB is running. Error: {e}")
        return False
