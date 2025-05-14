from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)
from utils import get_pip_info

# Stages
ACCOUNT, RISK, PAIR, ENTRY, SL, TP = range(6)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Lot Size Calculator Bot!\n\nPlease enter your account size in USD:")
    return ACCOUNT

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["account"] = float(update.message.text)
    await update.message.reply_text("How much do you want to risk per trade (in USD)?")
    return RISK

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["risk"] = float(update.message.text)
    await update.message.reply_text("Enter the pair you want to trade (e.g., EURUSD, GBPJPY, XAUUSD):")
    return PAIR

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["pair"] = update.message.text.upper()
    await update.message.reply_text("Enter your entry price:")
    return ENTRY

async def entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["entry"] = float(update.message.text)
    await update.message.reply_text("Enter your stop loss price:")
    return SL

async def sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["sl"] = float(update.message.text)
    await update.message.reply_text("Enter your take profit price:")
    return TP

async def tp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["tp"] = float(update.message.text)
    result = calculate_lot_size(user_data)
    await update.message.reply_text(
        f"Pair: {user_data['pair']}\n"
        f"SL: {result['SL Pips']} pips\n"
        f"Lot Size: {result['Lot Size']}\n"
        f"RR: {result['Risk-Reward Ratio']}"
    )
    return ConversationHandler.END

def calculate_lot_size(data):
    entry = data["entry"]
    sl = data["sl"]
    tp = data["tp"]
    risk = data["risk"]
    pair = data["pair"]

    pip_multiplier, pip_value = get_pip_info(pair)
    sl_pips = abs(entry - sl) * pip_multiplier
    if sl_pips == 0:
        return {"SL Pips": 0, "Lot Size": 0, "Risk-Reward Ratio": 0}

    lot_size = risk / (sl_pips * (pip_value / 10))
    rr = abs(tp - entry) / abs(entry - sl)

    return {
        "SL Pips": round(sl_pips, 2),
        "Lot Size": round(lot_size, 2),
        "Risk-Reward Ratio": round(rr, 2)
    }

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, account)],
            RISK: [MessageHandler(filters.TEXT & ~filters.COMMAND, risk)],
            PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair)],
            ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, entry)],
            SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, sl)],
            TP: [MessageHandler(filters.TEXT & ~filters.COMMAND, tp)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()
