import os
import json
import requests

from telegram import (
    Update,
    BotCommand,
    BotCommandScopeChat,
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

# ================= CONFIG =================

ADMIN_ID = 1609002531
API_URL = "https://giga-seven.vercel.app/api?key=NIGHTFALLHUB&num="

APPROVED_FILE = "approved_users.json"
PENDING_FILE = "pending_users.json"
BANNED_FILE = "banned_users.json"

# ================= STORAGE =================

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

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    status = (
        "🤖 Bot Status: ONLINE 🟢\n"
        "⚡ Service: Active\n\n"
    )

    if uid in banned_users:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    if user.id == ADMIN_ID:
        await update.message.reply_text(
            status +
            "📱 Please Send Mobile No.\n"
            "Without +91\n"
            "In 10 Digit\n\n"
            "[ Note : Only Indian No. Allowed ]"
        )
        return

    if uid in approved_users:
        await update.message.reply_text(
            status +
            "📱 Please Send Mobile No.\n"
            "Without +91\n"
            "In 10 Digit\n\n"
            "[ Note : Only Indian No. Allowed ]"
        )
        return

    if uid not in pending_users:
        pending_users[uid] = user.full_name
        save_json(PENDING_FILE, pending_users)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 New User Approval Request\n\n"
                f"👤 Name: {user.full_name}\n"
                f"🆔 User ID: {uid}\n\n"
                f"Approve using:\n/approve {uid}"
            )
        )

    await update.message.reply_text(
        status +
        "⏳ You are not approved yet.\n"
        "Please wait for admin approval."
    )

# ================= ADMIN =================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    uid = context.args[0]
    approved_users[uid] = True
    pending_users.pop(uid, None)

    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)

    await update.message.reply_text(f"✅ Approved user {uid}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return

    uid = context.args[0]

    banned_users[uid] = True
    approved_users.pop(uid, None)
    pending_users.pop(uid, None)

    save_json(BANNED_FILE, banned_users)
    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)

    await update.message.reply_text(f"🚫 User {uid} banned")

async def pending_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not pending_users:
        await update.message.reply_text("✅ No pending users.")
        return

    msg = "⏳ Pending Users:\n\n"
    for uid, name in pending_users.items():
        msg += f"• {name} ({uid})\n"

    await update.message.reply_text(msg)

async def approved_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not approved_users:
        await update.message.reply_text("No approved users.")
        return

    msg = "✅ Approved Users:\n\n"
    for uid in approved_users:
        msg += f"• {uid}\n"

    await update.message.reply_text(msg)

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not banned_users:
        await update.message.reply_text("✅ No banned users.")
        return

    buttons = [
        [InlineKeyboardButton(f"Unban {uid}", callback_data=f"unban:{uid}")]
        for uid in banned_users
    ]

    await update.message.reply_text(
        "🚫 Banned Users:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.split(":")[1]
    banned_users.pop(uid, None)
    save_json(BANNED_FILE, banned_users)

    await query.edit_message_text(f"✅ User {uid} unbanned")

# ================= MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid in banned_users:
        return

    if update.effective_user.id != ADMIN_ID and uid not in approved_users:
        return

    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ Send valid 10-digit Indian number.")
        return

    await update.message.reply_text("🔍 Fetching details...")

    try:
        res = requests.get(API_URL + number, timeout=15)
        data = res.json()
    except:
        await update.message.reply_text("❌ API Error.")
        return

    if not data.get("success") or not data.get("result"):
        await update.message.reply_text("❌ No data found.")
        return

    msg = ""
    for i, p in enumerate(data["result"], 1):
        email = p.get("EMAIL", "").strip().lower()
        email_text = email if email else "Email Not Found ❌"

        msg += (
            f"👤 Person {i} Details\n"
            f"Name : {p.get('NAME','')}\n"
            f"Father Name : {p.get('FATHER_NAME','')}\n"
            f"Address : {p.get('ADDRESS','').replace('!', ', ')}\n"
            f"Sim : {p.get('CIRCLE/SIM','')}\n"
            f"Mobile No. : {p.get('MOBILE','')}\n"
            f"Alternative No. : {p.get('ALTERNATIVE_MOBILE','')}\n"
            f"Aadhaar No. : {p.get('AADHAR_NUMBER','')}\n"
            f"Email ID : {email_text}\n\n"
        )

    msg += "━━━━━━━━━━━━━━\n🤖 Bot Made by @Mafiakabaap"
    await update.message.reply_text(msg)

# ================= COMMAND MENU =================

async def set_admin_commands(app):
    commands = [
        BotCommand("start", "Start bot"),
        BotCommand("approve", "Approve user"),
        BotCommand("ban", "Ban user"),
        BotCommand("unban", "Unban user"),
        BotCommand("approved", "Approved users"),
        BotCommand("pending", "Pending users"),
    ]
    await app.bot.set_my_commands(
        commands,
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
    )

# ================= MAIN =================

def main():
    token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("approved", approved_list))
    app.add_handler(CommandHandler("pending", pending_list))
    app.add_handler(CallbackQueryHandler(unban_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.post_init = set_admin_commands

    print("🤖 Bot running on Railway")
    app.run_polling()

# ================= ENTRY =================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal startup error:", e)
