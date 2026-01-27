import asyncio
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response
# from services.openrouter import generate_response
from utils.sanitize import sanitize_all

from utils.guard import reject_if_busy

# -------- CONFIG --------

BUSY_KEY = "is_busy"

ALLOWED_TOPICS = [
    "correo", "email", "mail", "escribir", "redactar", "redacción",
    "reescribir", "rewrite", "traducir", "traducción", "translate",
    "resumir", "resumen", "shorten", "corregir", "corrección",
    "ortografía", "gramática", "tono", "formal", "informal",
    "mensaje", "texto",
]


# -------- FORMATTERS --------

def markdown_to_telegram_html(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def sanitize_telegram_html(text: str) -> str:
    for tag in ("<p>", "</p>", "<br>", "<br/>", "<br />"):
        text = text.replace(tag, "")
    return text


# -------- TYPING LOOP (BACKGROUND) --------

async def _typing_loop(context: ContextTypes.DEFAULT_TYPE, chat_id: int, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        except Exception:
            pass
        await asyncio.sleep(4)


# -------- BACKGROUND WORKER --------

async def _process_fallback_request(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        message_id: int,
        user_text: str,
):
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(
        _typing_loop(context, chat_id, stop_typing)
    )

    try:
        SYSTEM_INSTRUCTIONS = """\
Eres un asistente experto en redacción profesional.

Responde SOLO si la solicitud está relacionada con:
- redacción
- corrección
- traducción
- mejora de textos

Reglas:
- Respuesta breve y profesional
- No información fuera del ámbito
- Formato obligatorio:

**Respuesta**
Contenido conciso aquí.
"""

        prompt = f"{SYSTEM_INSTRUCTIONS}\n\nSolicitud:\n{user_text}\n\nRespuesta:"

        ai_text = await generate_response(prompt)
        ai_text = sanitize_all(ai_text)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=ai_text,
            parse_mode="HTML",
        )

    except Exception:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ <b>Error</b>\nNo se pudo generar la respuesta.",
            parse_mode="HTML",
        )

    finally:
        stop_typing.set()
        typing_task.cancel()
        context.user_data[BUSY_KEY] = False


# -------- FALLBACK HANDLER --------

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1️⃣ Ignore during /explainimg flow
    if context.user_data.get("awaiting_image") or context.user_data.get("awaiting_request"):
        return

    # 2️⃣ ⛔ CENTRALIZED BUSY GUARD (HERE)
    if await reject_if_busy(update, context, key=BUSY_KEY):
        return

    user_text = update.message.text.strip()
    lower_text = user_text.lower()

    # 3️⃣ 🚫 OUT OF SCOPE (FAST EXIT)
    if not any(k in lower_text for k in ALLOWED_TOPICS):
        await update.message.reply_text(
            "❌ <b>Fuera de alcance</b>\n\n"
            "Solo puedo ayudar con redacción y textos.\n"
            "Usa <b>/help</b>.",
            parse_mode="HTML",
        )
        return

    # 4️⃣ ✅ LOCK USER (ONLY AFTER PASSING GUARD)
    context.user_data[BUSY_KEY] = True

    # 5️⃣ ⏳ PLACEHOLDER (FAST)
    placeholder = await update.message.reply_text(
        "⏳ <i>Generando respuesta…</i>",
        parse_mode="HTML",
    )

    # 6️⃣ 🚀 BACKGROUND TASK (DO NOT AWAIT)
    asyncio.create_task(
        _process_fallback_request(
            context=context,
            chat_id=update.effective_chat.id,
            message_id=placeholder.message_id,
            user_text=user_text,
        )
    )
