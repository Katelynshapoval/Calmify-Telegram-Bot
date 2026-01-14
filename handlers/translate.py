import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect: /translate <language> <text>
    if len(context.args) < 2:
        await update.message.reply_text(
            (
                "❗ <b>Uso incorrecto del comando.</b>\n\n"
                "Indica el idioma de destino y el texto que quieres traducir.\n\n"
                "<b>Ejemplo:</b>\n"
                "<pre>/translate inglés Hola, solo quería confirmar la reunión de mañana.</pre>"
            ),
            parse_mode="HTML"
        )
        return

    target_language = context.args[0]
    user_text = " ".join(context.args[1:])

    SYSTEM_INSTRUCTIONS = f"""\
Vas a recibir mensajes destinados a correos electrónicos o chats laborales.
Tu tarea es **traducir el mensaje al {target_language} y mejorar ligeramente su redacción**
para que suene profesional, natural y adecuada para comunicación corporativa.

Reglas estrictas:
1. No cambies el significado del mensaje original.
2. Mejora la fluidez y el tono profesional si es necesario.
3. No añadas información nueva.
4. Evita un tono excesivamente formal o robótico.
5. Usa SOLO HTML compatible con Telegram.
6. NO uses <p>, <br>, <div> ni etiquetas no soportadas.
7. Para saltos de línea, usa saltos reales (\\n), no etiquetas HTML.

El resultado debe ser un mensaje profesional listo para enviar.
"""

    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nTexto original:\n{user_text}\n\nTraducción:"

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
    temp_msg = await update.message.reply_text("🌍 Traduciendo tu mensaje...")

    try:
        ai_text = await generate_response(prompt)
    except Exception as e:
        ai_text = f"Error al generar la traducción: {e}"
    finally:
        typing_done.set_result(True)

    ai_text = sanitize_telegram_html(ai_text)
    await temp_msg.edit_text(ai_text, parse_mode="HTML")


def sanitize_telegram_html(text: str) -> str:
    # Remove unsupported HTML tags commonly produced by LLMs
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        text = text.replace(tag, "")
    return text
