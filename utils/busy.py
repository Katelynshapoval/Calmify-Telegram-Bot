from telegram import Update
from telegram.ext import ContextTypes

BUSY_KEY = "is_busy"


async def check_and_set_busy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Returns True if user is already busy (and sends warning).
    Returns False and sets busy flag otherwise.
    """
    if context.user_data.get(BUSY_KEY):
        await update.message.reply_text(
            (
                "⏳ <b>Solicitud en curso</b>\n\n"
                "Ya estoy procesando una solicitud. "
                "Espera a que termine antes de enviar otra."
            ),
            parse_mode="HTML",
        )
        return True

    context.user_data[BUSY_KEY] = True
    return False


def clear_busy(context: ContextTypes.DEFAULT_TYPE):
    context.user_data[BUSY_KEY] = False
