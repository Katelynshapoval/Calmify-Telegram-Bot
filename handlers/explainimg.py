import os
import uuid
import ollama

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
)
from telegram.constants import ChatAction

# -------- CONFIG --------

IMG_DIR = "img"

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)


# -------- OLLAMA IMAGE CALL --------

async def ollama_image_request(
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


# -------- /explainimg COMMAND --------

async def explainimg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🖼️ <b>Envía la imagen que quieres analizar.</b>",
        parse_mode="HTML",
    )

    context.user_data["awaiting_image"] = True


# -------- IMAGE RECEIVER --------

async def explainimg_receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_image"):
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    photo = update.message.photo[-1]
    file = await photo.get_file()

    filename = f"{uuid.uuid4().hex}.jpg"
    photo_path = os.path.join(IMG_DIR, filename)

    await file.download_to_drive(photo_path)

    context.user_data["photo_path"] = photo_path
    context.user_data["awaiting_image"] = False
    context.user_data["awaiting_request"] = True

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Sin solicitud",
                    callback_data="explainimg_no_request",
                )
            ]
        ]
    )

    await update.message.reply_text(
        (
            "✍️ <b>¿Qué quieres que haga con la imagen?</b>\n\n"
            "Escribe tu solicitud o pulsa <b>Sin solicitud</b>."
        ),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# -------- NO REQUEST BUTTON --------

async def explainimg_no_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.chat.send_action(ChatAction.TYPING)

    photo_path = context.user_data.get("photo_path")

    system_prompt = (
        "Eres un asistente visual.\n\n"
        "Reglas estrictas:\n"
        "- Describe brevemente lo que ves en la imagen.\n"
        "- NO copies ni transcribas texto presente en la imagen.\n"
        "- Si hay un error o problema visible, sugiere una solución breve.\n"
        "- Sé conciso.\n"
        "- No inventes información."
    )

    user_message = "Describe la imagen."

    try:
        result = await ollama_image_request(
            system_prompt=system_prompt,
            user_message=user_message,
            photo_path=photo_path,
        )
    except Exception as e:
        result = f"❌ Error al analizar la imagen: {e}"

    await query.edit_message_text(result)

    context.user_data.clear()


# -------- USER TEXT REQUEST --------

async def explainimg_user_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_request"):
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    user_request = update.message.text
    photo_path = context.user_data.get("photo_path")

    system_prompt = (
        "Eres un asistente visual.\n\n"
        "Reglas estrictas:\n"
        "- Cumple SOLO la solicitud del usuario.\n"
        "- No añadas información adicional.\n"
        "- No describas la imagen si no se solicita explícitamente.\n"
        "- NO transcribas texto presente en la imagen.\n"
        "- No hagas suposiciones."
    )

    try:
        result = await ollama_image_request(
            system_prompt=system_prompt,
            user_message=user_request,
            photo_path=photo_path,
        )
    except Exception as e:
        result = f"❌ Error al procesar la solicitud: {e}"

    await update.message.reply_text(result)

    context.user_data.clear()
