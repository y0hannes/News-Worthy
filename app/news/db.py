import logging
import os
from enum import Enum
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

LOGGER = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    LOGGER.warning("SUPABASE_URL or SUPABASE_KEY not found in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


class NewsTopics(Enum):
    GENERAL = "general"
    WORLD = "world"
    NATION = "nation"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    SCIENCE = "science"
    HEALTH = "health"


async def init_db():
    """
    Supabase schema is managed via the Supabase dashboard.
    This function remains for compatibility but doesn't perform SQL execution.
    """
    if not supabase:
        LOGGER.error("Supabase client not initialized.")
        return
    LOGGER.info("Supabase client initialized.")


async def save_user(user) -> bool:
    try:
        data = {
            "user_id": user.id,
            "username": user.username,
        }
        # upsert with ignore-like behavior (Supabase upsert by default updates but we can use it to ensure user exists)
        supabase.table("users").upsert(data, on_conflict="user_id").execute()
        return True
    except Exception as e:
        LOGGER.error(f"Error saving user {user.id}: {e}")
        return False


async def fetch_my_subscriptions(user_id: int) -> list[str]:
    try:
        response = supabase.table("subscriptions").select("topic").eq("user_id", user_id).execute()
        return [row["topic"] for row in response.data]
    except Exception as e:
        LOGGER.error(f"Error fetching subscriptions for {user_id}: {e}")
        return []


async def subscribe_to_topic(topic: NewsTopics, user_id: int) -> bool:
    try:
        data = {"user_id": user_id, "topic": topic.value}
        supabase.table("subscriptions").upsert(data, on_conflict="user_id,topic").execute()
        return True
    except Exception as e:
        LOGGER.error(f"Error subscribing to topic {topic.value} for {user_id}: {e}")
        return False


async def unsubscribe_from_topic(user_id: int, topic: str) -> bool:
    try:
        supabase.table("subscriptions").delete().eq("user_id", user_id).eq("topic", topic).execute()
        return True
    except Exception as e:
        LOGGER.error(f"Error unsubscribing from topic {topic} for {user_id}: {e}")
        return False


async def set_schedule_delivery_time(user_id: int, hour: int, minute: int) -> bool:
    try:
        data = {"delivery_hour": hour, "delivery_minute": minute}
        supabase.table("users").update(data).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        LOGGER.error(f"Error setting schedule for {user_id}: {e}")
        return False


async def get_scheduled_time(user_id: int):
    try:
        response = supabase.table("users").select("delivery_hour, delivery_minute").eq("user_id", user_id).execute()
        if response.data:
            row = response.data[0]
            return (row["delivery_hour"], row["delivery_minute"])
        return None
    except Exception as e:
        LOGGER.error(f"Error getting scheduled time for {user_id}: {e}")
        return None


async def get_users_by_delivery_time(hour: int, minute: int) -> list[int]:
    try:
        response = supabase.table("users").select("user_id").eq("delivery_hour", hour).eq("delivery_minute", minute).execute()
        return [row["user_id"] for row in response.data]
    except Exception as e:
        LOGGER.error(f"Error fetching users by delivery time: {e}")
        return []
