import asyncio
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response  # same service you already use


# -------- HELPERS --------

def markdown_to_telegram_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


async def typing_loop(context, chat_id, stop_event: asyncio.Event):
    while not stop_event.is_set():
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(4)


# -------- FALLBACK HANDLER --------
async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
            context.user_data.get("awaiting_image")
            or context.user_data.get("awaiting_request")
    ):
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id

    placeholder = await update.message.reply_text(
        "⏳ <i>Analizando tu mensaje…</i>",
        parse_mode="HTML",
    )

    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(
        typing_loop(context, chat_id, stop_event)
    )

    system_prompt = (
        "Eres un asistente especializado en redacción profesional.\n\n"
        "Si el mensaje está relacionado con escritura, corrección, mejora de textos o correos:\n"
        "- Responde de forma breve y útil.\n\n"
        "Si NO lo está, responde EXACTAMENTE:\n\n"
        "❌ <b>No puedo ayudarte con esa consulta</b>\n"
        "Este bot está enfocado en redacción y mejora de textos.\n\n"
        "Formato obligatorio:\n"
        "<b>✍️ Respuesta</b>\n"
        "Texto breve y claro."
    )

    try:
        ai_text = await generate_response(
            f"{system_prompt}\n\nMensaje:\n{user_text}\n\nRespuesta:"
        )
    except Exception:
        ai_text = "❌ <b>Error</b>\nNo se pudo procesar el mensaje."

    stop_event.set()
    await typing_task

    ai_text = markdown_to_telegram_html(ai_text)
    await placeholder.edit_text(ai_text, parse_mode="HTML")
