import os
import json
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

ADMIN_ID = 1609002531
APPROVED_FILE = "approved_users.json"

# ================= STORAGE =================

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

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if update.effective_user.id != ADMIN_ID and user_id not in approved_users:
        await update.message.reply_text("⛔ You are not approved.")
        return

    await update.message.reply_text(
        "📱 Please Send Mobile No.\n"
        "Without +91\n"
        "In 10 Digit\n\n"
        "[ Note : Only Indian No. Allowed ]"
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    uid = context.args[0]
    approved_users[uid] = True
    save_approved(approved_users)

    await update.message.reply_text(f"✅ Approved user {uid}")

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

# ================= MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if update.effective_user.id != ADMIN_ID and user_id not in approved_users:
        return

    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text(
            "❌ Send valid 10-digit Indian mobile number."
        )
        return

    await update.message.reply_text("🔍 Fetching details, please wait...")

    api_url = f"https://giga-seven.vercel.app/api?key=NIGHTFALLHUB&num={number}"

    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
    except Exception:
        await update.message.reply_text("❌ API error. Try again later.")
        return

    if not data.get("success") or not data.get("result"):
        await update.message.reply_text("❌ No data found.")
        return

    msg = ""

    for i, person in enumerate(data["result"], start=1):
        address = person.get("ADDRESS", "").replace("!", ", ").strip()
        email = person.get("EMAIL", "").lower()

        msg += (
            f"👤 Person {i} Details\n"
            f"Name : {person.get('NAME','')}\n"
            f"Father Name : {person.get('FATHER_NAME','')}\n"
            f"Address : {address}\n"
            f"Sim : {person.get('CIRCLE/SIM','')}\n"
            f"Mobile No. : {person.get('MOBILE','')}\n"
            f"Alternative No. : {person.get('ALTERNATIVE_MOBILE','')}\n"
            f"ID No. : {person.get('AADHAR_NUMBER','')}\n"
            f"Email ID : {email}\n\n"
        )

    msg += "━━━━━━━━━━━━━━\n🤖 Bot Made by @Mafiakabaap"

    await update.message.reply_text(msg)

# ================= MAIN =================

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
