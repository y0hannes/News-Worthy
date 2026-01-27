import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from news_fetcher import (
    init_db,
    save_user,
    fetch_and_store_news,
    get_cached_news,
    NewsTopics,
    send_scheduled_news,
    subscribe_to_topic,
    fetch_my_subscriptions,
    unsubscribe_from_topic,
    set_schedule_delivery_time,
    get_scheduled_time,
)
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_TOKEN = os.getenv("NEWS_API_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in environment variables")
if not NEWS_API_TOKEN:
    raise ValueError("No NEWS_API_KEY found in environment variables")

# commands


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_saved = await save_user(user)
    if user_saved:
        await update.message.reply_text(f"Hello, {user.first_name}!")
    else:
        await update.message.reply_text(f"Hello, {user.first_name}, There was a problem registering you \n please try again!")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Here are the commands supported by our bot:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/news - Get your news feed\n"
        "/mynews - To get all the news tailored to your subscriptions\n"
        "/subscribe - Subscribe to a news topic\n"
        "/mysubscriptions - To see all the topics you subscribed to \n"
        "/set_delivery_time <HH:MM> - Set your daily news delivery time (24h format)"
    )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(topic.name, callback_data=f"news:{topic.value}")] for topic in NewsTopics
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose a topic:', reply_markup=reply_markup)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(topic.name, callback_data=f"subscribe:{topic.value}")] for topic in NewsTopics
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose a topic to subscribe to:', reply_markup=reply_markup)


async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    topics = await fetch_my_subscriptions(user_id)

    if not topics:
        await update.message.reply_text("You are not subscribed to any topics.")
        return

    keyboard = [
        [InlineKeyboardButton(
            f"❌ Unsubscribe from {NewsTopics(topic).name}", callback_data=f"unsubscribe:{topic}")]
        for topic in topics
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Your current subscriptions:", reply_markup=reply_markup)


async def my_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    topics = await fetch_my_subscriptions(user_id)

    if not topics:
        await update.message.reply_text("You are not subscribed to any topics. Use /subscribe to start.")
        return

    response = []
    for topic_value in topics:
        try:
            topic = NewsTopics(topic_value)
            headlines = await get_cached_news(topic)
            if not headlines:
                headlines = await fetch_and_store_news(topic)
            if headlines:
                response.append(f"**{topic.name}**\n" + "\n\n".join(headlines))
        except ValueError:
            continue

    if response:
        await update.message.reply_text("\n\n".join(response))
    else:
        await update.message.reply_text("No news available for your subscribed topics.")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("news:"):
        topic_value = data.split(":", 1)[1]
        try:
            topic = NewsTopics(topic_value)
        except ValueError:
            await query.edit_message_text(text="Invalid topic selected.")
            return

        headlines = await get_cached_news(topic)

        if not headlines:
            await query.edit_message_text(text=f"No cached news for '{topic.value}'. Fetching fresh articles now...")
            headlines = await fetch_and_store_news(topic)

        if not headlines:
            await query.edit_message_text(text=f"Sorry, couldn't fetch any news for '{topic.value}' at the moment.")
        else:
            await query.edit_message_text(text="\n\n".join(headlines))

    elif data.startswith("subscribe:"):
        topic_value = data.split(":", 1)[1]
        try:
            topic = NewsTopics(topic_value)
        except ValueError:
            await query.edit_message_text(text="Invalid topic selected.")
            return

        user_id = query.from_user.id

        isSubscribed = await subscribe_to_topic(topic, user_id)
        if isSubscribed:
            await query.edit_message_text(text=f"You have subscribed to '{topic.name}'.")
        else:
            await query.edit_message_text(text=f"Failed to subscribe to topic  '{topic.name}'.")

    elif data.startswith("unsubscribe:"):
        topic_value = data.split(":", 1)[1]
        user_id = query.from_user.id

        success = await unsubscribe_from_topic(user_id, topic_value)
        if success:
            await query.edit_message_text(text=f"You have unsubscribed from {NewsTopics(topic_value).name}.")
        else:
            await query.edit_message_text(text="You were not subscribed to this topic or an error occurred.")


async def set_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Please provide a time in HH:MM format. Example: /set_delivery_time 09:30")
        return

    time_str = context.args[0]
    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid time format. Please use HH:MM (24-hour format). Example: 09:30")
        return

    success = await set_schedule_delivery_time(user_id, hour, minute)
    if success:
        await update.message.reply_text(f"Your daily news delivery time has been set to {hour:02d}:{minute:02d}.")
    else:
        await update.message.reply_text("Failed to set delivery time. Please try again later.")


async def get_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    result = await get_scheduled_time(user_id)

    if not result:
        await update.message.reply_text("Failed to get scheduled delivery time")
        return

    hour, minute = result
    await update.message.reply_text(f"Your scheduled delivery time is at {hour}:{minute}. \nuse /set_delivery_time to change it")
    return


async def post_init(app) -> None:
    await init_db(app)

    # Scheduler runs every minute
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_scheduled_news, "cron", minute="*", args=[app])
    scheduler.start()


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('news', news))
    app.add_handler(CommandHandler('subscribe', subscribe))
    app.add_handler(CommandHandler('mynews', my_news))
    app.add_handler(CommandHandler('get_delivery_time', get_delivery_time))
    app.add_handler(CommandHandler('mysubscriptions', my_subscriptions))
    app.add_handler(CommandHandler('set_delivery_time', set_delivery_time))
    app.add_handler(CallbackQueryHandler(button))

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
