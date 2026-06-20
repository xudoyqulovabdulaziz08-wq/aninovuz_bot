from aiogram import Router, html, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from dotenv.main import logger

router = Router()

@router.callback_query(lambda c: c.data == "search_menu")
async def search_menu(callback: CallbackQuery):
    await callback.answer()
    
    # 🖼 Qidiruv bo'limi uchun rasm (Startdagi rasmni qoldirdik, o'zgartirmoqchi bo'lsangiz yangi file_id qo'yasiz)
    search_image_file_id = "AgACAgIAAxkBAAI8Vmo2h33mXWFJrVt2WytylhrKnSRKAAJHGGsbZ6WxSVOJWvc1e0TUAQADAgADdwADPAQ"
    
    text = (
        "╔═════════ 🔍 ═════════╗\n"
        "   <b>ANIME QIDIRISH</b>\n"
        "╚═════════ 🔍 ═════════╝\n\n"
        "Qidiruv menyusiga xush kelibsiz! 🌟\n\n"
        "<blockquote expandable><b>Nomi bo'yicha qidirish</b></blockquote>\n"
        "<blockquote expandable><b>ID bo'yicha qidirish</b></blockquote>\n"
        "<blockquote expandable><b>Janr bo'yicha qidirish</b></blockquote>\n"
        
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Nomi bo'yicha qidirish", callback_data="search_by_name", style="primary")],
            [InlineKeyboardButton(text="🔢 ID bo'yicha qidirish", callback_data="search_by_id", style="primary")],
            [InlineKeyboardButton(text="🎭 Janr bo'yicha qidirish", callback_data="search_by_genre", style="primary")],
            # ⬇️ "Orqaga" tugmasi start.py faylidagi 'back_to_start' handleriga ulandi!
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_start", style="danger")]
        ]
    )
    
    try:
        # Matn o'rniga Media va Klaviatura birga chiroyli edit bo'ladi
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=search_image_file_id,
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"❌ Qidiruv menyusini yuborishda xatolik: {e}")
        await callback.message.answer("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")




