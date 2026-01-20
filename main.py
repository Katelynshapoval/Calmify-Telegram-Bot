from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import os
from dotenv import load_dotenv

from handlers.start import start
from handlers.tip import tip
from handlers.rewrite import rewrite
from handlers.translate import translate
from handlers.check import check
from handlers.shorten import shorten
from handlers.help import help

from handlers.explainimg import (
    explainimg,
    explainimg_receive_image,
    explainimg_no_request,
    explainimg_user_request,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("tip", tip))
app.add_handler(CommandHandler("rewrite", rewrite))
app.add_handler(CommandHandler("translate", translate))
app.add_handler(CommandHandler("check", check))
app.add_handler(CommandHandler("shorten", shorten))
app.add_handler(CommandHandler("explainimg", explainimg))

app.add_handler(
    MessageHandler(filters.PHOTO, explainimg_receive_image)
)

app.add_handler(
    CallbackQueryHandler(
        explainimg_no_request,
        pattern="^explainimg_no_request$",
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        explainimg_user_request,
    )
)

print("Bot is running...")
app.run_polling()
