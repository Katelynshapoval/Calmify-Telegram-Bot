# Import Telegram bot classes
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
# Import environment variable tools
import os
from dotenv import load_dotenv
# Load variables from .env file into the environment
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
STARTMESSAGE = ""

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import textwrap

    await update.message.reply_text(
        textwrap.dedent("""\
            <b>¡Hola! 👋</b>

            Soy tu asistente para redactar mensajes profesionales.
            Si me envías notas rápidas, mensajes informales o escritos con prisa, puedo ayudarte a convertirlos en correos o mensajes claros y educados.

            También puedo ajustar el tono: más formal, más cordial o más directo, y evitar que suene brusco.

            Por ejemplo, si escribes algo como:
            <pre>Ya he respondido a esta pregunta como cinco veces. Lo sabrías si te hubieras molestado en mirar antes de repetirla.</pre>

            Yo puedo convertirlo en algo como:
            <pre>Hola,

            Solo quería comentarte que esta cuestión ya la he respondido en varias ocasiones.
            Si quieres, puedo enviarte la información de nuevo o ayudarte a encontrarla.

            Quedo a tu disposición para cualquier otra cosa que necesites.

            Un saludo,
            [Tu nombre]</pre>

            Envíame tu mensaje y te ayudo a darle un tono profesional sin complicaciones.
        """),
        parse_mode="HTML"
    )


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
