from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from keyboards.inline.movie import episodes_list_keyboard

router = Router()


@router.callback_query(F.data.startswith("user_watch:"))
async def user_watch_movie(callback: CallbackQuery):
    movie_id = int(callback.data.split(":")[1])
    movie = await db.get_movie_by_id(movie_id)
    if not movie:
        await callback.answer("Kino topilmadi.", show_alert=True)
        return
    if not movie["video_file_id"]:
        await callback.answer("Bu kino uchun video hali yuklanmagan.", show_alert=True)
        return
    await callback.answer()
    await db.increment_views(movie_id)
    await callback.message.answer_video(
        movie["video_file_id"],
        caption=f"🎬 {movie['code']}",
        protect_content=True
    )


@router.callback_query(F.data.startswith("user_episodes:"))
async def user_episodes_list(callback: CallbackQuery):
    movie_id = int(callback.data.split(":")[1])
    episodes = await db.get_episodes(movie_id)
    await callback.answer()
    if not episodes:
        await callback.message.answer("⚠️ Bu serial uchun hali qismlar qo'shilmagan.")
        return
    await callback.message.answer(
        "📺 Qismni tanlang:", reply_markup=episodes_list_keyboard(movie_id, episodes, for_admin=False)
    )


@router.callback_query(F.data.startswith("user_ep_watch:"))
async def user_episode_watch(callback: CallbackQuery):
    _, movie_id, ep_number = callback.data.split(":")
    episode = await db.get_episode(int(movie_id), int(ep_number))
    await callback.answer()
    if not episode:
        await callback.message.answer("⚠️ Bu qism topilmadi.")
        return
    await db.increment_views(int(movie_id))
    await callback.message.answer_video(
        episode["video_file_id"], caption=f"📺 {ep_number}-qism", protect_content=True
    )