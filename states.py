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