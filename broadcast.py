from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_USERNAME
from db import get_all_chats

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.username
    if sender != ADMIN_USERNAME:
        return await update.message.reply_text("❌ У вас нет прав для этой команды.")
    # Текст и/или фото
    text = update.message.caption or update.message.text or ""
    photo = update.message.photo[-1] if update.message.photo else None

    chats = get_all_chats()
    sent = 0
    for chat_id in chats:
        try:
            if photo:
                await context.bot.send_photo(chat_id, photo=photo.file_id, caption=text, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id, text, parse_mode="HTML")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Разослано в {sent}/{len(chats)} чатов.") 