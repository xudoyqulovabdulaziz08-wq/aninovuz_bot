import logging
import aiohttp
import asyncio
from typing import Any
from aiogram import Router, html, types, F
from config import config

from services.user_service import UserService



from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto

logger = logging.getLogger("kabinet_router")
router = Router()





# 3️⃣ 🖥 SHAXSIY KABINET TUGMASI BOSILGANDA
@router.callback_query(F.data == "open_cabinet")
async def open_cabinet_handler(callback: CallbackQuery, user_service: UserService):
    user_id = callback.from_user.id
    
    # Yuklanish belgisini ko'rsatamiz
    await callback.answer("⏳ Kabinet yuklanmoqda...")
    
    # 🌐 Haqiqiy Node.js Backend URL (Render yoki ishlab turgan server manzili bo'lishi shart)
    # Mahalliy localhost:3000 Render serverida ishlamaydi! 
    # Eng yaxshisi config.BACKEND_URL orqali ulash
    BACKEND_URL = getattr(config, "BACKEND_URL", "https://sizning-backend-loyiha.onrender.com") + "/api/auth/bot/generate-password"
    
    password = None
    
    # Backend bilan xavfsiz bog'lanish (Timeout bilan)
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(4.0):  # 4 soniyadan ko'p kuttirmaymiz
                payload = {"userId": user_id}
                async with session.post(BACKEND_URL, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        password = result.get("password")
                    else:
                        logger.warning(f"⚠️ Backend noto'g'ri status qaytardi: {response.status}")
    except Exception as api_error:
        # Xatoni faqat logga yozamiz, foydalanuvchiga ko'rsatmaymiz
        logger.error(f"❌ Backend API bilan ulanishda xatolik: {api_error}")
        password = None

    # 🟢 Agar backend parolni bermasa (API o'chiq bo'lsa yoki xato bersa) foydalanuvchiga chiroyli xabar beramiz
    if not password:
        await callback.message.answer(
            "❌ Kechirasiz, ayni vaqtda shaxsiy kabinet tizimi vaqtincha ishlamayapti.\n"
            "Texnik ishlar olib borilayotgan bo'lishi mumkin. Birozdan so'ng qayta urinib ko'ring."
        )
        return

    # 🔥 Backend parolni yaratgach, bot keshini (L1 va L2) sinxronizatsiya qilamiz
    try:
        await user_service.sync_web_password(user_id)
    except Exception as sync_err:
        logger.error(f"❌ Keshni sinxronlashda xatolik: {sync_err}")

    # Foydalanuvchiga premium, toza interfeysda ma'lumotlarini taqdim etamiz
    cabinet_text = (
        f"🖥 {html.bold('SHAXSIY KABINET')}\n\n"
        f"Aninov.uz saytiga istalgan qurilmadan (telefon, kompyuter yoki televizor) "
        f"kirish uchun quyidagi shaxsiy ma'lumotlaringizdan foydalaning:\n\n"
        f"🆔 {html.bold('Telegram ID:')} <code>{user_id}</code>\n"
        f"🔑 {html.bold('Maxsus Parol:')} <code>{password}</code>\n\n"
        f"⚠️ {html.italic('Eslatma: Parol va ID raqamingizni nusxalash uchun ustiga bir marta bosing. ')}"
        f"{html.italic('Ushbu maxfiy parolni hech kimga bermang!')}"
    )

    cabinet_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_start")]
        ]
    )

    # Start menyuni media tahrirlash (Edit) orqali chiroyli kabinet oynasiga aylantiramiz
    try:
        await callback.message.edit_caption(
            caption=cabinet_text,
            reply_markup=cabinet_keyboard,
            parse_mode="HTML"
        )
    except Exception:
        # Agar rasm captionini tahrirlashda muammo bo'lsa, yangi xabar sifatida chiqaradi
        await callback.message.answer(
            text=cabinet_text,
            reply_markup=cabinet_keyboard,
            parse_mode="HTML"
        )
