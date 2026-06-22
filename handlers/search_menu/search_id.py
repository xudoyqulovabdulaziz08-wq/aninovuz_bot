
from typing import Any
from aiogram import Router, html, types, F
from aiogram.fsm.state import StatesGroup, State

from services.anime_service import AnimeService
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
from dotenv.main import logger
from aiogram.fsm.context import FSMContext
from handlers.search_menu.anime_card import send_anime_card



router = Router()
# Qidiruv holatlarini belgilash
class SearchStates(StatesGroup):
    waiting_for_anime_id = State()






@router.callback_query(lambda c: c.data == "search_by_id")
async def search_by_id(callback: CallbackQuery, state: FSMContext): # state qo'shildi
    await callback.answer()
    
    search_image_file_id = "AgACAgIAAxkBAAI8pmo2wwmGj_SoELEjURiyUyabzhwoAAI5GWsbZ6WxSUf3FNSMy6ajAQADAgADdwADPAQ"
    
    text = (
        "╔═════════ 🔍 ═════════╗\n"
        "   <b>ID BO'YICHA QIDIRISH</b>\n"
        "╚═════════ 🔍 ═════════╝\n\n"
        "🔢 Iltimos, qidirayotgan anime ID sini yozib yuboring.\n\n"
        "⚠️ <b>Eslatma:</b> ID raqamlardan iborat bo'lib, har bir anime uchun yagona bo'ladi!"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="search_menu")] # style="danger" olib tashlandi (inline buttonda style bo'lmaydi)
        ]
    )
    
    try:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=search_image_file_id,
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"❌ Kutilmagan xatolik: {e}")
    except Exception as e:
        logger.error(f"❌ Tizimda xatolik yuz berdi: {e}")

    # 🚀 MANA SHU QATOR QO'SHILDI: Bot foydalanuvchidan ID kelishini kutadi
    await state.set_state(SearchStates.waiting_for_anime_id)




@router.message(SearchStates.waiting_for_anime_id, F.text)
async def process_anime_id_search(message: Message, state: FSMContext, session: Any):
    raw_text = message.text.strip().replace("#", "")
    
    # ✅ TO'G'RILANDI: Kichik harf bilan va show_alert'siz
    await message.answer("🔍 Qidirilmoqda...") 
    
    if not raw_text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan iborat ID kiriting!")
        return

    anime_id = int(raw_text)
    
    from services.anime_service import AnimeService
    anime_service = AnimeService(session=session)
    anime = await anime_service.get_anime(anime_id)

    if not anime:
        await message.answer(f"🔍 <b>#{anime_id}</b> kodli anime topilmadi!\nQayta tekshirib ko'ring.")
        return

    # 🚀 XUDDI O'SHA UNIVERSAL DIZAYN BU YERDA HAM ISHLAYDI:
    await send_anime_card(message, anime, session)
    
    # Muaffaqiyatli yakunlangach, holatni tozalaymiz
    await state.clear()