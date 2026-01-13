import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from services.ollama import generate_response


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Extract the text sent by the user
    user_text = update.message.text

    # System instructions that guide how the AI should rewrite the message
    SYSTEM_INSTRUCTIONS = """\
        Vas a recibir mensajes escritos de forma apresurada o frustrada que después deberán enviarse a un compañero de trabajo o un superior. 
        Tu tarea es reformularlos como correos electrónicos o mensajes profesionales en español de España.  

        Sigue estas reglas estrictamente:

        1. **Neutraliza y suaviza cualquier lenguaje brusco, negativo o frustrado** sin perder la información esencial.  
        2. **Estructura el mensaje como un correo profesional**: saludo inicial, cuerpo claro y despedida formal o cordial.  
        3. Mantén un **tono natural, humano, cercano y ligeramente amable**, proyectando colaboración y profesionalidad.  
        4. Asegúrate de que las frases fluyan y sean fáciles de leer; evita que suene robótico o generado por IA.  
        5. Usa **HTML compatible con Telegram**: `<pre>` y `<b>` donde corresponda, pero evita etiquetas no soportadas como `<br>`.  
        6. No agregues información que no esté en el mensaje original; solo reescribe lo que el usuario envió de manera profesional y amigable.

        El objetivo es que el resultado sea un **correo o mensaje listo para enviar** que suene educado, colaborativo y profesional.
        """

    # Build the final prompt sent to the language model
    prompt = f"{SYSTEM_INSTRUCTIONS}\n\nUsuario: {user_text}\n\nRespuesta:"

    # Future used to signal when the AI response is ready
    typing_done = asyncio.get_event_loop().create_future()

    async def send_typing():
        # Periodically send "typing…" so the user knows the bot is working
        while not typing_done.done():
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(5)

    # Start the typing indicator in the background
    asyncio.create_task(send_typing())

    try:
        # Generate the rewritten professional message
        ai_text = await generate_response(prompt)
    except Exception as e:
        # Fallback message if something goes wrong
        ai_text = f"Error al generar la respuesta: {e}"
    finally:
        # Stop the typing indicator
        typing_done.set_result(True)

    # Send the final response back to the user
    await update.message.reply_text(ai_text, parse_mode="HTML")
