import logging
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()

# Initialize Firebase
try:
    cred = credentials.Certificate("firebase/vaultcoin_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://vaultcoin-87145-default-rtdb.firebaseio.com/'
    })
    db_ref = db.reference()
    FIREBASE_READY = True
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    FIREBASE_READY = False

# Get bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN', "8022426994:AAEyqW-PnwKlssmV29rNV7kFIPY-GRkvA9c")

# Initialize bot and dispatcher with storage
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# States for user registration
class UserStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_referral = State()

# Admin user IDs (add your admin Telegram IDs here)
ADMIN_IDS = [7087777545]  # Vault Link Coordinator

# User management functions
def get_user_data(user_id: int) -> Optional[Dict[str, Any]]:
    if not FIREBASE_READY:
        return None
    try:
        data = db_ref.child('users').child(str(user_id)).get()
        return data if isinstance(data, dict) else None
    except:
        return None

def save_user_data(user_id: int, data: Dict[str, Any]) -> bool:
    if not FIREBASE_READY:
        return False
    try:
        db_ref.child('users').child(str(user_id)).set(data)
        return True
    except:
        return False

def update_user_stats(user_id: int, field: str, value: Any) -> bool:
    if not FIREBASE_READY:
        return False
    try:
        db_ref.child('users').child(str(user_id)).child(field).set(value)
        return True
    except:
        return False

def get_global_stats() -> Dict[str, Any]:
    if not FIREBASE_READY:
        return {}
    try:
        stats = db_ref.child('global_stats').get()
        return stats if isinstance(stats, dict) else {}
    except:
        return {}

def update_global_stats(field: str, value: Any) -> bool:
    if not FIREBASE_READY:
        return False
    try:
        db_ref.child('global_stats').child(field).set(value)
        return True
    except:
        return False

# --- /start command with user registration
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Check if user exists
    if not user_data:
        # New user registration
        await state.set_state(UserStates.waiting_for_wallet.state)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("❌ Cancel", request_contact=False, request_location=False)]],
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="",
            selective=False,
            is_persistent=False
        )
        await message.answer(
            "🎉 Welcome to VaultCoin!\n\n"
            "To get started, please provide your TON wallet address:",
            reply_markup=keyboard
        )
        return
    
    # Existing user - show main menu
    await show_main_menu(message, user_data)

# --- Handle all other messages (reply with start menu)
@dp.message_handler()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # If user is not registered, show registration prompt
    if not user_data:
        await message.answer(
            "🎉 Welcome to VaultCoin!\n\n"
            "Please use /start to register with your TON wallet address."
        )
        return
    
    # If user is registered, show main menu
    await show_main_menu(message, user_data)

async def show_main_menu(message, user_data: Optional[Dict[str, Any]] = None):
    if not user_data:
        user_data = get_user_data(message.from_user.id) or {}
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎮 Play Game", web_app=types.WebAppInfo(url="https://your-webapp-url.com"))  # type: ignore
    )
    keyboard.add(
        InlineKeyboardButton("📢 Join Our Channel", url="https://t.me/yourchannel")  # type: ignore
    )
    keyboard.add(
        InlineKeyboardButton("❓ Help", callback_data="help")  # type: ignore
    )

    # Admin panel for admins
    if message.from_user.id in ADMIN_IDS:
        keyboard.add(InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel"))  # type: ignore
    
    welcome_text = f"👋 Welcome to VaultCoin, {message.from_user.first_name}!\n\n"
    if user_data:
        welcome_text += f"💰 Balance: {user_data.get('balance', 0)} VLTC\n"
        welcome_text += f"🎯 Level: {user_data.get('level', 1)}\n"
        welcome_text += f"👥 Referrals: {user_data.get('referral_count', 0)}\n\n"
    
    welcome_text += "Choose an option below:"
    
    await message.answer(welcome_text, reply_markup=keyboard)

# --- Wallet registration handler
@dp.message_handler(state=UserStates.waiting_for_wallet)
async def wallet_handler(message: types.Message, state: FSMContext):
    if message.text == "❌ Cancel":
        await state.finish()
        await message.answer(
            "Registration cancelled.", 
            reply_markup=types.ReplyKeyboardRemove(selective=False)
        )
        return
    
    # Basic wallet validation (TON addresses start with UQ, EQ, or 0:)
    wallet = message.text.strip()
    if not (wallet.startswith('UQ') or wallet.startswith('EQ') or wallet.startswith('0:')):
        await message.answer("❌ Invalid TON wallet address. Please provide a valid TON wallet address:")
        return
    
    # Save user data
    user_data = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'wallet_address': wallet,
        'balance': 0,
        'level': 1,
        'experience': 0,
        'referral_count': 0,
        'referral_code': f"REF{message.from_user.id}",
        'joined_date': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat()
    }
    
    if save_user_data(message.from_user.id, user_data):
        await state.finish()
        await message.answer(
            "✅ Registration successful!\n\n"
            f"Your wallet: {wallet}\n"
            f"Your referral code: {user_data['referral_code']}\n\n"
            "Share your referral code to earn bonuses!",
            reply_markup=types.ReplyKeyboardRemove(selective=False)
        )
        
        # Update global stats
        stats = get_global_stats()
        stats['total_users'] = stats.get('total_users', 0) + 1
        update_global_stats('total_users', stats['total_users'])
        
        await show_main_menu(message, user_data)
    else:
        await message.answer("❌ Registration failed. Please try again later.")

# --- Callback handlers
@dp.callback_query_handler(lambda c: c.data == 'how_to_buy')
async def how_to_buy_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        "💸 *How to Buy TON*\n\n"
        "1. **Download Trust Wallet**\n"
        "   • Available on iOS and Android\n"
        "   • Create a new wallet\n\n"
        "2. **Buy TON**\n"
        "   • Use MoonPay (credit card)\n"
        "   • Use OKX, Bybit, or other exchanges\n"
        "   • Use P2P services\n\n"
        "3. **Send to Game Wallet**\n"
        "   • Copy the wallet address from the WebApp\n"
        "   • Send TON from your Trust Wallet\n\n"
        "💡 *Alternative methods:*\n"
        "• Buy with credit card on MoonPay\n"
        "• Use centralized exchanges\n"
        "• Use P2P services for better rates",
        parse_mode='Markdown')

@dp.callback_query_handler(lambda c: c.data == 'about')
async def about_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
        "ℹ️ *About VaultCoin*\n\n"
        "VaultCoin is a revolutionary Telegram-based grind-to-earn crypto game built on the TON blockchain.\n\n"
        "🎯 *Our Mission:*\n"
        "• Make crypto gaming accessible to everyone\n"
        "• Provide fair and transparent earning opportunities\n"
        "• Build a strong community of players\n\n"
        "🚀 *Technology:*\n"
        "• Built on TON blockchain\n"
        "• Secure and transparent transactions\n"
        "• Fast and low-cost operations\n\n"
        "🎮 *Game Features:*\n"
        "• Swipe to mine VLTC tokens\n"
        "• Upgrade vaults and equipment\n"
        "• Compete on leaderboards\n"
        "• Earn through referrals\n"
        "• Daily challenges and rewards\n\n"
        "Join thousands of players already earning with VaultCoin! 🚀",
        parse_mode='Markdown')

@dp.callback_query_handler(lambda c: c.data == 'referrals')
async def referrals_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_data = get_user_data(callback_query.from_user.id)
    
    if not user_data:
        await bot.send_message(callback_query.from_user.id, "❌ User data not found.")
        return
    
    ref_code = user_data.get('referral_code', f"REF{callback_query.from_user.id}")
    ref_count = user_data.get('referral_count', 0)
    
    ref_text = f"👥 *Referral Program*\n\n"
    ref_text += f"Your code: `{ref_code}`\n"
    ref_text += f"Total referrals: {ref_count}\n"
    ref_text += f"Earnings: {ref_count * 10} VLTC\n\n"
    ref_text += "💡 *How it works:*\n"
    ref_text += "• Share your referral code\n"
    ref_text += "• Earn 10 VLTC per referral\n"
    ref_text += "• Your friends get 5 VLTC bonus\n"
    ref_text += "• Unlimited earning potential\n\n"
    ref_text += "📤 *Share your code:*\n"
    ref_text += "Copy and share your referral code with friends!"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text="📤 Share Code", 
        switch_inline_query=ref_code
    ))  # type: ignore
    
    await bot.send_message(callback_query.from_user.id, ref_text, parse_mode='Markdown', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'leaderboard')
async def leaderboard_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    if not FIREBASE_READY:
        await bot.send_message(callback_query.from_user.id, "❌ Leaderboard temporarily unavailable.")
        return
    
    try:
        users = db_ref.child('users').get()
        if not users or not isinstance(users, dict):
            await bot.send_message(callback_query.from_user.id, "No users found yet.")
            return
        
        # Sort users by balance
        sorted_users = sorted(users.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:10]
        
        leaderboard_text = "🏆 *Top 10 Players*\n\n"
        for i, (user_id, user_data) in enumerate(sorted_users, 1):
            name = user_data.get('first_name', 'Unknown')
            balance = user_data.get('balance', 0)
            leaderboard_text += f"{i}. {name}: {balance} VLTC\n"
        
        await bot.send_message(callback_query.from_user.id, leaderboard_text, parse_mode='Markdown')
    except:
        await bot.send_message(callback_query.from_user.id, "❌ Error loading leaderboard.")

@dp.callback_query_handler(lambda c: c.data == 'admin_panel')
async def admin_panel_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    if callback_query.from_user.id not in ADMIN_IDS:
        await bot.send_message(callback_query.from_user.id, "❌ Access denied.")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Global Stats", callback_data="admin_stats"),  # type: ignore
        InlineKeyboardButton("👥 All Users", callback_data="admin_users")  # type: ignore
    )
    keyboard.add(
        InlineKeyboardButton("💰 Add Balance", callback_data="admin_add_balance"),  # type: ignore
        InlineKeyboardButton("🔧 Settings", callback_data="admin_settings")  # type: ignore
    )
    
    await bot.send_message(callback_query.from_user.id, "🔧 *Admin Panel*\n\nChoose an option:", parse_mode='Markdown', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'admin_stats')
async def admin_stats_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    if callback_query.from_user.id not in ADMIN_IDS:
        return
    
    stats = get_global_stats()
    users = db_ref.child('users').get() if FIREBASE_READY else {}
    
    stats_text = "📊 *Global Statistics*\n\n"
    stats_text += f"👥 Total Users: {len(users) if users else 0}\n"
    stats_text += f"💰 Total VLTC: {stats.get('total_vltc', 0)}\n"
    stats_text += f"🎮 Total Games: {stats.get('total_games', 0)}\n"
    stats_text += f"📅 Bot Created: {stats.get('bot_created', 'Unknown')}\n"
    
    await bot.send_message(callback_query.from_user.id, stats_text, parse_mode='Markdown')

# --- Original callback handlers (keeping them)
@dp.callback_query_handler(lambda c: c.data == 'help')
async def help_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    help_keyboard = InlineKeyboardMarkup(row_width=2)
    help_keyboard.add(
        InlineKeyboardButton("💸 How to Buy TON", callback_data="how_to_buy"),  # type: ignore
        InlineKeyboardButton("ℹ️ About Us", callback_data="about")  # type: ignore
    )
    help_keyboard.add(
        InlineKeyboardButton("🎮 Play Game", web_app=types.WebAppInfo(url="https://your-webapp-url.com")),  # type: ignore
        InlineKeyboardButton("📢 Join Channel", url="https://t.me/yourchannel")  # type: ignore
    )
    help_keyboard.add(
        InlineKeyboardButton("👥 Referral Program", callback_data="referrals"),  # type: ignore
        InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")  # type: ignore
    )
    
    # Add admin panel for admins
    if callback_query.from_user.id in ADMIN_IDS:
        help_keyboard.add(
            InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")  # type: ignore
        )
    
    help_text = "❓ *Help & Support*\n\n"
    help_text += "Welcome to VaultCoin! Here's everything you need to know:\n\n"
    help_text += "🎮 *Getting Started:*\n"
    help_text += "• Use /start to register\n"
    help_text += "• Tap 'Play Game' to start mining\n"
    help_text += "• Complete daily challenges\n\n"
    help_text += "💰 *Earning VLTC:*\n"
    help_text += "• Play the game daily\n"
    help_text += "• Invite friends with referrals\n"
    help_text += "• Climb the leaderboard\n\n"
    help_text += "Choose an option below for more information:"
    
    await bot.send_message(callback_query.from_user.id, help_text, parse_mode='Markdown', reply_markup=help_keyboard)

# --- Web app data handler (for when users send data from your webapp)
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def web_app_data_handler(message: types.Message):
    try:
        data = message.web_app_data.data
        user_id = message.from_user.id
        
        # Update user's last active time
        update_user_stats(user_id, 'last_active', datetime.now().isoformat())
        
        # Handle different types of data from webapp
        # You can customize this based on what your webapp sends
        await message.answer(f"✅ Data received from game: {data}")
        
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        await message.answer("❌ Error processing game data.")

# --- Error handler
@dp.errors_handler()
async def errors_handler(update, exception):
    logger.error(f"Update: {update}\nException: {exception}")
    return True

# --- Start polling
if __name__ == '__main__':
    logger.info("Starting VaultCoin bot...")
    try:
        # Initialize global stats if not exists
        if FIREBASE_READY:
            stats = get_global_stats()
            if not stats:
                update_global_stats('bot_created', datetime.now().isoformat())
                update_global_stats('total_vltc', 0)
                update_global_stats('total_games', 0)
        
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
