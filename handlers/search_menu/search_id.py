
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
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="search_menu", style="danger")] 
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
    
    # 🌟 "🔍 Yuborilmoqda..." xabari yuboriladi
    waiting_msg = await message.answer("🔍 So'rov bajarilmoqda...") 
    
    if not raw_text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan iborat ID kiriting!")
        await waiting_msg.delete()
        return

    anime_id = int(raw_text)
    
    from services.anime_service import AnimeService
    anime_service = AnimeService(session=session)
    anime = await anime_service.get_anime(anime_id)

    if not anime:
        # 1. Ham "Yuborilmoqda..." xabarini, ham foydalanuvchi yuborgan ID matnini o'chirib tashlaymiz
        try:
            await waiting_msg.delete()
            await message.delete()
        except Exception as e:
            logger.debug(f"Xabarlarni o'chirishda xatolik: {e}")

        # 2. Yangitdan toza xabar ko'rinishida tugmalarni yuboramiz (Style saqlangan)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Qayta urinish", callback_data="search_by_id", style="success")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="search_menu", style="danger")]
            ]
        )
        
        await message.answer(
            text=f"❌ <b>#{anime_id}</b> kodli anime topilmadi!\n\nQayta tekshirib ko'ring yoki boshqa ID kiriting.",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    # 🚀 Anime topilsa, universal funksiyaga o'chib ketishi uchun waiting_msg berib yuboriladi
    await send_anime_card(waiting_msg, anime, session)
    
    # Foydalanuvchi yuborgan ID raqam chatda chiroyli ko'rinib turishi uchun uni o'chirmaymiz
    await state.clear()