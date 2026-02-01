import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

ADMIN_ID = 1609002531
APPROVED_FILE = "approved_users.json"

def load_approved():
    try:
        with open(APPROVED_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_approved(data):
    with open(APPROVED_FILE, "w") as f:
        json.dump(data, f, indent=2)

approved_users = load_approved()

# ---------- USER ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if update.effective_user.id != ADMIN_ID and uid not in approved_users:
        await update.message.reply_text("⛔ You are not approved.")
        return

    await update.message.reply_text(
        "📱 Please Send Mobile No.\n"
        "Without +91\n"
        "In 10 Digit\n\n"
        "[ Note : Only Indian No. Allowed ]"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if update.effective_user.id != ADMIN_ID and uid not in approved_users:
        return

    text = update.message.text.strip()
    if text.isdigit() and len(text) == 10:
        await update.message.reply_text(f"✅ Number received: {text}")
    else:
        await update.message.reply_text("❌ Send valid 10-digit number.")

# ---------- ADMIN ----------

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    uid = context.args[0]
    approved_users[uid] = True
    save_approved(approved_users)
    await update.message.reply_text(f"✅ Approved {uid}")

async def approved_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not approved_users:
        await update.message.reply_text("No approved users.")
        return

    msg = "✅ Approved Users:\n\n"
    for uid in approved_users:
        msg += f"• {uid}\n"

    await update.message.toggle_text(msg)

# ---------- MAIN ----------

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("approved", approved_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot running on Railway")
    app.run_polling()

if __name__ == "__main__":
    main()