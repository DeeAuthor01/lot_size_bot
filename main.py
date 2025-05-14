import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

ACCOUNT_SIZE, RISK_DOLLAR, PAIR, ENTRY, STOP_LOSS = range(5)

user_data = {}

# Dictionary of pip values
pip_values = {
    # Majors
    "EURUSD": 10, "GBPUSD": 10, "USDJPY": 9.13, "USDCHF": 9.24,
    "AUDUSD": 10, "NZDUSD": 10, "USDCAD": 7.99,
    
    # Minors
    "EURGBP": 11.27, "EURJPY": 8.36, "GBPJPY": 7.72, "CHFJPY": 7.08, "EURAUD": 7.68,

    # Exotics
    "USDZAR": 6.51, "USDTRY": 6.12, "USDMXN": 5.87, "USDNOK": 5.97, "USDSEK": 5.92,

    # Metals
    "XAUUSD": 1.0, "XAGUSD": 0.5,
}

def calculate_lot_size(risk_amount, entry_price, stop_loss_price, pip_value):
    pips = abs(entry_price - stop_loss_price)
    if "JPY" in str(entry_price):
        pips *= 100
    else:
        pips *= 10000
    risk_per_pip = pip_value
    lot_size = risk_amount / (pips * risk_per_pip)
    return round(pips, 1), round(lot_size, 2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Lot Size Calculator Bot!\n\nPlease enter your *Account Size* (in USD):", parse_mode="Markdown")
    return ACCOUNT_SIZE

async def get_account_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["account_size"] = float(update.message.text)
    await update.message.reply_text("Enter the amount you want to risk (in USD):")
    return RISK_DOLLAR

async def get_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["risk"] = float(update.message.text)
    await update.message.reply_text("Enter the Forex Pair (e.g., EURUSD, GBPJPY, USDZAR):")
    return PAIR

async def get_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = update.message.text.upper()
    if pair not in pip_values:
        await update.message.reply_text("Unsupported pair. Please try again.")
        return PAIR
    user_data["pair"] = pair
    await update.message.reply_text("Enter Entry Price:")
    return ENTRY

async def get_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["entry"] = float(update.message.text)
    await update.message.reply_text("Enter Stop Loss Price:")
    return STOP_LOSS

async def get_stop_loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entry = user_data["entry"]
    sl = float(update.message.text)
    pair = user_data["pair"]
    risk = user_data["risk"]
    pip_val = pip_values[pair]

    pips, lot = calculate_lot_size(risk, entry, sl, pip_val)

    await update.message.reply_text(
        f"**Result:**\n\n"
        f"Pair: {pair}\n"
        f"Pip Size: {pips} pips\n"
        f"Lot Size: {lot} lots\n\n"
        f"Risk: ${risk} | Entry: {entry} | SL: {sl}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ACCOUNT_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_account_size)],
            RISK_DOLLAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_risk)],
            PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pair)],
            ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_entry)],
            STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stop_loss)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot running...")
    app.run_polling()
