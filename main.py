# Import Telegram bot classes
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
# Import environment variable tools
import os
from dotenv import load_dotenv
# Load variables from .env file into the environment
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm alive 🚀")

# Echo handler (repeats any text the user sends)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# Initialize the Telegram bot app using the token
app = ApplicationBuilder().token(TOKEN).build()

# Add handlers so the bot knows how to react to messages
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

print("Bot is running...")
app.run_polling()
