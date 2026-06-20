from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from services.user_service import UserService
from config import config
CREATOR_ID = config.CREATOR_ID  # Config faylidan CREATOR_ID ni olish
from aiogram.types import InputMediaPhoto
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: dict, user_service: UserService):
    user_id = message.from_user.id
    username = message.from_user.username or "do'stim"
    user_status = user.get('status', 'user').lower()
    
    start_image_file_id = "AgACAgIAAxkBAAI8Vmo2h33mXWFJrVt2WytylhrKnSRKAAJHGGsbZ6WxSVOJWvc1e0TUAQADAgADdwADPAQ" 
    
    welcome_text = (
        f"👋 Xush kelibsiz, {html.bold(username)}!\n\n"
        f"🎬 {html.bold('AniNovuz')} — siz qidirgan eng sara, sifatli va sevimli animelar makoniga qadam qo'ydingiz.\n\n"
        f"⚡️ Quyidagi menyudan foydalanib, darhol tomosha qilishni boshlashingiz mumkin:"
    )
    
    start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Qidiruv bo'limi", callback_data="search_menu", style="primary")],
            [
                InlineKeyboardButton(text="Reklama berish 📢", callback_data="advertise", style="primary"),
                InlineKeyboardButton(text="Qo'llanma 📖", callback_data="guide", style="primary")
            ],
            [InlineKeyboardButton(text="VIP olish 💎", callback_data="buy_vip", style="success")],
            [InlineKeyboardButton(text="💬 Muammo bormi? Aloqa", callback_data="support", style="danger")]
        ]
    )

    # 1. Eski matnli xabarni o'chiramiz
    try:
        await message.delete()
    except:
        pass

    # 2. Yangi rasm yuboramiz (Edit emas, yangi xabar!)
    await message.answer_photo(
        photo=start_image_file_id,
        caption=welcome_text,
        reply_markup=start_keyboard,
        parse_mode="HTML"
    )

    # 3. Admin/Creator panellarini alohida xabar sifatida chiqaramiz
    if user_id == CREATOR_ID:
        creator_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚙️ Creator Paneli"), KeyboardButton(text="🛠 Admin Paneli")]],
            resize_keyboard=True
        )
        await message.answer("👑 Tizim asoschisi! Barcha boshqaruv panellari faollashtirildi:", reply_markup=creator_keyboard)
        
    elif user_status == 'admin':
        admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🛠 Admin Paneli")]],
            resize_keyboard=True
        )
        await message.answer("🛡 Tizim administratori tan olindi. Admin boshqaruv paneli faollashtirildi:", reply_markup=admin_keyboard)
