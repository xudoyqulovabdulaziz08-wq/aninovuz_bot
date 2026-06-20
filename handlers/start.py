from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from services.user_service import UserService
from config import CREATOR_ID
from aiogram.types import InputMediaPhoto
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: dict, user_service: UserService):
    user_id = message.from_user.id
    username = message.from_user.username or "do'stim"
    user_status = user.get('status', 'user').lower() # 'creator', 'admin' yoki 'user'
    
    # ⬇️ 100% ishlaydigan sifatli rasm file_id si
    start_image_file_id = "AgACAgIAAxkBAAFM9eZqNnyFaTj3fypf08VZfu0tYxfaeAACMhhrG3ncsEnzIfMcSD907wEAAwIAA3cAAzwE" 
    
    welcome_text = (
        f"👋 Xush kelibsiz, {html.bold(username)}!\n\n"
        f"🎬 {html.bold('AniNovuz')} — siz qidirgan eng sara, sifatli va sevimli animelar makoniga qadam qo'ydingiz.\n\n"
        f"⚡️ Quyidagi menyudan foydalanib, darhol tomosha qilishni boshlashingiz mumkin:"
    )
    
    # 🎨 Doimiy inline tugmalar (Barcha foydalanuvchilar uchun)
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
    
    # 🚀 Asosiy xabar (Rasm + matn + inline tugmalar)
    await message.edit_media(
        media=InputMediaPhoto(
            media=start_image_file_id,
            caption=welcome_text,
            parse_mode="HTML" # Agar html formatlash ishlatsangiz
        ),
        reply_markup=start_keyboard
    )

    # 👑 FAQQAT CREATOR (SIZ) UCHUN - IKKALA TUGMA HAM BIRGA
    if user_id == CREATOR_ID or user_status == 'creator':
        creator_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="⚙️ Creator Paneli"),
                    KeyboardButton(text="🛠 Admin Paneli")
                ]
            ],
            resize_keyboard=True
        )
        await message.answer("👑 Tizim asoschisi! Barcha boshqaruv panellari faollashtirildi:", reply_markup=creator_keyboard)
        
    # 🛡 ODDIY ADMINLAR UCHUN - FAQAT ADMIN PANEL
    elif user_status == 'admin':
        admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🛠 Admin Paneli")]],
            resize_keyboard=True
        )
        await message.answer("🛡 Tizim administratori tan olindi. Admin boshqaruv paneli faollashtirildi:", reply_markup=admin_keyboard)
