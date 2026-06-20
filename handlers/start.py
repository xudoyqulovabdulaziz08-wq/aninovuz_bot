from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from services.user_service import UserService

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: dict, user_service: UserService):
    user_id = message.from_user.id
    username = message.from_user.username or "do'stim"
    
    # ✅ 100% ishlaydigan to'g'ridan-to'g'ri rasm havolasi
    start_image_url = "https://images.telegraph.uz/file/f4d7b2a59a72dfbe26fc8.png" 
    
    welcome_text = (
        f"👋 Xush kelibsiz, {html.bold(username)}!\n\n"
        f"🎬 {html.bold('AniNovuz')} — siz qidirgan eng sara, sifatli va sevimli animelar makoniga qadam qo'ydingiz.\n\n"
        f"📌 {html.italic('Sizning IDingiz')}: {html.code(user_id)}\n"
        f"🔑 {html.italic('Sizning maqomingiz')}: {html.bold(user.get('status', 'user').upper())}\n\n"
        f"⚡️ Quyidagi rangli menyudan foydalanib, darhol tomosha qilishni boshlashingiz mumkin:"
    )
    
    start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Qidiruv bo'limi", 
                    callback_data="search_menu",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Reklama berish 📢",
                    callback_data="advertise",
                    style="primary"
                ),
                InlineKeyboardButton(
                    text="Qo'llanma 📖",
                    callback_data="guide",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text="VIP olish 💎", 
                    callback_data="buy_vip",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Muammo bormi? Aloqa", 
                    callback_data="support",
                    style="danger"
                )
            ]
        ]
    )
    
    # Rasm havolasini yuboramiz
    await message.answer_photo(
        photo=start_image_url,
        caption=welcome_text,
        reply_markup=start_keyboard
    )