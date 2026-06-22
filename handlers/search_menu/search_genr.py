import math
from typing import Any
from aiogram import Router, html, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from dotenv.main import logger
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database.models import Genre



router = Router()






async def get_user_genres_search_markup(
    session: Any, 
    selected_genres: list[int], 
    page: int = 1, 
    per_page: int = 20
) -> InlineKeyboardMarkup:
    """Foydalanuvchi multi-qidiruvi uchun janrlar klaviaturasi (Stylelar saqlangan)"""
    stmt = select(Genre).order_by(Genre.name)
    result = await session.execute(stmt)
    genres = result.scalars().all()
    
    total_items = len(genres)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_genres = genres[start_idx:end_idx]
    
    keyboard = []
    row = []
    
    for genre in current_genres:
        is_selected = genre.id in selected_genres
        tick = "✅ " if is_selected else ""
        btn_style = "success" if is_selected else "default"
        
        row.append(InlineKeyboardButton(
            text=f"{tick}{genre.name}",
            callback_data=f"user_g_tog:{genre.id}:{page}", # user_ prefiksi bilan
            style=btn_style
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # Sahifalash (Paginatsiya)
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"user_g_page:{page-1}"))
    if total_pages > 1:
        nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="none"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"user_g_page:{page+1}"))
        
    if nav_row:
        keyboard.append(nav_row)
        
    # Boshqaruv tugmalari (Siz aytgan O'zgarishlar)
    keyboard.append([
        InlineKeyboardButton(text="🔍 Tanlanganlar bo'yicha qidirish", callback_data="user_g_search", style="success")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Qidiruv menyusi", callback_data="search_menu", style="danger")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)





@router.callback_query(lambda c: c.data == "search_by_genre")
async def search_by_genre(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Har safar kirganda tanlangan janrlar keshini tozalab yuboramiz
    await state.update_data(selected_genres=[])
    
    search_image_file_id = "AgACAgIAAxkBAAI8pmo2wwmGj_SoELEjURiyUyabzhwoAAI5GWsbZ6WxSUf3FNSMy6ajAQADAgADdwADPAQ"
    
    text = (
        "╔═════════ 🔍 ═════════╗\n"
        "   <b>JANR BO'YICHA QIDIRISH</b>\n"
        "╚═════════ 🔍 ═════════╝\n\n"
        "🎭 Janrlar bo'yicha qidirish tizimiga xush kelibsiz!\n"
        "Siz bir vaqtning o'zida bir nechta janrni belgilab qidirishingiz mumkin.\n\n"
        "🚀 Janrlar ro'yxatini ochish uchun quyidagi tugmani bosing:"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Qidiruvni boshlash", callback_data="user_g_page:1", style="success")],
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
    except Exception as e:
        logger.error(f"❌ Janr menyusida xatolik: {e}")















@router.callback_query(F.data.startswith("user_g_page:"))
async def process_user_genre_page(callback: CallbackQuery, state: FSMContext, session: Any):
    page = int(callback.data.split(":")[1])
    
    # 🌟 "Janrlar yuklanmoqda..." ogohlantirishi (Bot qotib qolmasligi uchun)
    await callback.answer("⏳ Janrlar ro'yxati yuklanmoqda...", show_alert=False)
    
    user_data = await state.get_data()
    selected_genres = user_data.get("selected_genres", [])
    
    # Faqat klaviaturani va matnni yangilaymiz (Rasm joyida qoladi)
    kb = await get_user_genres_search_markup(session, selected_genres, page=page)
    
    text = "🎭 <b>O'zingizga yoqqan janrlarni belgilang va pastdagi Qidirish tugmasini bosing:</b>"
    await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("user_g_tog:"))
async def process_user_genre_toggle(callback: CallbackQuery, state: FSMContext, session: Any):
    await callback.answer() # Silliq bosilish uchun
    
    _, genre_id, page = callback.data.split(":")
    genre_id, page = int(genre_id), int(page)
    
    user_data = await state.get_data()
    selected_genres = user_data.get("selected_genres", [])
    
    if genre_id in selected_genres:
        selected_genres.remove(genre_id)
    else:
        selected_genres.append(genre_id)
        
    await state.update_data(selected_genres=selected_genres)
    
    # Tugma holatini o'zgartirib qayta chizamiz
    kb = await get_user_genres_search_markup(session, selected_genres, page=page)
    await callback.message.edit_reply_markup(reply_markup=kb)










@router.callback_query(F.data == "user_g_search")
async def process_user_genre_search_submit(callback: CallbackQuery, state: FSMContext, session: Any):
    user_data = await state.get_data()
    selected_genres = user_data.get("selected_genres", [])
    
    if not selected_genres:
        await callback.answer("⚠️ Iltimos, kamida bitta janrni belgilang!", show_alert=True)
        return
        
    # 1. Eski interfeysni (rasmli janrlar ro'yxatini) darhol o'chiramiz
    try:
        await callback.message.delete()
    except:
        pass
        
    # 2. Darhol vaqtinchalik xabarni chiqaramiz (Qotib qolish oldi olindi)
    waiting_msg = await callback.message.answer("🔍 Qidirilmoqda...")
    await callback.answer()
    
    # 3. 🚀 YANGI ENGLIL VA TEZKOR QIDIRUV (Baza darajasida):
    from services.anime_service import AnimeService
    anime_service = AnimeService(session=session)
    found_animes = await anime_service.search_by_genres(selected_genres)
            
    # Vaqtinchalik xabarni o'chiramiz
    try:
        await waiting_msg.delete()
    except:
        pass
        
    if not found_animes:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Qayta urinish", callback_data="search_by_genre", style="success")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="search_menu", style="danger")]
        ])
        await callback.message.answer(
            text="🔍 Tanlangan janrlar kombinatsiyasi bo'yicha hech qanday anime topilmadi.",
            reply_markup=kb
        )
        return
        
    # 4. Topilgan animelarni tugma qilib chiqaramiz
    buttons = []
    for anime in found_animes[:15]: # Maksimal 15 ta natija
        buttons.append([InlineKeyboardButton(
            text=f"🎬 {anime['title']}", 
            callback_data=f"user_g_view_{anime['anime_id']}" # Maxsus callback
        )])
        
    buttons.append([InlineKeyboardButton(text="⬅️ Qidiruv menyusi", callback_data="search_menu", style="danger")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        text=f"🎯 <b>Janrlar bo'yicha natijalar (Topildi: {len(found_animes)} ta):</b>\n\nO'zingizga maqbul animeni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )