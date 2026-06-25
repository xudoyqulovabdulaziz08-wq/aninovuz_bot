import logging
from typing import Any
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from services.anime_service import AnimeService



class EditAnimeStates(StatesGroup):
    waiting_for_new_name = State()       # Yangi nomni kiritish holati
    waiting_for_confirmation = State()   # Ha/Yo'q tasdiqlash holati








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
            InlineKeyboardButton(text="📝 Nomi", callback_data=f"edit_field:title:{anime_id}", style="primary" ),
            InlineKeyboardButton(text="📅 Yili", callback_data=f"edit_field:year:{anime_id}", style="primary")
        ],
        [
            InlineKeyboardButton(text="🌐 Tili", callback_data=f"edit_field:lang:{anime_id}", style="primary"),
            InlineKeyboardButton(text="🔮 Janr", callback_data=f"edit_genre_menu:{anime_id}", style="primary")
        ],
        [
            InlineKeyboardButton(text="📝 Tasnif", callback_data=f"edit_field:desc:{anime_id}", style="primary"),
            InlineKeyboardButton(text="🖼 Poster", callback_data=f"edit_field:poster:{anime_id}", style="primary")
        ],
        [
            # Orqaga bosganda eski daxshatli chiroyli ramkali vizual menyuga qaytaradi (page=1 default)
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"v_anime:{anime_id}:1",  style="danger")
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
                






# =====================================================================
# 📑 1-QADAM: "📝 Nomi" tugmasi bosilganda holatga (State) o'tkazish
# =====================================================================
@router.callback_query(F.data.startswith("edit_field:title:"))
async def edit_anime_title_start(callback: CallbackQuery, state: FSMContext):
    anime_id = int(callback.data.split(":")[2])
    
    # Kelajakda kerak bo'lishi uchun anime_id va eski pleer xabarining ID sini holatga saqlaymiz
    await state.update_data(edit_anime_id=anime_id, main_msg_id=callback.message.message_id)
    
    # State-ni o'zgartiramiz
    await state.set_state(EditAnimeStates.waiting_for_new_name)
    
    # Media joyida qoladi, faqat matn o'zgaradi va tugmalar yo'qoladi
    text = (
        "✍️ <b>Yangi nom kiritish:</b>\n\n"
        "Iltimos, animening yangi nomini to'g'ri yozib, botga xabar shaklida yuboring..."
    )
    
    await callback.answer("Nom tahrirlash boshlandi")
    try:
        await callback.message.edit_caption(caption=text, reply_markup=None, parse_mode="HTML")
    except TelegramBadRequest:
        pass


# =====================================================================
# 📑 2-QADAM: Admin yangi nom yuborganda uni ushlash va Ha/Yo'q so'rash
# =====================================================================
@router.message(EditAnimeStates.waiting_for_new_name, F.text)
async def process_new_anime_name(message: Message, state: FSMContext):
    new_name = message.text.strip()
    state_data = await state.get_data()
    
    anime_id = state_data.get("edit_anime_id")
    main_msg_id = state_data.get("main_msg_id")
    
    # 🗑 Admin yuborgan matnli xabarni darhol o'chirib tashlaymiz (Toza UX uchun)
    try:
        await message.delete()
    except Exception:
        pass
        
    # Kelajakda saqlash uchun yangi nomni ham state-ga yozamiz
    await state.update_data(new_anime_title=new_name)
    
    # Tasdiqlash tugmalari
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="confirm_edit:yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_edit:no")
        ]
    ])
    
    confirm_text = (
        f"❓ <b>Haqiqatdan ham anime nomi o'zgartirilsinmi?</b>\n\n"
        f"📝 Yangi nom: <u>{new_name}</u>"
    )
    
    # Asosiy media xabarining matnini tasdiqlash rejimiga o'tkazamiz
    await state.set_state(EditAnimeStates.waiting_for_confirmation)
    try:
        await message.bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=main_msg_id,
            caption=confirm_text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Tasdiqlash xabarini chiqarishda xato: {e}")


# =====================================================================
# 📑 3-QADAM: Tasdiqlash (Ha yoki Yo'q) tugmalari bosilganda
# =====================================================================
@router.callback_query(EditAnimeStates.waiting_for_confirmation, F.data.startswith("confirm_edit:"))
async def save_or_cancel_anime_title(callback: CallbackQuery, state: FSMContext, session: Any):
    action = callback.data.split(":")[1]
    state_data = await state.get_data()
    
    anime_id = state_data.get("edit_anime_id")
    new_name = state_data.get("new_anime_title")
    
    # ❌ AGAR ADMIN "YO'Q" DEB RAD ETSA
    if action == "no":
        await callback.answer("Tahrirlash bekor qilindi.", show_alert=True)
        await state.clear()
        
        # Siz aytgandek, edit_anime: ga qaytish uchun xabarni o'chirib qayta yuboramiz (media qo'llab quvvatlashi uchun)
        try:
            await callback.message.delete()
        except:
            pass
            
        # edit_anime jarayonini boshidan ishga tushirish (Siz yozgan bosh menyuni chaqirish)
        # callback.data ni qo'lda yasab bosh menyu funksiyasiga qaytaramiz:
        callback.data = f"edit_anime:{anime_id}"
        from handlers.admin_panel.admin_anime.edit_anime import process_edit_anime_menu # O'zingizning bosh menyu importingiz
        await process_edit_anime_menu(callback, session)
        return

    # ✅ AGAR ADMIN "HA" DEB TASDIQLASA
    await callback.answer("Saqlanmoqda...")
    
    # Backend (Service) orqali yangilaymiz
    try:
        service = AnimeService(session=session)
        success = await service.update_anime(anime_id=anime_id, update_data={"title": new_name})
    except Exception as e:
        logger.error(f"DB Update error: {e}")
        success = False

    if not success:
        await callback.message.edit_caption(
            caption="❌ <b>Xatolik:</b> Ma'lumotni bazaga saqlashda texnik xato yuz berdi.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⚙️ Tahrirlash bo'limiga qaytish", callback_data=f"force_refresh_edit:{anime_id}")
            ]]),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Muvaffaqiyatli o'zgartirildi deb edit text (caption) bo'ladi
    success_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Tahrirlashga qaytish", callback_data=f"force_refresh_edit:{anime_id}")]
    ])
    
    await callback.message.edit_caption(
        caption=f"✅ <b>Anime nomi muvaffaqiyatli o'zgartirildi!</b>\n\n✨ Yangi nom: <u>{new_name}</u>",
        reply_markup=success_kb,
        parse_mode="HTML"
    )
    await state.clear()


# =====================================================================
# 📑 4-QADAM: Xabarni o'chirib yangidan yuboradigan majburiy qaytish handler
# =====================================================================
@router.callback_query(F.data.startswith("force_refresh_edit:"))
async def force_refresh_edit_menu(callback: CallbackQuery, session: Any):
    anime_id = int(callback.data.split(":")[1])
    
    # 🗑 Matnli edit_text qilingan xabarni butunlay o'chirib tashlaymiz
    try:
        await callback.message.delete()
    except:
        pass
        
    # Qayta yuborish uchun callback datani o'zgartiramiz va bosh menyu handlerini chaqiramiz
    callback.data = f"edit_anime:{anime_id}"
    from handlers.admin_panel.admin_anime.edit_anime import process_edit_anime_menu
    await process_edit_anime_menu(callback, session)