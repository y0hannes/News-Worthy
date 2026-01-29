import aiosqlite
import logging
from enum import Enum

LOGGER = logging.getLogger(__name__)
DB_PATH = "news.db"


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
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                url TEXT,
                published_at TEXT,
                topic TEXT,
                fetched_at TEXT
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                topic TEXT,
                PRIMARY KEY (user_id, topic)
            );
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                delivery_hour INTEGER DEFAULT 9,
                delivery_minute INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.commit()


async def save_user(user) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user.id, user.username),
            )
            await conn.commit()
            return True
    except Exception as e:
        LOGGER.error(f"Error saving user {user.id}: {e}")
        return False


async def fetch_my_subscriptions(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT topic FROM subscriptions WHERE user_id = ?", (user_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def subscribe_to_topic(topic: NewsTopics, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "INSERT OR IGNORE INTO subscriptions (user_id, topic) VALUES (?, ?)",
            (user_id, topic.value),
        )
        await conn.commit()
        return cursor.rowcount > 0


async def unsubscribe_from_topic(user_id: int, topic: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "DELETE FROM subscriptions WHERE user_id = ? AND topic = ?",
            (user_id, topic),
        )
        await conn.commit()
        return cursor.rowcount > 0


async def set_schedule_delivery_time(user_id: int, hour: int, minute: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "UPDATE users SET delivery_hour = ?, delivery_minute = ? WHERE user_id = ?",
            (hour, minute, user_id),
        )
        await conn.commit()
        return cursor.rowcount > 0


async def get_scheduled_time(user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT delivery_hour, delivery_minute FROM users WHERE user_id = ?",
            (user_id,),
        )
        return await cursor.fetchone()


async def get_users_by_delivery_time(hour: int, minute: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT user_id FROM users WHERE delivery_hour = ? AND delivery_minute = ?",
            (hour, minute),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
