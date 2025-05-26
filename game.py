import secrets
import asyncio
import random
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.error import RetryAfter
from db import get_user, save_user
from utils import ensure_registered, seconds_until_next_daily, format_timer

# Хранение комнат: код -> данные
rooms = {}  # room_code -> {creator, min_bet, players, msg, active}

async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await msg.edit_text(text)
    except:
        pass

@ensure_registered
async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /dap <минимальная_ставка>
    Открывает комнату с любыми депами от участников, 
    но не ниже указанной суммы.
    """
    try:
        min_bet = int(context.args[0])
    except:
        return await update.message.reply_text("Укажи сумму минимальной ставки: /dap 50")
    
    user_id = update.effective_user.id
    user = get_user(user_id)
    if user["capybaras"] < min_bet:
        return await update.message.reply_text("Недостаточно капибар для депа.")

    # сразу резервируем у создателя его ставкуминимум
    user["capybaras"] -= min_bet
    save_user(user_id, user)

    room_code = secrets.token_hex(3)  # например, 'a1b2c3'
    text = (
        f"🎲 Комната {room_code} открыта!\n"
        f"Минимальная ставка: {min_bet} капибар\n"
        f"⏳ Осталось 60 сек.\n"
        f"🧑‍🤝‍🧑 Участников: 1 (потолок: {min_bet})\n\n"
        "Чтобы зайти — ответь на это сообщение числом (не меньше минимальной ставки)."
    )
    room_msg = await update.message.reply_text(text)

    rooms[room_code] = {
        "creator": user_id,
        "min_bet": min_bet,
        "players": {user_id: min_bet},
        "msg": room_msg,
        "active": True,
    }
    asyncio.create_task(countdown(room_code))

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ловит любой текстовый ответ на сообщение комнаты и пытается сделать деп.
    """
    replied = update.message.reply_to_message
    if not replied:
        return  # не ответ на сообщение
    # находим комнату по ID сообщения
    room = next(
        (r for r in rooms.values() if r["msg"].message_id == replied.message_id and r["active"]),
        None
    )
    if not room:
        return  # не наша комната или закрыта

    # парсим число из текста
    try:
        amount = int(update.message.text.strip())
    except ValueError:
        return  # не число — игнорируем

    user_id = update.effective_user.id
    user = get_user(user_id)
    if amount < room["min_bet"]:
        return await update.message.reply_text(f"Ставка должна быть не меньше {room['min_bet']} капибар.")
    if user["capybaras"] < amount:
        return await update.message.reply_text("Недостаточно капибар для этой ставки.")
    if user_id in room["players"]:
        return await update.message.reply_text("Ты уже участвовал в этой комнате.")

    # списываем и сохраняем
    user["capybaras"] -= amount
    save_user(user_id, user)
    room["players"][user_id] = amount

    # обновляем сообщение комнаты (счётчик участников и сумму пула)
    total_pool = sum(room["players"].values())
    await safe_edit(
        room["msg"],
        f"🎲 Комната {next(code for code, data in rooms.items() if data is room)}\n"
        f"Минимальная ставка: {room['min_bet']} капибар\n"
        f"🧑‍🤝‍🧑 Участников: {len(room['players'])} (пул: {total_pool})\n"
        f"⏳ Осталось: (таймер идёт)\n\n"
        "Ответь числом, чтобы присоединиться."
    )
    await update.message.reply_text(f"Твоя ставка {amount} капибар принята! Удачи!")

async def countdown(room_code: str):
    for i in range(60, 0, -1):
        room = rooms.get(room_code)
        if not room or not room["active"]:
            return
        if i % 5 == 0:  # обновляем каждые 5 сек
            total_pool = sum(room["players"].values())
            await safe_edit(
                room["msg"],
                f"🎲 Комната {room_code}\n"
                f"Минимальная ставка: {room['min_bet']} капибар\n"
                f"🧑‍🤝‍🧑 Участников: {len(room['players'])} (пул: {total_pool})\n"
                f"⏳ Осталось: {i} сек.\n\n"
                "Ответь числом, чтобы присоединиться."
            )
        await asyncio.sleep(1)

    room = rooms.get(room_code)
    if not room or not room["active"]:
        return

    if len(room["players"]) < 2:
        await room["msg"].reply_text("Никто, кроме тебя, не ставил. Деп отменён.")
        # возвращаем ставки
        for uid, amt in room["players"].items():
            u = get_user(uid)
            u["capybaras"] += amt
            save_user(uid, u)
    else:
        await spin_wheel(room_code)

    room["active"] = False

async def spin_wheel(room_code: str):
    room = rooms[room_code]
    players = list(room["players"].keys())
    # создаём пул для вероятностей
    pool = []
    for uid, bet in room["players"].items():
        pool += [uid] * bet
    winner = random.choice(pool)
    total_pot = sum(room["players"].values())

    # анимация кручения
    sequence = players * 2 + [winner]
    for pid in sequence:
        cup = f"🏆 @{get_user(pid)['name']}"
        others = "\n".join(f"@{get_user(u)['name']}" for u in players if u != pid)
        text = f"🎡 Крутим колесо...\n\n{cup}"
        if others:
            text += "\n" + others
        await safe_edit(room["msg"], text)
        await asyncio.sleep(0.3 if pid != winner else 1.5)

    # выдача выигрыша
    win = get_user(winner)
    win["capybaras"] += total_pot
    save_user(winner, win)
    await room["msg"].reply_text(f"🎉 Победил @{win['name']} и забрал весь пул: {total_pot} капибар!")

@ensure_registered
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    secs = seconds_until_next_daily(user["last_daily"])
    timer = format_timer(secs) if secs else "доступна!"
    await update.message.reply_text(
        f"👤 Профиль @{user['name']}\n"
        f"🪙 Капибары: {user['capybaras']}\n"
        f"🎁 Ежедневка: {timer}"
    )