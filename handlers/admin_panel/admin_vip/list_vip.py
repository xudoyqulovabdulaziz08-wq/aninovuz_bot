import math
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.user_service import UserService
from typing import Any
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.cache import cache_manager

logger = logging.getLogger("AdminVIPlist")
router = Router()





async def get_vip_list_markup(session, page: int = 1, per_page: int = 10) -> tuple[InlineKeyboardMarkup, int]:
    service = UserService(session=session)
    
    # 1. Keshdan yoki DB dan ma'lumotlarni xavfsiz yuklash
    try:
        all_vips = await service.list_vip_users()
        if not all_vips:  # Agar None kelsa bo'sh ro'yxat
            all_vips = []
    except Exception as e:
        logger.error(f"❌ VIP ro'yxatini olishda xatolik: {e}")
        all_vips = []
        
    total_vips = len(all_vips)
    
    # 2. Agar VIP foydalanuvchi umuman topilmasa
    if total_vips == 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ VIP menyusiga", callback_data="admin_panel", style="danger")]
        ])
        return kb, 0

    # 3. Sahifalarni xavfsiz va qisqa yo'l bilan hisoblash
    total_pages = math.ceil(total_vips / per_page)
    page = max(1, min(page, total_pages))

    # 4. Ro'yxatdan joriy sahifaga kerakli qismini kesib olish
    start_idx = (page - 1) * per_page
    current_page_vips = all_vips[start_idx : start_idx + per_page]

    inline_keyboard = []

    # 5. Tugmalarni shakllantirish (Lug'at kalitlarini xavfsiz o'qish)
    for vip in current_page_vips:
        user_id = vip.get("user_id")
        username = vip.get("username") or f"ID: {user_id}"
        
        # Sanani chiroyli formatda ko'rsatish uchun parse qilamiz
        expire_str = vip.get("vip_expire_date")
        date_short = "—"
        if expire_str:
            try:
                # ISO formatdan faqat yil-oy-kun qismini ajratamiz
                date_short = expire_str.split("T")[0]
            except Exception:
                pass
        
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"💎 {username} [{date_short}]", 
                callback_data=f"view_vip:{user_id}:{page}"
            )
        ])

    # 6. Paginatsiya (Navigatsiya) satri - UX Andozangiz bilan 100% bir xil
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"list_vip_page:{page-1}", style="primary"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void", style="danger"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="void", style="primary"))

    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"list_vip_page:{page+1}", style="primary"))
    else:
        nav_row.append(InlineKeyboardButton(text="⛔️", callback_data="void", style="danger"))

    inline_keyboard.append(nav_row)

    # 7. Ortga qaytish satri
    inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ VIP menyusiga", callback_data="admin_panel", style="danger")
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard), total_vips













# 1. Asosiy "📃 VIPlar ro‘yxati" tugmasi bosilganda
@router.callback_query(F.data == "list_vip")
async def process_list_vip_initial(callback: CallbackQuery, session: Any):
    await callback.answer("⏳ Yuklanmoqda...", show_alert=False)
    
    # 1-sahifani generatsiya qilamiz
    markup, total_count = await get_vip_list_markup(session=session, page=1)
    
    if total_count == 0:
        await callback.message.edit_text(
            text="💎 <b>Hozirda bot tizimida hech qanday VIP foydalanuvchi mavjud emas!</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text=f"📃 <b>VIP maqomiga ega foydalanuvchilar ro'yxati:</b>\n\n"
                 f"ℹ️ Jami: <code>{total_count} ta user</code>\n"
                 f"<i>Batafsil ko'rish yoki VIP statusni o'chirish uchun foydalanuvchi ustiga bosing.</i>",
            reply_markup=markup,
            parse_mode="HTML"
        )


# 2. Paginatsiya tugmalari bosilganda (list_vip_page:X)
@router.callback_query(F.data.startswith("list_vip_page:"))
async def process_vip_pagination(callback: CallbackQuery, session: Any):
    # Callback datadan sahifa raqamini ajratamiz
    target_page = int(callback.data.split(":")[1])
    await callback.answer()
    
    markup, total_count = await get_vip_list_markup(session=session, page=target_page)
    
    try:
        await callback.message.edit_text(
            text=f"📃 <b>VIP maqomiga ega foydalanuvchilar ro'yxati:</b>\n\n"
                 f"ℹ️ Jami: <code>{total_count} ta user</code>\n"
                 f"<i>Batafsil ko'rish yoki VIP statusni o'chirish uchun foydalanuvchi ustiga bosing.</i>",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception:
        # Agar sahifa o'zgarmasdan tahrirlansa xato bermasligi uchun
        pass


# 3. Bo'sh tugma (⛔️ yoki sahifa raqami) bosilganda Telegram "soat"ini to'xtatish
@router.callback_query(F.data == "void")
async def process_void_click(callback: CallbackQuery):
    await callback.answer()







# 1. VIP foydalanuvchi tugmasi bosilganda (Batafsil ma'lumot va boshqaruv)
@router.callback_query(F.data.startswith("view_vip:"))
async def process_view_vip_details(callback: CallbackQuery, session: Any):
    await callback.answer()
    
    # Callback datadan kerakli ma'lumotlarni ajratib olamiz
    params = callback.data.split(":")
    target_user_id = int(params[1])
    current_page = int(params[2]) # Orqaga qaytishda aynan shu sahifaga qaytish uchun

    user_service = UserService(session=session)
    user_data = await user_service.get_user(user_id=target_user_id)

    if not user_data:
        await callback.message.edit_text(
            text="❌ Foydalanuvchi ma'lumotlari topilmadi yoki u tizimdan o'chirilgan.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data=f"list_vip_page:{current_page}", style="danger")]
            ]),
            parse_mode="HTML"
        )
        return

    username = user_data.get("username") or "Foydalanuvchi"
    expire_str = user_data.get("vip_expire_date")
    
    # Qancha vaqt qolganini aniq hisoblash (Server va Baza UTC vaqtida)
    time_left_str = "Muddat tugagan yoki belgilanmagan"
    formatted_expire_date = "—"
    
    if expire_str:
        try:
            # ISO stringdan datetime ob'ektiga o'tkazamiz
            expire_dt = datetime.fromisoformat(expire_str)
            formatted_expire_date = expire_dt.strftime("%d.%m.%Y %H:%M")
            
            # Server UTC vaqti bilan taqqoslaymiz
            now = datetime.now(timezone.utc)
            
            if expire_dt > now:
                diff = expire_dt - now
                days = diff.days
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                
                time_left_str = f"🟢 <b>{days} kun, {hours} soat, {minutes} daqiqa</b>"
            else:
                time_left_str = "🔴 <b>Muddati tugagan</b> (Kesh tozalanishi kutilmoqda)"
        except Exception as e:
            logger.error(f"Sana hisoblashda xatolik: {e}")
            time_left_str = "⚠️ Sanani hisoblashda xatolik"

    # Tugmalar konfiguratsiyasi (current_page zanjirini uzatib boramiz)
    vip_manage_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏳ VIP Uzaytirish", callback_data=f"extend_vip:{target_user_id}:{current_page}", style="primary"),
            InlineKeyboardButton(text="❌ VIP O'chirish", callback_data=f"revoke_vip_confirm:{target_user_id}:{current_page}", style="danger")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"list_vip_page:{current_page}", style="danger" )
        ]
    ])

    await callback.message.edit_text(
        text=f"👤 <b>VIP Foydalanuvchi profili (Admin nazorati)</b>\n\n"
             f"🆔 <b>Telegram ID:</b> <code>{target_user_id}</code>\n"
             f"🎭 <b>Username:</b> @{username if username != 'Foydalanuvchi' else '—'}\n"
             f"📅 <b>Tugash sanasi (UTC):</b> <code>{formatted_expire_date}</code>\n"
             f"⏱ <b>Qolgan vaqt:</b> {time_left_str}\n\n"
             f"✨ Foydalanuvchi ustida bajariladigan amalni tanlang:"
             f"⚠️ Eslatib otamiz vaqt mintaqasi bizning soatdan 5 soat orqada bu bilan hech qanday muddat qoshmaydi yoki muddat kamaymaydi",
        reply_markup=vip_manage_kb,
        parse_mode="HTML"
    )






# 1. Uzaytirish bosqichi - Muddatlarni ko'rsatish
@router.callback_query(F.data.startswith("extend_vip:"))
async def process_extend_vip_select_duration(callback: CallbackQuery):
    await callback.answer()
    
    params = callback.data.split(":")
    target_user_id = params[1]
    current_page = params[2]
    
    # Uzaytirish uchun maxsus tugmalar jamlanmasi (Dinamik ma'lumotlar bilan)
    duration_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 1 Oylik", callback_data=f"ext_dur:1:{target_user_id}:{current_page}", style="primary"),
            InlineKeyboardButton(text="📅 2 Oylik", callback_data=f"ext_dur:2:{target_user_id}:{current_page}", style="primary")
        ],
        [
            InlineKeyboardButton(text="📅 3 Oylik", callback_data=f"ext_dur:3:{target_user_id}:{current_page}", style="primary"),
            InlineKeyboardButton(text="📅 6 Oylik", callback_data=f"ext_dur:6:{target_user_id}:{current_page}", style="primary")
        ],
        [
            InlineKeyboardButton(text="📆 1 Yillik", callback_data=f"ext_dur:12:{target_user_id}:{current_page}", style="primary")
        ],
        [
            # Bekor qilsa foydalanuvchining ma'lumotlar oynasiga qaytaradi
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"view_vip:{target_user_id}:{current_page}", style="danger")
        ]
    ])
    
    await callback.message.edit_text(
        text=f"⏳ <b>ID: {target_user_id} foydalanuvchining VIP maqomini uzaytirish.</b>\n\n"
             f"<i>Iltimos, amaldagi muddatga qo'shiladigan yangi muddatni tanlang:</i>",
        reply_markup=duration_kb,
        parse_mode="HTML"
    )




@router.callback_query(F.data.startswith("ext_dur:"))
async def process_extend_vip_confirm_prompt(callback: CallbackQuery):
    await callback.answer()
    
    params = callback.data.split(":")
    months = int(params[1])
    target_user_id = int(params[2])
    current_page = int(params[3])
    
    duration_text = f"{months} oylik" if months < 12 else "1 yillik"
    
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"ext_conf:yes:{months}:{target_user_id}:{current_page}", style="primary"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"ext_conf:no:{months}:{target_user_id}:{current_page}", style="danger")
        ]
    ])
    
    await callback.message.edit_text(
        text=f"❓ <b>Tasdiqlash:</b>\n\n"
             f"Rostdan ham <code>{target_user_id}</code> ID raqamli foydalanuvchining VIP muddatiga "
             f"yana <b>{duration_text}</b> qo'shib, statusini uzaytirmoqchimisiz?",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )





from datetime import datetime, timedelta, timezone
from sqlalchemy import update

# 3. Uzaytirish bosqichi - Yakuniy ijro (Baza bilan xavfsiz tranzaksiya)
@router.callback_query(F.data.startswith("ext_conf:"))
async def process_extend_vip_final_execution(callback: CallbackQuery, session: Any):
    params = callback.data.split(":")
    decision = params[1]
    months = int(params[2])
    target_user_id = int(params[3])
    current_page = int(params[4])
    
    # Agar adminga "Yo'q" tugmasini bossa, darhol profil ko'rinishiga qaytaramiz
    if decision == "no":
        await callback.answer("Uzaytirish bekor qilindi.")
        # Avval yozgan profilni ko'rish handlerimizni qo'lda chaqirib qo'ysak ham bo'ladi yoki redirect
        await callback.message.edit_text(text="⏳ Profil ma'lumotlariga qaytilmoqda...")
        # Profilni qayta yuklash callback'ini simulyatsiya qilamiz
        callback.data = f"view_vip:{target_user_id}:{current_page}"
        return await process_view_vip_details(callback, session)

    await callback.answer("⏳ VIP muddat uzaytirilmoqda...", show_alert=False)
    
    try:
        user_service = UserService(session=session)
        user_data = await user_service.get_user(user_id=target_user_id)
        
        if not user_data:
            await callback.message.edit_text(text="❌ Xatolik: Foydalanuvchi bazadan topilmadi.")
            return

        from database.models import DBUser, UserStatus
        
        # 📌 ESKI MUDDATGA QO'SHISH MATEMATIKASI (Server UTC vaqtida)
        now = datetime.now(timezone.utc)
        days_to_add = months * 30
        
        expire_str = user_data.get("vip_expire_date")
        base_date = now
        
        if expire_str:
            try:
                expire_dt = datetime.fromisoformat(expire_str)
                # Agar amaldagi VIP muddati hali tugamagan bo'lsa, yangi muddatni joriy tugash sanasining USTIGA qo'shamiz!
                if expire_dt > now:
                    base_date = expire_dt
            except Exception:
                base_date = now

        # Yangi yakuniy sana
        new_expire_date = base_date + timedelta(days=days_to_add)

        # SQL Alchemy orqali bazani yangilaymiz
        stmt = (
            update(DBUser)
            .where(DBUser.user_id == target_user_id)
            .values(status=UserStatus.VIP, vip_expire_date=new_expire_date)
        )
        await session.execute(stmt)
        await session.commit()

        # Keshni tozalaymiz, shunda middleware va servis yangi sanani oqiydi
        await cache_manager.invalidate("users", str(target_user_id), broadcast=True)
        await cache_manager.invalidate("sub_status", str(target_user_id), broadcast=True)

        formatted_date = new_expire_date.strftime("%d.%m.%Y %H:%M")
        duration_text = f"{months} oylik" if months < 12 else "1 yillik"

        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Profilga qaytish", callback_data=f"view_vip:{target_user_id}:{current_page}", style="danger")]
        ])

        await callback.message.edit_text(
            text=f"🚀 <b>VIP muvaffaqiyatli uzaytirildi!</b>\n\n"
                 f"👤 Foydalanuvchi: <code>{target_user_id}</code>\n"
                 f"➕ Qo'shildi: <b>{duration_text}</b>\n"
                 f"📅 Yangi tugash muddati (UTC): <code>{formatted_date}</code>",
            reply_markup=back_kb,
            parse_mode="HTML"
        )

        # Foydalanuvchini xabardor qilish
        try:
            await callback.bot.send_message(
                chat_id=target_user_id,
                text=f"✨ <b>VIP maqomingiz uzaytirildi!</b>\n"
                     f"Admin tomonidan sizga yana {duration_text} VIP muddat qo'shildi.\n"
                     f"📅 Yangi amal qilish muddati: <code>{formatted_date}</code> (UTC) gacha.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    except Exception as e:
        await session.rollback()
        logger.error(f"VIP uzaytirishda xatolik: {e}")
        await callback.message.edit_text(
            text="❌ <b>Xatolik yuz berdi!</b> VIP muddatini uzaytirish imkoni bo'lmadi.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Profilga qaytish", callback_data=f"view_vip:{target_user_id}:{current_page}", style="danger")]
            ])
        )
