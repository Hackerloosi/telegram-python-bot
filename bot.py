import os
import json
import requests

from telegram import (
    Update,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
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

def user_text(uid, info):
    name = info.get("name", "Unknown")
    username = info.get("username")
    uname = f"@{username}" if username else "NoUsername"
    return f"{name} ({uname})\nID: {uid}"

# ================= BROADCAST FLAG =================

ADMIN_BROADCAST_MODE = False

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

    if user.id == ADMIN_ID or uid in approved_users:
        await update.message.reply_text(
            status +
            "📱 Please Send Mobile No.\n"
            "Without +91\n"
            "In 10 Digit\n\n"
            "[ Note : Only Indian No. Allowed ]"
        )
        return

    if uid not in pending_users:
        pending_users[uid] = {
            "name": user.full_name,
            "username": user.username
        }
        save_json(PENDING_FILE, pending_users)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 New User Approval Request\n\n"
                f"{user_text(uid, pending_users[uid])}\n\n"
                f"Approve using:\n/approve {uid}"
            )
        )

    await update.message.reply_text(
        status +
        "⏳ Awaiting for approval from owner...\n"
        "🕒 Please wait, you will be notified once approved."
    )

# ================= ADMIN =================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        return

    uid = context.args[0]

    if uid not in pending_users:
        await update.message.reply_text("User not found in pending list.")
        return

    approved_users[uid] = pending_users[uid]
    pending_users.pop(uid)

    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)

    await update.message.reply_text(f"✅ Approved:\n{user_text(uid, approved_users[uid])}")

    await context.bot.send_message(
        chat_id=int(uid),
        text="✅ Owner approved you!\n\nSend /start to begin."
    )

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        return

    uid = context.args[0]

    info = approved_users.pop(uid, None) or pending_users.pop(uid, None)
    if not info:
        await update.message.reply_text("User not found.")
        return

    banned_users[uid] = info

    save_json(APPROVED_FILE, approved_users)
    save_json(PENDING_FILE, pending_users)
    save_json(BANNED_FILE, banned_users)

    await update.message.reply_text(f"🚫 Banned:\n{user_text(uid, info)}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_BROADCAST_MODE

    if update.effective_user.id != ADMIN_ID:
        return

    ADMIN_BROADCAST_MODE = True
    await update.message.reply_text(
        "📢 Broadcast Mode\n\nSend message to broadcast."
    )

async def approved_list(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    if not approved_users:
        await update.message.reply_text("No approved users.")
        return

    msg = "✅ Approved Users:\n\n"
    for uid, info in approved_users.items():
        msg += user_text(uid, info) + "\n\n"

    await update.message.reply_text(msg)

async def pending_list(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    if not pending_users:
        await update.message.reply_text("No pending users.")
        return

    msg = "⏳ Pending Users:\n\n"
    for uid, info in pending_users.items():
        msg += user_text(uid, info) + "\n\n"

    await update.message.reply_text(msg)

# ================= MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_BROADCAST_MODE

    # Broadcast
    if update.effective_user.id == ADMIN_ID and ADMIN_BROADCAST_MODE:
        ADMIN_BROADCAST_MODE = False
        text = update.message.text

        for uid in approved_users:
            try:
                await context.bot.send_message(int(uid), f"📢 Announcement\n\n{text}")
            except:
                pass

        await update.message.reply_text("✅ Broadcast sent.")
        return

    uid = str(update.effective_user.id)

    if uid not in approved_users and update.effective_user.id != ADMIN_ID:
        return

    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text("❌ Send valid 10-digit Indian number.")
        return

    await update.message.reply_text("🔍 Fetching details, please wait...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        response = requests.get(API_URL + number, headers=headers, timeout=30)

        try:
            data = response.json()
        except:
            await update.message.reply_text(f"❌ HTTP {response.status_code}\n\n{response.text}")
            return

    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")
        return

    # If API returns server error JSON
    if not data.get("success"):
        await update.message.reply_text(json.dumps(data, indent=2))
        return

    # Handle nested result
    result_data = data.get("result")

    if isinstance(result_data, dict):
        result_list = result_data.get("result", [])
    else:
        result_list = result_data

    if not result_list:
        await update.message.reply_text("❌ No data found.")
        return

    # Send RAW JSON like other bot
    await update.message.reply_text(
        json.dumps(data, indent=2),
        disable_web_page_preview=True
    )

# ================= COMMAND MENU =================

async def set_admin_commands(app):
    # Default users
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Start the bot")
        ],
        scope=BotCommandScopeDefault()
    )

    # Admin menu (START FIRST)
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Start the bot"),
            BotCommand("admin", "Broadcast message"),
            BotCommand("approve", "Approve user"),
            BotCommand("ban", "Ban user"),
            BotCommand("approved", "Approved users"),
            BotCommand("pending", "Pending users"),
        ],
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
    )

# ================= MAIN =================

def main():
    token = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("approved", approved_list))
    app.add_handler(CommandHandler("pending", pending_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.post_init = set_admin_commands
    app.run_polling()

if __name__ == "__main__":
    main()
