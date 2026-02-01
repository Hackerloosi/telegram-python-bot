import requests

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if update.effective_user.id != ADMIN_ID and uid not in approved_users:
        return

    number = update.message.text.strip()

    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text(
            "❌ Send valid 10-digit Indian mobile number."
        )
        return

    await update.message.reply_text("🔍 Fetching details, please wait...")

    url = f"https://giga-seven.vercel.app/api?key=NIGHTFALLHUB&num={number}"

    try:
        response = requests.get(url, timeout=15)
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
