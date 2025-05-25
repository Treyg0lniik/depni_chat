import secrets
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user, save_user
from utils import ensure_registered, seconds_until_next_daily, format_timer
import asyncio
import random
from telegram.error import RetryAfter

rooms = {}  # room_code -> room_data

async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await msg.edit_text(text)
    except:
        pass

@ensure_registered
async def create_room(update, context):
    try:
        amount = int(context.args[0])
    except:
        return await update.message.reply_text("Укажи сумму депа: /dap 50")

    user_id = update.effective_user.id
    user = get_user(user_id)
    if user["capybaras"] < amount:
        return await update.message.reply_text("Недостаточно капибар для депа :(")

    user["capybaras"] -= amount
    save_user(user_id, user)

    # Генерируем случайный код комнаты
    room_code = secrets.token_hex(3)  # 6 символов
    room_msg = await update.message.reply_text(
        f"🎲 Комната {room_code} открыта!\n"
        f"Ставка: {amount} капибар\n"
        f"Участвуй, ответив на это сообщение числом.\n"
        f"⏳ Осталось 60 сек.\n"
        f"Депальщиков: 1 (сумма пула: {amount})"
    )

    rooms[room_code] = {
        "creator": user_id,
        "bet": amount,
        "players": {user_id: amount},
        "msg": room_msg,
        "active": True,
    }
    asyncio.create_task(countdown(room_code))

@ensure_registered
async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied = update.message.reply_to_message
    if not replied:
        return
    room = next((r for r in rooms.values() if r["msg"].message_id == replied.message_id and r["active"]), None)
    if not room:
        return

    user_id = update.effective_user.id
    user = get_user(user_id)
    bet = room["bet"]

    if user["capybaras"] < bet:
        await update.message.reply_text("Недостаточно капибар для депа....")
        return

    if user_id in room["players"]:
        await update.message.reply_text("Ты уже депнул.")
        return

    user["capybaras"] -= bet
    save_user(user_id, user)
    room["players"][user_id] = bet
    await update.message.reply_text("Ура, вы депнули свою зп!")

async def countdown(room_id):
    for i in range(60, 0, -1):
        if room_id not in rooms or not rooms[room_id]["active"]:
            return
        if i % 3 == 0:  # Обновлять каждую 3 секунду
            msg = rooms[room_id]["msg"]
            try:
                await msg.edit_text(f"🎲 Комната #{room_id} открыта!\n"
                                    f"деп: {rooms[room_id]['bet']} капибар\n"
                                    f"депальщиков: {len(rooms[room_id]['players'])}\n"
                                    f"⏳ Осталось: {i} сек.")
            except:
                pass
        await asyncio.sleep(1)

    if len(rooms[room_id]["players"]) < 2:
        await rooms[room_id]["msg"].reply_text("Никто не депнул. Игра отменена.")
        for uid, amount in rooms[room_id]["players"].items():
            user = get_user(uid)
            user["capybaras"] += amount
            save_user(uid, user)
    else:
        await spin_wheel(room_id)

    rooms[room_id]["active"] = False

import asyncio
import random
from db import get_user, save_user
from telegram.error import RetryAfter

async def safe_edit(msg, text):
    try:
        await msg.edit_text(text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await msg.edit_text(text)
    except:
        pass

async def spin_wheel(room_id):
    room = rooms[room_id]
    players = list(room["players"].keys())
    # создаём пул для определения победителя
    pool = []
    for uid, bet in room["players"].items():
        pool.extend([uid] * bet)
    winner = random.choice(pool)
    total_pot = sum(room["players"].values())

    # собираем цикл обхода: каждый пользователь поочередно + в конце победитель
    cycle = players * 3  # три полных круга
    cycle.append(winner)  # и одна финальная остановка

    for pid in cycle:
        # формируем текст: кубок над pid, остальные — ниже
        cup = f"🏆 @{get_user(pid)['name']}"
        others = [f"@{get_user(u)['name']}" for u in players if u != pid]
        text = "🎡 Крутим колесо...\n\n" + cup
        if others:
            text += "\n" + "\n".join(others)

        await safe_edit(room["msg"], text)
        # пауза короче в начале, подлиннее перед финалом
        if pid == winner:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(0.5)

    # выдача выигрыша
    user_win = get_user(winner)
    user_win["capybaras"] += total_pot
    save_user(winner, user_win)

    # финальное сообщение
    await room["msg"].reply_text(
        f"🎉 Победил @{user_win['name']} и забрал {total_pot} капибар!"
    )


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    seconds = seconds_until_next_daily(user["last_daily"])
    timer = format_timer(seconds) if seconds else "доступна!"
    await update.message.reply_text(
        f"👤 Профиль @{user['name']}\n"
        f"🪙 Капибары: {user['capybaras']}\n"
        f"🎁 Ежедневка: {timer}"
    )

async def safe_edit_text(msg, text):
    try:
        await msg.edit_text(text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await msg.edit_text(text)
    except Exception:
        pass