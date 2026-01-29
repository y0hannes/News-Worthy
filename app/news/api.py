import os
import aiohttp
import logging
from .db import NewsTopics

LOGGER = logging.getLogger(__name__)
NEWS_API_TOKEN = os.getenv("NEWS_API_TOKEN")
ENDPOINT = "https://gnews.io/api/v4/search"


async def fetch_news(topic: NewsTopics, max_articles=10) -> list[dict]:
    if not NEWS_API_TOKEN:
        LOGGER.error("NEWS_API_TOKEN not found.")
        return []
    params = {
        "q": topic.value,
        "lang": "en",
        "max": max_articles,
        "token": NEWS_API_TOKEN,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ENDPOINT, params=params) as res:
                res.raise_for_status()
                return (await res.json()).get("articles", [])
    except Exception as e:
        LOGGER.error(f"Error fetching news for {topic.value}: {e}")
        return []
