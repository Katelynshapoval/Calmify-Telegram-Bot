import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response


async def shorten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get text after /shorten
    user_text = " ".join(context.args)

    # If no text provided, show usage message
    if not user_text:
        await update.message.reply_text(
            (
                "❗ <b>No has incluido ningún texto.</b>\n\n"
                "Escribe el mensaje que quieres hacer más conciso después del comando.\n\n"
                "<b>Ejemplo:</b>\n"
                "<pre>/shorten Hola, solo quería comentar que esta cuestión ya ha sido respondida varias veces y si necesitas puedo enviarte nuevamente la información.</pre>"
            ),
            parse_mode="HTML"
        )
        return

    SYSTEM_INSTRUCTIONS = """\
Eres un asistente experto en comunicación profesional y redacción corporativa.

Tu tarea es:
1. Tomar el mensaje proporcionado y hacerlo más conciso y directo.
2. Mantener claridad, profesionalismo y el significado original.
3. No añadas información nueva ni cambies el contenido esencial.
4. Usa SOLO HTML compatible con Telegram.
5. NO uses <p>, <br>, <div> ni etiquetas no soportadas.
6. Usa saltos de línea reales (\\n) en lugar de etiquetas HTML.

El resultado debe ser un mensaje listo para enviar.
"""

    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nTexto original:\n{user_text}\n\nVersión concisa:"

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
    temp_msg = await update.message.reply_text("✂️ Acortando tu mensaje...")

    try:
        ai_text = await generate_response(prompt)
    except Exception as e:
        ai_text = f"Error al acortar el mensaje: {e}"
    finally:
        typing_done.set_result(True)

    # Sanitize any unsupported HTML
    ai_text = sanitize_telegram_html(ai_text)

    # Sanitize unsupported HTML
    ai_text = sanitize_telegram_html(ai_text)

    # Replace literal \n with actual line breaks
    ai_text = ai_text.replace("\\n", "\n")

    # Send final message
    await temp_msg.edit_text(ai_text, parse_mode="HTML")


def sanitize_telegram_html(text: str) -> str:
    # Remove unsupported HTML tags commonly produced by AI
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        text = text.replace(tag, "")
    return text
