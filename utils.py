from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_USERNAME

async def is_admin(update: Update) -> bool:
    return update.effective_user.username and \
           f"@{update.effective_user.username}" == ADMIN_USERNAME

def seconds_until_next_daily(last_claim):
    if not last_claim:
        return 0
    last_time = datetime.fromisoformat(last_claim)
    next_time = last_time + timedelta(days=1)
    delta = (next_time - datetime.now()).total_seconds()
    return max(int(delta), 0)

def format_timer(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins:02}:{secs:02}"

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user, save_user

def ensure_registered(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        user = get_user(user_id)
        # считаем, что пользователь зарегистрирован, если у него задан name
        if not user.get("name"):
            # автоматически сохраняем имя, чтобы не было зацикливания
            user["name"] = update.effective_user.username or update.effective_user.first_name
            save_user(user_id, user)
            await update.message.reply_text(
                "❗ Для начала нужно зарегистрироваться: отправь /start"
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
