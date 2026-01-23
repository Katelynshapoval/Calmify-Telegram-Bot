import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

# from services.ollama import generate_response
from services.openrouter import generate_response

from utils.sanitize import sanitize_all


async def rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get text after /rewrite
    user_text = " ".join(context.args)

    # If no text was provided, show usage message
    if not user_text:
        await update.message.reply_text(
            (
                "❗ <b>No has incluido ningún texto.</b>\n\n"
                "Escribe el mensaje que quieres convertir en un correo profesional después del comando.\n\n"
                "<b>Ejemplo:</b>\n"
                "<pre>/rewrite Ya he respondido a esto varias veces, deberíais revisarlo antes.</pre>"
            ),
            parse_mode="HTML"
        )
        return

    SYSTEM_INSTRUCTIONS = """\
    Vas a recibir mensajes escritos de forma apresurada o frustrada que después deberán enviarse a un compañero de trabajo o un superior.
    Tu tarea es reformularlos como correos electrónicos o mensajes profesionales en español de España.

    Reglas estrictas:
    1. Neutraliza y suaviza cualquier lenguaje brusco sin perder información.
    2. Estructura el mensaje como un correo profesional.
    3. Usa un tono natural, humano y cordial.
    4. No añadas información nueva.
    5. Usa SOLO HTML compatible con Telegram.
    6. NO uses <p>, <br>, <div> ni etiquetas no soportadas.
    7. Para saltos de línea, usa saltos reales (\\n), no etiquetas HTML.

    El resultado debe ser un mensaje profesional listo para enviar.
    """

    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nUsuario: {user_text}\n\nRespuesta:"

    typing_done = asyncio.get_event_loop().create_future()

    async def send_typing():
        while not typing_done.done():
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(5)

    asyncio.create_task(send_typing())

    # Temporary placeholder message
    temp_msg = await update.message.reply_text("✍️ Redactando tu correo profesional...")

    try:
        ai_text = await generate_response(prompt)
    except Exception as e:
        ai_text = f"Error al generar la respuesta: {e}"
    finally:
        typing_done.set_result(True)

    ai_text = await generate_response(prompt)
    ai_text = sanitize_all(ai_text)

    await temp_msg.edit_text(ai_text, parse_mode="HTML")
