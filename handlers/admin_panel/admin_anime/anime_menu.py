from aiogram import Router, html, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from dotenv.main import logger
from aiogram.fsm.context import FSMContext
router = Router()




@router.callback_query(lambda c: c.data == "admin_anime")
async def admin_anime(callback: CallbackQuery, state: FSMContext):
    # Tugma bosilganda yuqoridagi soat belgisini darhol o'chiramiz
    await callback.answer()
    await state.clear()
    
    # Botingizning umumiy dizayniga mos, chiroyli sarlavhali matn
    text = (
        f"📚 {html.bold('Anime boshqaruvi bo‘limi')}\n\n"
        f"Ushbu bo‘lim orqali bazadagi animelarni tahrirlashingiz, "
        f"yangi kontent qo‘shishingiz yoki o‘chirishingiz mumkin.\n\n"
        f"Kerakli amalni tanlang:"
    )
    
    # Tugmalar iyerarxiyasi (rang bera olmasak ham emojilar bilan vizual ajratildi)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Anime qo‘shish", callback_data="add_anime")],
            [InlineKeyboardButton(text="📃 Anime ro‘yxati", callback_data="list_anime")],
            [InlineKeyboardButton(text="➖ Anime o‘chirish", callback_data="del_anime")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel", style="danger")]  
        ]
    )
    
    # To'g'ri chekinishlar bilan try-except bloki
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Xabar o'zgarmagan bo'lsa, indamay o'tkazib yuboramiz
            pass
        else:
            logger.error(f"❌ Anime bo'limida Telegram xatoligi: {e}")
    except Exception as e:
        logger.error(f"❌ Anime bo'limida kutilmagan xatolik: {e}")

