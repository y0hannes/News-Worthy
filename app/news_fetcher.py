import os
import aiohttp
import aiosqlite
import logging
from enum import Enum
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram.ext import Application

# setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

load_dotenv()


class NewsTopics(Enum):
    GENERAL = 'general'
    WORLD = 'world'
    NATION = 'nation'
    BUSINESS = 'business'
    TECHNOLOGY = 'technology'
    ENTERTAINMENT = 'entertainment'
    SPORTS = 'sports'
    SCIENCE = 'science'
    HEALTH = 'health'


CACHE_DURATION = timedelta(hours=1)


async def init_db(application: Application):
    async with aiosqlite.connect("news.db") as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at TEXT NOT NULL,
                topic TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                topic TEXT,
                PRIMARY KEY (user_id, topic)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                delivery_hour INTEGER DEFAULT 9,
                delivery_minute INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await conn.commit()

NEWS_API_TOKEN = os.getenv('NEWS_API_TOKEN')

if not NEWS_API_TOKEN:
    LOGGER.error("API TOKEN not found.")

ENDPOINT = 'https://gnews.io/api/v4/search'


async def save_user(user):
    try:
        async with aiosqlite.connect("news.db") as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user.id, user.username)
            )
            await conn.commit()
            return True
    except aiosqlite.Error as e:
        LOGGER.error(
            f"Error adding user with user id {user.id} to users database: {e}")
        return False


async def fetch_and_store_news(topic: NewsTopics, max_articles=10):
    params = {
        'q': topic.value,
        'lang': 'en',
        'max': max_articles,
        'token': NEWS_API_TOKEN
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ENDPOINT, params=params) as res:
                res.raise_for_status()
                data = await res.json()
    except aiohttp.ClientError as e:
        LOGGER.error(f"Error fetching news for topic '{topic.value}': {e}")
        return []

    articles = data.get('articles', [])
    if not articles:
        LOGGER.info(f"No articles found for topic '{topic.value}'.")
        return []

    headlines_to_return = []
    async with aiosqlite.connect("news.db") as conn:
        fetched_at = datetime.now().isoformat()

        for article in articles:
            title = article.get('title')
            url = article.get('url')
            published_at = article.get('publishedAt')
            content = article.get('content')

            await conn.execute('''
                INSERT INTO news (title, content, url, published_at, topic, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, url, published_at, topic.value, fetched_at))

            headlines_to_return.append(f"• {title}\n{url}")
        await conn.commit()

    LOGGER.info(
        f"Successfully fetched and stored {len(articles)} articles for topic '{topic.value}'.")
    return headlines_to_return


async def get_cached_news(topic: NewsTopics, limit=5):
    async with aiosqlite.connect("news.db") as conn:
        cursor = await conn.cursor()

        cutoff_time = datetime.now() - CACHE_DURATION
        # cursor.execute("DELETE FROM news WHERE fetched_at < ?", (cutoff_time.isoformat(),))

        await cursor.execute('''
            SELECT title, url FROM news
            WHERE topic =? 
            ORDER BY published_at DESC
            LIMIT ?
        ''', (topic.value, limit))
        results = await cursor.fetchall()

    return [f"• {title}\n{url}" for title, url in results]


async def subscribe_to_topic(topic: NewsTopics, user_id: int) -> bool:
    try:
        async with aiosqlite.connect("news.db") as conn:
            cursor = await conn.execute("INSERT OR IGNORE INTO subscriptions (user_id, topic) VALUES (?, ?)", (user_id, topic.value))
            await conn.commit()
            return cursor.rowcount > 0  # Returns True if a new row was inserted
    except aiosqlite.Error as e:
        LOGGER.error(
            f"Error subscribing user {user_id} to topic '{topic.value}': {e}")
        return False


async def fetch_my_subscriptions(user_id: int):
    try:
        async with aiosqlite.connect("news.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT topic FROM subscriptions WHERE user_id = ?", (user_id,))
            return [row[0] for row in await cursor.fetchall()]
    except aiosqlite.Error as e:
        LOGGER.error(f"Error fetching subscriptions for user {user_id}: {e}")
        return []


async def unsubscribe_from_topic(user_id: int, topic: str) -> bool:
    try:
        async with aiosqlite.connect("news.db") as conn:
            cursor = await conn.execute(
                "DELETE FROM subscriptions WHERE user_id = ? AND topic = ?",
                (user_id, topic)
            )
            await conn.commit()
            return cursor.rowcount > 0  # True if something was deleted
    except aiosqlite.Error as e:
        LOGGER.error(
            f"Error unsubscribing user {user_id} from topic '{topic}': {e}")
        return False


async def get_all_subscribed_users():
    try:
        async with aiosqlite.connect("news.db") as conn:
            cursor = await conn.execute("SELECT  user_id FROM users")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    except aiosqlite.Error as e:
        LOGGER.error(f"Error fetching subscribed users: {e}")
        return []
