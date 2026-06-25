import logging
from aiogram import Router, F
from datetime import datetime, timedelta, timezone
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.user_service import UserService 
from typing import Any


logger = logging.getLogger("AdminVIP")
router = Router()

class AdminVIPStates(StatesGroup):
    wait_for_user_id = State()  # User ID sini kutish holati






@router.callback_query(F.data == "add_vip")
async def process_add_vip_click(callback: CallbackQuery, state: FSMContext):
    # Holatni o'rnatamiz (Bot endi aynan shu foydalanuvchidan ID kutadi)
    await state.set_state(AdminVIPStates.wait_for_user_id)
    
    # Orqaga qaytish tugmasi
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_vip_panel", style="danger")]
    ])
    
    # Matnni o'zgartiramiz
    await callback.message.edit_text(
        text="🆔 <b>Iltimos, VIP status bermoqchi bo'lgan foydalanuvchining Telegram ID raqamini yuboring:</b>\n\n"
             "<i>Masalan: 123456789</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await callback.answer()




@router.callback_query(AdminVIPStates.wait_for_user_id) # Callback bosib yuborsa ham tekshirish uchun
@router.message(AdminVIPStates.wait_for_user_id, ~F.text.isdigit())
async def process_invalid_user_id(message: Message):
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_vip_panel", style="danger")]
    ])
    
    await message.answer(
        text="⚠️ <b>Xato format!</b> Foydalanuvchi ID raqami faqat sonlardan iborat bo'lishi kerak.\n"
             "Iltimos, qaytadan faqat raqamlarni yuboring:",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )







  # UserService importi

# 5. To'g'ri ID (faqat raqamlar) kelganda ishlaydigan xavfsiz handler
@router.message(AdminVIPStates.wait_for_user_id, F.text.isdigit())
async def process_valid_user_id(message: Message, state: FSMContext, session: Any):
    user_id = int(message.text)
    
    # 🔍 1. Bazadan foydalanuvchini xavfsiz qidiramiz
    try:
        user_service = UserService(session=session)
        # Kesh-aware va xavfsiz usulda user ma'lumotlarini olamiz
        user_data = await user_service.get_user(user_id=user_id)
    except Exception as e:
        logger.error(f"VIP tekshiruvida user qidirishda xato: {e}")
        await message.answer("❌ Bazadan foydalanuvchini qidirishda texnik xatolik yuz berdi.")
        return

    # 🛑 2. Agar user bazada umuman mavjud bo'lmasa
    if not user_data:
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_vip_panel", style="danger")]
        ])
        await message.answer(
            text=f"❌ <b>ID: {user_id}</b> raqamli foydalanuvchi tizimda (bot bazasida) mavjud emas!\n"
                 f"Iltimos, ID raqamni to'g'ri kiritganingizni qayta tekshiring:",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
        return

    # ✅ 3. Foydalanuvchi topilsa, ID va Ismini saqlab qo'yamiz
    await state.update_data(target_user_id=user_id)
    
    username = user_data.get("username") or "Foydalanuvchi"
    current_status = user_data.get("status", "user")

    # 📅 4. Muddat tanlash tugmalarini hosil qilamiz (Callback_data ga oylarni yozamiz)
    duration_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 1 Oylik", callback_data="set_vip_duration:1", style="primary"),
            InlineKeyboardButton(text="📅 2 Oylik", callback_data="set_vip_duration:2", style="primary")
        ],
        [
            InlineKeyboardButton(text="📅 3 Oylik", callback_data="set_vip_duration:3", style="primary"),
            InlineKeyboardButton(text="📅 6 Oylik", callback_data="set_vip_duration:6", style="primary")
        ],
        [
            InlineKeyboardButton(text="📆 1 Yillik", callback_data="set_vip_duration:12", style="primary")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_vip_panel", style="danger")
        ]
    ])

    await message.answer(
        text=f"🔍 <b>Foydalanuvchi topildi!</b>\n\n"
             f"👤 <b>Nomi:</b> {username}\n"
             f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
             f"📊 <b>Joriy statusi:</b> <code>{current_status.upper()}</code>\n\n"
             f"✨ <i>Iltimos, ushbu foydalanuvchi uchun VIP muddatini tanlang:</i>",
        reply_markup=duration_kb,
        parse_mode="HTML"
    )