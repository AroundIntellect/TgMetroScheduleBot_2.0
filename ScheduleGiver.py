from os import sep
import datetime
import pytz
import json

station_priority = {
    "Kosmonavtov_Avenue": 0,
    "Uralmash": 1,
    "Mashinostroiteley": 2,
    "Uralskaya": 3,
    "Dinamo": 4,
    "Square_of_1905": 5,
    "Geologicheskaya": 6,
    "Chkalovskaya": 7,
    "Botanicheskaya": 8
}

station_translator = {
    "Kosmonavtov_Avenue": "Проспект Космонавтов",
    "Uralmash": "Уралмаш",
    "Mashinostroiteley": "Машиностроителей",
    "Uralskaya": "Уральская",
    "Dinamo": "Динамо",
    "Square_of_1905": "Площадь 1905 года",
    "Geologicheskaya": "Геологическая",
    "Chkalovskaya": "Чкаловская",
    "Botanicheskaya": "Ботаническая"
}


def get_day_type(date: datetime.date = None) -> str:
    """
    Функция проверяет переданную дату на принадлежность к выходному или рабочему дням.
    В случае, если дата не была передана - использует текущую
    :param date: дата в формате datetime.date
    :return: Возвращает "Выходные", если переданная дата является выходным днём, и "Рабочие", если это рабочий день
    """
    if date is None:
        date = datetime.date.today()

    non_weekends = [
        datetime.date(2024, 11, 2),
        datetime.date(2024, 12, 28)
    ]

    weekends = [
        datetime.date(2024, 5, 9),
        datetime.date(2024, 5, 10),
        datetime.date(2024, 6, 12),
        datetime.date(2024, 11, 4),
        datetime.date(2024, 12, 30),
        datetime.date(2024, 12, 31)
    ]

    if date in non_weekends:
        return "Рабочие"
    elif date in weekends:
        return "Выходные"
    elif date.weekday() >= 5:
        return "Выходные"
    else:
        return "Рабочие"


def get_current_time() -> int:
    """
    Функция возвращает текущее время для временной зоны Екатеринбурга
    :return: Время в формате (Часы * 60 + Минуты)
    """
    hours = int(datetime.datetime.now(pytz.utc).strftime("%H")) + 5
    if hours >= 25:
        hours -= 24
    minutes = int(datetime.datetime.now().strftime("%M"))
    return hours * 60 + minutes


def get_formatted_time(time: int) -> str:
    """
    Функция возвращает время в формате ЧЧ:ММ
    :param time: Время в формате (Часы * 60 + Минуты)
    :return: Время в формате ЧЧ:ММ
    """
    minute = time % 60
    hour = (time - minute) // 60

    if minute < 10:
        minute = f"0{minute}"
    if hour < 10:
        hour = f"0{hour}"
    elif hour == 24:
        hour = "00"

    return f"{hour}:{minute}"


def get_schedule(station_name, day_type, direction) -> list:
    """
    Функция возвращает расписание поездов для требуемых станции, типа дня и направления
    :param station_name: Название начальной станции
    :param day_type: Тип дня (Выходные/Рабочие)
    :param direction: Направление (Ботаническая/Проспект космонавтов)
    :return: Массив с расписанием поездов
    """
    with open(f"ScheduleDB{sep}schedule.json", "r", encoding="utf-8") as file:
        schedule: dict = json.load(file)
        return schedule.get(station_name, {}).get(day_type, {}).get(direction)


def get_closest_trains(start_station: str, finish_station: str, count_trains: int) -> str:
    """
    Функция возвращает сообщение со списком ближайших поездов по параметрам.
    :param start_station: Название начальной станции
    :param finish_station: Название конечной станции
    :param count_trains: Требуемое количество поездов
    :return: Сообщение с перечислением поездов
    """

    start_times, finish_times = [], []
    message = ("Список ближайших 🚇 по маршруту\n"
               f"<u><i><b>"
               f"{station_translator.get(start_station)} ➜ {station_translator.get(finish_station)}:"
               f"</b></i></u>\n")

    # Так как расписания для "Ботаническая -> Ботаническая" и "Космонавтов -> Космонавтов" не существует,
    # время до прибытия на эти станции считается как время до предыдущей станции + 2 минуты.
    was_changed = False
    if finish_station == "Botanicheskaya":
        finish_station = "Chkalovskaya"
        was_changed = True
    elif finish_station == "Kosmonavtov_Avenue":
        finish_station = "Uralmash"
        was_changed = True

    if station_priority.get(start_station) < station_priority.get(finish_station):
        direction = "Ботаническая"
    else:
        direction = "Проспект Космонавтов"

    current_time = get_current_time()

    start_schedule = get_schedule(start_station, get_day_type(), direction)
    finish_schedule = get_schedule(finish_station, get_day_type(), direction)
    for i in range(len(start_schedule)):
        if start_schedule[i] >= current_time:
            f_time = finish_schedule[i]
            if was_changed:
                f_time += 2
            message += f"<u><i>Время в пути составит {f_time - start_schedule[i]} минут(ы)</i></u>\n"
            message += (f"\n<b>1. {get_formatted_time(start_schedule[i])} ➜ {get_formatted_time(f_time)} - ⏳ "
                        f"до отправления осталось {start_schedule[i] - current_time} минут(ы).</b>\n")

            start_times = start_schedule[i + 1:i + count_trains]
            finish_times = finish_schedule[i + 1:i + count_trains]
            break

    for k in range(len(start_times)):
        f_time = finish_times[k]
        if was_changed:
            f_time += 2

        message += (f"\n<i>{k + 2}. {get_formatted_time(start_times[k])} ➜ {get_formatted_time(f_time)} - "
                    f"до отправления осталось {start_times[k] - current_time} минут(ы).</i>\n")

    return message
