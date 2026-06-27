import logging
from asyncio.log import logger
from aiogram.exceptions import TelegramBadRequest

from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, html, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
from services.user_service import UserService
from config import config
from services.orchestrator import get_ai_stats
router = Router()

@router.callback_query(F.data == "creator_db_panel")
async def creator_db_menu(callback: CallbackQuery, user_service: UserService):
    # Tugma bosilganda yuqoridagi yuklanish soat belgisini darhol o'chiramiz
    await callback.answer()
    
    # 📊 1. Real vaqtda bazaning hajmini yuklab olamiz
    db_size = await user_service.get_database_storage_info()
    ai_stats = get_ai_stats()
    
    # 🗄️ UX ENGINIYERING: Maksimal darajada professional monitoring paneli dizayni
    text = (
        f"🗄️ {html.bold('Baza Nazorati va Tizim Control')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 {html.bold('Tizim statistikasi:')}\n"
        f"📝 Baza holati: <code>🟢 Faol / Stabil</code>\n"
        f"💾 Egallangan joy: {html.code(db_size)} 📦\n\n"
        f"🧠 {html.bold('AI Cache Brain holati:')}\n"
        f"├ 🔥 Kuzatuvdagi faol a'zolar: <code>{ai_stats['tracked_hot_users_count']} ta</code>\n"
        f"├ ⚡️ L1/L2 umumiy yozishlar: <code>{ai_stats['l1_total_writes']}/{ai_stats['l2_total_writes']}</code>\n"
        f"├ ⏱️ O'rtacha kechikish (Latency): <code>{ai_stats['avg_latency_ms']} ms</code>\n"
        f"└ 💤 Joriy dinamik uyqu: <code>{ai_stats['current_dynamic_sleep']}s</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ {html.bold('DIQQAT:')} Bu yerda amallarni bajarishda ehtiyot bo'ling.\n"
        f"👇 Ijro etish uchun operatsiyani tanlang:"
    )

    # 🎛️ Tugmalar dizayni va joylashuvi
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 Baza Import (.json)", callback_data="baza_import", style="primary"),
                InlineKeyboardButton(text="📤 Baza Export (Backup)", callback_data="baza_export", style="primary")
            ],
            [
                # Yangilash tugmasi - joy o'zgarganini qayta tekshirish uchun silliqqina shu oynani qayta yuklaydi
                InlineKeyboardButton(text="🔄 Statni yangilash", callback_data="creator_db_panel", style="primary")
            ],
            [
                InlineKeyboardButton(text="🗑️  OutboxEvent tozalash", callback_data="outboxevent_clear", style="primary")
            ],
            [
                InlineKeyboardButton(text="🗑️ Bazani toliq tozalash (Clear)", callback_data="baza_clear", style="danger")
            ],
            [
                InlineKeyboardButton(text="⬅️ Bosh panelga", callback_data="creator_panel", style="danger")  
            ]
        ]
    )

    # Media xabarlarni toza matnga almashtirish mantiqi
    if callback.message.photo or callback.message.video:
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        await callback.message.answer(text=text, reply_markup=kb, parse_mode="HTML")
        return

    # Toza matn bo'lsa, silliq edit_text (Xuddi dashboardlar kabi ma'lumot silliq yangilanadi)
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"❌ Baza bo'limida Telegram xatoligi: {e}")
    except Exception as e:
        logger.error(f"❌ Baza bo'limida kutilmagan xatolik: {e}")



    
    # =========================================================
# 1. 🗑️ OUTBOX TOZALASH TUGMASI BOSILGANDA (TASDIQLASH)
# =========================================================
@router.callback_query(F.data == "outboxevent_clear")
async def confirm_outbox_clear_request(callback: CallbackQuery):
    await callback.answer()
    
    text = (
        f"❓ {html.bold('OutboxEvent loglarini tozalash')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Rostdan ham tizimda qayta ishlab bo‘lingan barcha kesh va sinxronizatsiya loglarini o‘chirmoqchimisiz?\n\n"
        f"ℹ️ {html.italic('Bu amal faqat muvaffaqiyatli yakunlangan loglarni o‘chiradi, asosiy kontent (anime, qism, user) larga mutlaqo zarar yetkazmaydi hamda bazada ancha joy ochadi.')}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, tozalansin", callback_data="confirm_outbox:yes", style="primary"),
            InlineKeyboardButton(text="❌ Yo‘q, bekor qilish", callback_data="creator_db_panel", style="danger")
        ]
    ])
    
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")


# =========================================================
# 2. ⚡ YAKUNIY TOZALASH AMALI (HA / YO'Q)
# =========================================================
@router.callback_query(F.data.startswith("confirm_outbox:"))
async def finalize_outbox_clear(callback: CallbackQuery, user_service: UserService):
    await callback.answer()
    
    decision = callback.data.split(":")[1]
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Baza paneliga qaytish", callback_data="creator_db_panel", style="danger")]
    ])
    
    if decision == "yes":
        # Servis orqali eski loglarni tozalaymiz
        count = await user_service.clean_outbox_events()
        
        text = (
            f"🧹 {html.bold('Tozalash yakunlandi!')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Vazifasini bajarib bo‘lgan jami {html.code(count)} ta OutboxEvent loglari bazadan muvaffaqiyatli o‘chirib tashlandi.\n\n"
            f"📉 Baza diski yengillashdi va xavfsizlik ta'minlandi."
        )
    else:
        text = f"❌ {html.bold('Tozalash amali bekor qilindi.')}\n\nHech qanday log o‘chirilmadi."

    await callback.message.edit_text(text=text, reply_markup=back_kb, parse_mode="HTML")