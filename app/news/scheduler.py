from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .db import get_users_by_delivery_time, fetch_my_subscriptions, NewsTopics
from .cache import get_cached_news, fetch_and_store_news, get_last_fetch_time
import logging

LOGGER = logging.getLogger(__name__)
UPDATE_CUTOFF = timedelta(minutes=144)


async def send_scheduled_news(app):
    now = datetime.now()
    users = await get_users_by_delivery_time(now.hour, now.minute)
    for user_id in users:
        topics = await fetch_my_subscriptions(user_id)
        messages = []
        for topic_value in topics:
            try:
                topic = NewsTopics(topic_value)
                headlines = await get_cached_news(topic)
                if not headlines:
                    headlines = await fetch_and_store_news(topic)
                if headlines:
                    messages.append(f"**{topic.name}**\n" + "\n\n".join(headlines))
            except Exception as e:
                LOGGER.error(f"Error sending news for {topic_value} to {user_id}: {e}")
        if messages:
            try:
                await app.bot.send_message(chat_id=user_id, text="\n\n".join(messages))
            except Exception as e:
                LOGGER.error(f"Failed to send news to {user_id}: {e}")


async def periodic_news_update():
    """
    Background task to ensure each news topic is refreshed at least every 144 minutes.
    This stays within the 100 requests/day limit (9 topics * 24h / 144min = 90 requests/day).
    """
    LOGGER.info("Checking for periodic news updates...")
    for topic in NewsTopics:
        try:
            last_fetch = await get_last_fetch_time(topic)
            if not last_fetch or (datetime.now() - last_fetch) > UPDATE_CUTOFF:
                LOGGER.info(f"Updating news for topic: {topic.value}")
                await fetch_and_store_news(topic)
        except Exception as e:
            LOGGER.error(f"Error in periodic update for {topic.value}: {e}")


async def setup_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_scheduled_news, "cron", minute="*", args=[app])
    # Check every 10 minutes if any topic needs an update
    scheduler.add_job(periodic_news_update, "interval", minutes=10)
    scheduler.start()
