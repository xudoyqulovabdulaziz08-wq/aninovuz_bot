from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import math
from typing import Any
from aiogram import Router, F, html






from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
router = Router()









@router.callback_query(F.data.startswith("list_anime_page:"))
async def process_anime_list_page(callback: CallbackQuery, session: Any):
    await callback.answer()
    page = int(callback.data.split(":")[1])
    
    markup, total_count = await get_anime_list_markup(session, page=page)
    
    text = (
        f"📋 {html.bold('Bazadagi animelar ro‘yxati')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Jami anime soni: {html.code(total_count)} ta\n"
        f"👇 Tafsilotlarini ko‘rish uchun kerakli animeni tanlang:"
    )
    
    # Agar bu handlerga rasm ostidagi orqaga tugmasidan kelingan bo'lsa
    if callback.message.photo or callback.message.video:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text=text, reply_markup=markup, parse_mode="HTML")
    else:
        try:
            await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass
















async def get_anime_list_markup(session, page: int = 1, per_page: int = 10) -> tuple[InlineKeyboardMarkup, int]:
    from services.anime_service import AnimeService
    service = AnimeService(session=session)
    
    # Kesh-first tizimidan barcha animelarni olamiz
    all_anime = await service.list_anime()
    total_anime = len(all_anime)
    
    if total_anime == 0:
        # Agar anime bo'lmasa, faqat orqaga tugmasi
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Anime menyusiga", callback_data="admin_anime")]
        ])
        return kb, total_anime

    # Sahifalarni hisoblaymiz
    total_pages = math.ceil(total_anime / per_page)
    if page < 1: page = 1
    if page > total_pages: page = total_pages

    # Joriy sahifaga mos keluvchi kesim (Slice)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_page_anime = all_anime[start_idx:end_idx]

    inline_keyboard = []

    # 1. Animelar tugmalari ro'yxati
    for anime in current_page_anime:
        anime_id = anime["anime_id"]
        title = anime["title"]
        year = anime.get("year", "—")
        inline_keyboard.append([
            InlineKeyboardButton(text=f"🎬 {title} ({year})", callback_data=f"v_anime:{anime_id}:{page}")
        ])

    # 2. Paginatsiya (Navigatsiya) satri
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"list_anime_page:{page-1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="❌", callback_data="void"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="void"))

    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"list_anime_page:{page+1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="❌", callback_data="void"))

    inline_keyboard.append(nav_row)

    # 3. Ortga qaytish satri
    inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Anime menyusiga", callback_data="admin_anime", style="danger")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard), total_anime





@router.callback_query(F.data.startswith("del_anime:"))
async def delete_anime_handler(callback: CallbackQuery, session: Any):
    await callback.answer()
    anime_id = int(callback.data.split(":")[1])
    
    from services.anime_service import AnimeService
    service = AnimeService(session=session)
    
    # Tranzaksiya bilan bazadan o'chirish va keshni tozalash
    ok = await service.delete_anime(anime_id)
    
    # Eski posterli/mediali xabarni barqaror o'chirib tashlaymiz
    try:
        await callback.message.delete()
    except Exception:
        pass

    if ok:
        success_text = (
            f"🗑 {html.bold('Muvaffaqiyatli o‘chirildi!')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Tanlangan anime va unga tegishli barcha qismlar (seriyalar) ma’lumotlar bazasidan hamda keshdan butunlay olib tashlandi."
        )
    else:
        success_text = (
            f"❌ {html.bold('Xatolik yuz berdi!')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ Ushbu anime allaqachon o‘chirilgan yoki tizimda kutilmagan xatolik yuz berdi."
        )

    # Faqatgina orqaga, ya'ni ro'yxatning birinchi sahifasiga qaytish tugmasi
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Animelar ro‘yxatiga", callback_data="list_anime_page:1")]
    ])
    
    # Toza matn ko'rinishida tasdiq xabarini yuboramiz
    await callback.message.answer(text=success_text, reply_markup=kb, parse_mode="HTML")