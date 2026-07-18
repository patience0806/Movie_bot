import asyncio

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import database as db
from states import BroadcastMessage
from utils.filters import IsAdmin
from keyboards.reply.admin import get_admin_menu

router = Router()
router.message.filter(IsAdmin())

CANCEL_TEXT = "❌ Bekor qilish"
CONFIRM_TEXT = "✅ Yuborish"


def cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


def confirm_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=CONFIRM_TEXT))
    builder.row(KeyboardButton(text=CANCEL_TEXT))
    return builder.as_markup(resize_keyboard=True)


async def ads_entry(message: Message, state: FSMContext):
    await state.set_state(BroadcastMessage.waiting_content)
    await message.answer(
        "📣 Yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "Matn, rasm, video yoki forward qilingan xabar bo'lishi mumkin:",
        reply_markup=cancel_keyboard()
    )


@router.message(BroadcastMessage.waiting_content, F.text == CANCEL_TEXT)
@router.message(BroadcastMessage.confirm, F.text == CANCEL_TEXT)
async def ads_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Reklama bekor qilindi.", reply_markup=get_admin_menu())


@router.message(BroadcastMessage.waiting_content)
async def ads_receive_content(message: Message, state: FSMContext):
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        content_type=message.content_type
    )
    await state.set_state(BroadcastMessage.confirm)
    total_users = await db.get_users_count()
    await message.answer(
        f"👥 Ushbu xabar {total_users} ta foydalanuvchiga yuborilsinmi?",
        reply_markup=confirm_keyboard()
    )


@router.message(BroadcastMessage.confirm, F.text == CONFIRM_TEXT)
async def ads_send_broadcast(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    users = await db.get_all_users()
    status_msg = await message.answer(
        f"⏳ Yuborilmoqda... 0/{len(users)}", reply_markup=get_admin_menu()
    )

    sent, failed = 0, 0
    for i, user in enumerate(users, start=1):
        if user["is_banned"] == 1:
            continue
        try:
            await bot.copy_message(
                chat_id=user["telegram_id"],
                from_chat_id=data["from_chat_id"],
                message_id=data["message_id"]
            )
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1

        if i % 20 == 0:
            try:
                await status_msg.edit_text(f"⏳ Yuborilmoqda... {i}/{len(users)}")
            except Exception:
                pass
            await asyncio.sleep(0.05)

    await db.add_ad(
        content_type=data.get("content_type", "text"),
        text=None,
        file_id=None,
        sent_count=sent,
        failed_count=failed
    )
    await db.add_log(message.from_user.id, "Reklama yuborildi", f"sent={sent} failed={failed}")

    await message.answer(
        f"✅ Reklama yuborish yakunlandi!\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Yuborilmadi: {failed}"
    )