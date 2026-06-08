import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import sqlite3
import time

# ===== CONFIG =====
TOKEN = "vk1.a.8PIfDxNiJ7UMLRSKiWf_GboSxjFdmCG2H6l6eudJb..."  # токен сообщества
GROUP_ID = 123456789  # ID твоего сообщества
OWNER_ID = 730518436   # твой VK ID, главный админ

# ===== VK =====
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

def send(peer_id, message):
    vk.messages.send(peer_id=peer_id, message=message, random_id=0)

# ===== DATABASE =====
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, role INTEGER DEFAULT 0)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS warns (user_id INTEGER, reason TEXT)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS mutes (user_id INTEGER PRIMARY KEY, end_time INTEGER)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS bans (user_id INTEGER PRIMARY KEY, end_time INTEGER, reason TEXT)""")
db.commit()

# ===== ROLES =====
def get_role(user_id):
    if user_id == OWNER_ID:
        return 3
    cursor.execute("SELECT role FROM users WHERE user_id=?", (user_id,))
    r = cursor.fetchone()
    return r[0] if r else 0

def set_role(user_id, role):
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, role))
    db.commit()

# ===== WARNS =====
def add_warn(user_id, reason):
    cursor.execute("INSERT INTO warns VALUES (?, ?)", (user_id, reason))
    db.commit()

# ===== MUTES =====
def mute(user_id, minutes):
    cursor.execute("INSERT OR REPLACE INTO mutes VALUES (?, ?)", (user_id, int(time.time()) + minutes*60))
    db.commit()

def is_muted(user_id):
    cursor.execute("SELECT end_time FROM mutes WHERE user_id=?", (user_id,))
    r = cursor.fetchone()
    return r and r[0] > int(time.time())

# ===== BANS =====
def ban(user_id, days, reason):
    end = -1 if days == -1 else int(time.time()) + days*86400
    cursor.execute("INSERT OR REPLACE INTO bans VALUES (?, ?, ?)", (user_id, end, reason))
    db.commit()

def is_banned(user_id):
    cursor.execute("SELECT end_time FROM bans WHERE user_id=?", (user_id,))
    r = cursor.fetchone()
    if not r:
        return False
    if r[0] == -1:
        return True
    if r[0] < int(time.time()):
        cursor.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
        db.commit()
        return False
    return True

# ===== BOT LOOP =====
print("Бот запущен...")

for event in longpoll.listen():
    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    text = (event.object.message.get("text") or "").lower()
    peer_id = event.object.message.get("peer_id")
    user_id = event.object.message.get("from_id")

    role = get_role(user_id)

    # BAN CHECK
    if is_banned(user_id):
        send(peer_id, "🚫 Вы забанены")
        continue

    # MUTE CHECK
    if is_muted(user_id):
        send(peer_id, "🔇 У вас мут")
        continue

    # HELP
    if text in ["/help", "/h"]:
        send(peer_id,
f"""🤖 Assistant
━━━━━━━━━━━━
/help
/cid
/kick
/mute
/warn
/setrole
/ban
━━━━━━━━━━━━
Роль: {role}""")
        continue

    # CID
    if text == "/cid":
        send(peer_id, f"ID чата: {peer_id}")
        continue

    # KICK
    if text.startswith("/kick") and role >= 1:
        try:
            uid = int(text.split()[1].replace("@id", ""))
            if peer_id > 2000000000:  # чат
                vk.messages.removeChatUser(chat_id=peer_id-2000000000, user_id=uid)
            send(peer_id, "Кик выполнен")
        except:
            send(peer_id, "Ошибка kick")
        continue

    # MUTE
    if text.startswith("/mute") and role >= 1:
        try:
            uid = int(text.split()[1].replace("@id", ""))
            mins = int(text.split()[2])
            mute(uid, mins)
            send(peer_id, "Мут выдан")
        except:
            send(peer_id, "Ошибка mute")
        continue

    # WARN
    if text.startswith("/warn") and role >= 1:
        try:
            uid = int(text.split()[1].replace("@id", ""))
            reason = " ".join(text.split()[2:])
            add_warn(uid, reason)
            send(peer_id, "Варн выдан")
        except:
            send(peer_id, "Ошибка warn")
        continue

    # SET ROLE
    if text.startswith("/setrole") and role >= 2:
        try:
            uid = int(text.split()[1].replace("@id", ""))
            r = int(text.split()[2])
            set_role(uid, r)
            send(peer_id, "Роль изменена")
        except:
            send(peer_id, "Ошибка setrole")
        continue

    # BAN
    if text.startswith("/ban") and role >= 2:
        try:
            uid = int(text.split()[1].replace("@id", ""))
            days = int(text.split()[2])
            reason = " ".join(text.split()[3:])
            ban(uid, days, reason)
            send(peer_id, "Бан выдан")
        except:
            send(peer_id, "Ошибка ban")
        continue