import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response
# from services.openrouter import generate_response
from utils.sanitize import sanitize_all


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Instructions for the model: generate a single useful tip about common writing mistakes
    SYSTEM_INSTRUCTIONS = """\
Eres un experto en comunicación profesional y redacción corporativa. 
Genera **únicamente un consejo concreto sobre un error común** que cometen las personas al escribir correos o mensajes laborales. 
El consejo debe ser **directo, útil y aplicable inmediatamente**, máximo 1 frase. 
No escribas introducciones, listas ni recomendaciones obvias.
"""

    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nConsejo:"

    # Show "typing..." action while waiting for AI response
    typing_done = asyncio.get_event_loop().create_future()

    async def send_typing():
        while not typing_done.done():
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(5)

    asyncio.create_task(send_typing())

    # Send a temporary placeholder message
    temp_msg = await update.message.reply_text("⏳ Generando consejo...")

    try:
        # Generate the tip using Ollama
        ai_text = await generate_response(prompt)
    except Exception as e:
        ai_text = f"Error generating tip: {e}"
    finally:
        # Stop the typing indicator
        typing_done.set_result(True)

    # Replace literal \n with actual line breaks
    ai_text = await generate_response(prompt)
    ai_text = sanitize_all(ai_text)

    # Replace the temporary message with the AI-generated tip
    await temp_msg.edit_text(ai_text, parse_mode="HTML")
