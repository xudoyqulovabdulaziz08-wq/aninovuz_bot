
import math
import logging
from typing import Any
from aiogram import Router, F, html
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select




from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
router = Router()









@router.callback_query(F.data.startswith("list_anime_page:"))
async def process_anime_list_page(callback: CallbackQuery, session: Any):
    page = int(callback.data.split(":")[1])
    
    # Ma'lumotlarni bazadan/keshdan yuklaymiz
    markup, total_count = await get_anime_list_markup(session, page=page)
    
    text = (
        f"📋 {html.bold('Bazadagi animelar ro‘yxati')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Jami anime soni: {html.code(total_count)} ta\n"
        f"👇 Tafsilotlarini ko‘rish uchun kerakli animeni tanlang:"
    )
    
    # 💡 Agar bu handlerga rasm yoki video ostidagi tugmadan kelingan bo'lsa
    if callback.message.photo or callback.message.video:
        await callback.answer() # Yuklanish soatini darhol o'chiramiz
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text=text, reply_markup=markup, parse_mode="HTML")
    
    # Agar oddiy matnli xabardan bosilgan bo'lsa (Silliq o'tish)
    else:
        try:
            await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
            await callback.answer() # Faqat muvaffaqiyatli editdan keyin soatni o'chiramiz
        except Exception:
            await callback.answer()






@router.callback_query(F.data.startswith("v_anime:"))
async def view_anime_details(callback: CallbackQuery, session: Any):
    _, anime_id_str, page_str = callback.data.split(":")
    anime_id = int(anime_id_str)
    page = int(page_str) # Orqaga qaytishda aynan shu sahifaga qaytish uchun
    
    from services.anime_service import AnimeService
    service = AnimeService(session=session)
    
    # 1. DB/Cache dan xavfsiz yuklash
    try:
        anime = await service.get_anime(anime_id)
    except Exception as e:
        logger.error(f"❌ Anime yuklashda xato: {e}")
        anime = None
        
    if not anime:
        await callback.answer("❌ Anime topilmadi yoki o‘chirilgan!", show_alert=True)
        return

    # 2. KeyError oldini olish uchun lug'atdan xavfsiz o'qish
    title = anime.get("title", "Nomsiz anime")
    anime_id_val = anime.get("anime_id", anime_id)
    year = anime.get("year", "—")
    description = anime.get("description") or "Tavsif kiritilmagan."
    episodes_count = len(anime.get("episodes", []))
    
    languages = anime.get("languages", [])
    languages_str = ", ".join(languages) if languages else "Mavjud emas"
    
    # 3. Janr nomlarini xavfsiz shakllantirish
    genres_str = "Mavjud emas"
    try:
        genre_ids = anime.get("genres", [])
        if genre_ids:
            from database.models import Genre
            from sqlalchemy import select
            res = await session.execute(select(Genre).where(Genre.id.in_(genre_ids)))
            genre_names = [g.name for g in res.scalars().all()]
            if genre_names:
                genres_str = ", ".join(genre_names)
    except Exception as e:
        logger.error(f"❌ Janrlarni yuklashda xato: {e}")

    # 4. Siz aytgan daxshat ramkali UX dizayn
    caption = (
        f"╔══════════════════╗\n"
        f"     🎬 <b>{title}</b>\n"
        f"╚══════════════════╝\n\n"
        f"📌 <b>Anime haqida ma'lumot:</b>\n"
        f"╔══════════════════╗\n"
        f"├ 🆔 Kod: <code>#{anime_id_val}</code>\n"  
        f"├ 📅 Yil: <b>{year}</b>\n"
        f"├ ▶️ Qism: <b>{episodes_count}</b> \n"
        f"├ 🌐 Til: <b>{languages_str}</b>\n"
        f"╚══════════════════╝\n"
        f"╔══════════════════╗\n"
        f"  🔮 Janrlar: <i>{genres_str}</i>\n"
        f"╚══════════════════╝\n\n"
        f"📝 <b>Tavsif:</b>\n"
        f"<blockquote expandable>{description}</blockquote>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📹 Qismlarni tahrirlash", callback_data=f"manage_episodes:{anime_id}"),
            InlineKeyboardButton(text="🗑 Animeni o‘chirish", callback_data=f"del_anime:{anime_id}", style="danger")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ro‘yxatga qaytish", callback_data=f"list_anime_page:{page}")
        ]
    ])

    # 5. Interfeys qotib qolmasligi uchun answer shu yerda beriladi
    await callback.answer() 
    
    try:
        await callback.message.delete()
    except Exception:
        pass

    # 6. Fallback mexanizmi (Posterni xavfsiz yuborish)
    poster_id = anime.get("poster_id")
    
    if poster_id:
        try:
            # Avval rasm sifatida jo'natishga urinamiz
            await callback.message.answer_photo(photo=poster_id, caption=caption, reply_markup=kb, parse_mode="HTML")
        except TelegramBadRequest:
            try:
                # Agar rasm bo'lmasa, video sifatida urinamiz
                await callback.message.answer_video(video=poster_id, caption=caption, reply_markup=kb, parse_mode="HTML")
            except TelegramBadRequest:
                # Agar Telegram media ID ni umuman tanimasa, matn yuboramiz (bot qotmasligi uchun)
                await callback.message.answer(text=f"⚠️ (Media topilmadi)\n\n{caption}", reply_markup=kb, parse_mode="HTML")
    else:
        # Agar poster_id bazada umuman saqlanmagan bo'lsa
        await callback.message.answer(text=caption, reply_markup=kb, parse_mode="HTML")






logger = logging.getLogger(__name__)

async def get_anime_list_markup(session, page: int = 1, per_page: int = 10) -> tuple[InlineKeyboardMarkup, int]:
    from services.anime_service import AnimeService
    service = AnimeService(session=session)
    
    # 1. Keshdan yoki DB dan ma'lumotlarni xavfsiz yuklash
    try:
        all_anime = await service.list_anime()
        if not all_anime:  # Agar None kelsa, ishdan chiqmasligi uchun bo'sh ro'yxat
            all_anime = []
    except Exception as e:
        logger.error(f"❌ Anime ro'yxatini olishda xatolik: {e}")
        all_anime = []
        
    total_anime = len(all_anime)
    
    # 2. Agar anime umuman topilmasa
    if total_anime == 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Anime menyusiga", callback_data="admin_anime")]
        ])
        return kb, 0

    # 3. Sahifalarni xavfsiz va qisqa yo'l bilan hisoblash
    total_pages = math.ceil(total_anime / per_page)
    # Page chegaradan chiqib ketmasligini bitta qatorda ta'minlaymiz:
    page = max(1, min(page, total_pages))

    # 4. Ro'yxatdan joriy sahifaga kerakli qismini kesib olish (Juda tez)
    start_idx = (page - 1) * per_page
    current_page_anime = all_anime[start_idx : start_idx + per_page]

    inline_keyboard = []

    # 5. Tugmalarni shakllantirish (Lug'at kalitlarini xavfsiz o'qish)
    for anime in current_page_anime:
        anime_id = anime.get("anime_id")
        title = anime.get("title", "Nomsiz anime")
        year = anime.get("year", "—")
        
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {title} ({year})", 
                callback_data=f"v_anime:{anime_id}:{page}"
            )
        ])

    # 6. Paginatsiya (Navigatsiya) satri
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"list_anime_page:{page-1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="void"))

    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"list_anime_page:{page+1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void"))

    inline_keyboard.append(nav_row)

    # 7. Ortga qaytish satri (style olib tashlandi, chunki Aiogram 3 oddiy tugmalarga rang bera olmaydi)
    inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Anime menyusiga", callback_data="admin_anime", style="danger")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard), total_anime



@router.callback_query(F.data.startswith("del_anime:"))
async def confirm_delete_anime_handler(callback: CallbackQuery, session: Any):
    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    
    confirm_text = (
        f"⚠️ {html.bold('DIQQAT! O‘chirishni tasdiqlang')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Ushbu animeni ro‘yxatdan butunlay o‘chirib tashlamoqchimisiz?\n\n"
        f"🛑 {html.italic('Bu amalni ortga qaytarib bo‘lmaydi! Animega tegishli barcha qismlar (seriyalar) ham bazadan o‘chib ketadi.')}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha,  o‘chirish", callback_data=f"burn_anime:{anime_id}"),
            InlineKeyboardButton(text="❌ bekor qilish", callback_data=f"v_anime:{anime_id}:1")
        ]
    ])
    
    # Agar xabarda rasm yoki video bo'lsa, posterni saqlab faqat matnni o'zgartiramiz
    if callback.message.photo or callback.message.video:
        try:
            await callback.message.edit_caption(caption=confirm_text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    else:
        try:
            await callback.message.edit_text(text=confirm_text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass








@router.callback_query(F.data.startswith("burn_anime:"))
async def execute_delete_anime_handler(callback: CallbackQuery, session: Any):
    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    
    # 🎯 MUAMMONI ILDIZI BILAN YUQOTISH:
    # SafeSession proxy hali bazaga ulanmagan bo'lsa, uni majburan uyg'otamiz.
    # Bu orqali ichki _session obyekti None bo'lishdan to'xtaydi va SQLAlchemy sessiyasiga aylanadi.
    try:
        if hasattr(session, "_ensure_session"):
            await session._ensure_session()
    except Exception as e:
        logger.error(f"❌ Lazy sessionni faollashtirishda xato: {e}")

    from services.anime_service import AnimeService
    # Endi session ichidagi _session mutlaqo tayyor va None emas!
    service = AnimeService(session=session)
    
    ok = False
    try:
        # Tranzaksiya bilan bazadan o'chirish va keshni butunlay tozalash
        ok = await service.delete_anime(anime_id)
    except Exception as e:
        logger.error(f"❌ Anime o'chirishda jiddiy xatolik: {e}")

    # Eski posterli/mediali tasdiqlash xabarini barqaror o'chirib tashlaymiz
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Adminga yakuniy natija matnini tayyorlaymiz
    if ok:
        success_text = (
            f"🗑 {html.bold('Muvaffaqiyatli o‘chirildi!')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Tanlangan anime, uning barcha qismlari ma’lumotlar bazasidan hamda kesh xotirasidan butunlay yo‘q qilindi."
        )
    else:
        success_text = (
            f"❌ {html.bold('Xatolik yuz berdi!')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ Ushbu animeni o‘chirishda xatolik yuz berdi. U allaqachon o‘chirilgan yoki tizimda ulanish uzilgan bo‘lishi mumkin."
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Animelar ro‘yxatiga", callback_data="list_anime_page:1")]
    ])
    
    # Toza matn ko'rinishida yakuniy javobni yuboramiz
    try:
        await callback.message.answer(text=success_text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"❌ Yakuniy xabarni yuborishda xato: {e}")