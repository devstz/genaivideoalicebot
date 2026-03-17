from aiogram.fsm.state import State, StatesGroup


class GenerationStates(StatesGroup):
    choosing_template = State()
    viewing_preview = State()
    uploading_photo = State()
    entering_wishes = State()
    confirming = State()


class ChangePasswordStates(StatesGroup):
    waiting_current_password = State()
    waiting_new_password = State()
