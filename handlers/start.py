from telegram import Update
from telegram.ext import ContextTypes
import textwrap


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        textwrap.dedent("""\
            <b>¡Hola! 👋</b>

            Soy tu asistente para redactar mensajes profesionales.
            Si me envías notas rápidas, mensajes informales o escritos con prisa, puedo ayudarte a convertirlos en correos o mensajes claros y educados.

            También puedo ajustar el tono: más formal, más cordial o más directo, y evitar que suene brusco.

            Por ejemplo, si escribes algo como:
            <pre>Ya he respondido a esta pregunta como cinco veces. Lo sabrías si te hubieras molestado en mirar antes de repetirla.</pre>

            Yo puedo convertirlo en algo como:
            <pre>Hola,

            Solo quería comentarte que esta cuestión ya la he respondido en varias ocasiones.
            Si quieres, puedo enviarte la información de nuevo o ayudarte a encontrarla.

            Quedo a tu disposición para cualquier otra cosa que necesites.

            Un saludo,
            [Tu nombre]</pre>

            Envíame tu mensaje y te ayudo a darle un tono profesional sin complicaciones.
        """),
        parse_mode="HTML"
    )
