from datetime import time

WORK_SCHEDULE = {
    0: (time(10, 0), time(22, 0)),  # пн
    1: (time(10, 0), time(22, 0)),  # вт
    2: (time(10, 0), time(22, 0)),  # ср
    3: (time(10, 0), time(22, 0)),  # чт
    4: (time(10, 0), time(23, 0)),  # пт
    5: (time(10, 0), time(23, 0)),  # сб
    6: (None, None),  # вс – выходной
}

HELP_EMAIL = ["help@help.com", "help@help.ru", "asvidet@jinr.ru"]
