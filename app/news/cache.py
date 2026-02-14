from datetime import datetime, timedelta
import logging
from .db import NewsTopics, supabase
from .api import fetch_news

LOGGER = logging.getLogger(__name__)
CACHE_DURATION = timedelta(hours=1)


async def store_news(topic: NewsTopics, articles: list[dict]):
    if not supabase:
        LOGGER.error("Supabase client not initialized.")
        return
    try:
        fetched_at = datetime.now().isoformat()
        rows = []
        for article in articles:
            rows.append({
                "title": article.get("title"),
                "content": article.get("content"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "topic": topic.value,
                "fetched_at": fetched_at,
            })
        if rows:
            supabase.table("news").insert(rows).execute()
    except Exception as e:
        LOGGER.error(f"Error storing news: {e}")


async def get_cached_news(topic: NewsTopics, limit=10) -> list[str]:
    if not supabase:
        LOGGER.error("Supabase client not initialized.")
        return []
    try:
        response = supabase.table("news") \
            .select("title, url") \
            .eq("topic", topic.value) \
            .order("published_at", desc=True) \
            .limit(limit) \
            .execute()
        return [f"• {row['title']}\n{row['url']}" for row in response.data]
    except Exception as e:
        LOGGER.error(f"Error getting cached news: {e}")
        return []


async def get_last_fetch_time(topic: NewsTopics) -> datetime | None:
    if not supabase:
        return None
    try:
        response = (
            supabase.table("news")
            .select("fetched_at")
            .eq("topic", topic.value)
            .order("fetched_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return datetime.fromisoformat(response.data[0]["fetched_at"])
        return None
    except Exception as e:
        LOGGER.error(f"Error getting last fetch time for {topic.value}: {e}")
        return None


async def fetch_and_store_news(topic: NewsTopics) -> list[str]:
    articles = await fetch_news(topic)
    if articles:
        await store_news(topic, articles)
        return [f"• {a['title']}\n{a['url']}" for a in articles]
    return []
