from telegram import Update
from telegram.ext import ContextTypes
import textwrap


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        textwrap.dedent("""\
<b>📌 Comandos disponibles</b>

<b>/start</b> - Inicia el bot.
Ejemplo: <pre>/start</pre>

<b>/help</b> - Muestra esta guía.
Ejemplo: <pre>/help</pre>

<b>/tip</b> - Consejo práctico de redacción profesional.
Ejemplo: <pre>/tip</pre>

<b>/rewrite</b> - Convierte un mensaje informal o brusco en un correo profesional.
Ejemplo: <pre>/rewrite Ya he respondido a esto varias veces, deberían revisarlo.</pre>

<b>/translate</b> - Traduce y pule un mensaje al idioma indicado.
Ejemplo: <pre>/translate inglés Hola, solo quería confirmar la reunión de mañana.</pre>

<b>/check</b> - Revisa errores de ortografía, gramática y tono, y sugiere correcciones.
Ejemplo: <pre>/check Ya has respondido esto muchs veces.</pre>

<b>/shorten</b> - Hace un mensaje largo más conciso y directo.
Ejemplo: <pre>/shorten Hola, solo quería comentar que esta cuestión ya ha sido respondida varias veces y si necesitas puedo enviarte nuevamente la información.</pre>
        """),
        parse_mode="HTML"
    )
