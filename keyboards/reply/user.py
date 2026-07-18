from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_ADMIN_PANEL = "👤 Admin Panel"


def get_user_menu(is_admin: bool = False):
    """Oddiy foydalanuvchi uchun menyu ko'rsatilmaydi (klaviatura olib tashiladi).
    Faqat adminlar uchun "Admin Panel" tugmasi chiqadi."""
    if is_admin:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text=BTN_ADMIN_PANEL))
        return builder.as_markup(resize_keyboard=True)
    return ReplyKeyboardRemove()