import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers import (
    start,
    help_command,
    news,
    subscribe,
    my_news,
    my_subscriptions,
    set_delivery_time,
    get_delivery_time,
    button,
)
from news.db import init_db
from news.scheduler import setup_scheduler
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


logging.getLogger("telegram").setLevel(logging.INFO)
logging.getLogger("apscheduler").setLevel(logging.INFO)


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in environment variables")


async def post_init(app):
    await init_db()
    await setup_scheduler(app)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("mynews", my_news))
    app.add_handler(CommandHandler("mysubscriptions", my_subscriptions))
    app.add_handler(CommandHandler("set_delivery_time", set_delivery_time))
    app.add_handler(CommandHandler("get_delivery_time", get_delivery_time))

    app.add_handler(CallbackQueryHandler(button))

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
