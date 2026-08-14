from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

EDITABLE_PLAN_FIELDS = [
    ("Nomi", "name"),
    ("Davomiyligi (kun)", "duration_days"),
    ("Narxi", "price"),
]


# ---------- USER: tarif tanlash ----------

def premium_plans_keyboard(plans) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.row(InlineKeyboardButton(
            text=f"💎 {plan['name']} — {plan['price']} so'm",
            callback_data=f"premium_plan:{plan['id']}"
        ))
    return builder.as_markup()


# ---------- ADMIN: to'lovni tasdiqlash/rad etish ----------

def premium_payment_admin_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"premium_approve:{payment_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"premium_reject:{payment_id}"),
    )
    return builder.as_markup()


# ---------- ADMIN: karta sozlamalari ----------

def premium_card_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Karta raqamini o'zgartirish", callback_data="premium_card_number"))
    builder.row(InlineKeyboardButton(text="✏️ Karta egasini o'zgartirish", callback_data="premium_card_holder"))
    return builder.as_markup()


# ---------- ADMIN: tariflar ro'yxati ----------

def premium_plans_admin_keyboard(plans) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        status_icon = "✅" if plan["status"] == "active" else "🚫"
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {plan['name']} — {plan['price']} so'm",
            callback_data=f"premium_plan_open:{plan['id']}"
        ))
    builder.row(InlineKeyboardButton(text="➕ Tarif qo'shish", callback_data="premium_plan_add"))
    return builder.as_markup()


# ---------- ADMIN: bitta tarif tafsiloti ----------

def premium_plan_detail_keyboard(plan_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, field in EDITABLE_PLAN_FIELDS:
        builder.button(text=f"✏️ {label}", callback_data=f"premium_plan_edit:{plan_id}:{field}")
    builder.adjust(1)
    toggle_text = "🚫 Deaktiv qilish" if is_active else "✅ Aktiv qilish"
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data=f"premium_plan_toggle:{plan_id}"))
    builder.row(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"premium_plan_delete:{plan_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data="premium_plans_back"))
    return builder.as_markup()


def premium_plan_delete_confirm_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha", callback_data=f"premium_plan_delete_yes:{plan_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"premium_plan_delete_no:{plan_id}"),
    )
    return builder.as_markup()


# ---------- ADMIN: Premium foydalanuvchilar ro'yxati (pagination) ----------

def premium_users_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"premium_users_page:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{max(total_pages, 1)}", callback_data="premium_users_noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"premium_users_page:{page + 1}"))
    builder.row(*nav_row)
    return builder.as_markup()