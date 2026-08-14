from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_CARD_SETTINGS = "💳 Karta sozlamalari"
BTN_PLANS = "💰 Tariflar"
BTN_PREMIUM_USERS = "👥 Premium foydalanuvchilar"
BTN_BACK = "⬅️ Orqaga"


def get_premium_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_CARD_SETTINGS))
    builder.row(KeyboardButton(text=BTN_PLANS))
    builder.row(KeyboardButton(text=BTN_PREMIUM_USERS))
    builder.row(KeyboardButton(text=BTN_BACK))
    return builder.as_markup(resize_keyboard=True)