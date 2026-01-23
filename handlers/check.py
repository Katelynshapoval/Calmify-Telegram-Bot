import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

# from services.ollama import generate_response
from services.openrouter import generate_response
from utils.sanitize import sanitize_all


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get text after /check
    user_text = " ".join(context.args)

    # If no text was provided, show usage message
    if not user_text:
        await update.message.reply_text(
            (
                "❗ <b>No has incluido ningún texto.</b>\n\n"
                "Pega el mensaje que quieres revisar después del comando.\n\n"
                "<b>Ejemplo:</b>\n"
                "<pre>/check Ya has respondido esto muchs veces.</pre>"
            ),
            parse_mode="HTML"
        )
        return

    SYSTEM_INSTRUCTIONS = """\
    Eres un asistente experto en redacción profesional.

    Tu tarea consta de DOS PASOS OBLIGATORIOS:

    PASO 1: Observaciones
    - Analiza el mensaje de forma LITERAL.
    - Detecta SOLO errores que estén explícitamente presentes en el texto.
    - NO infieras errores comunes ni supongas palabras que el usuario no haya escrito.
    - Redacta cada observación de forma MUY concisa.
    - Usa el formato: tipo de error + corrección breve.
      Ejemplo: "Error ortográfico: 'eh' → 'he'".

    Revisa únicamente:
    - Ortografía
    - Gramática
    - Claridad
    - Tono profesional

    PASO 2: Versión corregida
    - Genera una versión corregida del mensaje.
    - La corrección DEBE solucionar explícitamente TODAS las observaciones del PASO 1.
    - NO introduzcas cambios que no estén justificados por las observaciones.
    - NO conviertas el mensaje en un correo largo.
    - NO añadas información nueva.

    Formato OBLIGATORIO de la respuesta:

    <b>Observaciones:</b>
    - Observación 1
    - Observación 2 (si aplica)

    <b>Versión corregida:</b>
    <pre>Texto corregido aquí</pre>

    Reglas estrictas:
    - Si no hay errores, indícalo claramente y no modifiques el texto.
    - Usa SOLO HTML compatible con Telegram.
    - NO uses <p>, <br>, <div> ni etiquetas no soportadas.
    - Usa saltos de línea reales (\\n).
    """

    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nMensaje:\n{user_text}\n\nRespuesta:"

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
    temp_msg = await update.message.reply_text("🔍 Analizando el mensaje...")

    try:
        ai_text = await generate_response(prompt)
    except Exception as e:
        ai_text = f"Error al analizar el mensaje: {e}"
    finally:
        typing_done.set_result(True)

    ai_text = await generate_response(prompt)
    ai_text = sanitize_all(ai_text)

    await temp_msg.edit_text(ai_text, parse_mode="HTML")


def sanitize_telegram_html(text: str) -> str:
    # Remove unsupported HTML tags that models sometimes generate
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        text = text.replace(tag, "")
    return text
