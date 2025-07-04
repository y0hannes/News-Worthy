
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from news_fetcher import init_db, news

with open('TOKEN.txt') as file:
    token = file.read().strip()
    
with open('API_KEY.txt') as file:
    api_key = file.read().strip()

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

def main():
    init_db()
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('news', news))

    print("Bot is running...")
    app.run_polling()
    

if __name__ == "__main__":
    main()