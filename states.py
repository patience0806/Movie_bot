from aiogram.fsm.state import State, StatesGroup


class MovieAdd(StatesGroup):
    code = State()
    description = State()
    video = State()
    confirm = State()


class MovieEdit(StatesGroup):
    choose_field = State()
    new_value = State()


class MovieDelete(StatesGroup):
    waiting_code = State()


class SerialAdd(StatesGroup):
    movie_code = State()
    episode_number = State()
    episode_video = State()
    confirm = State()


class SerialRemove(StatesGroup):
    movie_code = State()
    episode_number = State()
    confirm = State()


class ChannelAdd(StatesGroup):
    name = State()
    type = State()
    url = State()
    chat_id = State()
    confirm = State()


class ChannelEdit(StatesGroup):
    choose_field = State()
    new_value = State()


class BroadcastMessage(StatesGroup):
    waiting_content = State()
    confirm = State()


class PremiumBuy(StatesGroup):
    """Oddiy foydalanuvchi Premium sotib olayotganda ishlatiladi."""
    waiting_screenshot = State()


class PremiumPlanAdd(StatesGroup):
    """Admin yangi Premium tarif qo'shayotganda ishlatiladi."""
    name = State()
    duration_days = State()
    price = State()
    confirm = State()


class PremiumPlanEdit(StatesGroup):
    """Admin mavjud Premium tarifni tahrirlayotganda ishlatiladi."""
    new_value = State()


class PremiumCard(StatesGroup):
    """Admin karta raqami/egasini o'zgartirayotganda ishlatiladi."""
    waiting_number = State()
    waiting_holder = State()