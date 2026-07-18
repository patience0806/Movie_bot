from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

EDITABLE_MOVIE_FIELDS = [
    ("Kod", "code"),
    ("Tavsif", "description"),
    ("Poster", "poster_file_id"),
    ("Video", "video_file_id"),
]


def movies_list_keyboard(movies, page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for movie in movies:
        series_icon = "📺 " if movie["is_series"] else "🎬 "
        builder.row(InlineKeyboardButton(
            text=f"{series_icon}{movie['code']}",
            callback_data=f"movie_open:{movie['id']}:{page}"
        ))

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"movies_page:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{max(total_pages, 1)}", callback_data="movies_noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"movies_page:{page + 1}"))
    builder.row(*nav_row)
    return builder.as_markup()


def movie_detail_keyboard(movie_id: int, page: int, is_series: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️", callback_data=f"movie_edit:{movie_id}:{page}"),
        InlineKeyboardButton(text="🗑", callback_data=f"movie_delete:{movie_id}:{page}"),
    )
    if is_series:
        builder.row(InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"movie_episodes:{movie_id}"))
    else:
        builder.row(InlineKeyboardButton(text="🎥 Videoni ko'rish", callback_data=f"movie_watch:{movie_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data=f"movies_page:{page}"))
    return builder.as_markup()


def movie_delete_confirm_keyboard(movie_id: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha", callback_data=f"movie_delete_yes:{movie_id}:{page}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"movie_delete_no:{movie_id}:{page}"),
    )
    return builder.as_markup()


def movie_edit_fields_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, field in EDITABLE_MOVIE_FIELDS:
        builder.button(text=label, callback_data=f"medit_field:{movie_id}:{field}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data=f"medit_cancel:{movie_id}"))
    return builder.as_markup()


def movie_user_keyboard(movie_id: int, is_series: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_series:
        builder.row(InlineKeyboardButton(text="📺 Qismlarni ko'rish", callback_data=f"user_episodes:{movie_id}"))
    else:
        builder.row(InlineKeyboardButton(text="🎥 Kinoni ko'rish", callback_data=f"user_watch:{movie_id}"))
    return builder.as_markup()


def episodes_list_keyboard(movie_id: int, episodes, for_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    prefix = "admin_ep_watch" if for_admin else "user_ep_watch"
    for ep in episodes:
        builder.button(
            text=f"{ep['episode_number']}-qism",
            callback_data=f"{prefix}:{movie_id}:{ep['episode_number']}"
        )
    builder.adjust(4)
    return builder.as_markup()