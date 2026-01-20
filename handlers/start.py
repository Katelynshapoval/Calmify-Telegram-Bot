from telegram import Update
from telegram.ext import ContextTypes
import textwrap


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        textwrap.dedent("""\
            <b>¡Hola! 👋</b>

            Soy tu asistente para redactar mensajes profesionales.
            Puedo ayudarte a:
            - Convertir notas rápidas o mensajes informales en correos claros y profesionales (/rewrite).
            - Dar consejos prácticos de redacción y errores comunes a evitar (/tip).
            - Revisar errores de ortografía, gramática y tono, y sugerir correcciones (/check).
            - Acortar mensajes largos manteniendo claridad y profesionalismo (/shorten).
            - Traducir y pulir mensajes a otros idiomas (/translate).
            - Analizar imágenes técnicas, explicarlas o responder a tu solicitud (/explainimg).

            Para ver todos los comandos y ejemplos de uso, escribe <b>/help</b>.
        """),
        parse_mode="HTML"
    )
