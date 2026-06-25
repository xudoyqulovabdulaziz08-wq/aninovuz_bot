import logging
from typing import Any
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger("EditAnimeMenu")
router = Router()

@router.callback_query(F.data.startswith("edit_anime:"))
async def process_edit_anime_menu(callback: CallbackQuery, session: Any):
    # 1. Callback datadan anime_id ni ajratib olamiz
    try:
        anime_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("🚨 Noto'g'ri anime ID!", show_alert=True)
        return

    # 2. Anime xizmatini chaqirib, joriy ma'lumotlarni tekshiramiz (nomini sarlavhada ko'rsatish uchun)
    from services.anime_service import AnimeService
    service = AnimeService(session=session)
    
    try:
        anime = await service.get_anime(anime_id)
    except Exception as e:
        logger.error(f"❌ Tahrirlash menyusida animeni yuklashda xato: {e}")
        anime = None

    if not anime:
        await callback.answer("❌ Anime topilmadi yoki o‘chirilgan!", show_alert=True)
        return

    anime_title = anime.get("title", "Nomsiz anime")

    # 3. Siz aytgan toza va siqilib ketmaydigan qisqa tugmalar paneli (UX Optimized)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nomi", callback_data=f"edit_field:title:{anime_id}"),
            InlineKeyboardButton(text="📅 Yili", callback_data=f"edit_field:year:{anime_id}")
        ],
        [
            InlineKeyboardButton(text="🌐 Tili", callback_data=f"edit_field:lang:{anime_id}"),
            InlineKeyboardButton(text="🔮 Janr", callback_data=f"edit_genre_menu:{anime_id}")
        ],
        [
            InlineKeyboardButton(text="📝 Tasnif", callback_data=f"edit_field:desc:{anime_id}"),
            InlineKeyboardButton(text="🖼 Poster", callback_data=f"edit_field:poster:{anime_id}")
        ],
        [
            # Orqaga bosganda eski daxshatli chiroyli ramkali vizual menyuga qaytaradi (page=1 default)
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"v_anime:{anime_id}:1")
        ]
    ])

    # 4. Sarlavha matni (Admin aniq qayerdaligini bilishi uchun)
    text = (
        f"⚙️ <b>Siz anime tahrirlash bo'limidasiz!</b>\n"
        f"🎬 Tanlangan anime: <u>{anime_title}</u>\n\n"
        f"<i>Iltimos, o'zgartirmoqchi bo'lgan ma'lumotingizni quyidagi qisqa tugmalardan tanlang:</i>"
    )

    await callback.answer("Tahrirlash menyusi...")

    # 5. 🖼 MEDIA EDIT MANTIQI (Poster rasm yoki video bo'lishiga qarab silliq edit qilish)
    try:
        # Eski xabarning caption (matn) va reply_markup (tugmalar) qismini silliq yangilaymiz
        await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        # Agar qandaydir sabab bilan caption yangilanmasa (masalan matnsiz media bo'lsa), xabarni qayta yuboramiz
        if "message to edit not found" in str(e) or "there is no caption" in str(e):
            try:
                await callback.message.delete()
            except:
                pass
            
            poster_id = anime.get("poster_id")
            if poster_id:
                try:
                    await callback.message.answer_photo(photo=poster_id, caption=text, reply_markup=kb, parse_mode="HTML")
                except TelegramBadRequest:
                    await callback.message.answer_video(video=poster_id, caption=text, reply_markup=kb, parse_mode="HTML")
            else:
                await callback.message.answer(text=text, reply_markup=kb, parse_mode="HTML")