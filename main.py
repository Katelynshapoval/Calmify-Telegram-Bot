from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from handlers.start import start
from handlers.messages import process_message
from handlers.tip import tip

# Load variables from .env file into the environment
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Initialize the Telegram bot app using the token
app = ApplicationBuilder().token(TOKEN).build()

# Add handlers so the bot knows how to react to messages
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tip", tip))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

print("Bot is running...")
app.run_polling()
