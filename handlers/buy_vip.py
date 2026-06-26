from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
import logging

from services.user_service import UserService
router = Router()
logger = logging.getLogger("UserVipMenu")

@router.callback_query(F.data == "buy_vip")
async def buy_vip_menu(callback: CallbackQuery, user_service: UserService):
    await callback.answer()
    
    vip_image_file_id = "AgACAgIAAxkBAAI8tmo2zpXedWfk2pHIT5yhD3bo3ksoAAKFGWsbZ6WxSZsBcZaddInXAQADAgADdwADPAQ"
    
    # 💎 1. Kesh-first orqali foydalanuvchi ma'lumotlarini olamiz va VIP muddatini tekshiramiz
    user_data = await user_service.get_user(callback.from_user.id)
    user_data = user_service._ensure_fresh_vip_status(user_data)
    
    is_vip = user_data.get("is_vip", False)
    vip_expire = user_data.get("vip_expire_date") # ISO string formatda keladi
    
    # 📝 2. Umumiy imtiyozlar matni (Har ikkala status uchun ham ko'rinadi)
    benefits_text = (
        "👑 <b>VIP IMTIYOZLAR:</b>\n"
        "━ 🎬 Premyeralarni hammadan birinchi ko'rish\n"
        "━ 🚀 Yuqori tezlikda cheklovsiz yuklab olish\n"
        "━ 🚫 Mutlaqo reklamasiz botdan foydalanish\n"
        "━ 🎧 Eksklyuziv funksiyalardan foydalanish\n\n"
    )
    
    # 🎰 3. Statusga qarab dinamik matn va klaviaturani shakllantiramiz
    inline_keyboard = []
    
    if is_vip:
        # Sanani chiroyli formatga keltiramiz
        expire_str = "Noma'lum"
        if vip_expire:
            try:
                expire_dt = datetime.fromisoformat(vip_expire)
                expire_str = expire_dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                expire_str = str(vip_expire)
                
        text = (
            "╔═════════ 💎 ═════════╗\n"
            "   <b>VIP STATUSINGIZ FAOL</b>\n"
            "╚═════════ 💎 ═════════╝\n\n"
            f"👤 Status: <code>💎 VIP Obunachi</code>\n"
            f"⏰ Amal qilish muddati: <b>{expire_str}</b> gacha\n\n"
            f"{benefits_text}"
            "✨ <i>Obunangizni muddatidan oldin uzaytirishingiz ham mumkin:</i>"
        )
        # VIP foydalanuvchilar uchun uzaytirish tugmasi
        inline_keyboard.append([InlineKeyboardButton(text="🔄 VIP Obunani uzaytirish", callback_data="renew_vip")])
    else:
        text = (
            "╔═════════ 💎 ═════════╗\n"
            "    <b>VIP OBUNA BO'LISH</b>\n"
            "╚═════════ 💎 ═════════╝\n\n"
            f"👤 Status: <code>👤 Oddiy foydalanuvchi</code>\n\n"
            f"{benefits_text}"
            "💵 <i>VIP obuna narxi: 1 oy uchun 15,000 so'm.</i>\n\n"
            "⚠️ Sizda VIP status faol emas. Obuna bo'lishni xohlaysizmi?"
        )
        # Oddiy foydalanuvchilar uchun sotib olish tugmasi
        inline_keyboard.append([InlineKeyboardButton(text="💳 VIP Sotib olish", callback_data="purchase_vip")])
        
    # ⬅️ Har doim eng tagida turadigan ORQAGA tugmasi
    inline_keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_start")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    
    # 📸 4. Mediani va matnni bitta oynada silliq edit qilamiz
    try:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=vip_image_file_id,
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"❌ Kutilmagan BadRequest xatoligi: {e}")
    except Exception as e:
        logger.error(f"❌ Umumiy xatolik: {e}")