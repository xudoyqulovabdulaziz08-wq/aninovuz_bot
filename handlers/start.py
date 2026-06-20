from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from services.user_service import UserService

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: dict, user_service: UserService):
    
    user_id = message.from_user.id
    username = message.from_user.username or "do'stim"
    
    # 1. Start uchun rasm havolasi
    start_image_url = "https://telegra.ph/file/a8d839bb002f256037e46.jpg" 
    
    # 2. Hech kimnikiga o'xshamaydigan, original Copywriting (Matn)
    welcome_text = (
        f"👋 Xush kelibsiz, {html.bold(username)}!\n\n"
        f"🎬 {html.bold('Anime Olami')} — siz qidirgan eng sara, sifatli va sevimli animelar makoniga qadam qo'ydingiz.\n\n"
        f"📌 {html.italic('Sizning IDingiz')}: {html.code(user_id)}\n"
        f"🔑 {html.italic('Sizning maqomingiz')}: {html.bold(user.get('status', 'user').upper())}\n\n"
        f"⚡️ Quyidagi rangli menyudan foydalanib, darhol tomosha qilishni boshlashingiz mumkin:"
    )
    
    # 3. Mualliflik huquqini buzmaydigan, o'ziga xos va rang-barang tugmalar tuzilishi
    start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            # 🔵 Primary (Ko'k) - Asosiy brend harakati (Qidiruv)
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
                    callback_data="advertise", # <-- Vergul qo'shildi
                    style="primary"
                ),
                InlineKeyboardButton(
                    text="Qo'llanma 📖",
                    callback_data="guide", # <-- Bo'sh joy o'rniga "guide" so'zi yozildi
                    style="primary"
                )
            ],
            # 🟢 Success (Yashil) - Diqqatni jalb qiluvchi Premium taklif
            [
                InlineKeyboardButton(
                    text="VIP olish 💎", 
                    callback_data="buy_vip",
                    style="success"
                )
            ],
            # 🔴 Danger (Qizil) - Muhim yordam va qo'llab-quvvatlash bo'limi
            [
                InlineKeyboardButton(
                    text="💬 Muammo bormi? Aloqa", 
                    callback_data="support",
                    style="danger"
                )
            ]
        ]
    )
    
    # 4. Rasmli xabarni yuborish
    await message.answer_photo(
        photo=start_image_url,
        caption=welcome_text,
        reply_markup=start_keyboard
    )