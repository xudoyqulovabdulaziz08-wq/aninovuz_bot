import asyncio
import logging
from typing import Any, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database.cache import valkey
from services.channel_service import ChannelService
logger = logging.getLogger("CheckSubscriptionMiddleware")

class CheckSubscriptionMiddleware(BaseMiddleware):
    
    async def __call__(self, handler: Any, event: Any, data: Dict[str, Any]) -> Any:
        # 1. Faqat xabarlar va callback query so'rovlarini tekshiramiz
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        # 2. 🚀 VIP, Admin va System so'rovlari uchun Bypass (Tekshirmay o'tkazish)
        user_data = data.get("user", {})
        if user_data.get("is_system") or user_data.get("is_vip") or user_data.get("status") in ["admin", "owner"]:
            return await handler(event, data)

        user_id = data["event_from_user"].id
        bot = data["bot"]
        
        is_callback = isinstance(event, CallbackQuery)
        # Foydalanuvchi aynan tasdiqlash tugmasini bosgandagina real-time tekshirishga majburlaymiz
        force_check = is_callback and event.data and event.data.startswith("check_sub")

        # 3. 🚀 RATE LIMIT HIMOYASI (Kesh vaqtini 15 daqiqadan 45 soniyaga tushiramiz!)
        if not force_check and valkey.is_alive:
            try:
                is_subbed = await valkey.get(table="sub_status", obj_id=str(user_id))
                if is_subbed == "ok":
                    # 🔥 Kesh hali eskirgani yo'q va foydalanuvchi o'tkazib yuboriladi
                    return await handler(event, data)
            except Exception as e:
                logger.debug(f"Sub cache get error: {e}")

        # 4. DbSessionMiddleware taqdim etgan xavfsiz proxy sessiyani olish
        session = data.get("session")
        if not session:
            logger.warning("⚠️ DbSessionMiddleware sessiyasi topilmadi, tekshiruv o'tkazib yuborildi.")
            return await handler(event, data)

        # 5. Service qatlamini yaratamiz va kesh-aware funksiyani chaqiramiz
        try:
            channel_service = ChannelService(session=session)
            channels = await channel_service.get_active_channels()
        except Exception as e:
            logger.error(f"🚨 Middleware kanallarni olishda xato: {e}")
            return await handler(event, data)

        # Majburiy kanallar bazada yo'q bo'lsa, erkin o'tkazamiz
        if not channels:
            return await handler(event, data)

        # 6. Telegram API orqali parallel obunani tekshirish
        async def check_single(ch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            try:
                chat_id = int(ch["channel_id"])
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    return ch
            except Exception as api_err:
                logger.debug(f"⚠️ Telegram API xatosi (Kanal ID: {ch.get('channel_id')}): {api_err}")
                return None
            return None

        results = await asyncio.gather(*(check_single(ch) for ch in channels))
        not_subscribed = [r for r in results if r is not None]

        # ======================================================
        # 🛑 Middleware ichidagi blok: Agar obuna bo'lmagan bo'lsa:
        # ======================================================
        if not_subscribed:
            cb_data = "check_sub"
            if isinstance(event, Message) and event.text and "anime_" in event.text:
                try:
                    clean_param = event.text.split(" ")[1].replace(",", "")
                    cb_data = f"check_sub:{clean_param}"
                except IndexError:
                    pass

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch['url'])] for ch in not_subscribed
            ] + [[InlineKeyboardButton(text="🔄 Obunani tasdiqlash", callback_data=cb_data)]])
            
            text = "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi homiy kanallarga a'zo bo'ling:</b>"
            
            # 🛡️ Agar foydalanuvchi kanaldan chiqib ketgan bo'lsa va bot ichida tasdiqlash tugmasidan boshqa
            # har qanday callback (pleer, menyu va h.k.) ni bossa, uning keshini tozalab, pultni majburiy obunaga almashtiramiz!
            if isinstance(event, Message):
                await event.answer(text=text, reply_markup=kb, parse_mode="HTML")
            elif is_callback:
                if force_check:
                    # Agar tasdiqlash tugmasini bosgan bo'lsa-yu hali a'zo bo'lmagan bo'lsa Alert beramiz
                    await event.answer("⚠️ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
                else:
                    # Agar boshqa tugmani bosgan paytda chiqib ketgani aniqlansa
                    await event.answer("🚨 Siz homiy kanaldan chiqib ketgansiz! Obuna qayta tekshirildi.", show_alert=True)
                
                try:
                    await event.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
                except TelegramBadRequest as e:
                    if "message is not modified" not in str(e):
                        try:
                            await event.message.delete()
                        except:
                            pass
                        await event.message.answer(text=text, reply_markup=kb, parse_mode="HTML")
            
            # Foydalanuvchi kanaldan chiqib ketgani aniq bo'ldimi, keshni majburiy o'chiramiz!
            if valkey.is_alive:
                try:
                    await valkey.invalidate(table="sub_status", obj_id=str(user_id), broadcast=False)
                except Exception:
                    pass

            return  # 🛑 Oqim uziladi, foydalanuvchi o'tolmaydi.

        # ======================================================
        # 🟢 Agarda foydalanuvchi HAMMA kanalga obuna bo'lgan bo'lsa:
        # ======================================================
        if valkey.is_alive:
            try:
                # 🔥 TTL 900 (15 daqiqa) dan 45 soniyaga tushirildi!
                # Foydalanuvchi kanaldan chiqsa, ko'pi bilan 45 soniya botni ishlata oladi xolos!
                await valkey.set(table="sub_status", obj_id=str(user_id), data="ok", ttl=45)
            except Exception as e:
                logger.debug(f"Sub cache set error: {e}")

        return await handler(event, data)