from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import database as db
from states import ChannelAdd, ChannelEdit
from utils.filters import IsAdmin
from keyboards.reply.channel import (
    get_channel_menu, BTN_ADD_CHANNEL, BTN_CHANNEL_LIST, BTN_CHANNEL_EDIT, BTN_CHANNEL_DELETE
)
from keyboards.inline.channel import (
    channels_list_keyboard, channel_detail_keyboard, channel_delete_confirm_keyboard,
    channel_edit_fields_keyboard, channel_type_keyboard, EDITABLE_CHANNEL_FIELDS
)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

CANCEL_TEXT = "❌ Bekor qilish"


def cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


def format_channel_detail(channel) -> str:
    status = "✅ Faol" if channel["status"] == 1 else "🚫 O'chirilgan"
    return (
        f"📢 <b>{channel['name']}</b>\n\n"
        f"🔗 Turi: {channel['type']}\n"
        f"🌐 Link: {channel['url']}\n"
        f"🆔 Chat ID: {channel['chat_id'] or '—'}\n"
        f"🔢 Tartib raqami: {channel['order_number']}\n"
        f"📊 Holati: {status}"
    )


async def send_channels_list(message: Message):
    channels = await db.get_channels(active_only=False)
    if not channels:
        await message.answer("📢 Hozircha linklar mavjud emas.")
        return
    await message.answer("📋 Majburiy obuna linklari:", reply_markup=channels_list_keyboard(channels))


# ==================== LINK QO'SHISH (FSM) ====================

@router.message(F.text == BTN_ADD_CHANNEL)
async def add_channel_start(message: Message, state: FSMContext):
    await state.set_state(ChannelAdd.name)
    await message.answer("📢 Kanal/link nomini yuboring:", reply_markup=cancel_keyboard())


@router.message(ChannelAdd.name, F.text == CANCEL_TEXT)
@router.message(ChannelAdd.url, F.text == CANCEL_TEXT)
@router.message(ChannelAdd.chat_id, F.text == CANCEL_TEXT)
@router.message(ChannelAdd.confirm, F.text == CANCEL_TEXT)
async def add_channel_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_channel_menu())


@router.message(ChannelAdd.name)
async def add_channel_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(ChannelAdd.type)
    await message.answer("🔗 Turini tanlang:", reply_markup=channel_type_keyboard())


@router.callback_query(ChannelAdd.type, F.data.startswith("ctype:"))
async def add_channel_type_chosen(callback: CallbackQuery, state: FSMContext):
    channel_type = callback.data.split(":")[1]
    await state.update_data(type=channel_type)
    await state.set_state(ChannelAdd.url)
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "🌐 Link manzilini yuboring (masalan: https://t.me/kanal):",
        reply_markup=cancel_keyboard()
    )


@router.message(ChannelAdd.url)
async def add_channel_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    data = await state.get_data()
    if data.get("type") == "telegram":
        await state.set_state(ChannelAdd.chat_id)
        await message.answer(
            "🆔 Kanalning chat ID yoki @username qiymatini yuboring "
            "(bot getChatMember tekshiruvi uchun, masalan: @mychannel yoki -1001234567890):"
        )
    else:
        await state.update_data(chat_id=None)
        await _ask_channel_confirm(message, state)


@router.message(ChannelAdd.chat_id)
async def add_channel_chat_id(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.text.strip())
    await _ask_channel_confirm(message, state)


async def _ask_channel_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(ChannelAdd.confirm)
    text = (
        "✅ Ma'lumotlarni tekshiring:\n\n"
        f"📢 Nomi: {data.get('name')}\n"
        f"🔗 Turi: {data.get('type')}\n"
        f"🌐 Link: {data.get('url')}\n"
        f"🆔 Chat ID: {data.get('chat_id') or '—'}\n\n"
        "Saqlansinmi?"
    )
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="✅ Saqlash"))
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    await message.answer(text, reply_markup=builder.as_markup(resize_keyboard=True))


@router.message(ChannelAdd.confirm, F.text == "✅ Saqlash")
async def add_channel_save(message: Message, state: FSMContext):
    data = await state.get_data()
    channels = await db.get_channels(active_only=False)
    next_order = len(channels) + 1
    await db.add_channel(
        name=data.get("name"),
        type_=data.get("type"),
        url=data.get("url"),
        chat_id=data.get("chat_id"),
        order_number=next_order
    )
    await db.add_log(message.from_user.id, "Kanal qo'shildi", data.get("name"))
    await state.clear()
    await message.answer("✅ Link muvaffaqiyatli qo'shildi!", reply_markup=get_channel_menu())


# ==================== LINKLAR RO'YXATI ====================

@router.message(F.text == BTN_CHANNEL_LIST)
async def channel_list_open(message: Message):
    await send_channels_list(message)


@router.callback_query(F.data == "channels_back")
async def channels_back_callback(callback: CallbackQuery):
    await callback.answer()
    channels = await db.get_channels(active_only=False)
    if not channels:
        await callback.message.edit_text("📢 Hozircha linklar mavjud emas.")
        return
    await callback.message.edit_text(
        "📋 Majburiy obuna linklari:", reply_markup=channels_list_keyboard(channels)
    )


@router.callback_query(F.data.startswith("channel_open:"))
async def channel_open_callback(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    channel = await db.get_channel_by_id(channel_id)
    await callback.answer()
    if not channel:
        await callback.message.answer("⚠️ Link topilmadi.")
        return
    await callback.message.edit_text(
        format_channel_detail(channel), reply_markup=channel_detail_keyboard(channel_id)
    )


# ==================== LINK O'CHIRISH ====================

@router.message(F.text == BTN_CHANNEL_DELETE)
async def channel_delete_hint(message: Message):
    await message.answer(
        "🗑 Linkni o'chirish uchun \"📋 Linklar\" ro'yxatidan kerakli linkni tanlang "
        "va 🗑 tugmasini bosing."
    )


@router.callback_query(F.data.startswith("channel_delete:"))
async def channel_delete_ask(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.edit_text(
        "❗️ Ushbu linkni o'chirishga ishonchingiz komilmi?",
        reply_markup=channel_delete_confirm_keyboard(channel_id)
    )


@router.callback_query(F.data.startswith("channel_delete_yes:"))
async def channel_delete_confirm_yes(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    channel = await db.get_channel_by_id(channel_id)
    await db.delete_channel(channel_id)
    await db.add_log(callback.from_user.id, "Kanal o'chirildi", channel["name"] if channel else str(channel_id))
    await callback.answer("🗑 O'chirildi.")
    channels = await db.get_channels(active_only=False)
    if not channels:
        await callback.message.edit_text("📢 Hozircha linklar mavjud emas.")
        return
    await callback.message.edit_text(
        "📋 Majburiy obuna linklari:", reply_markup=channels_list_keyboard(channels)
    )


@router.callback_query(F.data.startswith("channel_delete_no:"))
async def channel_delete_confirm_no(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    channel = await db.get_channel_by_id(channel_id)
    await callback.answer("Bekor qilindi.")
    if channel:
        await callback.message.edit_text(
            format_channel_detail(channel), reply_markup=channel_detail_keyboard(channel_id)
        )


# ==================== LINK TAHRIRLASH ====================

@router.message(F.text == BTN_CHANNEL_EDIT)
async def channel_edit_hint(message: Message):
    await message.answer(
        "✏️ Linkni tahrirlash uchun \"📋 Linklar\" ro'yxatidan kerakli linkni tanlang "
        "va ✏️ tugmasini bosing."
    )


@router.callback_query(F.data.startswith("channel_edit:"))
async def channel_edit_open(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.edit_text(
        "✏️ Qaysi maydonni tahrirlaysiz?",
        reply_markup=channel_edit_fields_keyboard(channel_id)
    )


@router.callback_query(F.data.startswith("cedit_cancel:"))
async def channel_edit_cancel(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    channel = await db.get_channel_by_id(channel_id)
    await callback.answer("Bekor qilindi.")
    if channel:
        await callback.message.edit_text(
            format_channel_detail(channel), reply_markup=channel_detail_keyboard(channel_id)
        )


@router.callback_query(F.data.startswith("cedit_field:"))
async def channel_edit_field_chosen(callback: CallbackQuery, state: FSMContext):
    _, channel_id, field = callback.data.split(":")
    await state.update_data(edit_channel_id=int(channel_id), edit_field=field)
    await state.set_state(ChannelEdit.new_value)
    await callback.answer()

    field_labels = dict(EDITABLE_CHANNEL_FIELDS)
    label = field_labels.get(field, field)
    await callback.message.answer(f"✏️ \"{label}\" uchun yangi qiymatni yuboring:")


@router.message(ChannelEdit.new_value)
async def channel_edit_receive_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    channel_id = data.get("edit_channel_id")
    value = message.text.strip()

    if field == "order_number":
        if not value.isdigit():
            await message.answer("⚠️ Tartib raqami faqat son bo'lishi kerak. Qaytadan kiriting:")
            return
        value = int(value)

    if field == "type" and value not in ("telegram", "instagram", "youtube", "tiktok", "website"):
        await message.answer(
            "⚠️ Turi faqat quyidagilardan biri bo'lishi kerak: "
            "telegram, instagram, youtube, tiktok, website"
        )
        return

    await db.update_channel_field(channel_id, field, value)
    await db.add_log(message.from_user.id, "Kanal tahrirlandi", f"channel_id={channel_id} field={field}")
    await state.clear()
    await message.answer("✅ Ma'lumot yangilandi.", reply_markup=get_channel_menu())