from datetime import time

WORK_SCHEDULE = {
    0: (time(10, 0), time(22, 0)),  # вс
    1: (time(10, 0), time(22, 0)),  # пн
    2: (time(10, 0), time(22, 0)),  # вт
    3: (time(10, 0), time(22, 0)),  # ср
    4: (time(10, 0), time(22, 0)),  # чт
    5: (time(10, 0), time(23, 59)),  # пт
    6: (time(10, 0), time(23, 59)),  # сб
}
STEP_MINUTES = 15
