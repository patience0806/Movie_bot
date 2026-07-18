import math

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import database as db
from config import MOVIES_PER_PAGE
from states import MovieAdd, MovieEdit, MovieDelete, SerialAdd, SerialRemove
from utils.filters import IsAdmin
from keyboards.reply.movie import (
    get_movie_menu, BTN_ADD_MOVIE, BTN_MOVIE_LIST, BTN_MOVIE_DELETE,
    BTN_SERIAL_ADD, BTN_SERIAL_REMOVE
)
from keyboards.inline.movie import (
    movies_list_keyboard, movie_detail_keyboard, movie_delete_confirm_keyboard,
    movie_edit_fields_keyboard, episodes_list_keyboard, EDITABLE_MOVIE_FIELDS
)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

CANCEL_TEXT = "❌ Bekor qilish"
CONFIRM_TEXT = "✅ Saqlash"


def cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


def confirm_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CONFIRM_TEXT))
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


def format_movie_detail_text(movie) -> str:
    type_text = "📺 Serial" if movie["is_series"] else "🎬 Kino"
    return (
        f"{type_text}\n\n"
        f"🔢 Kod: <code>{movie['code']}</code>\n"
        f"📝 Tavsif: {movie['description']}\n"
        f"👁 Ko'rilgan: {movie['views']}\n"
        f"🔍 Qidirilgan: {movie['search_count']}"
    )


async def send_movie_detail(message: Message, movie, page: int):
    text = format_movie_detail_text(movie)
    kb = movie_detail_keyboard(movie["id"], page, bool(movie["is_series"]))
    if movie["poster_file_id"]:
        await message.answer_photo(movie["poster_file_id"], caption=text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


async def send_movies_page(message: Message, page: int):
    total = await db.get_movies_count()
    total_pages = max(math.ceil(total / MOVIES_PER_PAGE), 1)
    page = max(1, min(page, total_pages))
    movies = await db.get_movies_paginated(page, MOVIES_PER_PAGE)
    if not movies:
        await message.answer("🎬 Hozircha kinolar mavjud emas.")
        return
    await message.answer(
        f"📋 Kinolar ro'yxati ({page}/{total_pages}):",
        reply_markup=movies_list_keyboard(movies, page, total_pages)
    )


# ==================== KINO QO'SHISH (FSM: Kod -> Tavsif -> Video -> Tasdiqlash) ====================

@router.message(F.text == BTN_ADD_MOVIE)
async def add_movie_start(message: Message, state: FSMContext):
    await state.set_state(MovieAdd.code)
    await message.answer("🔢 Kino kodini yuboring (masalan: 001):", reply_markup=cancel_keyboard())


@router.message(MovieAdd.code, F.text == CANCEL_TEXT)
@router.message(MovieAdd.description, F.text == CANCEL_TEXT)
@router.message(MovieAdd.video, F.text == CANCEL_TEXT)
@router.message(MovieAdd.confirm, F.text == CANCEL_TEXT)
async def add_movie_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Kino qo'shish bekor qilindi.", reply_markup=get_movie_menu())


@router.message(MovieAdd.code)
async def add_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()
    existing = await db.get_movie_by_code(code)
    if existing:
        await message.answer("⚠️ Bu kod band. Boshqa kod kiriting:")
        return
    await state.update_data(code=code)
    await state.set_state(MovieAdd.description)
    await message.answer("📝 Kino tavsifini yuboring:")


@router.message(MovieAdd.description)
async def add_movie_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(MovieAdd.video)
    await message.answer("🎥 Kino videosini yuboring:")


@router.message(MovieAdd.video, F.video)
async def add_movie_video(message: Message, state: FSMContext):
    await state.update_data(video_file_id=message.video.file_id)
    data = await state.get_data()
    await state.set_state(MovieAdd.confirm)
    text = (
        "✅ Quyidagi ma'lumotlarni tekshiring:\n\n"
        f"🔢 Kod: {data.get('code')}\n"
        f"📝 Tavsif: {data.get('description')}\n"
        f"🎥 Video: ✅ bor\n\n"
        "Saqlansinmi?"
    )
    await message.answer(text, reply_markup=confirm_keyboard())


@router.message(MovieAdd.video)
async def add_movie_video_invalid(message: Message):
    await message.answer("⚠️ Iltimos, video fayl yuboring.")


@router.message(MovieAdd.confirm, F.text == CONFIRM_TEXT)
async def add_movie_save(message: Message, state: FSMContext):
    data = await state.get_data()
    ok = await db.add_movie(
        code=data.get("code"),
        description=data.get("description"),
        poster_file_id=None,
        video_file_id=data.get("video_file_id"),
    )
    await state.clear()
    if ok:
        await db.add_log(message.from_user.id, "Kino qo'shildi", data.get("code"))
        await message.answer("✅ Kino muvaffaqiyatli saqlandi!", reply_markup=get_movie_menu())
    else:
        await message.answer("⚠️ Bu kod band, kino saqlanmadi.", reply_markup=get_movie_menu())


# ==================== KINOLAR RO'YXATI ====================

@router.message(F.text == BTN_MOVIE_LIST)
async def movie_list_open(message: Message):
    await send_movies_page(message, 1)


@router.callback_query(F.data.startswith("movies_page:"))
async def movies_page_callback(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    total = await db.get_movies_count()
    total_pages = max(math.ceil(total / MOVIES_PER_PAGE), 1)
    page = max(1, min(page, total_pages))
    movies = await db.get_movies_paginated(page, MOVIES_PER_PAGE)
    await callback.answer()
    if not movies:
        await callback.message.edit_text("🎬 Hozircha kinolar mavjud emas.")
        return
    await callback.message.edit_text(
        f"📋 Kinolar ro'yxati ({page}/{total_pages}):",
        reply_markup=movies_list_keyboard(movies, page, total_pages)
    )


@router.callback_query(F.data == "movies_noop")
async def movies_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("movie_open:"))
async def movie_open_callback(callback: CallbackQuery):
    _, movie_id, page = callback.data.split(":")
    movie = await db.get_movie_by_id(int(movie_id))
    await callback.answer()
    if not movie:
        await callback.message.answer("⚠️ Kino topilmadi (o'chirilgan bo'lishi mumkin).")
        return
    await callback.message.delete()
    await send_movie_detail(callback.message, movie, int(page))


@router.callback_query(F.data.startswith("movie_watch:"))
async def movie_watch_callback(callback: CallbackQuery):
    movie_id = int(callback.data.split(":")[1])
    movie = await db.get_movie_by_id(movie_id)
    await callback.answer()
    if not movie or not movie["video_file_id"]:
        await callback.message.answer("⚠️ Bu kino uchun video mavjud emas.")
        return
    await callback.message.answer_video(
        movie["video_file_id"], caption=f"🎬 {movie['code']}", protect_content=True
    )


@router.callback_query(F.data.startswith("movie_episodes:"))
async def movie_episodes_callback(callback: CallbackQuery):
    movie_id = int(callback.data.split(":")[1])
    episodes = await db.get_episodes(movie_id)
    await callback.answer()
    if not episodes:
        await callback.message.answer("⚠️ Bu serial uchun hali qismlar qo'shilmagan.")
        return
    await callback.message.answer(
        "📺 Qismni tanlang:", reply_markup=episodes_list_keyboard(movie_id, episodes, for_admin=True)
    )


@router.callback_query(F.data.startswith("admin_ep_watch:"))
async def admin_episode_watch_callback(callback: CallbackQuery):
    _, movie_id, ep_number = callback.data.split(":")
    episode = await db.get_episode(int(movie_id), int(ep_number))
    await callback.answer()
    if not episode:
        await callback.message.answer("⚠️ Bu qism topilmadi.")
        return
    await callback.message.answer_video(
        episode["video_file_id"], caption=f"📺 {ep_number}-qism", protect_content=True
    )


# ==================== KINO O'CHIRISH (ro'yxatdan) ====================

@router.callback_query(F.data.startswith("movie_delete:"))
async def movie_delete_ask(callback: CallbackQuery):
    _, movie_id, page = callback.data.split(":")
    await callback.answer()
    await callback.message.answer(
        "❗️ Ushbu kinoni o'chirishga ishonchingiz komilmi?",
        reply_markup=movie_delete_confirm_keyboard(int(movie_id), int(page))
    )


@router.callback_query(F.data.startswith("movie_delete_yes:"))
async def movie_delete_confirm_yes(callback: CallbackQuery):
    _, movie_id, page = callback.data.split(":")
    movie = await db.get_movie_by_id(int(movie_id))
    await db.delete_movie(int(movie_id))
    await db.add_log(callback.from_user.id, "Kino o'chirildi", movie["code"] if movie else str(movie_id))
    await callback.answer("🗑 O'chirildi.")
    await callback.message.delete()
    if int(page) > 0:
        await send_movies_page(callback.message, int(page))
    else:
        await callback.message.answer("🗑 Kino o'chirildi.", reply_markup=get_movie_menu())


@router.callback_query(F.data.startswith("movie_delete_no:"))
async def movie_delete_confirm_no(callback: CallbackQuery):
    await callback.answer("Bekor qilindi.")
    await callback.message.delete()


# ==================== KINO O'CHIRISH (kod orqali, panel tugmasi) ====================

@router.message(F.text == BTN_MOVIE_DELETE)
async def movie_delete_by_code_start(message: Message, state: FSMContext):
    await state.set_state(MovieDelete.waiting_code)
    await message.answer("🗑 O'chirmoqchi bo'lgan kino kodini yuboring:", reply_markup=cancel_keyboard())


@router.message(MovieDelete.waiting_code, F.text == CANCEL_TEXT)
async def movie_delete_by_code_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_movie_menu())


@router.message(MovieDelete.waiting_code)
async def movie_delete_by_code_process(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = await db.get_movie_by_code(code)
    await state.clear()
    if not movie:
        await message.answer("⚠️ Bunday kodli kino topilmadi.", reply_markup=get_movie_menu())
        return
    await message.answer(
        f"❗️ \"{movie['code']}\" kodli kinoni o'chirishga ishonchingiz komilmi?",
        reply_markup=movie_delete_confirm_keyboard(movie["id"], 0)
    )


# ==================== KINO TAHRIRLASH (ro'yxatdan) ====================

@router.callback_query(F.data.startswith("movie_edit:"))
async def movie_edit_open(callback: CallbackQuery):
    _, movie_id, page = callback.data.split(":")
    await callback.answer()
    await callback.message.answer(
        "✏️ Qaysi maydonni tahrirlaysiz?",
        reply_markup=movie_edit_fields_keyboard(int(movie_id))
    )


@router.callback_query(F.data.startswith("medit_cancel:"))
async def movie_edit_cancel(callback: CallbackQuery):
    await callback.answer("Bekor qilindi.")
    await callback.message.delete()


@router.callback_query(F.data.startswith("medit_field:"))
async def movie_edit_field_chosen(callback: CallbackQuery, state: FSMContext):
    _, movie_id, field = callback.data.split(":")
    await state.update_data(edit_movie_id=int(movie_id), edit_field=field)
    await state.set_state(MovieEdit.new_value)
    await callback.answer()

    field_labels = dict(EDITABLE_MOVIE_FIELDS)
    label = field_labels.get(field, field)

    if field == "poster_file_id":
        await callback.message.answer("🖼 Yangi poster (rasm) yuboring:")
    elif field == "video_file_id":
        await callback.message.answer("🎥 Yangi video yuboring:")
    else:
        await callback.message.answer(f"✏️ \"{label}\" uchun yangi qiymatni yuboring:")


@router.message(MovieEdit.new_value, F.photo)
async def movie_edit_receive_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") != "poster_file_id":
        await message.answer("⚠️ Bu maydon uchun rasm emas, matn yuborish kerak.")
        return
    await db.update_movie_field(data["edit_movie_id"], "poster_file_id", message.photo[-1].file_id)
    await db.add_log(message.from_user.id, "Kino tahrirlandi", f"movie_id={data['edit_movie_id']} field=poster")
    await state.clear()
    await message.answer("✅ Poster yangilandi.", reply_markup=get_movie_menu())


@router.message(MovieEdit.new_value, F.video)
async def movie_edit_receive_video(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") != "video_file_id":
        await message.answer("⚠️ Bu maydon uchun video emas, matn yuborish kerak.")
        return
    await db.update_movie_field(data["edit_movie_id"], "video_file_id", message.video.file_id)
    await db.add_log(message.from_user.id, "Kino tahrirlandi", f"movie_id={data['edit_movie_id']} field=video")
    await state.clear()
    await message.answer("✅ Video yangilandi.", reply_markup=get_movie_menu())


@router.message(MovieEdit.new_value)
async def movie_edit_receive_text(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    movie_id = data.get("edit_movie_id")

    if field in ("poster_file_id", "video_file_id"):
        await message.answer("⚠️ Bu maydon uchun media fayl yuborishingiz kerak.")
        return

    value = message.text.strip()
    if field == "code":
        existing = await db.get_movie_by_code(value)
        if existing and existing["id"] != movie_id:
            await message.answer("⚠️ Bu kod band. Boshqa kod kiriting:")
            return

    await db.update_movie_field(movie_id, field, value)
    await db.add_log(message.from_user.id, "Kino tahrirlandi", f"movie_id={movie_id} field={field}")
    await state.clear()
    await message.answer("✅ Kino ma'lumoti yangilandi.", reply_markup=get_movie_menu())


# ==================== SERIAL QO'SHISH (FSM: Kino kodi -> Qism raqami -> Video -> Tasdiqlash) ====================

@router.message(F.text == BTN_SERIAL_ADD)
async def serial_add_start(message: Message, state: FSMContext):
    await state.set_state(SerialAdd.movie_code)
    await message.answer(
        "📺 Qism qo'shmoqchi bo'lgan kino kodini yuboring:", reply_markup=cancel_keyboard()
    )


@router.message(SerialAdd.movie_code, F.text == CANCEL_TEXT)
@router.message(SerialAdd.episode_number, F.text == CANCEL_TEXT)
@router.message(SerialAdd.episode_video, F.text == CANCEL_TEXT)
@router.message(SerialAdd.confirm, F.text == CANCEL_TEXT)
async def serial_add_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_movie_menu())


@router.message(SerialAdd.movie_code)
async def serial_add_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = await db.get_movie_by_code(code)
    if not movie:
        await message.answer("⚠️ Bunday kodli kino topilmadi. Qaytadan kiriting:")
        return
    await state.update_data(movie_id=movie["id"], movie_code=movie["code"])
    await state.set_state(SerialAdd.episode_number)
    await message.answer("🔢 Qism raqamini yuboring (masalan: 1):")


@router.message(SerialAdd.episode_number)
async def serial_add_episode_number(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Qism raqami faqat son bo'lishi kerak. Qaytadan kiriting:")
        return
    data = await state.get_data()
    episode_number = int(message.text.strip())
    existing = await db.get_episode(data["movie_id"], episode_number)
    if existing:
        await message.answer("⚠️ Bu qism raqami allaqachon mavjud. Boshqa raqam kiriting:")
        return
    await state.update_data(episode_number=episode_number)
    await state.set_state(SerialAdd.episode_video)
    await message.answer(f"🎥 {episode_number}-qism uchun videoni yuboring:")


@router.message(SerialAdd.episode_video, F.video)
async def serial_add_episode_video(message: Message, state: FSMContext):
    await state.update_data(video_file_id=message.video.file_id)
    data = await state.get_data()
    await state.set_state(SerialAdd.confirm)
    text = (
        "✅ Quyidagilarni tekshiring:\n\n"
        f"🎬 Kino kodi: {data.get('movie_code')}\n"
        f"🔢 Qism: {data.get('episode_number')}\n"
        f"🎥 Video: ✅ bor\n\n"
        "Saqlansinmi?"
    )
    await message.answer(text, reply_markup=confirm_keyboard())


@router.message(SerialAdd.episode_video)
async def serial_add_episode_video_invalid(message: Message):
    await message.answer("⚠️ Iltimos, video fayl yuboring.")


@router.message(SerialAdd.confirm, F.text == CONFIRM_TEXT)
async def serial_add_save(message: Message, state: FSMContext):
    data = await state.get_data()
    ok = await db.add_episode(data["movie_id"], data["episode_number"], data["video_file_id"])
    await state.clear()
    if ok:
        await db.add_log(
            message.from_user.id, "Serial qismi qo'shildi",
            f"movie_id={data['movie_id']} episode={data['episode_number']}"
        )
        await message.answer("✅ Qism muvaffaqiyatli qo'shildi!", reply_markup=get_movie_menu())
    else:
        await message.answer("⚠️ Bu qism raqami allaqachon mavjud.", reply_markup=get_movie_menu())


# ==================== SERIAL O'CHIRISH (FSM: Kino kodi -> Qism raqami -> Tasdiqlash) ====================

@router.message(F.text == BTN_SERIAL_REMOVE)
async def serial_remove_start(message: Message, state: FSMContext):
    await state.set_state(SerialRemove.movie_code)
    await message.answer(
        "🗑 Qismini o'chirmoqchi bo'lgan kino kodini yuboring:", reply_markup=cancel_keyboard()
    )


@router.message(SerialRemove.movie_code, F.text == CANCEL_TEXT)
@router.message(SerialRemove.episode_number, F.text == CANCEL_TEXT)
@router.message(SerialRemove.confirm, F.text == CANCEL_TEXT)
async def serial_remove_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_movie_menu())


@router.message(SerialRemove.movie_code)
async def serial_remove_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = await db.get_movie_by_code(code)
    if not movie:
        await message.answer("⚠️ Bunday kodli kino topilmadi. Qaytadan kiriting:")
        return
    episodes = await db.get_episodes(movie["id"])
    if not episodes:
        await message.answer("⚠️ Bu kino uchun qismlar mavjud emas.", reply_markup=get_movie_menu())
        await state.clear()
        return
    await state.update_data(movie_id=movie["id"], movie_code=movie["code"])
    await state.set_state(SerialRemove.episode_number)
    ep_list = ", ".join(str(e["episode_number"]) for e in episodes)
    await message.answer(f"🔢 O'chirmoqchi bo'lgan qism raqamini yuboring.\nMavjud qismlar: {ep_list}")


@router.message(SerialRemove.episode_number)
async def serial_remove_episode_number(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("⚠️ Qism raqami faqat son bo'lishi kerak. Qaytadan kiriting:")
        return
    data = await state.get_data()
    episode_number = int(message.text.strip())
    episode = await db.get_episode(data["movie_id"], episode_number)
    if not episode:
        await message.answer("⚠️ Bunday qism topilmadi. Qaytadan kiriting:")
        return
    await state.update_data(episode_number=episode_number)
    await state.set_state(SerialRemove.confirm)
    await message.answer(
        f"❗️ \"{data['movie_code']}\" kinosining {episode_number}-qismini o'chirishga "
        "ishonchingiz komilmi?",
        reply_markup=confirm_keyboard()
    )


@router.message(SerialRemove.confirm, F.text == CONFIRM_TEXT)
async def serial_remove_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.delete_episode(data["movie_id"], data["episode_number"])
    await db.add_log(
        message.from_user.id, "Serial qismi o'chirildi",
        f"movie_id={data['movie_id']} episode={data['episode_number']}"
    )
    await state.clear()
    await message.answer("🗑 Qism o'chirildi.", reply_markup=get_movie_menu())