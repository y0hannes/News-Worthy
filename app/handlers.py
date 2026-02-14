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


# --- Keyboards ---

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📰 Latest News", callback_data="menu:news"),
            InlineKeyboardButton("🔔 My News", callback_data="menu:my_news"),
        ],
        [
            InlineKeyboardButton("✅ Subscribe", callback_data="menu:subscribe"),
            InlineKeyboardButton("📋 Subscriptions", callback_data="menu:my_subscriptions"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings"),
            InlineKeyboardButton("❓ Help", callback_data="menu:help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu:main")]]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("⏰ Delivery Time", callback_data="menu:delivery_time")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_user(user)
    
    welcome_text = (
        f"👋 Hello, {user.first_name}!\n\n"
        "Welcome to **News-Worthy**, your personal news assistant. "
        "I can fetch the latest headlines and deliver them to you daily.\n\n"
        "Use the buttons below to navigate:"
    )
    
    if update.message:
        await update.message.reply_text(
            welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **How to use News-Worthy**\n\n"
        "• **Latest News**: Browse headlines by topic.\n"
        "• **My News**: Get headlines from your subscribed topics.\n"
        "• **Subscribe**: Choose topics you are interested in.\n"
        "• **Subscriptions**: Manage your active subscriptions.\n"
        "• **Settings**: Set your daily news delivery time.\n\n"
        "You can also use commands like /news, /subscribe, etc."
    )
    
    if update.message:
        await update.message.reply_text(
            help_text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            help_text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown"
        )


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(topic.name.title(), callback_data=f"news:{topic.value}")]
        for topic in NewsTopics
    ]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    text = "🔍 **Choose a topic to see the latest headlines:**"
    
    if update.message:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"➕ {topic.name.title()}", callback_data=f"subscribe:{topic.value}")]
        for topic in NewsTopics
    ]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    text = "🔔 **Select a topic to subscribe to:**"
    
    if update.message:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    topics = await fetch_my_subscriptions(user_id)
    
    if not topics:
        text = "You are not subscribed to any topics yet."
        keyboard = [[InlineKeyboardButton("➕ Subscribe", callback_data="menu:subscribe")]]
    else:
        text = "📋 **Your Current Subscriptions**\nClick to unsubscribe:"
        keyboard = [
            [
                InlineKeyboardButton(
                    f"❌ {NewsTopics(topic).name.title()}",
                    callback_data=f"unsubscribe:{topic}",
                )
            ]
            for topic in topics
        ]
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
    
    if update.message:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def my_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    topics = await fetch_my_subscriptions(user_id)
    
    if not topics:
        text = "You are not subscribed to any topics. Please subscribe first!"
        keyboard = [[InlineKeyboardButton("➕ Subscribe", callback_data="menu:subscribe")]]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu:main")])
        
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Show loading message if it's a callback
    if update.callback_query:
        await update.callback_query.edit_message_text("⌛ Fetching your personalized news...")

    response = []
    for topic_value in topics:
        try:
            topic = NewsTopics(topic_value)
            headlines = await get_cached_news(topic)
            if not headlines:
                headlines = await fetch_and_store_news(topic)
            if headlines:
                response.append(f"📍 **{topic.name.title()}**\n" + "\n\n".join(headlines))
        except ValueError:
            continue
            
    if response:
        final_text = "\n\n---\n\n".join(response)
        # Split message if it's too long (Telegram limit is 4096)
        if len(final_text) > 4000:
            final_text = final_text[:3997] + "..."
    else:
        final_text = "No news available for your subscribed topics at the moment."

    if update.message:
        await update.message.reply_text(
            final_text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            final_text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown"
        )


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = await get_scheduled_time(user_id)
    
    if result:
        hour, minute = result
        # Adjust for TZ if needed, but here we just show what's in DB (stored as UTC-3 or something based on previous code)
        # Previous code had hour + 3 in get_delivery_time
        display_hour = (hour + 3) % 24
        time_text = f"{display_hour:02d}:{minute:02d}"
    else:
        time_text = "Not set"

    text = (
        "⚙️ **Settings**\n\n"
        f"⏰ Current Delivery Time: **{time_text}** (EAT/GMT+3)\n\n"
        "Choose an option:"
    )
    
    if update.message:
        await update.message.reply_text(
            text, reply_markup=get_settings_keyboard(), parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=get_settings_keyboard(), parse_mode="Markdown"
        )


async def set_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        text = (
            "⏰ **Set Delivery Time**\n\n"
            "Choose a preset or send the time in **HH:MM** format (e.g., `/set_delivery_time 08:30`).\n\n"
            "Default presets (EAT/GMT+3):"
        )
        keyboard = [
            [
                InlineKeyboardButton("🌅 Morning (08:00)", callback_data="set_time:08:00"),
                InlineKeyboardButton("☀️ Noon (12:00)", callback_data="set_time:12:00"),
            ],
            [
                InlineKeyboardButton("🌇 Evening (18:00)", callback_data="set_time:18:00"),
                InlineKeyboardButton("🌙 Night (21:00)", callback_data="set_time:21:00"),
            ],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="menu:settings")],
        ]
        
        if update.message:
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        return

    try:
        # Handle input from command
        time_str = context.args[0]
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid time format. Please use HH:MM (e.g., 09:15).")
        return

    # Database stores UTC time (assuming local is GMT+3 based on original code)
    utc_hour = (hour - 3) % 24
    success = await set_schedule_delivery_time(user_id, utc_hour, minute)
    
    if success:
        message = f"✅ Delivery time set to **{hour:02d}:{minute:02d}**."
        if update.message:
            await update.message.reply_text(message, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Failed to update delivery time.")


async def get_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is handled by settings_menu now, but keeping it for the command
    await settings_menu(update, context)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu:main":
        await start(update, context)
    elif data == "menu:news":
        await news(update, context)
    elif data == "menu:my_news":
        await my_news(update, context)
    elif data == "menu:subscribe":
        await subscribe(update, context)
    elif data == "menu:my_subscriptions":
        await my_subscriptions(update, context)
    elif data == "menu:settings":
        await settings_menu(update, context)
    elif data == "menu:help":
        await help_command(update, context)
    elif data == "menu:delivery_time":
        await set_delivery_time(update, context)

    elif data.startswith("set_time:"):
        time_str = data.split(":", 1)[1]
        hour, minute = map(int, time_str.split(":"))
        utc_hour = (hour - 3) % 24
        success = await set_schedule_delivery_time(user_id, utc_hour, minute)
        if success:
            await query.edit_message_text(
                f"✅ Delivery time set to **{time_str}**.",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Failed to update delivery time.")

    elif data.startswith("news:"):
        topic_value = data.split(":", 1)[1]
        topic = NewsTopics(topic_value)
        
        await query.edit_message_text(f"⌛ Fetching latest news for **{topic.name.title()}**...", parse_mode="Markdown")
        
        headlines = await get_cached_news(topic)
        if not headlines:
            headlines = await fetch_and_store_news(topic)
            
        if headlines:
            text = f"📰 **Latest {topic.name.title()} News**\n\n" + "\n\n".join(headlines)
            if len(text) > 4000: text = text[:3997] + "..."
            await query.edit_message_text(text, reply_markup=get_back_to_menu_keyboard(), parse_mode="Markdown")
        else:
            await query.edit_message_text(
                f"No news available for '{topic.name}'.", 
                reply_markup=get_back_to_menu_keyboard()
            )

    elif data.startswith("subscribe:"):
        topic_value = data.split(":", 1)[1]
        topic = NewsTopics(topic_value)
        subscribed = await subscribe_to_topic(topic, user_id)
        
        if subscribed:
            await query.edit_message_text(
                f"✅ Subscribed to **{topic.name.title()}**!",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"You are already subscribed to {topic.name}.",
                reply_markup=get_back_to_menu_keyboard()
            )

    elif data.startswith("unsubscribe:"):
        topic_value = data.split(":", 1)[1]
        success = await unsubscribe_from_topic(user_id, topic_value)
        if success:
            await query.edit_message_text(
                f"✅ Unsubscribed from **{NewsTopics(topic_value).name.title()}**.",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("Failed to unsubscribe.", reply_markup=get_back_to_menu_keyboard())

