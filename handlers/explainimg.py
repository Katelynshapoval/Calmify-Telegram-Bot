import os
import uuid
import asyncio
import re
import base64

import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from services.openrouter_vision import generate_vision_response

from utils.guard import reject_if_busy

# ---------------- CONFIG ----------------

IMG_DIR = "img"
BUSY_KEY = "is_busy_explainimg"

os.makedirs(IMG_DIR, exist_ok=True)


def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ---------------- FORMAT ----------------

def markdown_to_telegram_html(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


# ---------------- OLLAMA ----------------

def _ollama_image_request_sync(system_prompt, user_message, photo_path):
    try:
        image_b64 = image_to_base64(photo_path)

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "gemma3",  # must be a vision-capable model
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                        "images": [image_b64],
                    },
                ],
            },
            timeout=None,
        )

        response.raise_for_status()
        data = response.json()

        return data["message"]["content"]

    except ConnectionError:
        return "❌ Ollama no está iniciado o no se puede conectar."

    except Timeout:
        return "❌ Tiempo de espera excedido."

    except HTTPError as e:
        status = e.response.status_code if e.response else "?"
        return f"❌ Error HTTP ({status})."

    except Exception:
        return "❌ Error inesperado al analizar la imagen."


async def ollama_image_request(system_prompt, user_message, photo_path):
    return await asyncio.to_thread(
        _ollama_image_request_sync,
        system_prompt,
        user_message,
        photo_path,
    )


# ---------------- TYPING ----------------

async def typing_loop(context, chat_id, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        except Exception:
            pass
        await asyncio.sleep(4)


# ---------------- BACKGROUND WORKER ----------------

async def _process_explainimg(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        message_id: int,
        system_prompt: str,
        user_message: str,
        photo_path: str,
):
    stop_typing = asyncio.Event()
    asyncio.create_task(typing_loop(context, chat_id, stop_typing))

    try:
        # result = await ollama_image_request(
        #     system_prompt=system_prompt,
        #     user_message=user_message,
        #     photo_path=photo_path,
        # )

        result = await generate_vision_response(
            system_prompt=system_prompt,
            user_message=user_message,
            image_path=photo_path,
        )

        result = markdown_to_telegram_html(result)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=result,
            parse_mode="HTML",
        )

    except Exception:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ <b>Error</b>\nNo se pudo analizar la imagen.",
            parse_mode="HTML",
        )

    finally:
        stop_typing.set()
        context.user_data.pop(BUSY_KEY, None)
        context.user_data.pop("awaiting_request", None)
        context.user_data.pop("photo_path", None)


# ---------------- /explainimg ----------------

async def explainimg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["awaiting_image"] = True

    await update.message.reply_text(
        "🖼️ <b>Envía la imagen que quieres analizar.</b>\n\n"
        "Debe estar relacionada con <b>software, programación o tecnología</b>.",
        parse_mode="HTML",
    )


# ---------------- IMAGE RECEIVER ----------------

async def explainimg_receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_image"):
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()

    photo_path = os.path.join(IMG_DIR, f"{uuid.uuid4().hex}.jpg")
    await file.download_to_drive(photo_path)

    context.user_data.update(
        awaiting_image=False,
        awaiting_request=True,
        photo_path=photo_path,
    )

    await update.message.reply_text(
        "✍️ <b>¿Qué quieres que haga con la imagen?</b>\n\n"
        "Escribe tu solicitud o pulsa <b>Sin solicitud</b>.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Sin solicitud", callback_data="explainimg_no_request")]]
        ),
        parse_mode="HTML",
    )


# ---------------- NO REQUEST BUTTON ----------------

async def explainimg_no_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await reject_if_busy(query.message, context, key=BUSY_KEY):
        return

    context.user_data[BUSY_KEY] = True

    placeholder = await query.edit_message_text(
        "⏳ <i>Generando respuesta…</i>",
        parse_mode="HTML",
    )

    # 🔒 ORIGINAL SYSTEM PROMPT — UNCHANGED
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
        "Descripción corta del problema.\n"
        "<b>💡 Sugerencia</b>\n"
        "Solución breve.\n\n"
        "Si NO hay problemas visibles, añade:\n"
        "<b>✅ Estado</b>\n"
        "No se detectan problemas visibles.\n\n"
        "Reglas adicionales:\n"
        "- NO transcribas texto de la imagen.\n"
        "- NO inventes información.\n"
        "- Mantén la respuesta clara, concisa y profesional."
    )

    asyncio.create_task(
        _process_explainimg(
            context=context,
            chat_id=query.message.chat.id,
            message_id=placeholder.message_id,
            system_prompt=system_prompt,
            user_message="Describe la imagen.",
            photo_path=context.user_data["photo_path"],
        )
    )


# ---------------- USER TEXT REQUEST ----------------

async def explainimg_user_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ✅ Always acknowledge
    placeholder = await update.message.reply_text(
        "⏳ <i>Generando respuesta…</i>",
        parse_mode="HTML",
    )

    if not context.user_data.get("awaiting_request"):
        await placeholder.edit_text(
            "❌ <b>No hay ninguna imagen pendiente.</b>\nUsa /explainimg primero.",
            parse_mode="HTML",
        )
        return

    if await reject_if_busy(update, context, key=BUSY_KEY):
        return

    context.user_data[BUSY_KEY] = True

    # 🔒 ORIGINAL SYSTEM PROMPT — UNCHANGED
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

    asyncio.create_task(
        _process_explainimg(
            context=context,
            chat_id=update.effective_chat.id,
            message_id=placeholder.message_id,
            system_prompt=system_prompt,
            user_message=update.message.text,
            photo_path=context.user_data["photo_path"],
        )
    )
