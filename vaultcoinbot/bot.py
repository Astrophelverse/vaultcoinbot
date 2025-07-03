import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# --- Use direct token (no .env)
bot = Bot(token="8022426994:AAEyqW-PnwKlssmV29rNV7kFIPY-GRkvA9c")
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# --- /start command
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("▶️ Play", web_app=types.WebAppInfo(url="https://your-webapp-url.com")),  # Change this
        InlineKeyboardButton("📢 Join Channel", url="https://t.me/yourchannel")  # Change this
    )
    keyboard.add(
        InlineKeyboardButton("💸 How to Buy TON", callback_data="how_to_buy"),
        InlineKeyboardButton("❓ Help", callback_data="help")
    )
    keyboard.add(
        InlineKeyboardButton("ℹ️ About VaultCoin", callback_data="about")
    )

    await message.answer("👋 Welcome to VaultCoin!\nChoose an option below to begin:", reply_markup=keyboard)

# --- Callback for How to Buy TON
@dp.callback_query_handler(lambda c: c.data == 'how_to_buy')
async def how_to_buy_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        "💸 *How to Buy TON*\n\n1. Download Trust Wallet\n2. Buy or receive TON\n3. Send to the wallet shown in the WebApp when you click 'Buy VLTC'.",
        parse_mode='Markdown')

# --- Callback for Help
@dp.callback_query_handler(lambda c: c.data == 'help')
async def help_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        "❓ *Help Section*\n\n- Use /start to open the menu\n- Tap 'Play' to enter the WebApp\n- VLTC is mined inside the WebApp\n- Questions? Join our channel!",
        parse_mode='Markdown')

# --- Callback for About
@dp.callback_query_handler(lambda c: c.data == 'about')
async def about_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        "ℹ️ *About VaultCoin*\n\nVaultCoin is a Telegram-based grind-to-earn crypto game built on TON. Swipe to mine, upgrade vaults, and flex status.\n\nThe WebApp is where the magic happens.",
        parse_mode='Markdown')

# --- Start polling
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
