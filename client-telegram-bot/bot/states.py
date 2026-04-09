from aiogram.fsm.state import State, StatesGroup


class NewPlanStates(StatesGroup):
    waiting_exam_name = State()
    waiting_days_available = State()
    waiting_hours_per_day = State()
    waiting_weak_topics = State()
    waiting_preferred_mode = State()


class PlanStates(StatesGroup):
    waiting_plan_selection = State()
    plan_actions = State()
    waiting_material_upload = State()
    waiting_delete_confirmation = State()
