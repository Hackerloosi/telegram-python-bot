import json
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= BASIC CONFIG =================

BOT_TOKEN = "8205122688:AAE48BND_nVDNfkIulK_GldTN3QTSUJF9r0"
ADMIN_ID = 1609002531
API_URL = "https://giga-seven.vercel.app/api?key=NIGHTFALLHUB&num="

APPROVED_FILE = "approved_users.json"
PENDING_FILE = "pending_users.json"
BANNED_FILE = "banned_users.json"

# ================= FILE STORAGE =================

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

approved_users = load_json(APPROVED_FILE)
pending_users = load_json(PENDING_FILE)
banned_users = load_json(BANNED_FILE)

# ================= HELPERS =================

def get_username(user):
    return f"@{user.username}" if user.username else "@NoUsername"

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    if uid in banned_users:
        await update.message.reply_text("🚫 You are banned.")
        return

    if uid in approved_users or user.id == ADMIN_ID:
        await update.message.reply_text(
            "📱 Send 10-digit Indian mobile number\n"
            "🤖 Bot Status: ONLINE 🟢"
        )
        return

    if uid not in pending_users:
        pending_users[uid] = {
            "name": user.first_name,
            "username": user.username
        }
        save_json(PENDING_FILE, pending_users)

        await context.bot.send_message(
            ADMIN_ID,
            f"🔔 New Approval Request\n\n"
            f"{user.first_name} ({get_username(user)})\n"
            f"ID: {user.id}\n\n"
            f"Approve using:\n/approve {user.id}"
        )

    await update.message.reply_text(
        "⏳ Awaiting approval from owner…"
    )

# ================= APPROVE =================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        return

    uid = context.args[0]
    user = pending_users.pop(uid, None)

    if not user:
        await update.message.reply_text("User not found.")
        return

    approved_users[uid] = user
    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)

    await update.message.reply_text(
        f"✅ Approved:\n"
        f"{user['name']} (@{user.get('username') or 'NoUsername'})\n"
        f"ID: {uid}"
    )

    await context.bot.send_message(
        int(uid),
        "✅ Owner approved you!\nSend /start"
    )

# ================= ADMIN PANEL =================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🗑 Delete User", callback_data="delete_menu")]
    ]

    await update.message.reply_text(
        "👑 Admin Panel",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= DELETE USER =================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "delete_menu":
        if not approved_users:
            await query.edit_message_text("No approved users.")
            return

        buttons = []
        for uid, info in approved_users.items():
            uname = f"@{info['username']}" if info.get("username") else "@NoUsername"
            buttons.append([
                InlineKeyboardButton(
                    f"{info['name']} ({uname})",
                    callback_data=f"delete_{uid}"
                )
            ])

        await query.edit_message_text(
            "🗑 Select user to delete:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data.startswith("delete_"):
        uid = query.data.split("_")[1]

        approved_users.pop(uid, None)
        pending_users.pop(uid, None)
        banned_users.pop(uid, None)

        save_json(APPROVED_FILE, approved_users)
        save_json(PENDING_FILE, pending_users)
        save_json(BANNED_FILE, banned_users)

        await query.edit_message_text(
            f"🗑 User deleted\nID: {uid}\n"
            f"User must request approval again."
        )

# ================= NUMBER SEARCH =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in approved_users and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⏳ Awaiting approval…")
        return

    text = update.message.text.strip()

    if not text.isdigit() or len(text) != 10:
        await update.message.reply_text("❌ Invalid number.")
        return

    await update.message.reply_text("🔍 Searching…")

    try:
        res = requests.get(API_URL + text, timeout=10).json()
    except:
        await update.message.reply_text("❌ API error.")
        return

    if not res.get("success"):
        await update.message.reply_text("❌ No data found.")
        return

    msg = ""
    for i, p in enumerate(res["result"], 1):
        email = p.get("EMAIL") or "Email Not Found ❌"
        msg += (
            f"👤 Person {i}\n"
            f"Name: {p.get('NAME','')}\n"
            f"Mobile: {p.get('MOBILE','')}\n"
            f"Aadhaar No: {p.get('AADHAR_NUMBER','')}\n"
            f"Email: {email}\n\n"
        )

    msg += "━━━━━━━━━━━━━━\n🤖 Bot Made by @Mafiakabaap"
    await update.message.reply_text(msg)

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is ONLINE 🟢")
    app.run_polling()

if __name__ == "__main__":
    main()
