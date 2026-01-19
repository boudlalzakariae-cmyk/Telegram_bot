import telebot, json, os, time, random, string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("8508415510:AAHa5oL4UO-9CDENNE9ZyXfbKEA6p5mGOTE")
bot = telebot.TeleBot(8508415510:AAHa5oL4UO-9CDENNE9ZyXfbKEA6p5mGOTE)

# ===== LOAD / SAVE =====
def load(path):
    with open(path, "r") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

users = load("database/users.json")
codes = load("database/codes.json")
logs  = load("database/logs.json")
config = load("config.json")
ADMIN = config["admin_id"]

# ===== HELPERS =====
def log(text):
    logs.append({"time": int(time.time()), "log": text})
    save("database/logs.json", logs)

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "points": 0,
            "vip": False,
            "spam": 0,
            "last": 0
        }
        save("database/users.json", users)
    return users[uid]

def anti_spam(uid):
    u = get_user(uid)
    now = time.time()
    if now - u["last"] < 1:
        u["spam"] += 1
        save("database/users.json", users)
        return u["spam"] > 3
    u["last"] = now
    u["spam"] = 0
    save("database/users.json", users)
    return False

# ===== MENU =====
def main_menu(uid):
    u = get_user(uid)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("⭐ Points", callback_data="points"),
        InlineKeyboardButton("📂 Files", callback_data="files"),
        InlineKeyboardButton("💎 VIP", callback_data="vip"),
        InlineKeyboardButton("⚙️ Get Points", callback_data="getpoints")
    )
    return kb

# ===== START =====
@bot.message_handler(commands=["start"])
def start(m):
    if anti_spam(m.from_user.id): return
    u = get_user(m.from_user.id)
    bot.send_message(
        m.chat.id,
        f"""𝗛𝗲𝗹𝗹𝗼 𝗲𝘃𝗲𝗿𝘆𝗼𝗻𝗲 👋
𝗪𝗲 𝘄𝗶𝘀𝗵 𝘆𝗼𝘂 𝗮 𝘄𝗼𝗻𝗱𝗲𝗿𝗳𝘂𝗹 𝗲𝘅𝗽𝗲𝗿𝗶𝗲𝗻𝗰𝗲 🍁

👤 ID: {m.from_user.id}
⭐ Points: {u['points']}
💎 Status: {"VIP" if u['vip'] else "Free"}""",
        reply_markup=main_menu(m.from_user.id)
    )

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id
    u = get_user(uid)

    if c.data == "points":
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, f"⭐ Your Points: {u['points']}")

    elif c.data == "files":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("📱 iPhone", callback_data="iphone"),
            InlineKeyboardButton("🤖 Android", callback_data="android")
        )
        bot.edit_message_text("📂 Choose:", c.message.chat.id, c.message.id, reply_markup=kb)

    elif c.data == "iphone":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("IPA (200⭐)", callback_data="buy_ipa"),
            InlineKeyboardButton("DYLIB (200⭐)", callback_data="buy_dylib")
        )
        bot.edit_message_text("📱 iPhone:", c.message.chat.id, c.message.id, reply_markup=kb)

    elif c.data == "android":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("Hologram", callback_data="buy_holo"),
            InlineKeyboardButton("Menu Root Device", callback_data="buy_root")
        )
        bot.edit_message_text("🤖 Android:", c.message.chat.id, c.message.id, reply_markup=kb)

    elif c.data.startswith("buy_"):
        if u["points"] < 200:
            bot.send_message(c.message.chat.id, "❌ Not enough points")
            return
        u["points"] -= 200
        save("database/users.json", users)

        link = {
            "buy_ipa": config["ipa_site"],
            "buy_dylib": config["dylib_site"],
            "buy_holo": config["hologram_site"],
            "buy_root": config["rootdevice_site"]
        }[c.data]

        bot.send_message(c.message.chat.id, f"✅ Purchased\n🔗 {link}")
        log(f"{uid} bought {c.data}")

    elif c.data == "vip":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                "🎁 Send 15 Telegram Stars",
                url=f"https://t.me/{bot.get_me().username}"
            ),
            InlineKeyboardButton("🆘 Support", url=config["support"])
        )
        bot.edit_message_text(
            "💎 VIP\n\nSend **15 Telegram Stars** to admin.\nThen admin confirms.",
            c.message.chat.id, c.message.id,
            reply_markup=kb,
            parse_mode="Markdown"
        )

    elif c.data == "getpoints":
        bot.send_message(c.message.chat.id, "🔑 Send your code:")

# ===== CODES =====
@bot.message_handler(func=lambda m: m.text and m.text in codes)
def redeem(m):
    uid = str(m.from_user.id)
    if codes[m.text]["used"]:
        bot.reply_to(m, "❌ Code already used")
        return
    pts = codes[m.text]["points"]
    users[uid]["points"] += pts
    codes[m.text]["used"] = True
    save("database/users.json", users)
    save("database/codes.json", codes)
    bot.reply_to(m, f"✅ {pts} Points added")
    log(f"{uid} redeemed {m.text}")

# ===== ADMIN =====
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN)
def admin(m):
    if m.text.startswith("/addcode"):
        pts = int(m.text.split()[1])
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{key}-{pts}"
        codes[code] = {"points": pts, "used": False}
        save("database/codes.json", codes)
        bot.reply_to(m, f"🔑 Code: `{code}`", parse_mode="Markdown")

    elif m.text.startswith("/confirm"):
        uid = m.text.split()[1]
        users[uid]["points"] += 200
        users[uid]["vip"] = True
        save("database/users.json", users)
        bot.send_message(uid, "💎 VIP Activated +200 Points")

    elif m.text.startswith("/set"):
        _, k, v = m.text.split(" ",2)
        config[f"{k}_site"] = v
        save("config.json", config)
        bot.reply_to(m, "✅ Updated")

    elif m.text == "/stats":
        bot.reply_to(m, f"👥 Users: {len(users)}\n🔑 Codes: {len(codes)}")

bot.infinity_polling()
