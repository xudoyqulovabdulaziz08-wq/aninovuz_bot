from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.anime_service import AnimeService

router = Router()

# FSM States guruhini shakllantiramiz
class TempDubberStates(StatesGroup):
    waiting_dubbers = State()  # Dubberlar matnini kutish
    confirm_save = State()     # Tasdiqlash oynasi


# ================= 1. /dubber BUYRUG‘I ORQALI BOSHLASH =================
@router.message(Command("dubber", "dublyajchi"))
async def start_quick_dubbers(message: Message, state: FSMContext):
    await state.set_state(TempDubberStates.waiting_dubbers)
    
    text = (
        f"🎙 {html.bold('Vaqtinchalik tezkor dubber qo‘shish bo‘limi')}\n\n"
        f"Iltimos, bazaga qo‘shmoqchi bo‘lgan dubberlarni (ovoz beruvchilarni) {html.underline('vergul')} orqali ajratib yuboring.\n\n"
        f"📌 Masalan: {html.code('Amonov, Shaxzod, Anvar, Real_Dubber')}"
    )
    
    await message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_dubber_add")]
        ]),
        parse_mode="HTML"
    )


# ================= 2. TEXT QABUL QILISH VA FORMATLASH =================
@router.message(TempDubberStates.waiting_dubbers, F.text)
async def process_raw_dubbers(message: Message, state: FSMContext):
    raw_text = message.text
    
    # Vergul bilan ajratib, bo'sh joylarni kesamiz va tozalaymiz
    dubbers_list = [d.strip() for d in raw_text.split(",") if d.strip()]
    
    if not dubbers_list:
        await message.answer("❌ Hech qanday ism aniqlanmadi. Qayta to‘g‘ri formatda yuboring!")
        return
        
    # Takrorlangan ismlarni (set orqali) bitta qilib tozalaymiz
    dubbers_list = list(set(dubbers_list))
    
    await state.update_data(parsed_dubbers=dubbers_list)
    await state.set_state(TempDubberStates.confirm_save)
    
    # Vizual ko'rinish
    preview_dubbers = "\n".join([f"🎙 {d}" for d in dubbers_list])
    
    text = (
        f"📝 {html.bold('Quyidagi dubberlar bazaga saqlashga tayyorlandi:')}\n\n"
        f"{preview_dubbers}\n\n"
        f"👇 Tasdiqlash uchun quyidagi tugmani bosing:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Bazaga saqlash", callback_data="db_save_quick_dubbers")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_dubber_add")
        ]
    ])
    
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML")


# ================= 3. YAKUNIY BAZAGA SAQLASH (SERVICE ORQALI) =================
@router.callback_query(TempDubberStates.confirm_save, F.data == "db_save_quick_dubbers")
async def save_dubbers_to_db(callback: CallbackQuery, state: FSMContext, anime_service: AnimeService):
    data = await state.get_data()
    dubbers_list: list[str] = data.get("parsed_dubbers", [])
    await state.clear()
    
    # Yuklanish effektini beramiz
    await callback.answer("⏳ Bazaga yozilmoqda...")
    
    try:
        # Service'ga yuklaymiz. U tranzaksiya va keshni o'zi boshqaradi
        added_count, skipped_dubbers = await anime_service.add_quick_dubbers(dubbers_list)
        
        result_text = f"✅ {html.bold('Dubberlar muvaffaqiyatli yakunlandi!')}\n\n"
        result_text += f"➕ {html.bold('Yangi qo‘shilganlar:')} {added_count} ta\n"
        
        if skipped_dubbers:
            result_text += f"⚠️ {html.bold('Bazada allaqachon bor bo‘lganlar (tashlab ketildi):')}\n"
            result_text += f"{html.code(', '.join(skipped_dubbers))}\n"
            
        result_text += f"\n💡 Endi anime yuklash jarayonida ushbu dubberlarni tanlashingiz mumkin."
        
        await callback.message.edit_text(text=result_text, reply_markup=None, parse_mode="HTML")
        
    except Exception as e:
        await callback.message.edit_text(
            text=f"❌ Dubberlarni saqlashda xatolik yuz berdi: {html.code(str(e))}",
            reply_markup=None,
            parse_mode="HTML"
        )


# ================= BEKOR QILISH =================
@router.callback_query(F.data == "cancel_dubber_add")
async def cancel_dubber(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Amal bekor qilindi", show_alert=True)
    await callback.message.edit_text("❌ Dubber qo‘shish jarayoni bekor qilindi.")