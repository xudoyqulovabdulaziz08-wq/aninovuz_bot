
from aiogram import Router, html, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()




# 1. Reklama yuborish tugmasi bosilganda toifalarni ko'rsatish
@router.callback_query(F.data == "admin_advert")
async def process_admin_advert_menu(callback: CallbackQuery):
    await callback.answer()
    
    # Guruhlarga mos maxsus callback_data format: "send_adv:{guruh_nomi}"
    advert_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌍 Hammaga (User, VIP, Admin)", callback_data="send_adv:all", style="primary")
        ],
        [
            InlineKeyboardButton(text="💎 Faqat VIP foydalanuvchilarga", callback_data="send_adv:vip", style="primary"),
            InlineKeyboardButton(text="👤 Faqat oddiy foydalanuvchilarga", callback_data="send_adv:user", style="primary")
        ],
        [
            InlineKeyboardButton(text="🛠 Faqat Adminlarga", callback_data="send_adv:admin", style="primary")
        ],
        [
            # Admin bosh menyusiga yoki mos keladigan asosiy panelga qaytish
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_main_menu", style="danger")
        ]
    ])
    
    await callback.message.edit_text(
        text="📢 <b>Reklama va Bildirishnomalar yuborish bo'limi</b>\n\n"
             "<i>Ushbu bo'lim orqali bot foydalanuvchilariga reklama, aksiya yoki texnik "
             "xabarlarni yuborishingiz mumkin.</i>\n\n"
             "✨ Xabar yubormoqchi bo'lgan maqsadli (target) guruhni tanlang:",
        reply_markup=advert_kb,
        parse_mode="HTML"
    )