
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
    
    target_group = callback.data.split(":")[1] # all, vip, user, admin
    
    # Guruh nomini chiroyli matnga o'tkazamiz
    group_titles = {
        "all": "🌍 Hammaga (User, VIP, Admin)",
        "vip": "💎 Faqat VIP foydalanuvchilarga",
        "user": "👤 Faqat oddiy foydalanuvchilarga",
        "admin": "🛠 Faqat Adminlarga"
    }
    title = group_titles.get(target_group, target_group)
    
    # Ma'lumotlarni holatda saqlaymiz
    await state.update_data(target_group=target_group, group_title=title)
    await state.set_state(AdminAdvertSG.waiting_for_ad)
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_advert", style="danger")]
    ])
    
    await callback.message.edit_text(
        text=f"🎯 Target guruh: <b>{title}</b>\n\n"
             f"📥 <b>Iltimos, yubormoqchi bo'lgan reklama xabaringizni yuboring.</b>\n"
             f"<i>(Matn, rasm, video, albom, hujjat yoki inline tugmali xabar bo'lishi mumkin. Bot uni qanday bo'lsa shunday nusxalaydi)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )





@router.message(AdminAdvertSG.waiting_for_ad)
async def process_receive_advert_message(message: Message, state: FSMContext):
    # Admin yuborgan xabarning ID sini va Chat ID sini saqlaymiz
    await state.update_data(ad_message_id=message.message_id, ad_chat_id=message.chat.id)
    
    data = await state.get_data()
    title = data.get("group_title")
    
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, tarqatilsin", callback_data="adv_confirm:yes", style="primary"),
            InlineKeyboardButton(text="❌ Yo'q, bekor qilinsin", callback_data="adv_confirm:no", style="danger")
        ]
    ])
    
    # Admin yuborgan xabarga javob (reply) tariqasida tasdiqlash so'raymiz
    await message.reply(
        text=f"❓ <b>Reklamani tasdiqlash:</b>\n\n"
             f"Ushbu xabarni <b>{title}</b> guruhidagi barcha foydalanuvchilarga tarqatishni tasdiqlaysizmi?",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )









@router.callback_query(F.data.startswith("adv_confirm:"))
async def process_final_advert_decision(
    callback: CallbackQuery, 
    state: FSMContext, 
    user_service: UserService  # Middleware beradigan tayyor servis
):
    decision = callback.data.split(":")[1]
    
    if decision == "no":
        await callback.answer("Reklama yuborish bekor qilindi.")
        await state.clear()
        await callback.message.edit_text(
            text="❌ <b>Reklama yuborish bekor qilindi.</b>\nAsosiy admin panelga qaytishingiz mumkin.",
            parse_mode="HTML"
        )
        return

    # FSM ma'lumotlarini o'qiymiz
    data = await state.get_data()
    target_group = data.get("target_group")
    ad_message_id = data.get("ad_message_id")
    ad_chat_id = data.get("ad_chat_id")
    
    await callback.answer("🚀 Tarqatish boshlandi!", show_alert=False)
    await state.clear() # FSMni darhol tozalaymiz
    
    # 🔥 MUKAMMAL VA QISQA YECHIM: asyncio.create_task
    # UserService ichidagi tayyor metodni asinxron fonda chaqiramiz
    asyncio.create_task(
        user_service.broadcast_advert_in_background(
            bot=callback.bot,
            target_group=target_group,
            from_chat_id=ad_chat_id,
            message_id=ad_message_id
        )
    )
    
    # Adminga silliq va tezkor javob qaytaramiz
    await callback.message.edit_text(
        text="🚀 <b>Reklama orqa fonda tarqatila boshladi!</b>\n\n"
             "Bot foydalanuvchilarga odatiy rejimda xizmat ko'rsatishda davom etadi. "
             "Tarqatish yakunlangach, sizga yakuniy hisobot xabari yuboriladi.",
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