from aiogram.fsm.state import State, StatesGroup


class AddDnsRecordStates(StatesGroup):
    """States for adding DNS static records."""

    waiting_for_domain = State()
    waiting_for_confirmation = State()
