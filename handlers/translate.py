import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response
# from services.openrouter import generate_response
from utils.sanitize import sanitize_all


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
    Eres un MOTOR DE TRADUCCIÓN.

    Devuelve ÚNICAMENTE la traducción al {target_language}
    ENTRE las etiquetas <salida> y </salida>.

    REGLAS:
    - Nada fuera de <salida>
    - No etiquetas adicionales
    - No texto original
    - No explicaciones

    Ejemplo válido:
    <salida>Hello, I just wanted to confirm tomorrow’s meeting.</salida>
    """

    prompt = (
            SYSTEM_INSTRUCTIONS
            + "\n\nTEXTO A TRADUCIR:\n"
            + user_text
    )

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
        ai_text = sanitize_all(ai_text)
    except Exception as e:
        ai_text = f"Error al generar la traducción: {e}"
    finally:
        typing_done.set_result(True)

    ai_text = sanitize_telegram_html(ai_text)
    # Replace literal \n with actual line breaks
    ai_text = ai_text.replace("\\n", "\n")
    await temp_msg.edit_text(ai_text, parse_mode="HTML")


def sanitize_telegram_html(text: str) -> str:
    # Remove unsupported HTML tags commonly produced by LLMs
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        text = text.replace(tag, "")
    return text
