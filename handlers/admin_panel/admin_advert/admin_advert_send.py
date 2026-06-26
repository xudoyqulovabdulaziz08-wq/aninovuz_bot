
import asyncio
import logging
from typing import Any
from aiogram import Router, html, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from repositories.user_repository import UserRepository
from database.models import DBUser, UserStatus
from services.user_service import UserService
router = Router()
logger = logging.getLogger("AdminVIP")
class AdminAdvertSG(StatesGroup):
    waiting_for_ad = State()


# 1. Reklama yuborish tugmasi bosilganda toifalarni ko'rsatish
@router.callback_query(F.data == "admin_advert")
async def process_admin_advert_menu(callback: CallbackQuery):
    await callback.answer()
    
    # Guruhlarga mos maxsus callback_data format: "send_adv:{guruh_nomi}"
    advert_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌍 Hammaga (User, VIP, Admin)", callback_data="send_adv:all", style="primary")
        ],
        [
            InlineKeyboardButton(text="💎 Faqat VIP foydalanuvchilarga", callback_data="send_adv:vip", style="primary")
        ],
        [
            InlineKeyboardButton(text="👤 Faqat oddiy foydalanuvchilarga", callback_data="send_adv:user", style="primary")
        ],
        [
            InlineKeyboardButton(text="🛠 Faqat Adminlarga", callback_data="send_adv:admin", style="primary")
        ],
        [
            # Admin bosh menyusiga yoki mos keladigan asosiy panelga qaytish
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_panel", style="danger")
        ]
    ])
    
    await callback.message.edit_text(
        text="📢 <b>Reklama va Bildirishnomalar yuborish bo'limi</b>\n\n"
             "<i>Ushbu bo'lim orqali bot foydalanuvchilariga reklama, aksiya yoki texnik "
             "xabarlarni yuborishingiz mumkin.</i>\n\n"
             "✨ Xabar yubormoqchi bo'lgan maqsadli (target) guruhni tanlang:",
        reply_markup=advert_kb,
        parse_mode="HTML"
    )






@router.callback_query(F.data.startswith("send_adv:"))
async def process_select_advert_target(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    target_group = callback.data.split(":")[1]
    
    group_titles = {
        "all": "🌍 Hammaga (User, VIP, Admin)",
        "vip": "💎 Faqat VIP foydalanuvchilarga",
        "user": "👤 Faqat oddiy foydalanuvchilarga",
        "admin": "🛠 Faqat Adminlarga"
    }
    title = group_titles.get(target_group, target_group)
    
    # 🔥 HIYLA: Keyingi qadamda edit qilish uchun shu xabar ID sini saqlaymiz
    await state.update_data(
        target_group=target_group, 
        group_title=title, 
        main_msg_id=callback.message.message_id
    )
    await state.set_state(AdminAdvertSG.waiting_for_ad)
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_advert", style="danger")]
    ])
    
    await callback.message.edit_text(
        text=f"🎯 Target guruh: <b>{title}</b>\n\n"
             f"📥 <b>Iltimos, yubormoqchi bo'lgan reklama xabaringizni shu yerga yuboring...</b>\n\n"
             f"<i>(Rasm, video, matn yoki xohlagan formatingizni yuborsangiz, bot chatni tozalab, bitta xabarda davom ettiradi)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )




@router.message(AdminAdvertSG.waiting_for_ad)
async def broadcast_advert_in_background(
        self, 
        bot: Any, 
        target_group: str, 
        from_chat_id: int, 
        message_id: int
    ) -> None:
        import asyncio
        from sqlalchemy import select
        from database.models import DBUser, UserStatus

        logger.info(f"🚀 Background broadcast session optimized for: {target_group}")
        
        try:
            if hasattr(self.session, "_ensure_session"):
                await self.session._ensure_session()
                
            from repositories.user_repository import UserRepository
            real_session = UserRepository._get_real_session(self.session)

            stmt = select(DBUser.user_id)
            if target_group == "vip":
                stmt = stmt.where(DBUser.status == UserStatus.VIP)
            elif target_group == "user":
                stmt = stmt.where(DBUser.status == UserStatus.USER)
            elif target_group == "admin":
                stmt = stmt.where(DBUser.status == UserStatus.ADMIN)

            result = await real_session.execute(stmt)
            user_ids = result.scalars().all()
            
        except Exception as e:
            logger.error(f"❌ Error fetching users for advertisement: {e}")
            return

        success_count = 0
        fail_count = 0

        # Tarqatish jarayoni (Xabar hali o'chirilmagani uchun 100% muvaffaqiyatli o'tadi)
        for uid in user_ids:
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=from_chat_id,
                    message_id=message_id
                )
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                fail_count += 1
                logger.debug(f"Could not send ad to {uid}: {e}")

        logger.info(f"🏁 Advert broadcast finished. Success: {success_count}, Failed: {fail_count}")

        # 🔥 UX TOZALIK: Tarqatish tugagach, admin yuborgan o'sha asl xabarni chatdan o'chiramiz!
        try:
            await bot.delete_message(chat_id=from_chat_id, message_id=message_id)
        except Exception as del_err:
            logger.debug(f"Original message delete error: {del_err}")

        # Adminga yakuniy hisobot
        try:
            await bot.send_message(
                chat_id=from_chat_id,
                text=f"📊 <b>Reklama tarqatish yakunlandi!</b>\n\n"
                     f"🎯 Guruh: <code>{target_group.upper()}</code>\n"
                     f"✅ Yetkazildi: <code>{success_count} ta</code>\n"
                     f"❌ Yetkazilmadi (Botni bloklaganlar): <code>{fail_count} ta</code>\n\n"
                     f"✨ <i>Chat tozaligi saqlandi va reklama xabari o'chirildi.</i>",
                parse_mode="HTML"
            )
        except Exception:
            pass







@router.callback_query(F.data.startswith("adv_confirm:"))
async def process_final_advert_decision(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    decision = callback.data.split(":")[1]
    
    if decision == "no":
        await callback.answer("Reklama bekor qilindi.")
        data = await state.get_data()
        ad_message_id = data.get("ad_message_id")
        ad_chat_id = data.get("ad_chat_id")
        
        # Admin yuborgan xabarni o'chirib tashlaymiz
        try:
            await callback.bot.delete_message(chat_id=ad_chat_id, message_id=ad_message_id)
        except Exception:
            pass
            
        await state.clear()
        await callback.message.edit_text(
            text="❌ <b>Reklama yuborish bekor qilindi.</b>\nPanel toza saqlandi.",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    target_group = data.get("target_group")
    ad_message_id = data.get("ad_message_id")
    ad_chat_id = data.get("ad_chat_id")
    
    await callback.answer("🚀 Tarqatish boshlandi!", show_alert=False)
    await state.clear()
    
    # Orqa fonda (background) UserService orqali yuborishni ishga tushiramiz
    asyncio.create_task(
        user_service.broadcast_advert_in_background(
            bot=callback.bot,
            target_group=target_group,
            from_chat_id=ad_chat_id,
            message_id=ad_message_id
        )
    )
    
    # Aynan o'sha xabarning o'zini yakuniy statusga edit qilamiz!
    await callback.message.edit_text(
        text="🚀 <b>Reklama orqa fonda tarqatila boshladi!</b>\n\n"
             "Bot foydalanuvchilarga odatiy rejimda xizmat ko'rsatishda davom etadi. "
             "Tarqatish yakunlangach, shu yerda sizga hisobot chiqadi.",
        parse_mode="HTML"
    )
# 6. Har qanday vaqtda bekor qilish handler'i
@router.callback_query(F.data == "cancel_advert")
async def process_cancel_advert_global(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Jarayon bekor qilindi.")
    await state.clear()
    await callback.message.edit_text(
        text="❌ Reklama yuborish jarayoni bekor qilindi.",
        parse_mode="HTML"
    )