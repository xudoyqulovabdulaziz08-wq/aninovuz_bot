from aiogram import Router, html, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from dotenv.main import logger

router = Router()

@router.callback_query(lambda c: c.data == "support")
async def support_menu(callback: CallbackQuery):
    await callback.answer()
    
    # 🖼 Aloqa bo'limi uchun rasm (Startdagi rasmni qoldirdik, o'zgartirmoqchi bo'lsangiz yangi file_id qo'yasiz)
    support_image_file_id = "AgACAgIAAxkBAAI8tGo2zRs85gamwlBSbIpQSyz3hfQQAAKAGWsbZ6WxSaBJmU2Y6WwRAQADAgADdwADPAQ"
    
    text = (
        "╔═════════ 💬 ═════════╗\n"
        "   <b>ALOQA BO'LIMI</b>\n"
        "╚═════════ 💬 ═════════╝\n\n"
        "Agar sizda muammo yoki savol bo'lsa, iltimos, quyidagi tugmani bosing va biz bilan bog'laning. 🌟\n\n"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Biz bilan bog'lanish", url="https://t.me/@Khudoyqulov_pg")],
            # ⬇️ "Orqaga" tugmasi start.py faylidagi 'back_to_start' handleriga ulandi!
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_start", style="danger")]
        ]
    )
    
    try:
        # Matn o'rniga Media va Klaviatura birga chiroyli edit bo'ladi
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=support_image_file_id,
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"❌ Aloqa menyusini yuborishda xatolik: {e}")
        await callback.message.answer("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")