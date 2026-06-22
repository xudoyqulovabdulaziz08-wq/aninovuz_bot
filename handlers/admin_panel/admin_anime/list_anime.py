
import math
import logging
from typing import Any
from aiogram import Router, F, html
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from services.anime_service import AnimeService

from aiogram.types import InputMediaVideo



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
            await callback.answer("Yuklanmoqda...") # Faqat muvaffaqiyatli editdan keyin soatni o'chiramiz
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
            InlineKeyboardButton(text="📹 Qismlarni tahrirlash", callback_data=f"manage_episodes:{anime_id}", style="primary"),
            InlineKeyboardButton(text="🗑 Animeni o‘chirish", callback_data=f"del_anime:{anime_id}", style="danger")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ro‘yxatga qaytish", callback_data=f"list_anime_page:{page}", style="danger")
        ]
    ])

    # 5. Interfeys qotib qolmasligi uchun answer shu yerda beriladi
    await callback.answer("Yuklanmoqda...") 
    
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
            [InlineKeyboardButton(text="⬅️ Anime menyusiga", callback_data="admin_anime", style="danger")]
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
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"list_anime_page:{page-1}", style="primary"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void", style="danger"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="void", style="primary"))

    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"list_anime_page:{page+1}", style="primary"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void", style="danger"))

    inline_keyboard.append(nav_row)

    # 7. Ortga qaytish satri (style olib tashlandi, chunki Aiogram 3 oddiy tugmalarga rang bera olmaydi)
    inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Anime menyusiga", callback_data="admin_anime", style="danger")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard), total_anime



@router.callback_query(F.data.startswith("del_anime:"))
async def confirm_delete_anime_handler(callback: CallbackQuery, session: Any):
    await callback.answer("Yuklanmoqda...")
    anime_id = int(callback.data.split(":")[1])
    
    confirm_text = (
        f"⚠️ {html.bold('DIQQAT! O‘chirishni tasdiqlang')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Ushbu animeni ro‘yxatdan butunlay o‘chirib tashlamoqchimisiz?\n\n"
        f"🛑 {html.italic('Bu amalni ortga qaytarib bo‘lmaydi! Animega tegishli barcha qismlar (seriyalar) ham bazadan o‘chib ketadi.')}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha,  o‘chirish", callback_data=f"burn_anime:{anime_id}", style="success"),
            InlineKeyboardButton(text="❌ bekor qilish", callback_data=f"v_anime:{anime_id}:1", style="danger")
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
    await callback.answer("O'chirilmoqda")
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
        [InlineKeyboardButton(text="⬅️ Animelar ro‘yxatiga", callback_data="list_anime_page:1", style="danger")]
    ])
    
    # Toza matn ko'rinishida yakuniy javobni yuboramiz
    try:
        await callback.message.answer(text=success_text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"❌ Yakuniy xabarni yuborishda xato: {e}")











@router.callback_query(F.data.startswith("manage_episodes:"))
async def manage_episodes_handler(callback: CallbackQuery, session: Any):
    # Interfeys qotib qolmasligi uchun darhol javob beramiz
    await callback.answer("Yuklanmoqda...")
    
    anime_id = int(callback.data.split(":")[1])
    
    # 1. DB/Cache dan animeni xavfsiz yuklaymiz
    service = AnimeService(session=session)
    try:
        anime = await service.get_anime(anime_id)
    except Exception as e:
        logger.error(f"❌ Tahrirlash uchun anime yuklashda xato: {e}")
        anime = None

    if not anime:
        await callback.message.answer("❌ Anime topilmadi yoki o‘chirilgan!")
        return

    title = anime.get("title", "Nomsiz anime")
    episodes = anime.get("episodes", [])
    episodes_count = len(episodes)

    # 2. Qismlar boshqaruvi uchun maxsus dizayn
    caption = (
        f"╔══════════════════╗\n"
        f"  ⚙️ <b>Qismlarni boshqarish</b>\n"
        f"╚══════════════════╝\n\n"
        f"🎬 Anime: <b>{title}</b>\n"
        f"🔢 Mavjud qismlar soni: <b>{episodes_count} ta</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 {html.italic('Quyidagi tugmalar orqali ushbu animening qismlarini qo‘shishingiz, o‘chirishingiz yoki fayllarini yangilashingiz mumkin.')}"
    )

    # 3. Dinamik inline tugmalar ierarxiyasi
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Qism qo‘shish", callback_data=f"add_episode:{anime_id}", style="success")
        ],
        [
            InlineKeyboardButton(text="▶️ Qismlarni ko‘rish", callback_data=f"view_episodes_list:{anime_id}", style="primary")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"v_anime:{anime_id}:1", style="danger" )
        ]
    ])

    # 4. Posterni o'chirmasdan, uning ostidagi matn va tugmalarni silliq yangilash
    try:
        # Agar xabarda media (photo/video) bo'lsa, caption va reply_markup o'zgaradi
        await callback.message.edit_caption(caption=caption, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        # Agar xabar faqat matndan iborat bo'lsa (poster_id bo'lmagan holatda fallback)
        if "message is not modified" not in str(e).lower():
            try:
                await callback.message.edit_text(text=caption, reply_markup=kb, parse_mode="HTML")
            except Exception as err:
                logger.error(f"❌ Panelni yangilashda xato: {err}")










@router.callback_query(F.data.startswith("view_episodes_list:") | F.data.startswith("view_episodes_page:"))
async def view_episodes_list_handler(callback: CallbackQuery, session: Any):
    await callback.answer("Qismlar yuklanmoqda...")
    
    parts = callback.data.split(":")
    anime_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 1

    service = AnimeService(session=session)
    anime = await service.get_anime(anime_id)
    
    if not anime:
        await callback.message.answer("❌ Anime topilmadi!")
        return

    title = anime.get("title", "Nomsiz anime")
    episodes = anime.get("episodes", [])

    caption = (
        f"╔══════════════════╗\n"
        f"  🎬 <b>{title}</b>\n"
        f"╚══════════════════╝\n\n"
        f"📹 Ro‘yxatdan kerakli qismni tanlang.\n"
        f"💡 {html.italic('Tanlangan qism videosi va uni boshqarish tugmalari shu yerning o‘zida ochiladi.')}"
    )

    markup = await get_episode_list_markup(anime_id=anime_id, episodes=episodes, page=page)

    try:
        await callback.message.edit_caption(caption=caption, reply_markup=markup, parse_mode="HTML")
    except TelegramBadRequest:
        try:
            await callback.message.edit_text(text=caption, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            logger.error(f"❌ Qismlar ro'yxatini tahrirlashda xato: {e}")










async def get_episode_list_markup(anime_id: int, episodes: list, page: int = 1, per_page: int = 12) -> InlineKeyboardMarkup:
    total_episodes = len(episodes)
    
    # Agar qismlar hali yuklanmagan bo'lsa
    if total_episodes == 0:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⛔️ Qismlar mavjud emas", callback_data="void", style="danger")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"manage_episodes:{anime_id}", style="danger")]
        ])

    total_pages = math.ceil(total_episodes / per_page)
    page = max(1, min(page, total_pages))

    # Joriy sahifaga mos qismlarni kesib olish
    start_idx = (page - 1) * per_page
    current_page_episodes = episodes[start_idx : start_idx + per_page]

    inline_keyboard = []
    row = []

    # Qismlarni chiroyli to'r (grid) ko'rinishida 3 tadan qilib joylaymiz
    for ep in current_page_episodes:
        ep_num = ep.get("episode")
        # Har bir qism bosilganda 'show_ep:anime_id:ep_num:page' formatida callback ketadi
        row.append(InlineKeyboardButton(
            text=f"📹 {ep_num} ▶️", 
            callback_data=f"show_ep:{anime_id}:{ep_num}:{page}"
        ))
        
        if len(row) == 3:  # Har 3 ta tugmadan keyin yangi qatorga o'tadi
            inline_keyboard.append(row)
            row = []
            
    if row:  # Qolib ketgan tugmalar bo'lsa qo'shib qo'yamiz
        inline_keyboard.append(row)

    # Paginatsiya (Navigatsiya) satri
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"view_episodes_page:{anime_id}:{page-1}", style="primary"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void", style="danger"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="void", style="primary"))

    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"view_episodes_page:{anime_id}:{page+1}", style="primary"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void", style="danger"))

    inline_keyboard.append(nav_row)

    # Ortga qaytish satri
    inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"manage_episodes:{anime_id}", style="danger")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)














@router.callback_query(F.data.startswith("show_ep:"))
async def show_specific_episode_handler(callback: CallbackQuery, session: Any):
    await callback.answer("Video yuklanmoqda...")
    
    _, anime_id_str, ep_num_str, back_page_str = callback.data.split(":")
    anime_id = int(anime_id_str)
    ep_num = int(ep_num_str)
    back_page = int(back_page_str)  # Orqaga qaytganda o'sha sahifani eslab qolish uchun

    service = AnimeService(session=session)
    anime = await service.get_anime(anime_id)
    
    if not anime:
        await callback.message.answer("❌ Anime topilmadi!")
        return

    # Kerakli epizod ma'lumotlarini file_id si bilan ajratib olamiz
    episodes = anime.get("episodes", [])
    target_ep = next((ep for ep in episodes if ep.get("episode") == ep_num), None)

    if not target_ep:
        await callback.answer("❌ Ushbu qism videosi topilmadi!", show_alert=True)
        return

    file_id = target_ep.get("file_id")
    title = anime.get("title", "Nomsiz anime")

    # Siz aytgan tagidagi yozuv va dizayn
    caption = (
        f"🎬 <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📹 Joriy qism: <b>{ep_num}-qism</b>\n\n"
        f"🛠 <b>Admin amallari:</b>\n"
        f"⚠️ {html.italic('Ushbu qismni o‘chirish yoki yangi faylga almashtirish uchun quyidagi tugmalardan foydalaning.')}"
    )

    # Admin boshqaruv tugmalari
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑   O‘chirish", callback_data=f"burn_ep:{anime_id}:{ep_num}:{back_page}", style="danger" ),
            InlineKeyboardButton(text="🔄  Almashtirish", callback_data=f"swap_ep:{anime_id}:{ep_num}:{back_page}", style="primary" )
        ],
        [
            # Ro'yxatga qaytishda aynan qaysi sahifadan kelgan bo'lsa, o'shanga qaytadi
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"view_episodes_page:{anime_id}:{back_page}", style="danger" )
        ]
    ])

    # 🔥 MEDIA EDIT: Posterni o'rniga haqiqiy videoni silliq joylashtiramiz
    try:
        new_media = InputMediaVideo(media=file_id, caption=caption, parse_mode="HTML")
        await callback.message.edit_media(media=new_media, reply_markup=kb)
    except TelegramBadRequest as e:
        logger.error(f"❌ Media almashtirishda xatolik yuz berdi: {e}")
        await callback.answer("❌ Videoni yuklashda xatolik! Fayl ID buzilgan bo'lishi mumkin.", show_alert=True)