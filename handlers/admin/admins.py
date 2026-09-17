from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import database as db
from config import OWNER_ID
from states import AdminAdd, AdminRemove
from utils.filters import IsOwner
from keyboards.reply.admins import get_admins_menu, BTN_ADD_ADMIN, BTN_REMOVE_ADMIN, BTN_ADMIN_LIST

router = Router()
# MUHIM: bu butun router FAQAT owner (bosh admin) uchun ishlaydi. Oddiy adminlar
# uchun "👮 Adminlar" tugmasi umuman ko'rsatilmaydi (get_admin_menu is_owner=False
# bo'lsa tugmani yashiradi), lekin backend darajasida ham himoya qilingan - kimdir
# tugma matnini qo'lda yuborsa ham, IsOwner filtri uni rad etadi.
router.message.filter(IsOwner())

CANCEL_TEXT = "❌ Bekor qilish"
CONFIRM_REMOVE_TEXT = "✅ Ha, chiqarish"


def cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


def confirm_remove_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CONFIRM_REMOVE_TEXT))
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


async def admins_entry(message: Message, state: FSMContext):
    """handlers/admin/panel.py dagi '👮 Adminlar' tugmasi shu funksiyani chaqiradi."""
    await message.answer("👮 Adminlar bo'limi", reply_markup=get_admins_menu())


async def format_admins_list() -> str:
    admins = await db.get_admins()
    if not admins:
        return "👮 Hozircha adminlar mavjud emas."

    lines = ["👮 <b>Adminlar ro'yxati</b>\n"]
    for admin in admins:
        user = await db.get_user(admin["telegram_id"])
        name = user["full_name"] if user else "—"
        username = f"@{user['username']}" if user and user["username"] else "—"
        role = "👑 Bosh admin (Owner)" if admin["is_owner"] == 1 else "👮 Admin"
        lines.append(
            f"{role}\n"
            f"🆔 <code>{admin['telegram_id']}</code>\n"
            f"👤 {name} ({username})\n"
            f"📅 Qo'shilgan: {admin['added_at']}\n"
        )
    return "\n".join(lines)


@router.message(F.text == BTN_ADMIN_LIST)
async def admin_list_open(message: Message):
    text = await format_admins_list()
    await message.answer(text)


# ==================== ADMIN QO'SHISH (FSM) ====================

@router.message(F.text == BTN_ADD_ADMIN)
async def admin_add_start(message: Message, state: FSMContext):
    await state.set_state(AdminAdd.waiting_id)
    await message.answer(
        "🆔 Yangi admin qilib tayinlamoqchi bo'lgan foydalanuvchining Telegram ID "
        "raqamini yuboring.\n\n"
        "Eslatma: bu ID'ni bilish uchun o'sha foydalanuvchi botga /start bosgan "
        "bo'lishi kerak, yoki @userinfobot orqali bilib olishingiz mumkin.",
        reply_markup=cancel_keyboard()
    )


@router.message(AdminAdd.waiting_id, F.text == CANCEL_TEXT)
async def admin_add_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_admins_menu())


@router.message(AdminAdd.waiting_id)
async def admin_add_process(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ ID faqat raqamlardan iborat bo'lishi kerak. Qaytadan yuboring:")
        return

    new_admin_id = int(text)
    await state.clear()

    if await db.is_admin(new_admin_id):
        await message.answer("⚠️ Bu foydalanuvchi allaqachon admin.", reply_markup=get_admins_menu())
        return

    ok = await db.add_admin(telegram_id=new_admin_id, added_by=message.from_user.id, is_owner=False)
    if ok:
        await db.add_log(message.from_user.id, "Yangi admin qo'shildi", str(new_admin_id))
        await message.answer(
            f"✅ <code>{new_admin_id}</code> ID'li foydalanuvchi admin etib tayinlandi.",
            reply_markup=get_admins_menu()
        )
    else:
        await message.answer("⚠️ Xatolik yuz berdi, qaytadan urinib ko'ring.", reply_markup=get_admins_menu())


# ==================== ADMIN CHIQARISH (FSM) ====================

@router.message(F.text == BTN_REMOVE_ADMIN)
async def admin_remove_start(message: Message, state: FSMContext):
    await state.set_state(AdminRemove.waiting_id)
    await message.answer(
        "🆔 Chiqarmoqchi bo'lgan adminning Telegram ID raqamini yuboring:",
        reply_markup=cancel_keyboard()
    )


@router.message(AdminRemove.waiting_id, F.text == CANCEL_TEXT)
@router.message(AdminRemove.confirm, F.text == CANCEL_TEXT)
async def admin_remove_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_admins_menu())


@router.message(AdminRemove.waiting_id)
async def admin_remove_process(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ ID faqat raqamlardan iborat bo'lishi kerak. Qaytadan yuboring:")
        return

    target_id = int(text)

    if target_id == OWNER_ID or await db.is_owner(target_id):
        await message.answer(
            "⚠️ Bosh adminni (owner) chiqarib bo'lmaydi.", reply_markup=get_admins_menu()
        )
        await state.clear()
        return

    if not await db.is_admin(target_id):
        await message.answer("⚠️ Bu foydalanuvchi admin emas.", reply_markup=get_admins_menu())
        await state.clear()
        return

    await state.update_data(target_id=target_id)
    await state.set_state(AdminRemove.confirm)
    await message.answer(
        f"❗️ <code>{target_id}</code> ID'li adminni chiqarishga ishonchingiz komilmi?",
        reply_markup=confirm_remove_keyboard()
    )


@router.message(AdminRemove.confirm, F.text == CONFIRM_REMOVE_TEXT)
async def admin_remove_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data["target_id"]
    await state.clear()

    ok = await db.remove_admin(target_id)
    if ok:
        await db.add_log(message.from_user.id, "Admin chiqarildi", str(target_id))
        await message.answer(f"🗑 <code>{target_id}</code> ID'li admin chiqarildi.", reply_markup=get_admins_menu())
    else:
        await message.answer(
            "⚠️ Chiqarib bo'lmadi (owner bo'lishi yoki admin topilmasligi mumkin).",
            reply_markup=get_admins_menu()
        )