from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_ADD_MOVIE = "➕ Kino qo'shish"
BTN_MOVIE_LIST = "📋 Kinolar ro'yxati"
BTN_MOVIE_DELETE = "🗑 Kino o'chirish"
BTN_SERIAL_ADD = "➕ Serial qo'shish"
BTN_SERIAL_REMOVE = "🗑 Serial o'chirish"
BTN_BACK = "⬅️ Orqaga"


def get_movie_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_ADD_MOVIE), KeyboardButton(text=BTN_MOVIE_LIST))
    builder.row(KeyboardButton(text=BTN_SERIAL_ADD), KeyboardButton(text=BTN_SERIAL_REMOVE))
    builder.row(KeyboardButton(text=BTN_MOVIE_DELETE))
    builder.row(KeyboardButton(text=BTN_BACK))
    return builder.as_markup(resize_keyboard=True)