import aiosqlite
from datetime import datetime, date, timedelta

from config import DB_PATH

DATE_FMT = "%Y-%m-%d %H:%M:%S"
DAY_FMT = "%Y-%m-%d"


def now_str() -> str:
    return datetime.now().strftime(DATE_FMT)


def today_str() -> str:
    return date.today().strftime(DAY_FMT)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            joined_at TEXT NOT NULL,
            is_banned INTEGER DEFAULT 0,
            last_active TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            added_by INTEGER,
            added_at TEXT NOT NULL,
            is_owner INTEGER DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            poster_file_id TEXT,
            video_file_id TEXT,
            is_series INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            search_count INTEGER DEFAULT 0,
            added_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            video_file_id TEXT NOT NULL,
            added_at TEXT NOT NULL,
            UNIQUE(movie_id, episode_number),
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            url TEXT NOT NULL,
            chat_id TEXT,
            status INTEGER DEFAULT 1,
            order_number INTEGER DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            text TEXT,
            file_id TEXT,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            new_users INTEGER DEFAULT 0,
            searches INTEGER DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS join_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT DEFAULT 'requested',
            UNIQUE(user_id, channel_id)
        )""")

        await db.commit()


# ==================== USERS ====================

async def add_user(telegram_id: int, username: str, full_name: str) -> bool:
    """Returns True if a new user was created, False if already existed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET last_active = ?, username = ?, full_name = ? WHERE telegram_id = ?",
                (now_str(), username, full_name, telegram_id)
            )
            await db.commit()
            return False
        await db.execute(
            "INSERT INTO users (telegram_id, username, full_name, joined_at, last_active) VALUES (?, ?, ?, ?, ?)",
            (telegram_id, username, full_name, now_str(), now_str())
        )
        await db.commit()
        await _increment_daily_stat_internal(db, "new_users")
        return True


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return await cursor.fetchone()


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_today_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE date(joined_at) = ?", (today_str(),)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_active_users_count(days: int = 7) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE date(last_active) >= date('now', ?)",
            (f"-{days} days",)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def update_last_active(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_active = ? WHERE telegram_id = ?", (now_str(), telegram_id))
        await db.commit()


# ==================== ADMINS ====================

async def add_admin(telegram_id: int, added_by: int, is_owner: bool = False) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM admins WHERE telegram_id = ?", (telegram_id,))
        if await cursor.fetchone():
            return False
        await db.execute(
            "INSERT INTO admins (telegram_id, added_by, added_at, is_owner) VALUES (?, ?, ?, ?)",
            (telegram_id, added_by, now_str(), 1 if is_owner else 0)
        )
        await db.commit()
        return True


async def is_admin(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM admins WHERE telegram_id = ?", (telegram_id,))
        return (await cursor.fetchone()) is not None


async def is_owner(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM admins WHERE telegram_id = ? AND is_owner = 1", (telegram_id,))
        return (await cursor.fetchone()) is not None


# ==================== MOVIES ====================

async def add_movie(code: str, description: str, poster_file_id, video_file_id, is_series: int = 0) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM movies WHERE code = ?", (code,))
        if await cursor.fetchone():
            return False
        await db.execute(
            """INSERT INTO movies
            (code, description, poster_file_id, video_file_id, is_series, views, search_count, added_at)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?)""",
            (code, description, poster_file_id, video_file_id, is_series, now_str())
        )
        await db.commit()
        return True


async def get_movie_by_code(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM movies WHERE code = ?", (code,))
        return await cursor.fetchone()


async def get_movie_by_id(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
        return await cursor.fetchone()


async def get_movies_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM movies")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_movies_paginated(page: int, per_page: int):
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM movies ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset)
        )
        return await cursor.fetchall()


ALLOWED_MOVIE_FIELDS = {"code", "description", "poster_file_id", "video_file_id"}


async def update_movie_field(movie_id: int, field: str, value):
    if field not in ALLOWED_MOVIE_FIELDS:
        raise ValueError(f"Invalid movie field: {field}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE movies SET {field} = ? WHERE id = ?", (value, movie_id))
        await db.commit()


async def delete_movie(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        await db.execute("DELETE FROM episodes WHERE movie_id = ?", (movie_id,))
        await db.commit()


async def increment_views(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET views = views + 1 WHERE id = ?", (movie_id,))
        await db.commit()


async def increment_search_count(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET search_count = search_count + 1 WHERE id = ?", (movie_id,))
        await db.commit()


async def log_search():
    """Har bir qidiruv urinishi uchun (natija topilgan yoki topilmaganidan qat'iy nazar) chaqiriladi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await _increment_daily_stat_internal(db, "searches")


async def get_today_searches_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT searches FROM statistics WHERE date = ?", (today_str(),))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_most_searched_movie():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM movies WHERE search_count > 0 ORDER BY search_count DESC LIMIT 1"
        )
        return await cursor.fetchone()


async def get_most_viewed_movie():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM movies WHERE views > 0 ORDER BY views DESC LIMIT 1"
        )
        return await cursor.fetchone()


# ==================== EPISODES (SERIAL) ====================

async def add_episode(movie_id: int, episode_number: int, video_file_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM episodes WHERE movie_id = ? AND episode_number = ?",
            (movie_id, episode_number)
        )
        if await cursor.fetchone():
            return False
        await db.execute(
            "INSERT INTO episodes (movie_id, episode_number, video_file_id, added_at) VALUES (?, ?, ?, ?)",
            (movie_id, episode_number, video_file_id, now_str())
        )
        await db.execute("UPDATE movies SET is_series = 1 WHERE id = ?", (movie_id,))
        await db.commit()
        return True


async def get_episodes(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM episodes WHERE movie_id = ? ORDER BY episode_number ASC", (movie_id,)
        )
        return await cursor.fetchall()


async def get_episode(movie_id: int, episode_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM episodes WHERE movie_id = ? AND episode_number = ?",
            (movie_id, episode_number)
        )
        return await cursor.fetchone()


async def delete_episode(movie_id: int, episode_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM episodes WHERE movie_id = ? AND episode_number = ?",
            (movie_id, episode_number)
        )
        await db.commit()
        cursor = await db.execute("SELECT COUNT(*) FROM episodes WHERE movie_id = ?", (movie_id,))
        row = await cursor.fetchone()
        if row and row[0] == 0:
            await db.execute("UPDATE movies SET is_series = 0 WHERE id = ?", (movie_id,))
            await db.commit()


# ==================== CHANNELS ====================

async def add_channel(name: str, type_: str, url: str, chat_id: str, order_number: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO channels (name, type, url, chat_id, status, order_number) VALUES (?, ?, ?, ?, 1, ?)",
            (name, type_, url, chat_id, order_number)
        )
        await db.commit()


async def get_channels(active_only: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if active_only:
            cursor = await db.execute(
                "SELECT * FROM channels WHERE status = 1 ORDER BY order_number ASC, id ASC"
            )
        else:
            cursor = await db.execute("SELECT * FROM channels ORDER BY order_number ASC, id ASC")
        return await cursor.fetchall()


async def get_channel_by_id(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        return await cursor.fetchone()


ALLOWED_CHANNEL_FIELDS = {"name", "type", "url", "chat_id", "status", "order_number"}


async def update_channel_field(channel_id: int, field: str, value):
    if field not in ALLOWED_CHANNEL_FIELDS:
        raise ValueError(f"Invalid channel field: {field}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE channels SET {field} = ? WHERE id = ?", (value, channel_id))
        await db.commit()


async def delete_channel(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.commit()


# ==================== ADS ====================

async def add_ad(content_type: str, text: str, file_id: str, sent_count: int, failed_count: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO ads (content_type, text, file_id, sent_count, failed_count, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (content_type, text, file_id, sent_count, failed_count, now_str())
        )
        await db.commit()
        return cursor.lastrowid


async def get_today_ads_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM ads WHERE date(created_at) = ?", (today_str(),)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_all_users():
    """Reklama (broadcast) barcha foydalanuvchilarga yuborish uchun ishlatiladi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users ORDER BY id DESC")
        return await cursor.fetchall()


# ==================== SETTINGS ====================

async def get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM settings WHERE key = ?", (key,))
        if await cursor.fetchone():
            await db.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
        else:
            await db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


# ==================== LOGS ====================

async def add_log(admin_id: int, action: str, details: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO logs (admin_id, action, details, created_at) VALUES (?, ?, ?, ?)",
            (admin_id, action, details, now_str())
        )
        await db.commit()


# ==================== STATISTICS (internal helper) ====================

async def _increment_daily_stat_internal(db: aiosqlite.Connection, field: str):
    """Must be called with an already-open db connection. field: 'new_users' or 'searches'."""
    today = today_str()
    cursor = await db.execute("SELECT id FROM statistics WHERE date = ?", (today,))
    row = await cursor.fetchone()
    if row:
        await db.execute(f"UPDATE statistics SET {field} = {field} + 1 WHERE date = ?", (today,))
    else:
        if field == "new_users":
            await db.execute(
                "INSERT INTO statistics (date, new_users, searches) VALUES (?, 1, 0)", (today,)
            )
        else:
            await db.execute(
                "INSERT INTO statistics (date, new_users, searches) VALUES (?, 0, 1)", (today,)
            )
    await db.commit()

# ==================== ADMINS (ro'yxat - Premium to'lov bildirishnomalari uchun) ====================

async def get_admins():
    """Barcha adminlar ro'yxati - Premium to'lov kelganda ularning barchasiga xabar
    yuborish uchun ishlatiladi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM admins ORDER BY is_owner DESC, id ASC")
        return await cursor.fetchall()


# ==================== PREMIUM: TARIFLAR (premium_plans) ====================

async def add_plan(name: str, duration_days: int, price: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO premium_plans (name, duration_days, price, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'active', ?, ?)",
            (name, duration_days, price, now_str(), now_str())
        )
        await db.commit()
        return cursor.lastrowid


async def get_plan_by_id(plan_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM premium_plans WHERE id = ?", (plan_id,))
        return await cursor.fetchone()


async def get_active_plans():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM premium_plans WHERE status = 'active' ORDER BY duration_days ASC"
        )
        return await cursor.fetchall()


async def get_all_plans():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM premium_plans ORDER BY id DESC")
        return await cursor.fetchall()


ALLOWED_PLAN_FIELDS = {"name", "duration_days", "price", "status"}


async def update_plan_field(plan_id: int, field: str, value):
    if field not in ALLOWED_PLAN_FIELDS:
        raise ValueError(f"Invalid plan field: {field}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE premium_plans SET {field} = ?, updated_at = ? WHERE id = ?",
            (value, now_str(), plan_id)
        )
        await db.commit()


async def delete_plan(plan_id: int):
    """Tarifni o'chiradi. Eski premium_payments/premium_subscriptions yozuvlariga TEGMAYDI,
    chunki ular plan_name_snapshot/price_snapshot orqali o'z holatini mustaqil saqlaydi."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM premium_plans WHERE id = ?", (plan_id,))
        await db.commit()


# ==================== PREMIUM: TO'LOVLAR (premium_payments) ====================

async def create_payment(user_id: int, plan_id: int, plan_name_snapshot: str,
                          price_snapshot: int, duration_days_snapshot: int,
                          screenshot_file_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO premium_payments
            (user_id, plan_id, plan_name_snapshot, price_snapshot, duration_days_snapshot,
             screenshot_file_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (user_id, plan_id, plan_name_snapshot, price_snapshot, duration_days_snapshot,
             screenshot_file_id, now_str())
        )
        await db.commit()
        return cursor.lastrowid


async def get_payment_by_id(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM premium_payments WHERE id = ?", (payment_id,))
        return await cursor.fetchone()


async def approve_payment(payment_id: int, admin_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE premium_payments SET status = 'approved', approved_at = ?, admin_id = ? WHERE id = ?",
            (now_str(), admin_id, payment_id)
        )
        await db.commit()


async def reject_payment(payment_id: int, admin_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE premium_payments SET status = 'rejected', rejected_at = ?, admin_id = ? WHERE id = ?",
            (now_str(), admin_id, payment_id)
        )
        await db.commit()


# ==================== PREMIUM: OBUNALAR (premium_subscriptions) ====================

async def create_subscription(user_id: int, payment_id: int, plan_id: int,
                               plan_name: str, price: int, duration_days: int) -> int:
    started = datetime.now()
    expires = started + timedelta(days=duration_days)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO premium_subscriptions
            (user_id, payment_id, plan_id, plan_name, price, started_at, expires_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""",
            (user_id, payment_id, plan_id, plan_name, price,
             started.strftime(DATE_FMT), expires.strftime(DATE_FMT))
        )
        await db.commit()
        return cursor.lastrowid


async def get_latest_subscription(user_id: int):
    """Foydalanuvchining eng oxirgi (id bo'yicha) premium yozuvini qaytaradi (active yoki expired)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM premium_subscriptions WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        return await cursor.fetchone()


async def is_premium_active(user_id: int) -> bool:
    """MUHIM: har chaqirilganda muddatni JONLI tekshiradi (background task ishlatilmaydi -
    bu eng ishonchli usul, chunki fon vazifasi server qayta ishga tushganda ishga
    tushmasligi yoki kechikishi mumkin, jonli tekshiruv esa har doim aniq natija beradi).
    Agar muddat o'tgan bo'lsa, statusni avtomatik 'expired' ga o'zgartiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM premium_subscriptions WHERE user_id = ? AND status = 'active' "
            "ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return False

        expires_at = datetime.strptime(row["expires_at"], DATE_FMT)
        if expires_at > datetime.now():
            return True

        await db.execute(
            "UPDATE premium_subscriptions SET status = 'expired' WHERE id = ?", (row["id"],)
        )
        await db.commit()
        return False


def is_subscription_currently_active(subscription_row) -> bool:
    """Vaqtga bog'liq holda, bazadagi 'status' ustuniga qaramasdan haqiqiy holatni hisoblaydi.
    Admin ro'yxatida har doim aniq (jonli) holat ko'rsatilishi uchun ishlatiladi.
    (Sinxron funksiya - DB ulanishi kerak emas, faqat berilgan qatordagi vaqtni solishtiradi.)"""
    expires_at = datetime.strptime(subscription_row["expires_at"], DATE_FMT)
    return expires_at > datetime.now()


async def get_premium_subscriptions_paginated(page: int, per_page: int):
    """Admin uchun - har bir foydalanuvchining ENG OXIRGI premium yozuvi (eski tarixiy
    yozuvlar ro'yxatda takrorlanmasligi uchun har bir user_id dan faqat MAX(id) olinadi)."""
    offset = (page - 1) * per_page
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ps.* FROM premium_subscriptions ps
            INNER JOIN (
                SELECT user_id, MAX(id) AS max_id FROM premium_subscriptions GROUP BY user_id
            ) latest ON ps.id = latest.max_id
            ORDER BY ps.id DESC LIMIT ? OFFSET ?""",
            (per_page, offset)
        )
        return await cursor.fetchall()


async def get_premium_subscriptions_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM premium_subscriptions")
        row = await cursor.fetchone()
        return row[0] if row else 0


# ==================== PREMIUM: SOZLAMALAR (premium_settings - karta ma'lumotlari) ====================

async def get_premium_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM premium_settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default


async def set_premium_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM premium_settings WHERE key = ?", (key,))
        if await cursor.fetchone():
            await db.execute("UPDATE premium_settings SET value = ? WHERE key = ?", (value, key))
        else:
            await db.execute("INSERT INTO premium_settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()
# ==================== JOIN REQUESTS (PRIVATE TELEGRAM CHANNELS) ====================

async def get_channel_by_chat_id(chat_id: str):
    """Kanalni uning chat_id qiymati bo'yicha topadi (chat_join_request kelganda
    kanalni bizning bazamizdagi yozuv bilan moslashtirish uchun ishlatiladi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM channels WHERE chat_id = ?", (str(chat_id),))
        return await cursor.fetchone()


async def add_join_request(user_id: int, channel_id: int):
    """Foydalanuvchi private kanalga Join Request yuborganda chaqiriladi.
    Agar bu foydalanuvchi/kanal juftligi uchun yozuv allaqachon mavjud bo'lsa, qayta yozilmaydi
    (UNIQUE(user_id, channel_id) tufayli xato bermasligi uchun avval tekshiramiz)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM join_requests WHERE user_id = ? AND channel_id = ?", (user_id, channel_id)
        )
        if await cursor.fetchone():
            await db.execute(
                "UPDATE join_requests SET status = 'requested' WHERE user_id = ? AND channel_id = ?",
                (user_id, channel_id)
            )
        else:
            await db.execute(
                "INSERT INTO join_requests (user_id, channel_id, requested_at, status) "
                "VALUES (?, ?, ?, 'requested')",
                (user_id, channel_id, now_str())
            )
        await db.commit()


async def has_active_join_request(user_id: int, channel_id: int) -> bool:
    """Foydalanuvchi shu private kanalga request yuborganmi (status='requested' yoki 'approved')."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM join_requests WHERE user_id = ? AND channel_id = ? "
            "AND status IN ('requested', 'approved')",
            (user_id, channel_id)
        )
        return (await cursor.fetchone()) is not None