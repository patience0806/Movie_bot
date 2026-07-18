from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

EDITABLE_CHANNEL_FIELDS = [
    ("Nomi", "name"),
    ("Turi", "type"),
    ("Link", "url"),
    ("Chat ID", "chat_id"),
    ("Tartib raqami", "order_number"),
]


def subscribe_keyboard(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(InlineKeyboardButton(text=f"🔗 {ch['name']}", url=ch['url']))
    builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub"))
    return builder.as_markup()


def channels_list_keyboard(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        status_icon = "✅" if ch["status"] == 1 else "🚫"
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {ch['name']} ({ch['type']})",
            callback_data=f"channel_open:{ch['id']}"
        ))
    return builder.as_markup()


def channel_detail_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️", callback_data=f"channel_edit:{channel_id}"),
        InlineKeyboardButton(text="🗑", callback_data=f"channel_delete:{channel_id}"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data="channels_back"))
    return builder.as_markup()


def channel_delete_confirm_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha", callback_data=f"channel_delete_yes:{channel_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"channel_delete_no:{channel_id}"),
    )
    return builder.as_markup()


def channel_edit_fields_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, field in EDITABLE_CHANNEL_FIELDS:
        builder.button(text=label, callback_data=f"cedit_field:{channel_id}:{field}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data=f"cedit_cancel:{channel_id}"))
    return builder.as_markup()


def channel_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    types = [
        ("Telegram", "telegram"),
        ("Instagram", "instagram"),
        ("YouTube", "youtube"),
        ("TikTok", "tiktok"),
        ("Website", "website"),
    ]
    for label, value in types:
        builder.button(text=label, callback_data=f"ctype:{value}")
    builder.adjust(2)
    return builder.as_markup()