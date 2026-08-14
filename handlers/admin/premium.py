import math

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import database as db
from states import PremiumPlanAdd, PremiumPlanEdit, PremiumCard
from utils.filters import IsAdmin
from keyboards.reply.premium import (
    get_premium_menu, BTN_CARD_SETTINGS, BTN_PLANS, BTN_PREMIUM_USERS
)
from keyboards.inline.premium import (
    premium_card_settings_keyboard, premium_plans_admin_keyboard, premium_plan_detail_keyboard,
    premium_plan_delete_confirm_keyboard, premium_users_pagination_keyboard, EDITABLE_PLAN_FIELDS
)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

CANCEL_TEXT = "❌ Bekor qilish"
CONFIRM_TEXT = "✅ Saqlash"
PREMIUM_USERS_PER_PAGE = 10


def cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


def confirm_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CONFIRM_TEXT))
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


async def premium_entry(message: Message, state: FSMContext):
    """handlers/admin/panel.py dagi '💎 Premium' tugmasi shu funksiyani chaqiradi."""
    await message.answer("💎 Premium bo'limi", reply_markup=get_premium_menu())


def format_plan_detail(plan) -> str:
    return (
        f"💎 <b>{plan['name']}</b>\n\n"
        f"⏳ Davomiyligi: {plan['duration_days']} kun\n"
        f"💰 Narxi: {plan['price']} so'm\n"
        f"📊 Holati: {'✅ Aktiv' if plan['status'] == 'active' else '🚫 Deaktiv'}"
    )


# ==================== KARTA SOZLAMALARI ====================

@router.message(F.text == BTN_CARD_SETTINGS)
async def card_settings_open(message: Message):
    card_number = await db.get_premium_setting("card_number", "— hali kiritilmagan —")
    card_holder = await db.get_premium_setting("card_holder", "— hali kiritilmagan —")
    text = (
        "💳 <b>Karta sozlamalari</b>\n\n"
        f"💳 Karta raqami:\n{card_number}\n\n"
        f"👤 Karta egasi:\n{card_holder}"
    )
    await message.answer(text, reply_markup=premium_card_settings_keyboard())


@router.callback_query(F.data == "premium_card_number")
async def card_number_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PremiumCard.waiting_number)
    await callback.answer()
    await callback.message.answer("💳 Yangi karta raqamini yuboring:", reply_markup=cancel_keyboard())


@router.callback_query(F.data == "premium_card_holder")
async def card_holder_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PremiumCard.waiting_holder)
    await callback.answer()
    await callback.message.answer(
        "👤 Karta egasining ism-familyasini yuboring:", reply_markup=cancel_keyboard()
    )


@router.message(PremiumCard.waiting_number, F.text == CANCEL_TEXT)
@router.message(PremiumCard.waiting_holder, F.text == CANCEL_TEXT)
async def card_edit_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_premium_menu())


@router.message(PremiumCard.waiting_number)
async def card_number_save(message: Message, state: FSMContext):
    await db.set_premium_setting("card_number", message.text.strip())
    await db.add_log(message.from_user.id, "Premium karta raqami o'zgartirildi", "")
    await state.clear()
    await message.answer("✅ Karta raqami yangilandi.", reply_markup=get_premium_menu())


@router.message(PremiumCard.waiting_holder)
async def card_holder_save(message: Message, state: FSMContext):
    await db.set_premium_setting("card_holder", message.text.strip())
    await db.add_log(message.from_user.id, "Premium karta egasi o'zgartirildi", "")
    await state.clear()
    await message.answer("✅ Karta egasi yangilandi.", reply_markup=get_premium_menu())


# ==================== TARIFLAR RO'YXATI ====================

@router.message(F.text == BTN_PLANS)
async def plans_list_open(message: Message):
    plans = await db.get_all_plans()
    await message.answer("💰 Premium tariflar:", reply_markup=premium_plans_admin_keyboard(plans))


@router.callback_query(F.data == "premium_plans_back")
async def plans_back(callback: CallbackQuery):
    plans = await db.get_all_plans()
    await callback.answer()
    await callback.message.edit_text("💰 Premium tariflar:", reply_markup=premium_plans_admin_keyboard(plans))


@router.callback_query(F.data.startswith("premium_plan_open:"))
async def plan_open(callback: CallbackQuery):
    plan_id = int(callback.data.split(":")[1])
    plan = await db.get_plan_by_id(plan_id)
    await callback.answer()
    if not plan:
        await callback.message.answer("⚠️ Tarif topilmadi.")
        return
    await callback.message.edit_text(
        format_plan_detail(plan),
        reply_markup=premium_plan_detail_keyboard(plan_id, plan["status"] == "active")
    )


@router.callback_query(F.data.startswith("premium_plan_toggle:"))
async def plan_toggle(callback: CallbackQuery):
    plan_id = int(callback.data.split(":")[1])
    plan = await db.get_plan_by_id(plan_id)
    if not plan:
        await callback.answer("Tarif topilmadi.", show_alert=True)
        return
    new_status = "inactive" if plan["status"] == "active" else "active"
    await db.update_plan_field(plan_id, "status", new_status)
    await db.add_log(
        callback.from_user.id, "Premium tarif holati o'zgartirildi", f"plan_id={plan_id} status={new_status}"
    )
    await callback.answer("✅ Yangilandi.")
    plan = await db.get_plan_by_id(plan_id)
    await callback.message.edit_text(
        format_plan_detail(plan),
        reply_markup=premium_plan_detail_keyboard(plan_id, plan["status"] == "active")
    )


# ==================== TARIF QO'SHISH (FSM) ====================

@router.callback_query(F.data == "premium_plan_add")
async def plan_add_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PremiumPlanAdd.name)
    await callback.answer()
    await callback.message.answer(
        "📝 Yangi tarif nomini yuboring (masalan: 1 haftalik):", reply_markup=cancel_keyboard()
    )


@router.message(PremiumPlanAdd.name, F.text == CANCEL_TEXT)
@router.message(PremiumPlanAdd.duration_days, F.text == CANCEL_TEXT)
@router.message(PremiumPlanAdd.price, F.text == CANCEL_TEXT)
@router.message(PremiumPlanAdd.confirm, F.text == CANCEL_TEXT)
async def plan_add_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_premium_menu())


@router.message(PremiumPlanAdd.name)
async def plan_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(PremiumPlanAdd.duration_days)
    await message.answer("⏳ Davomiyligini KUN hisobida yuboring (masalan: 7):")


@router.message(PremiumPlanAdd.duration_days)
async def plan_add_duration(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Faqat son kiriting. Qaytadan yuboring:")
        return
    await state.update_data(duration_days=int(message.text.strip()))
    await state.set_state(PremiumPlanAdd.price)
    await message.answer("💰 Narxini SO'MDA yuboring (masalan: 6000):")


@router.message(PremiumPlanAdd.price)
async def plan_add_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Faqat son kiriting. Qaytadan yuboring:")
        return
    await state.update_data(price=int(message.text.strip()))
    data = await state.get_data()
    await state.set_state(PremiumPlanAdd.confirm)
    text = (
        "✅ Quyidagini tekshiring:\n\n"
        f"📝 Nomi: {data['name']}\n"
        f"⏳ Davomiyligi: {data['duration_days']} kun\n"
        f"💰 Narxi: {data['price']} so'm\n\n"
        "Saqlansinmi?"
    )
    await message.answer(text, reply_markup=confirm_keyboard())


@router.message(PremiumPlanAdd.confirm, F.text == CONFIRM_TEXT)
async def plan_add_save(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_plan(data["name"], data["duration_days"], data["price"])
    await db.add_log(message.from_user.id, "Premium tarif qo'shildi", data["name"])
    await state.clear()
    await message.answer("✅ Tarif muvaffaqiyatli qo'shildi!", reply_markup=get_premium_menu())


# ==================== TARIF TAHRIRLASH ====================

@router.callback_query(F.data.startswith("premium_plan_edit:"))
async def plan_edit_field_chosen(callback: CallbackQuery, state: FSMContext):
    _, plan_id, field = callback.data.split(":")
    await state.update_data(edit_plan_id=int(plan_id), edit_field=field)
    await state.set_state(PremiumPlanEdit.new_value)
    await callback.answer()
    field_labels = dict(EDITABLE_PLAN_FIELDS)
    label = field_labels.get(field, field)
    await callback.message.answer(f"✏️ \"{label}\" uchun yangi qiymatni yuboring:")


@router.message(PremiumPlanEdit.new_value)
async def plan_edit_receive_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["edit_field"]
    plan_id = data["edit_plan_id"]
    value = message.text.strip()

    if field in ("duration_days", "price"):
        if not value.isdigit():
            await message.answer("⚠️ Faqat son kiriting. Qaytadan yuboring:")
            return
        value = int(value)

    await db.update_plan_field(plan_id, field, value)
    await db.add_log(message.from_user.id, "Premium tarif tahrirlandi", f"plan_id={plan_id} field={field}")
    await state.clear()
    await message.answer("✅ Tarif yangilandi.", reply_markup=get_premium_menu())


# ==================== TARIF O'CHIRISH ====================

@router.callback_query(F.data.startswith("premium_plan_delete:"))
async def plan_delete_ask(callback: CallbackQuery):
    plan_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.answer(
        "❗️ Ushbu tarifni o'chirishga ishonchingiz komilmi?\n\n"
        "(Eslatma: bu tarifni sotib olgan foydalanuvchilarning to'lov tarixi va faol "
        "obunalari o'zgarmaydi, ular saqlanib qoladi.)",
        reply_markup=premium_plan_delete_confirm_keyboard(plan_id)
    )


@router.callback_query(F.data.startswith("premium_plan_delete_yes:"))
async def plan_delete_confirm_yes(callback: CallbackQuery):
    plan_id = int(callback.data.split(":")[1])
    plan = await db.get_plan_by_id(plan_id)
    await db.delete_plan(plan_id)
    await db.add_log(callback.from_user.id, "Premium tarif o'chirildi", plan["name"] if plan else str(plan_id))
    await callback.answer("🗑 O'chirildi.")
    await callback.message.delete()
    plans = await db.get_all_plans()
    await callback.message.answer("💰 Premium tariflar:", reply_markup=premium_plans_admin_keyboard(plans))


@router.callback_query(F.data.startswith("premium_plan_delete_no:"))
async def plan_delete_confirm_no(callback: CallbackQuery):
    await callback.answer("Bekor qilindi.")
    await callback.message.delete()


# ==================== PREMIUM FOYDALANUVCHILAR (pagination) ====================

async def _build_premium_users_text_and_kb(page: int):
    total = await db.get_premium_subscriptions_count()
    total_pages = max(math.ceil(total / PREMIUM_USERS_PER_PAGE), 1)
    page = max(1, min(page, total_pages))
    subs = await db.get_premium_subscriptions_paginated(page, PREMIUM_USERS_PER_PAGE)

    if not subs:
        return "👥 Hozircha Premium foydalanuvchilar mavjud emas.", None

    lines = [f"👥 Premium foydalanuvchilar ({page}/{total_pages}):\n"]
    for sub in subs:
        user = await db.get_user(sub["user_id"])
        is_active = db.is_subscription_currently_active(sub)
        status_text = "🟢 Active" if is_active else "🔴 Expired"
        full_name = user["full_name"] if user else "—"
        username = f"@{user['username']}" if user and user["username"] else "—"
        started = sub["started_at"].split(" ")[0]
        expires = sub["expires_at"].split(" ")[0]
        lines.append(
            f"👤 {full_name}\n"
            f"🆔 {sub['user_id']}\n"
            f"👤 {username}\n"
            f"💎 {sub['plan_name']}\n"
            f"💰 {sub['price']} so'm\n"
            f"📅 Boshlangan: {started}\n"
            f"📅 Tugaydi: {expires}\n"
            f"{status_text}\n"
        )
    text = "\n".join(lines)
    kb = premium_users_pagination_keyboard(page, total_pages)
    return text, kb


@router.message(F.text == BTN_PREMIUM_USERS)
async def premium_users_open(message: Message):
    text, kb = await _build_premium_users_text_and_kb(1)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("premium_users_page:"))
async def premium_users_page_callback(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    text, kb = await _build_premium_users_text_and_kb(page)
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "premium_users_noop")
async def premium_users_noop(callback: CallbackQuery):
    await callback.answer()


# ==================== TO'LOVNI TASDIQLASH / RAD ETISH ====================

@router.callback_query(F.data.startswith("premium_approve:"))
async def premium_approve(callback: CallbackQuery, bot: Bot):
    payment_id = int(callback.data.split(":")[1])
    payment = await db.get_payment_by_id(payment_id)
    await callback.answer()

    if not payment:
        await callback.message.answer("⚠️ To'lov topilmadi.")
        return
    if payment["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.approve_payment(payment_id, callback.from_user.id)
    await db.create_subscription(
        user_id=payment["user_id"],
        payment_id=payment["id"],
        plan_id=payment["plan_id"],
        plan_name=payment["plan_name_snapshot"],
        price=payment["price_snapshot"],
        duration_days=payment["duration_days_snapshot"]
    )
    await db.add_log(callback.from_user.id, "Premium to'lov tasdiqlandi", f"payment_id={payment_id}")

    subscription = await db.get_latest_subscription(payment["user_id"])
    expires_date = subscription["expires_at"].split(" ")[0] if subscription else "—"

    try:
        await bot.send_message(
            chat_id=payment["user_id"],
            text=(
                "✅ To'lovingiz qabul qilindi.\n\n"
                "💎 Premium obunangiz faollashtirildi.\n\n"
                f"⏳ Amal qilish muddati: {payment['duration_days_snapshot']} kun\n"
                f"📅 Tugash sanasi: {expires_date}"
            )
        )
    except Exception:
        pass

    old_caption = callback.message.caption or ""
    await callback.message.edit_caption(caption=old_caption + "\n\n✅ TASDIQLANDI", reply_markup=None)


@router.callback_query(F.data.startswith("premium_reject:"))
async def premium_reject(callback: CallbackQuery, bot: Bot):
    payment_id = int(callback.data.split(":")[1])
    payment = await db.get_payment_by_id(payment_id)
    await callback.answer()

    if not payment:
        await callback.message.answer("⚠️ To'lov topilmadi.")
        return
    if payment["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.reject_payment(payment_id, callback.from_user.id)
    await db.add_log(callback.from_user.id, "Premium to'lov rad etildi", f"payment_id={payment_id}")

    try:
        await bot.send_message(
            chat_id=payment["user_id"],
            text=(
                "❌ To'lovingiz rad etildi.\n\n"
                "Chek noto'g'ri yoki to'lov amalga oshmagan bo'lishi mumkin."
            )
        )
    except Exception:
        pass

    old_caption = callback.message.caption or ""
    await callback.message.edit_caption(caption=old_caption + "\n\n❌ RAD ETILDI", reply_markup=None)