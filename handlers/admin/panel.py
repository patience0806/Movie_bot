from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from utils.filters import IsAdmin
from keyboards.reply.user import BTN_ADMIN_PANEL, get_user_menu
from keyboards.reply.admin import get_admin_menu, BTN_BACK, BTN_MOVIES, BTN_CHANNELS, \
    BTN_ADS, BTN_PREMIUM, BTN_ADMINS, BTN_STATISTICS
from keyboards.reply.movie import get_movie_menu
from keyboards.reply.channel import get_channel_menu

router = Router()
router.message.filter(IsAdmin())


@router.message(F.text == BTN_ADMIN_PANEL)
async def open_admin_panel(message: Message, state: FSMContext):
    await state.update_data(admin_section="main")
    is_owner = await db.is_owner(message.from_user.id)
    await message.answer("👤 Admin Panel", reply_markup=get_admin_menu(is_owner))


@router.message(F.text == BTN_MOVIES)
async def open_movies_panel(message: Message, state: FSMContext):
    await state.update_data(admin_section="movies")
    await message.answer("🎬 Kinolar bo'limi", reply_markup=get_movie_menu())


@router.message(F.text == BTN_CHANNELS)
async def open_channels_panel(message: Message, state: FSMContext):
    await state.update_data(admin_section="channels")
    await message.answer("📢 Majburiy obuna bo'limi", reply_markup=get_channel_menu())


@router.message(F.text == BTN_ADS)
async def open_ads_panel(message: Message, state: FSMContext):
    await state.update_data(admin_section="ads")
    from handlers.admin.ads import ads_entry
    await ads_entry(message, state)


@router.message(F.text == BTN_PREMIUM)
async def open_premium_panel(message: Message, state: FSMContext):
    await state.update_data(admin_section="premium")
    from handlers.admin.premium import premium_entry
    await premium_entry(message, state)


@router.message(F.text == BTN_ADMINS)
async def open_admins_panel(message: Message, state: FSMContext):
    # Ikkinchi darajali himoya: tugma faqat owner uchun ko'rsatiladi (get_admin_menu
    # is_owner=False bo'lsa yashiradi), lekin backend darajasida ham tekshiramiz -
    # agar oddiy admin biror sabab bilan shu matnni yuborsa, ichkariga kirmaydi.
    if not await db.is_owner(message.from_user.id):
        return
    await state.update_data(admin_section="admins")
    from handlers.admin.admins import admins_entry
    await admins_entry(message, state)


@router.message(F.text == BTN_STATISTICS)
async def show_statistics(message: Message):
    total_users = await db.get_users_count()
    today_users = await db.get_today_users_count()
    active_users = await db.get_active_users_count(days=7)
    total_movies = await db.get_movies_count()
    today_searches = await db.get_today_searches_count()
    today_ads = await db.get_today_ads_count()
    premium_users = await db.get_premium_subscriptions_count()
    most_searched = await db.get_most_searched_movie()
    most_viewed = await db.get_most_viewed_movie()

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"🆕 Bugungi foydalanuvchilar: <b>{today_users}</b>\n"
        f"🟢 Faol foydalanuvchilar (7 kun): <b>{active_users}</b>\n"
        f"🎬 Jami kinolar: <b>{total_movies}</b>\n"
        f"🔍 Bugungi qidiruvlar: <b>{today_searches}</b>\n"
        f"📣 Bugungi reklama: <b>{today_ads}</b>\n"
        f"💎 Premium foydalanuvchilar (jami): <b>{premium_users}</b>\n"
        f"🏆 Eng ko'p qidirilgan kino: <b>"
        f"{most_searched['code'] + ' (' + str(most_searched['search_count']) + ' marta)' if most_searched else '—'}</b>\n"
        f"👁 Eng ko'p ko'rilgan kino: <b>"
        f"{most_viewed['code'] + ' (' + str(most_viewed['views']) + ' marta)' if most_viewed else '—'}</b>"
    )
    await message.answer(text)


@router.message(F.text == BTN_BACK)
async def go_back(message: Message, state: FSMContext):
    data = await state.get_data()
    section = data.get("admin_section", "main")

    if section in ("movies", "channels", "ads", "premium", "admins"):
        await state.update_data(admin_section="main")
        is_owner = await db.is_owner(message.from_user.id)
        await message.answer("👤 Admin Panel", reply_markup=get_admin_menu(is_owner))
        return

    await state.update_data(admin_section=None)
    await message.answer("🏠 Bosh menyu", reply_markup=get_user_menu(is_admin=True))