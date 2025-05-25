import json
import os
from datetime import datetime, timedelta

DB_FILE = "data.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return {"chats": {}, "users": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # гарантируем, что "chats" всегда есть
    if "chats" not in data:
        data["chats"] = {}
    return data


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_backup():
    return open(DB_FILE, "rb")

def get_user(user_id):
    data = load_data()
    user = data.setdefault(str(user_id), {
        "capybaras": 0,
        "last_daily": None,
        "name": "",
    })
    return user

def save_user(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

def get_all_users():
    data = load_data()
    # фильтруем только пользователей (те, где ключи — это числа)
    users = {int(k): v for k, v in data.items() if k.isdigit()}
    return users

def find_user_by_username(username):
    data = load_data()["users"]
    for uid, u in data.items():
        if u.get("name") == username.lstrip("@"):
            return int(uid), u
    return None, None

def give_capybaras(user_id, amount):
    user = get_user(user_id)
    user["capybaras"] += amount
    save_user(user_id, user)
    return user["capybaras"]

def add_chat(chat_id, title=None):
    data = load_data()
    chats = data.setdefault("chats", {})
    chats[str(chat_id)] = title or ""
    save_data(data)

def get_all_chats():
    data = load_data()
    return [int(cid) for cid in data.get("chats", {}).keys()]
