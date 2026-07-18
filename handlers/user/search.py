from aiogram import Router, F
from aiogram.types import Message

import database as db
from keyboards.inline.movie import movie_user_keyboard

router = Router()


async def send_movie_card(message: Message, movie):
    type_text = "📺 Serial" if movie["is_series"] else "🎬 Kino"
    caption = (
        f"{type_text}\n\n"
        f"🔢 Kod: <code>{movie['code']}</code>\n"
        f"📝 Tavsif: {movie['description']}\n"
        f"👁 Ko'rilgan: {movie['views']}"
    )
    kb = movie_user_keyboard(movie["id"], bool(movie["is_series"]))
    if movie["poster_file_id"]:
        await message.answer_photo(movie["poster_file_id"], caption=caption, reply_markup=kb)
    else:
        await message.answer(caption, reply_markup=kb)


@router.message(F.text)
async def lookup_movie_by_code(message: Message):
    """Foydalanuvchi yuborgan har qanday matn kino kodi sifatida qidiriladi.
    Alohida qidiruv/trend/sevimlilar tugmalari endi kerak emas."""
    code = message.text.strip()
    movie = await db.get_movie_by_code(code)
    await db.log_search()

    if not movie:
        await message.answer("😔 Bunday kodli kino topilmadi. Kino kodini tekshirib qaytadan yuboring.")
        return

    await db.increment_search_count(movie["id"])
    await send_movie_card(message, movie)