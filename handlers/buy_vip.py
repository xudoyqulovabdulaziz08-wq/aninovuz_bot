from aiogram import Router, html, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from dotenv.main import logger

router = Router()


@router.callback_query(lambda c: c.data == "buy_vip")
async def buy_vip_menu(callback: CallbackQuery):
    await callback.answer()
    
    vip_image_file_id = "AgACAgIAAxkBAAI8tmo2zpXedWfk2pHIT5yhD3bo3ksoAAKFGWsbZ6WxSZsBcZaddInXAQADAgADdwADPAQ"
    
    text = (
        "╔═════════ 💎 ═════════╗\n"
        "   <b>VIP IMTIYOZLAR</b>\n"
        "╚═════════ 💎 ═════════╝\n\n"
        "VIP bolimi tez orada ishga tushadi! 🌟\n\n"
        
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_start", style="danger")]
        ]
    )
    
    try:
        # Matn o'rniga Media va Klaviatura birga chiroyli edit bo'ladi
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=vip_image_file_id,
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"❌ VIP menyusini yuborishda xatolik: {e}")
        await callback.message.answer("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")