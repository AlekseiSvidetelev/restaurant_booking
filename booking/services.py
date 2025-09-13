from datetime import time, timedelta
from constants import WORK_SCHEDULE, STEP_MINUTES


def time_choices_for_date(dt):
    """Возвращает 2 списка: (часы), (минуты) в рамках режима дня dt."""
    weekday = dt.weekday()  # 0=пн … 6=вс
    open_t, close_t = WORK_SCHEDULE[weekday]

    # превращаем в минуты от начала суток
    open_min = open_t.hour * 60 + open_t.minute
    close_min = close_t.hour * 60 + close_t.minute
    if close_min == 23 * 60 + 59:  # до полуночи
        close_min = 24 * 60

    # часы
    hours = list({(m // 60) for m in range(open_min, close_min, STEP_MINUTES)})
    # минуты
    minutes = list(range(0, 60, STEP_MINUTES))
    return sorted(hours), minutes
