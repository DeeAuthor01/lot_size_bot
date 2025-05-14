import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

(
    ACCOUNT, RISK, PAIR, ENTRY, SL_CHOICE, SL, TP_CHOICE, TP, POSITION, CONFIRM
) = range(10)

user_data = {}

pip_sizes = {
    'JPY': 0.01,
    'XAUUSD': 0.1,
    'XAGUSD': 0.01,
    'BTCUSD': 1,
    'ETHUSD': 1,
    'US30': 1,
    'NAS100': 1,
    'VOLATILITY75': 1,
    'default': 0.0001
}

def get_pip_size(pair: str):
    # Determine pip size by pair suffix or known keys
    pair = pair.upper()
    for key in pip_sizes:
        if pair.endswith(key):
            return pip_sizes[key]
    return pip_sizes['default']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id] = {}
    await update.message.reply_text("Welcome to the Advanced Lot Size Bot!\n\nEnter your account size in $ (e.g., 1000):")
    return ACCOUNT

async def get_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_data[update.effective_chat.id]['account'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for account size.")
        return ACCOUNT
    await update.message.reply_text("Enter your risk in $ (e.g., 20):")
    return RISK

async def get_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_data[update.effective_chat.id]['risk'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for risk.")
        return RISK
    await update.message.reply_text("Enter the trading pair (e.g., EURUSD, BTCUSD, US30):")
    return PAIR

async def get_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = update.message.text.upper()
    user_data[update.effective_chat.id]['pair'] = pair
    await update.message.reply_text("Enter your entry price (e.g., 1.1000):")
    return ENTRY

async def get_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_data[update.effective_chat.id]['entry'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for entry price.")
        return ENTRY

    keyboard = [
        [
            InlineKeyboardButton("Price", callback_data='sl_price'),
            InlineKeyboardButton("Pips", callback_data='sl_pips'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Will you enter Stop Loss as price or pips?", reply_markup=reply_markup)
    return SL_CHOICE

async def sl_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    context.user_data['sl_type'] = choice  # 'sl_price' or 'sl_pips'

    if choice == 'sl_price':
        await query.edit_message_text("Enter your Stop Loss price (e.g., 1.0950):")
    else:
        await query.edit_message_text("Enter your Stop Loss pips (e.g., 50):")

    return SL

async def get_sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sl_type = context.user_data.get('sl_type')
    pair = user_data[chat_id]['pair']
    entry = user_data[chat_id]['entry']

    try:
        val = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return SL

    pip_size = get_pip_size(pair)
    if sl_type == 'sl_price':
        sl = val
        sl_pips = abs(entry - sl) / pip_size
    else:
        sl_pips = val
        if update.message.text.startswith('-'):
            await update.message.reply_text("Please enter positive pips.")
            return SL
        sl = entry - (sl_pips * pip_size)  # temporary assume buy; will fix after position

    user_data[chat_id]['sl'] = sl
    user_data[chat_id]['sl_pips'] = sl_pips

    keyboard = [
        [
            InlineKeyboardButton("Price", callback_data='tp_price'),
            InlineKeyboardButton("Pips", callback_data='tp_pips'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Will you enter Take Profit as price or pips?", reply_markup=reply_markup)
    return TP_CHOICE

async def tp_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    context.user_data['tp_type'] = choice
    if choice == 'tp_price':
        await query.edit_message_text("Enter your Take Profit price (e.g., 1.1100):")
    else:
        await query.edit_message_text("Enter your Take Profit pips (e.g., 100):")
    return TP

async def get_tp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tp_type = context.user_data.get('tp_type')
    pair = user_data[chat_id]['pair']
    entry = user_data[chat_id]['entry']

    try:
        val = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return TP

    pip_size = get_pip_size(pair)
    if tp_type == 'tp_price':
        tp = val
        tp_pips = abs(tp - entry) / pip_size
    else:
        tp_pips = val
        if update.message.text.startswith('-'):
            await update.message.reply_text("Please enter positive pips.")
            return TP
        tp = entry + (tp_pips * pip_size)  # temporary assume buy

    user_data[chat_id]['tp'] = tp
    user_data[chat_id]['tp_pips'] = tp_pips

    # Ask position type now
    keyboard = [
        [
            InlineKeyboardButton("Buy", callback_data='pos_buy'),
            InlineKeyboardButton("Sell", callback_data='pos_sell'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select position type:", reply_markup=reply_markup)
    return POSITION

async def get_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pos = query.data  # 'pos_buy' or 'pos_sell'
    chat_id = query.message.chat.id

    user_data[chat_id]['position'] = pos.split('_')[1]

    # Adjust SL and TP for sell if pips were given as positive distance above/below entry
    position = user_data[chat_id]['position']
    entry = user_data[chat_id]['entry']
    sl = user_data[chat_id]['sl']
    tp = user_data[chat_id]['tp']

    # Fix SL and TP if they were calculated temporarily assuming buy
    # For SELL, SL is above entry, TP is below
    if position == 'sell':
        # If SL < Entry (wrong), flip
        if sl < entry:
            sl = entry + abs(entry - sl)
            user_data[chat_id]['sl'] = sl
        # If TP > Entry (wrong), flip
        if tp > entry:
            tp = entry - abs(tp - entry)
            user_data[chat_id]['tp'] = tp

    # Show confirmation with inline buttons
    text = (
        f"Please confirm your inputs:\n\n"
        f"Account Size: ${user_data[chat_id]['account']}\n"
        f"Risk: ${user_data[chat_id]['risk']}\n"
        f"Pair: {user_data[chat_id]['pair']}\n"
        f"Entry: {entry}\n"
        f"Stop Loss: {user_data[chat_id]['sl']} (~{round(user_data[chat_id]['sl_pips'],2)} pips)\n"
        f"Take Profit: {user_data[chat_id]['tp']} (~{round(user_data[chat_id]['tp_pips'],2)} pips)\n"
        f"Position: {position.capitalize()}\n"
        f"\nConfirm to calculate lot size?"
    )

    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data='confirm'),
            InlineKeyboardButton("Cancel", callback_data='cancel'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == 'cancel':
        await query.edit_message_text("Operation cancelled.")
        user_data.pop(chat_id, None)
        return ConversationHandler.END

    data = user_data.get(chat_id)
    if not data:
        await query.edit_message_text("No data found, please restart with /start")
        return ConversationHandler.END

    account = data['account']
    risk = data['risk']
    pair = data['pair']
    entry = data['entry']
    sl = data['sl']
    position = data['position']

    pip_size = get_pip_size(pair)
    pip_diff = abs(entry - sl)
    pips = pip_diff / pip_size
    if pips == 0:
        await query.edit_message_text("Stop Loss cannot be equal to entry price.")
        return ConversationHandler.END

    pip_value = (pip_size / entry) * 100000
    lot_size = risk / (pips * pip
