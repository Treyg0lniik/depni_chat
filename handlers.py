from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from db import add_chat, get_user, save_user, get_all_users
from utils import ensure_registered, seconds_until_next_daily, format_timer, is_admin
from config import ADMIN_ID, ADMIN_USERNAME
from telegram import InputFile
from db import get_backup, get_user, save_user, give_capybaras, get_all_chats
from game import create_room, join_room, show_profile

DAILY_REWARD = 1000

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    user["name"] = update.effective_user.username or update.effective_user.first_name
    save_user(update.effective_user.id, user)

    # Сохраняем чат, если это не личка
    if update.effective_chat.type != "private":
        add_chat(update.effective_chat.id, update.effective_chat.title)

    await update.message.reply_text("Добро пожаловать в деп казино! 🎰\n Тут вы можете испытать свою удачу! Скорее пишите /daily и /dap !")

@ensure_registered
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if seconds_until_next_daily(user["last_daily"]) > 0:
        await update.message.reply_text("Ты уже получал ежедневную награду сегодня.")
        return

    user["capybaras"] += DAILY_REWARD
    user["last_daily"] = datetime.now().isoformat()
    save_user(user_id, user)
    await update.message.reply_text(f"Ты получил {DAILY_REWARD} 🪙 капибар!")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    sorted_users = sorted(users.items(), key=lambda x: x[1]["capybaras"], reverse=True)[:10]
    text = "🏆 Топ 10 игроков:\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        text += f"{i}. @{data['name']}: {data['capybaras']} капибар\n"
    await update.message.reply_text(text)

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_admin(update):
        with get_backup() as f:
            await update.message.reply_document(InputFile(f, filename="backup.json"))
    else:
        await update.message.reply_text("У тебя нет доступа к бэкапу.")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_profile(update, context)

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await join_room(update, context)

async def cmd_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.id != ADMIN_ID:
        await update.message.reply_text("❌ Только админ может использовать эту команду.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Использование: /give @username 100")
        return

    username = context.args[0].lstrip("@")
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Сумма должна быть числом.")
        return

    from db import find_user_by_username, give_capybaras

    user_id, user = find_user_by_username(username)
    if user is None:
        await update.message.reply_text("Пользователь не найден.")
        return

    new_balance = give_capybaras(user_id, amount)
    await update.message.reply_text(f"✅ Выдано {amount} капибар @{username}. Новый баланс: {new_balance}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if sender.username != ADMIN_USERNAME:
        return  # игнорируем чужие ЛС

    text = update.message.text
    if not text.startswith("broadcast "):
        return

    message = text[len("broadcast "):]
    chats = get_all_chats()
    count = 0

    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id, message)
            count += 1
        except Exception as e:
            print(f"Не удалось отправить сообщение в чат {chat_id}: {e}")

    await update.message.reply_text(f"✅ Сообщение разослано в {count} чатов.")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_reply))


