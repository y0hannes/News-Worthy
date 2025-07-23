import os
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from news_fetcher import init_db, fetch_and_store_news, get_cached_news, NewsTopics
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_API_TOKEN = os.getenv("NEWS_API_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in environment variables")
if not NEWS_API_TOKEN:
    raise ValueError("No NEWS_API_KEY found in environment variables")

# commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello, {update.effective_user.first_name}!")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Here are the commands supported by our bot:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/news - Get your news feed"
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        topic_str = ' '.join(context.args).upper() if context.args else 'GENERAL'
        topic = NewsTopics[topic_str]
    except (KeyError, AttributeError):
        await update.message.reply_text(f"Invalid topic. Please use one of: {', '.join([t.name for t in NewsTopics])}")
        return

    headlines = get_cached_news(topic)
    
    if not headlines:
        await update.message.reply_text(f"No cached news for '{topic.value}'. Fetching fresh articles now...")
        headlines = fetch_and_store_news(topic)

    if not headlines:
        await update.message.reply_text(f"Sorry, couldn't fetch any news for '{topic.value}' at the moment.")
    else:
        await update.message.reply_text("\n\n".join(headlines))

def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('news', news))

    print("Bot is running...")
    app.run_polling()
    

if __name__ == "__main__":
    main()