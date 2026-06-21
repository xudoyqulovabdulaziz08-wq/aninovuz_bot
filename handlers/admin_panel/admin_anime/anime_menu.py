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
    
    # Umumiy dizayn tizimingizga mos, chiroyli va tartibli matn
    text = (
        f"📚 {html.bold('Anime boshqaruvi bo‘limi')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Ushbu bo‘lim orqali bazadagi animelarni tahrirlashingiz, "
        f"yangi kontent qo‘shishingiz yoki o‘chirishingiz mumkin.\n\n"
        f"👇 Kerakli amalni tanlang:"
    )
    
    # Telegram'ning yangi rang tizimiga moslangan tugmalar
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Anime qo‘shish", callback_data="add_anime", style="success")],
            [InlineKeyboardButton(text="📋 Anime ro‘yxati", callback_data="list_anime_page:1")], # Paginatsiya 1-sahifadan boshlanadi
            [InlineKeyboardButton(text="⬅️ Bosh panelga", callback_data="admin_panel", style="danger")]  
        ]
    )
    
    # 💡 UX ENGINIYERING ECHIMI: Xabar media (rasm/video) ekanligini tekshiramiz
    if callback.message.photo or callback.message.video:
        try:
            # Yakuniy posterli xabarni butunlay o'chirib tashlaymiz
            await callback.message.delete()
        except Exception:
            pass
        
        # Yangi toza matnli xabar ko'rinishida menyuni chiqaramiz
        await callback.message.answer(text=text, reply_markup=kb, parse_mode="HTML")
        return # Handler ishini shu yerda yakunlaydi

    # Agar xabar oddiy matn bo'lsa, edit_text silliq ishlayveradi
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"❌ Anime bo'limida Telegram xatoligi: {e}")
    except Exception as e:
        logger.error(f"❌ Anime bo'limida kutilmagan xatolik: {e}")