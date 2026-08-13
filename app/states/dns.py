from aiogram.fsm.state import State, StatesGroup


class AddDnsRecordStates(StatesGroup):
    """States for adding a DNS static record."""

    waiting_for_domain = State()
    waiting_for_confirmation = State()
