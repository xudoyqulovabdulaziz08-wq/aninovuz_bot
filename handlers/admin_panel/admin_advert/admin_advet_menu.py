from aiogram import Router, html, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from dotenv.main import logger
from aiogram.fsm.context import FSMContext
router = Router()




@router.callback_query(lambda c: c.data == "admin_advertisement")
async def admin_advertisement(callback: CallbackQuery, state: FSMContext):
    # Tugma bosilganda yuqoridagi soat belgisini darhol o'chiramiz
    await callback.answer()
    await state.clear()
    
    # Botingizning umumiy dizayniga mos, chiroyli sarlavhali matn (Imlosi to'g'rilandi)
    text = (
        f"📣 <b>REKLAMA BO'LMI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Ushbu bo'lim orqali barcha foydalanuvchilarga xabar yoki reklama yuborishingiz mumkin.\n\n"
        f"⚠️ <i>Reklama yuborishdan oldin statistika bilan tanishib chiqing.</i>"
    )
    
    # Tugmalar iyerarxiyasi (style="danger" o'z o'rnida qoldi)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢Reklama yuborish", callback_data="admin_advert", style="primary")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel", style="danger")]  
        ]
    )
    
    # Try-except bloki
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Xabar o'zgarmagan bo'lsa, indamay o'tkazib yuboramiz
            pass
        else:
            logger.error(f"❌ Reklama bo'limida Telegram xatoligi: {e}")
    except Exception as e:
        logger.error(f"❌ Reklama bo'limida kutilmagan xatolik: {e}")