import os
import uuid
import asyncio
import ollama
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

# -------- CONFIG --------

IMG_DIR = "img"

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)


# -------- OLLAMA IMAGE CALL --------

def _ollama_image_request_sync(
        system_prompt: str,
        user_message: str,
        photo_path: str,
) -> str:
    response = ollama.chat(
        model="gemma3",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_message,
                "images": [photo_path],
            },
        ],
    )
    return response["message"]["content"]


async def ollama_image_request(
        system_prompt: str,
        user_message: str,
        photo_path: str,
) -> str:
    return await asyncio.to_thread(
        _ollama_image_request_sync,
        system_prompt,
        user_message,
        photo_path,
    )


# -------- TYPING INDICATOR --------

async def typing_loop(context, chat_id, stop_event: asyncio.Event):
    while not stop_event.is_set():
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(4)


# -------- /explainimg COMMAND --------

async def explainimg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🖼️ <b>Envía la imagen que quieres analizar.</b>\n\n"
        "Debe estar relacionada con <b>software, programación o tecnología</b>.",
        parse_mode="HTML",
    )

    context.user_data["awaiting_image"] = True


# -------- IMAGE RECEIVER --------

async def explainimg_receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_image"):
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()

    filename = f"{uuid.uuid4().hex}.jpg"
    photo_path = os.path.join(IMG_DIR, filename)
    await file.download_to_drive(photo_path)

    context.user_data["photo_path"] = photo_path
    context.user_data["awaiting_image"] = False
    context.user_data["awaiting_request"] = True

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Sin solicitud", callback_data="explainimg_no_request")]]
    )

    await update.message.reply_text(
        "✍️ <b>¿Qué quieres que haga con la imagen?</b>\n\n"
        "Escribe tu solicitud o pulsa <b>Sin solicitud</b>.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# -------- NO REQUEST BUTTON --------

async def explainimg_no_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    photo_path = context.user_data.get("photo_path")

    placeholder = await query.edit_message_text(
        "⏳ <i>Generando respuesta…</i>",
        parse_mode="HTML",
    )

    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(
        typing_loop(context, chat_id, stop_event)
    )

    system_prompt = (
        "Eres un asistente visual especializado en ingeniería de software.\n\n"
        "Evalúa la imagen siguiendo estas reglas estrictas:\n\n"

        "1. Validación:\n"
        "- Si la imagen NO está relacionada con software, programación o tecnología, responde EXACTAMENTE:\n"
        "  ❌ <b>Imagen no válida</b>\n"
        "  Esta imagen no parece estar relacionada con software o programación.\n\n"
        "- Si contiene contenido inapropiado, responde EXACTAMENTE:\n"
        "  ❌ <b>Contenido no permitido</b>\n"
        "  No puedo analizar este tipo de contenido.\n\n"

        "2. Si la imagen es válida, usa SIEMPRE este formato:\n\n"
        "<b>📷 Análisis de la imagen</b>\n"
        "Descripción breve y clara de lo que se observa.\n\n"

        "Si hay un problema técnico visible, añade:\n"
        "<b>⚠️ Posible problema</b>\n"
        "Descripción corta del problema.(si hay un problema) \n"
        "<b>💡 Sugerencia</b>\n"
        "Solución breve (si hay un problema).\n\n"

        "Si NO hay problemas visibles, añade:\n"
        "<b>✅ Estado</b>\n"
        "No se detectan problemas visibles.\n\n"

        "Reglas adicionales:\n"
        "- NO transcribas texto de la imagen.\n"
        "- NO inventes información.\n"
        "- Mantén la respuesta clara, concisa y profesional."
    )

    try:
        result = await ollama_image_request(
            system_prompt=system_prompt,
            user_message="Describe la imagen.",
            photo_path=photo_path,
        )
    except Exception:
        result = "❌ <b>Error</b>\nNo se pudo analizar la imagen."

    stop_event.set()
    await typing_task

    result = markdown_to_telegram_html(result)
    await placeholder.edit_text(result, parse_mode="HTML")
    context.user_data.clear()


# -------- USER TEXT REQUEST --------

async def explainimg_user_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_request"):
        return

    chat_id = update.effective_chat.id
    photo_path = context.user_data.get("photo_path")
    user_request = update.message.text

    placeholder = await update.message.reply_text(
        "⏳ <i>Generando respuesta…</i>",
        parse_mode="HTML",
    )

    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(
        typing_loop(context, chat_id, stop_event)
    )

    system_prompt = (
        "Eres un asistente visual especializado en ingeniería de software.\n\n"
        "Reglas estrictas:\n"
        "- Si la imagen no está relacionada con software o programación, indícalo brevemente.\n"
        "- Si el contenido es inapropiado, rechaza la solicitud.\n"
        "- Cumple SOLO la solicitud del usuario.\n"
        "- NO transcribas texto de la imagen.\n"
        "- No añadas contexto innecesario.\n"
        "- Respuesta clara, breve y bien estructurada."
    )

    try:
        result = await ollama_image_request(
            system_prompt=system_prompt,
            user_message=user_request,
            photo_path=photo_path,
        )
    except Exception:
        result = "❌ <b>Error</b>\nNo se pudo procesar la solicitud."

    stop_event.set()
    await typing_task

    result = markdown_to_telegram_html(result)
    await placeholder.edit_text(result, parse_mode="HTML")
    context.user_data.clear()


def markdown_to_telegram_html(text: str) -> str:
    """
    Converts basic Markdown (**bold**) to Telegram-compatible HTML.
    """
    # Convert **bold** to <b>bold</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    return text
