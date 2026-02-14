import os
import asyncio
from aiohttp import web
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
    settings_menu,
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


async def handle_ping(request):
    return web.Response(text="pong")


async def keep_alive(url):
    """Periodically pings the given URL to keep the service alive."""
    if not url:
        logging.info("No RENDER_EXTERNAL_URL found, keep_alive task disabled.")
        return

    logging.info(f"Starting keep_alive task for {url}")
    import aiohttp

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Wait 14 minutes (Render timeout is 15min)
                await asyncio.sleep(14 * 60)
                async with session.get(f"{url}/ping") as response:
                    logging.info(f"Self-ping status: {response.status}")
            except Exception as e:
                logging.error(f"Error in keep_alive: {e}")


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables")

    # Build the Telegram application
    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("mynews", my_news))
    app.add_handler(CommandHandler("mysubscriptions", my_subscriptions))
    app.add_handler(CommandHandler("set_delivery_time", set_delivery_time))
    app.add_handler(CommandHandler("get_delivery_time", get_delivery_time))
    app.add_handler(CommandHandler("settings", settings_menu))

    app.add_handler(CallbackQueryHandler(button))

    # Set up the web server for Render
    web_app = web.Application()
    web_app.router.add_get("/ping", handle_ping)

    port = int(os.getenv("PORT", 8080))
    external_url = os.getenv("RENDER_EXTERNAL_URL")

    async def start_services():
        # Start the Telegram bot in polling mode
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        # Start the keep_alive pinger
        asyncio.create_task(keep_alive(external_url))

        # Start the web server
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        print(f"Web server started on port {port}")
        await site.start()

        # Keep the loop running
        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()

    asyncio.run(start_services())


if __name__ == "__main__":
    main()
