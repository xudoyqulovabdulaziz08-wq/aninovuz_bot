from dotenv.main import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any
from aiogram import Router, html, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime
from services.channel_service import ChannelService




router = Router()




def get_channels_keyboard(channels: List[Dict[str, Any]], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    # Sahifa chegaralarini aniqlaymiz
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_channels = channels[start_idx:end_idx]
    
    keyboard = []
    
    # Har bir kanal uchun inline tugma (bosganda kanal info ochiladi)
    for ch in page_channels:
        # Agar kanal faol bo'lsa yashil, o'chiq bo'lsa qizil emoji bilan ajratamiz
        status_emoji = "🟢" if ch.get("is_active") else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {ch.get('title')}", 
                callback_data=f"chaninfo:{ch.get('channel_id')}:{page}"
            )
        ])
        
    # Navigatsiya (Paginatsiya) tugmalari qatori
    nav_row = []
    total_pages = (len(channels) + per_page - 1) // per_page if channels else 1
    
    # Oldingi sahifa tugmasi
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"chanpage:{page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="❌", callback_data="noop")) # Bo'sh tugma
        
    # Joriy sahifa holati
    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    
    # Keyingi sahifa tugmasi
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"chanpage:{page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="❌", callback_data="noop"))
        
    keyboard.append(nav_row)
    
    # Orqaga qaytish bosh tugmasi (style="danger" o'z o'rnida)
    keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_channel_menu", style="danger")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)









@router.callback_query(F.data == "list_channel")
@router.callback_query(F.data.startswith("chanpage:"))
async def list_channels(callback: CallbackQuery, session: Any):
    await callback.answer()
    
    # Sahifa raqamini aniqlaymiz (agar list_channel bo'lsa 1-sahifa)
    page = 1
    if callback.data.startswith("chanpage:"):
        page = int(callback.data.split(":")[-1])
        
    service = ChannelService(session=session)
    all_channels = await service.get_all_channels()
    
    # Faol kanallar sonini filtrlab hisoblaymiz
    active_count = sum(1 for ch in all_channels if ch.get("is_active"))
    total_count = len(all_channels)
    
    text = (
        f"📊 {html.bold('Kanallar statistikasi va ro‘yxati')}\n\n"
        f"📌 {html.bold('Barcha kanallar soni:')} {total_count} ta\n"
        f"✅ {html.bold('Faol kanallar soni:')} {active_count} ta\n\n"
        f"👇 {html.underline('Batafsil ma’lumot olish uchun kanal ustiga bosing:')}"
    )
    
    kb = get_channels_keyboard(all_channels, page=page)
    
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass


# Hech qanday amal bajarmaydigan bo'sh tugma uchun handler (Paginatsiya chiroyli turishi uchun)
@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()





@router.callback_query(F.data.startswith("chaninfo:"))
async def show_channel_info(callback: CallbackQuery, session: Any):
    await callback.answer()
    
    # Callback ma'lumotlarini ajratib olamiz
    try:
        _, channel_id_str, page_str = callback.data.split(":")
        channel_id = int(channel_id_str)
        page = int(page_str)
    except ValueError:
        logger.error(f"❌ Callback data formatida xatolik: {callback.data}")
        return
    
    service = ChannelService(session=session)
    channel = await service.get_channel(channel_id)
    
    if not channel:
        try:
            await callback.message.edit_text(
                text="❌ Kanal ma'lumotlari topilmadi yoki u allaqachon o‘chirilgan.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Ro‘yxatga qaytish", callback_data=f"chanpage:{page}")]
                ])
            )
        except TelegramBadRequest:
            pass
        return
        
    status_text = "🟢 Faol (Majburiy obuna tekshirilmoqda)" if channel.get("is_active") else "🔴 O‘chiq (Tekshirilmayapti)"
    
    # created_at xavfsiz formatlash (Slicing xatosini oldini olish)
    created_val = channel.get('created_at')
    if isinstance(created_val, str):
        formatted_date = created_val[:19].replace("T", " ")
    elif isinstance(created_val, datetime):
        formatted_date = created_val.strftime("%Y-%m-%d %H:%M:%S")
    else:
        formatted_date = "Noma'lum"
    
    text = (
        f"ℹ️ {html.bold('Kanal haqida batafsil ma’lumot')}\n\n"
        f"📣 {html.bold('Kanal nomi:')} {channel.get('title')}\n"
        f"🆔 {html.bold('Kanal ID:')} {html.code(channel.get('channel_id'))}\n"
        f"🔗 {html.bold('Havola (URL):')} {channel.get('url') if channel.get('url') else 'Yo‘q'}\n"
        f"⚙️ {html.bold('Holati:')} {status_text}\n"
        f"📅 {html.bold('Qo‘shilgan vaqti:')} {formatted_date}\n"
    )
    
    # Aynan shu kanalni boshqarish (O'chirish yoki Statusini o'zgartirish) tugmalari qo'shildi
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Holatni o‘zgartirish", callback_data=f"chantoggle:{channel_id}:{page}"),
                InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"chandel:{channel_id}:{page}", style="danger")
            ],
            [InlineKeyboardButton(text="⬅️ Ro‘yxatga qaytish", callback_data=f"chanpage:{page}")]
        ]
    )
    
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"❌ chaninfo ko'rsatishda xatolik: {e}")

            