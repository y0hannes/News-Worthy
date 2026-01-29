from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from news.db import (
    save_user,
    fetch_my_subscriptions,
    subscribe_to_topic,
    unsubscribe_from_topic,
    set_schedule_delivery_time,
    get_scheduled_time,
)
from news.cache import get_cached_news, fetch_and_store_news
from news.db import NewsTopics


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_saved = await save_user(user)
    if user_saved:
        await update.message.reply_text(f"Hello, {user.first_name}!")
    else:
        await update.message.reply_text(
            f"Hello, {user.first_name}, There was a problem registering you. Please try again!"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Help\n"
        "/news - Get news feed\n"
        "/mynews - Get news from your subscriptions\n"
        "/subscribe - Subscribe to topic\n"
        "/mysubscriptions - List subscriptions\n"
        "/set_delivery_time HH:MM - Set delivery time"
    )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(topic.name, callback_data=f"news:{topic.value}")]
        for topic in NewsTopics
    ]
    await update.message.reply_text(
        "Choose a topic:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(topic.name, callback_data=f"subscribe:{topic.value}")]
        for topic in NewsTopics
    ]
    await update.message.reply_text(
        "Choose a topic to subscribe:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    topics = await fetch_my_subscriptions(user_id)
    if not topics:
        await update.message.reply_text("You are not subscribed to any topics.")
        return
    keyboard = [
        [
            InlineKeyboardButton(
                f"❌ Unsubscribe from {NewsTopics(topic).name}",
                callback_data=f"unsubscribe:{topic}",
            )
        ]
        for topic in topics
    ]
    await update.message.reply_text(
        "Your subscriptions:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def my_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    topics = await fetch_my_subscriptions(user_id)
    if not topics:
        await update.message.reply_text(
            "You are not subscribed to any topics. Use /subscribe first."
        )
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


async def set_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "Provide time in HH:MM format. Example: /set_delivery_time 09:30"
        )
        return
    try:
        hour, minute = map(int, context.args[0].split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM (24h).")
        return
    success = await set_schedule_delivery_time(user_id, hour, minute)
    if success:
        await update.message.reply_text(
            f"Daily news delivery time set to {hour:02d}:{minute:02d}."
        )
    else:
        await update.message.reply_text("Failed to set delivery time.")


async def get_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = await get_scheduled_time(user_id)
    if not result:
        await update.message.reply_text("Failed to get scheduled delivery time.")
        return
    hour, minute = result
    await update.message.reply_text(f"Your delivery time is {hour:02d}:{minute:02d}.")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("news:"):
        topic_value = data.split(":", 1)[1]
        try:
            topic = NewsTopics(topic_value)
        except ValueError:
            await query.edit_message_text("Invalid topic selected.")
            return
        headlines = await get_cached_news(topic)
        if not headlines:
            headlines = await fetch_and_store_news(topic)
        if headlines:
            await query.edit_message_text("\n\n".join(headlines))
        else:
            await query.edit_message_text(f"No news available for '{topic.name}'.")

    elif data.startswith("subscribe:"):
        topic_value = data.split(":", 1)[1]
        try:
            topic = NewsTopics(topic_value)
        except ValueError:
            await query.edit_message_text("Invalid topic selected.")
            return
        subscribed = await subscribe_to_topic(topic, user_id)
        if subscribed:
            await query.edit_message_text(f"Subscribed to '{topic.name}'.")
        else:
            await query.edit_message_text(f"Failed to subscribe to '{topic.name}'.")

    elif data.startswith("unsubscribe:"):
        topic_value = data.split(":", 1)[1]
        success = await unsubscribe_from_topic(user_id, topic_value)
        if success:
            await query.edit_message_text(
                f"Unsubscribed from '{NewsTopics(topic_value).name}'."
            )
        else:
            await query.edit_message_text("Failed to unsubscribe.")
