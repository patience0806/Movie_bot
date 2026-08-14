from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from states import PremiumBuy
from keyboards.inline.premium import premium_plans_keyboard, premium_payment_admin_keyboard

router = Router()

PREMIUM_INTRO_TEXT = (
    "💎 <b>PREMIUM</b>\n\n"
    "Premium obuna orqali botdan foydalanish uchun majburiy kanallarga obuna bo'lish shart emas.\n\n"
    "Premium obuna davomida kino kodlarini to'g'ridan-to'g'ri yuborishingiz mumkin.\n\n"
    "Quyidagi tariflardan birini tanlang:"
)


@router.callback_query(F.data == "premium_open")
async def premium_open(callback: CallbackQuery):
    plans = await db.get_active_plans()
    await callback.answer()
    if not plans:
        await callback.message.answer("💎 Hozircha faol Premium tariflar mavjud emas.")
        return
    await callback.message.answer(PREMIUM_INTRO_TEXT, reply_markup=premium_plans_keyboard(plans))


@router.callback_query(F.data.startswith("premium_plan:"))
async def premium_plan_chosen(callback: CallbackQuery, state: FSMContext):
    plan_id = int(callback.data.split(":")[1])
    plan = await db.get_plan_by_id(plan_id)
    await callback.answer()

    if not plan or plan["status"] != "active":
        await callback.message.answer("⚠️ Bu tarif hozir mavjud emas. Boshqa tarifni tanlang.")
        return

    card_number = await db.get_premium_setting("card_number", "Karta raqami hali kiritilmagan")
    card_holder = await db.get_premium_setting("card_holder", "Karta egasi hali kiritilmagan")

    # Tarif ma'lumotlari FSM holatiga "suratga olinadi" (snapshot) - shu bilan
    # admin keyinchalik tarifni o'zgartirsa ham, ushbu to'lov eski narx/muddat bilan qoladi.
    await state.update_data(
        plan_id=plan["id"],
        plan_name=plan["name"],
        price=plan["price"],
        duration_days=plan["duration_days"]
    )
    await state.set_state(PremiumBuy.waiting_screenshot)

    text = (
        f"{plan['name']} Premium obunani tanladingiz.\n\n"
        f"💎 Premium tarif: {plan['name']}\n"
        f"⏳ Muddat: {plan['duration_days']} kun\n"
        f"💰 To'lov miqdori: {plan['price']} so'm\n\n"
        f"💳 Karta:\n{card_number}\n\n"
        f"👤 Karta egasi:\n{card_holder}\n\n"
        "To'lovni amalga oshirgandan so'ng to'lov chekini screenshot sifatida shu yerga yuboring."
    )
    await callback.message.answer(text)


@router.message(PremiumBuy.waiting_screenshot, F.photo)
async def premium_receive_screenshot(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    screenshot_file_id = message.photo[-1].file_id
    payment_id = await db.create_payment(
        user_id=message.from_user.id,
        plan_id=data["plan_id"],
        plan_name_snapshot=data["plan_name"],
        price_snapshot=data["price"],
        duration_days_snapshot=data["duration_days"],
        screenshot_file_id=screenshot_file_id
    )

    await message.answer(
        "✅ Chekingiz adminga yuborildi.\n\n"
        "Admin tasdiqlashi bilan sizga xabar beramiz."
    )

    admin_text = (
        "💎 <b>YANGI PREMIUM TO'LOV</b>\n\n"
        f"👤 Foydalanuvchi:\n{message.from_user.full_name}\n\n"
        f"🆔 ID:\n<code>{message.from_user.id}</code>\n\n"
        f"👤 Username:\n@{message.from_user.username or '—'}\n\n"
        f"💎 Tarif:\n{data['plan_name']}\n\n"
        f"⏳ Muddat:\n{data['duration_days']} kun\n\n"
        f"💰 To'lov:\n{data['price']} so'm\n\n"
        f"📅 So'rov vaqti:\n{db.now_str()}"
    )

    admins = await db.get_admins()
    for admin in admins:
        try:
            await bot.send_photo(
                chat_id=admin["telegram_id"],
                photo=screenshot_file_id,
                caption=admin_text,
                reply_markup=premium_payment_admin_keyboard(payment_id)
            )
        except Exception:
            # Admin botni bloklagan yoki hali /start bosmagan bo'lishi mumkin - o'tkazib yuboriladi
            continue


@router.message(PremiumBuy.waiting_screenshot)
async def premium_screenshot_invalid(message: Message):
    await message.answer("⚠️ Iltimos, to'lov chekining screenshot (rasm) shaklida yuboring.")