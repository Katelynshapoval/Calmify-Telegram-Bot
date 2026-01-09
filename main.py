# Import Telegram bot classes
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
# Import environment variable tools
import os
from dotenv import load_dotenv
import requests
import asyncio
from telegram.constants import ChatAction

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


# Handler to process user messages and send them to Ollama
from telegram.constants import ChatAction  # <-- add this import

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    SYSTEM_INSTRUCTIONS = """\
    Vas a recibir mensajes escritos de forma apresurada o frustrada que después deberán enviarse a un compañero de trabajo o un superior. 
    Tu tarea es reformularlos como correos electrónicos o mensajes profesionales en español de España.  

    Sigue estas reglas estrictamente:

    1. **Neutraliza y suaviza cualquier lenguaje brusco, negativo o frustrado** sin perder la información esencial.  
    2. **Estructura el mensaje como un correo profesional**: saludo inicial, cuerpo claro y despedida formal o cordial.  
    3. Mantén un **tono natural, humano, cercano y ligeramente amable**, proyectando colaboración y profesionalidad.  
    4. Asegúrate de que las frases fluyan y sean fáciles de leer; evita que suene robótico o generado por IA.  
    5. Usa **HTML compatible con Telegram**: `<pre>` y `<b>` donde corresponda, pero evita etiquetas no soportadas como `<br>`.  
    6. No agregues información que no esté en el mensaje original; solo reescribe lo que el usuario envió de manera profesional y amigable.

    El objetivo es que el resultado sea un **correo o mensaje listo para enviar** que suene educado, colaborativo y profesional.
    """

    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nUsuario: {user_text}\n\nRespuesta:"

    async def send_typing():
        """Keep sending typing action every 5 seconds until stopped."""
        while not typing_done.done():
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(5)

    typing_done = asyncio.get_event_loop().create_future()

    try:
        # Start the typing indicator in the background
        asyncio.create_task(send_typing())

        # Run the blocking requests.post in a separate thread
        def call_ollama():
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gpt-oss:20b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=None  # wait as long as needed
            )
            response.raise_for_status()
            return response.json()

        data = await asyncio.to_thread(call_ollama)

        # Stop typing
        typing_done.set_result(True)

        # Extract AI response
        ai_text = data.get("response") or "Lo siento, no pude generar una respuesta."
        ai_text = ai_text.replace("<br>", "\n")

    except Exception as e:
        typing_done.set_result(True)
        ai_text = f"Error al generar la respuesta: {e}"

    await update.message.reply_text(ai_text, parse_mode="HTML")

# Initialize the Telegram bot app using the token
app = ApplicationBuilder().token(TOKEN).build()

# Add handlers so the bot knows how to react to messages
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

print("Bot is running...")
app.run_polling()
