from datetime import datetime, timedelta
import aiosqlite
from .db import NewsTopics, DB_PATH
from .api import fetch_news

CACHE_DURATION = timedelta(hours=1)


async def store_news(topic: NewsTopics, articles: list[dict]):
    async with aiosqlite.connect(DB_PATH) as conn:
        fetched_at = datetime.now().isoformat()
        for article in articles:
            await conn.execute(
                "INSERT INTO news (title, content, url, published_at, topic, fetched_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    article.get("title"),
                    article.get("content"),
                    article.get("url"),
                    article.get("publishedAt"),
                    topic.value,
                    fetched_at,
                ),
            )
        await conn.commit()


async def get_cached_news(topic: NewsTopics, limit=5) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "SELECT title, url FROM news WHERE topic=? ORDER BY published_at DESC LIMIT ?",
            (topic.value, limit),
        )
        rows = await cursor.fetchall()
        return [f"• {title}\n{url}" for title, url in rows]


async def fetch_and_store_news(topic: NewsTopics) -> list[str]:
    articles = await fetch_news(topic)
    if articles:
        await store_news(topic, articles)
        return [f"• {a['title']}\n{a['url']}" for a in articles]
    return []
