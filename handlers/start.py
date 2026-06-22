import logging
from aiogram import Router, html, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from services.user_service import UserService
from config import config
from aiogram.fsm.context import FSMContext

logger = logging.getLogger("StartRouter")
CREATOR_ID = config.CREATOR_ID
router = Router()


# 🎯 UNIVERSAL START INTERFEYSI (Ham yangi yuborish, ham edit qilish uchun)
async def send_or_edit_start_menu(target: Message | CallbackQuery, user_id: int, username: str):
    """
    Ushbu funksiya target turi Message bo'lsa yangi xabar yuboradi,
    CallbackQuery bo'lsa mavjud xabarni media edit (tahrirlash) qiladi.
    """
    start_image_file_id = "AgACAgIAAxkBAAI8Vmo2h33mXWFJrVt2WytylhrKnSRKAAJHGGsbZ6WxSVOJWvc1e0TUAQADAgADdwADPAQ" 
    
    welcome_text = (
        f"👋 Xush kelibsiz, {html.bold(username)}!\n\n"
        f"🎬 {html.bold('AniNovuz')} — siz qidirgan eng sara, sifatli va sevimli animelar makoniga qadam qo‘ydingiz.\n\n"
        f"⚡️ Quyidagi menyudan foydalanib, darhol tomosha qilishni boshlashingiz mumkin:"
    )
    
    start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Qidiruv bo'limi", callback_data="search_menu", style="primary")],
            [
                InlineKeyboardButton(text="Reklama berish 📢", callback_data="advertise", style="primary"),
                InlineKeyboardButton(text="Qo'llanma 📖", callback_data="guide", style="primary")
            ],
            [InlineKeyboardButton(text="VIP olish 💎", callback_data="buy_vip", style="success")],
            [InlineKeyboardButton(text="💬 Yordam", callback_data="support", style="danger")]
        ]
    )

    # Agar foydalanuvchi inline tugmani bosgan bo'lsa (CallbackQuery) - EDIT qilamiz
    if isinstance(target, CallbackQuery):
        await target.message.edit_media(
            media=InputMediaPhoto(
                media=start_image_file_id,
                caption=welcome_text,
                parse_mode="HTML"
            ),
            reply_markup=start_keyboard
        )
        await target.answer() # Telegram yuklanish belgisini olib tashlash uchun
        
    # Agar foydalanuvchi /start deb yozgan bo'lsa (Message) - YANGI xabar yuboramiz
    elif isinstance(target, Message):
        try:
            await target.delete() # Foydalanuvchi yozgan /start matnini o'chirish
        except:
            pass
            
        await target.answer_photo(
            photo=start_image_file_id,
            caption=welcome_text,
            reply_markup=start_keyboard,
            parse_mode="HTML"
        )


# 1️⃣ /start BUYRUG'I KELGANDA (Deep-Linking qo'llab-quvvatlaydi)
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, session: Any, user: dict, user_service: UserService, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or "do'stim"
    user_status = user.get('status', 'user').lower()
    
    # 🚀 KANAL TUGMASIDAN PARAMETR KELGANDA (Masalan: /start anime_15,)
    if command.args:
        clean_args = command.args.strip().rstrip(",") # Vergul yoki bo'shliqlarni tozalaymiz
        if clean_args.startswith("anime_"):
            try:
                anime_id = int(clean_args.split("_")[1])
                
                from services.anime_service import AnimeService
                service = AnimeService(session=session)
                anime = await service.get_anime(anime_id)
                
                if anime:
                    title = anime.get("title", "Nomsiz anime")
                    year = anime.get("year", "—")
                    description = anime.get("description") or "Tavsif kiritilmagan."
                    episodes_count = len(anime.get("episodes", []))
                    languages = anime.get("languages", [])
                    languages_str = ", ".join(languages) if languages else "Mavjud emas"
                    
                    # Janrlarni bazadan professional yuklash mantiqi
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
                    except Exception as genre_err:
                        logger.error(f"❌ Janrlarni yuklashda xato: {genre_err}")

                    # Daxshat ramkali professional UX dizayn (Foydalanuvchi ko'rinishi)
                    caption = (
                        f"╔══════════════════╗\n"
                        f"     🎬 <b>{title}</b>\n"
                        f"╚══════════════════╝\n\n"
                        f"📌 <b>Anime haqida ma'lumot:</b>\n"
                        f"╔══════════════════╗\n"
                        f"├ 🆔 Kod: <code>#{anime.get('anime_id', anime_id)}</code>\n"  
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

                    # Foydalanuvchilar uchun qismlarni ko'rish tugmasi (Admindan farqli o'laroq)
                    user_anime_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📹 Qismlarni tomosha qilish", callback_data=f"show_episodes_user:{anime_id}", style="primary")],
                        [InlineKeyboardButton(text="⬅️ Bosh menyuga qaytish", callback_data="back_to_start", style="danger")]
                    ])

                    try:
                        await message.delete()
                    except:
                        pass

                    poster_id = anime.get("poster_id")
                    if poster_id:
                        try:
                            await message.answer_photo(photo=poster_id, caption=caption, reply_markup=user_anime_kb, parse_mode="HTML")
                        except Exception:
                            try:
                                await message.answer_video(video=poster_id, caption=caption, reply_markup=user_anime_kb, parse_mode="HTML")
                            except Exception:
                                await message.answer(text=caption, reply_markup=user_anime_kb, parse_mode="HTML")
                    else:
                        await message.answer(text=caption, reply_markup=user_anime_kb, parse_mode="HTML")
                    
                    return # Jarayon yakunlandi, umumiy start menyusi chiqmaydi.
            except Exception as ex:
                logger.error(f"❌ Deep link ishlashida xatolik: {ex}")

    # Agarda oddiy start bo'lsa, asosiy menyuni yangi xabar sifatida yuboramiz
    await send_or_edit_start_menu(message, user_id, username)

    # Admin/Creator panellari
    if user_id == CREATOR_ID:
        creator_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚙️ Creator Paneli"), KeyboardButton(text="🛠 Admin Paneli")]],
            resize_keyboard=True
        )
        await message.answer("👑 Tizim asoschisi! Barcha boshqaruv panellari faollashtirildi:", reply_markup=creator_keyboard)
        
    elif user_status == 'admin':
        admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🛠 Admin Paneli")]],
            resize_keyboard=True
        )
        await message.answer("🛡 Tizim administratori tan olindi. Admin boshqaruv paneli faollashtirildi:", reply_markup=admin_keyboard)


# 2️⃣ ORQAGA TUGMASI BOSILGANDA
@router.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "do'stim"
    await send_or_edit_start_menu(callback, user_id, username)


# 3️⃣ 🔄 OBUNANI TASDIQLASH TUGMASI BOSILGANDA (Middleware muvaffaqiyatli o'tkazgandan keyingi qadam)
@router.callback_query(F.data.startswith("check_sub"))
async def check_sub_callback_handler(callback: CallbackQuery, session: Any):
    await callback.answer("🎉 Rahmat, obuna muvaffaqiyatli tasdiqlandi!", show_alert=True)
    user_id = callback.from_user.id
    username = callback.from_user.username or "do'stim"
    
    # Eskidan qolib ketgan majburiy obuna blok-xabarini butunlay o'chirib tashlaymiz
    try:
        await callback.message.delete()
    except:
        pass

    # Obunani tekshirish tugmasidan keyin toza bosh menyuni chiqarib beramiz
    await send_or_edit_start_menu(callback.message, user_id, username)