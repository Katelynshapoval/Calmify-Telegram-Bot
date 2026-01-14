from telegram.ext import ApplicationBuilder, CommandHandler
import os
from dotenv import load_dotenv

from handlers.start import start
from handlers.tip import tip
from handlers.rewrite import rewrite
from handlers.translate import translate
from handlers.check import check
from handlers.shorten import shorten

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tip", tip))
app.add_handler(CommandHandler("rewrite", rewrite))
app.add_handler(CommandHandler("translate", translate))
app.add_handler(CommandHandler("check", check))
app.add_handler(CommandHandler("shorten", shorten))

print("Bot is running...")
app.run_polling()
