async def reject_if_busy(update, context, key="is_busy"):
    if context.user_data.get(key):
        await update.message.reply_text(
            "⏳ <b>Solicitud en curso</b>\n\n"
            "Espera a que termine antes de enviar otra.",
            parse_mode="HTML",
        )
        return True
    return False
