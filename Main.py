import datetime
import pytz
import telebot
from telebot import types

from UsersDataBase import (add_user, get_current_user, update_user_data, add_favorite_trip, get_favorite_trips,
                           remove_favorite_trip)
from ScheduleGiver import get_closest_trains
from ScheduleParser import update_main_page, update_all_links, update_schedule_pages, update_schedule_json

token_main_bot, token_feedback_bot = get_favorite_trips(1)
main_bot = telebot.TeleBot(token_main_bot)
feedback_bot = telebot.TeleBot(token_feedback_bot)

MY_CHAT_ID = 740063203

station_button_names = {"Kosmonavtov_Avenue": "👨‍🚀 Проспект космонавтов",
                        "Uralmash": "🏭 Уралмаш",
                        "Mashinostroiteley": "🚘 Машиностроителей",
                        "Uralskaya": "🏔 Уральская",
                        "Dinamo": "🏟 Динамо",
                        "Square_of_1905": "🎊 Площадь 1905 года",
                        "Geologicheskaya": "🎪 Геологическая",
                        "Chkalovskaya": "🧳 Чкаловская",
                        "Botanicheskaya": "🌷 Ботаническая"}


@main_bot.message_handler(commands=['start'])
def start_func(message):
    """
    Обрабатывает команду /start и отправляет приветственное сообщение с инструкциями.

    :param message: Объект сообщения от пользователя
    """
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    main_menu_button = types.KeyboardButton("Главное меню 📝")
    settings_button = types.KeyboardButton("Настройки 🛠")
    feedback_button = types.KeyboardButton("Обратная связь ☺️")

    markup.add(main_menu_button)
    markup.row(feedback_button, settings_button)

    user_data = message.from_user
    add_user(message.chat.id, user_data.username, user_data.first_name, user_data.last_name, datetime.date.today())

    hello_message = (f"Привет, {user_data.first_name}! 👋\n"
                     "Я бот, который поможет узнать расписание ближайших поездов в метрополитене Екатеринбурга!\n"
                     "Краткая инструкция по использованию:\n"
                     "1. Выберите станцию, с которой планируете уехать\n"
                     "2. Выберите станцию, на которую планируете попасть\n"
                     "3. Получите расписание 3 ближайших (со стандартными настройками) поездов\n"
                     "\n"
                     "Вы можете настроить бота под себя, выбрав количество ближайших поездов, о прибытии которых будет "
                     "сообщать бот! Для этого перейдите в меню настроек, воспользовавшись "
                     'удобным меню или отправьте в чат сообщение "Настройки"\n\n'
                     'И самое главное - вы можете попросить бота запомнить ваши любимые маршруты. Для этого нажмите '
                     'соответствующую кнопку в меню или отправьте в чат сообщение "Избранные маршруты"\n'
                     "\n\n"
                     "Команды бота:\n"
                     "/menu - Вызов главного меню бота 📝\n"
                     "/settings - Настройка бота 🛠\n"
                     "/feedback - Обратная связь ☺️\n"
                     "Приятного пользования! ❤️\n"
                     "Жми по функциям выше или в меню\n"
                     "👇👇👇")

    main_bot.send_message(message.chat.id, hello_message, reply_markup=markup, parse_mode="html")


@main_bot.message_handler(func=lambda message:
                          message.text == "Главное меню 📝" or message.text.lower() == "главное меню"
                          or message.text == "/menu")
def main_menu(message):
    """
    Обрабатывает команду /menu и отправляет главное меню.

    :param message: Объект сообщения от пользователя
    """
    send_first_station_menu(message)
    main_bot.send_message(message.chat.id, "⌛")


@main_bot.message_handler(func=lambda message:
                          message.text == "Настройки 🛠" or message.text.lower() == "настройки"
                          or message.text == "/settings")
def settings_menu(message):
    """
    Обрабатывает команду /settings и отправляет меню настроек.

    :param message: Объект сообщения от пользователя
    """
    settings_message = "Из списка ниже выберите желаемое количество поездов, которые бот будет выводит в расписании:"
    num_translator = {
        1: "1⃣",
        2: "2⃣",
        3: "3⃣",
        4: "4⃣",
        5: "5⃣",
        6: "6⃣",
        7: "7⃣",
        8: "8⃣",
        9: "9⃣",
        10: "🔟",
    }
    current_user_settings = get_current_user(message.chat.id).get("count_trains")

    markup = types.InlineKeyboardMarkup()

    first_line = []
    second_line = []
    for i in range(1, 11):
        if i != current_user_settings:
            button = types.InlineKeyboardButton(str(num_translator.get(i)), callback_data=str(i))
        else:
            button = types.InlineKeyboardButton("✅", callback_data="pass")

        if len(first_line) < 5:
            first_line.append(button)
        else:
            second_line.append(button)

    markup.row(*first_line)
    markup.row(*second_line)

    main_bot.send_message(message.chat.id, settings_message, reply_markup=markup)


@main_bot.message_handler(func=lambda message:
                          message.text == "Обратная связь ☺️" or message.text.lower() == "обратная связь"
                          or message.text == "/feedback")
def feedback_menu(message):
    """
    Обрабатывает команду /feedback и отправляет сообщение с инструкциями по обратной связи.

    :param message: Объект сообщения от пользователя
    """
    feedback_message = ('Что бы ваше сообщение дошло до разработчика в начале сообщения напишите "Отзыв" без кавычек.\n'
                        "Я очень жду любую обратную связь, не стесняйтесь - пишите.\n"
                        "Так же, если вы нашли какой-то баг - пишите, но, надеюсь, нет :)\n"
                        "Заранее спасибо за любую обратную связь ☺️")

    main_bot.send_message(message.chat.id, feedback_message)


@main_bot.message_handler(func=lambda message: message.text.lower().startswith('отзыв'))
def send_me_feedback(message):
    """
    Обрабатывает сообщения, начинающиеся с 'отзыв', и отправляет их разработчику.

    :param message: Объект сообщения от пользователя
    """
    feedback_bot.send_message(MY_CHAT_ID, f"Сообщение отправлено {datetime.date.today()} в "
                                          f"{int(datetime.datetime.now(pytz.utc).strftime('%H')) + 5}:"
                                          f"{datetime.datetime.now().strftime('%M')} "
                                          f"пользователем @{message.from_user.username} с chad_id {message.chat.id}:\n"
                                          f"{message.text[5:]}")
    main_bot.send_message(message.chat.id, "Спасибо! Ваше сообщение передано разработчику!\n"
                                           "Приятного пользования! ❤️\n"
                                           "👇👇👇")


@main_bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обрабатывает callback-запросы от inline-кнопок.

    :param call: Объект callback-запроса от пользователя
    """
    data: str = call.data
    message = call.message

    # Настройка количества поездов у пользователя
    if data in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        main_bot.delete_message(message.chat.id, message.message_id)
        update_user_data(message.chat.id, [6], [int(data)])
        main_bot.send_message(message.chat.id, "Настройки изменены!\n"
                                               "Вызывайте меню, тыкнув сюда ➜ /menu или выбрав соответствующий пункт "
                                               "тут\n"
                                               "👇👇👇")

    # Обработка callback от уже выбранной станции
    if data.endswith("pass"):
        pass

    # Если пользователь выбрал станцию начала движения:
    elif data.startswith("start_"):
        selected_station = call.data[6:]
        update_user_data(message.chat.id, [5], [selected_station])

        draw_second_station_menu(message, selected_station)

    # Если пользователь выбрал станцию окончания маршрута
    elif data.startswith("finish_"):
        main_bot.edit_message_text("🤔", message.chat.id, message.message_id + 1)
        try:
            schedule_message = get_closest_trains(
                get_current_user(message.chat.id).get("last_selected_start_station"),
                call.data[7:],
                get_current_user(message.chat.id).get("count_trains")
            )
        except TypeError:
            schedule_message = 'Пожалуйста, нажмите кнопку "🔙 Назад" и используйте только 1 меню для управления ботом.'

        main_bot.edit_message_text(schedule_message, message.chat.id, message.message_id + 1, parse_mode="html")

    # Отправка расписания поездов при нажатии на выбранный маршрут
    elif data.startswith("favorite_"):
        main_bot.edit_message_text("🤔", message.chat.id, message.message_id + 1)
        start_station, finish_station = data[9:].split("->")
        schedule_message = get_closest_trains(
            start_station,
            finish_station,
            get_current_user(message.chat.id).get("count_trains")
        )

        main_bot.edit_message_text(schedule_message, message.chat.id, message.message_id + 1, parse_mode="html")

    # Если пользователь выбрал сохранённый путь для удаления. Отрисовка меню подтверждения
    elif data.startswith("remove_"):
        selected_trip_to_remove = call.data[7:]
        update_user_data(message.chat.id, [7], [selected_trip_to_remove])
        draw_confirm_remove_trip_menu(message)

    # Удаление маршрута из избранного и отрисовка меню удаления маршрутов
    elif data == "confirm_delete":
        remove_favorite_trip(message.chat.id, get_current_user(message.chat.id).get("selected_trip_to_remove"))

        update_user_data(message.chat.id, [7], [None])
        draw_remove_favorite_trip_menu(message)

    # Возврат в мею избранных маршрутов
    elif data == "go_to_favorite_trips_menu":
        draw_favorite_trips_menu(message)

    # Отрисовка станций для добавления избранного маршрута шаг 1
    elif data == "draw_add_favorite_trip_menu_step_one":
        draw_add_favorite_trip_menu_step_one(message)

    # Отрисовка станций для добавления избранного маршрута шаг 2
    elif data.startswith("select_"):
        selected_station = call.data[7:]
        update_user_data(message.chat.id, [5], [selected_station])

        draw_add_favorite_trip_menu_step_two(message, selected_station)

    # Добавление нового избранного маршрута в базу данных
    elif data.startswith("add_"):
        start_station = get_current_user(message.chat.id).get("last_selected_start_station")
        finish_station = data[4:]

        selected_trip = f"{start_station}->{finish_station}"

        if selected_trip not in get_favorite_trips(message.chat.id):
            add_favorite_trip(message.chat.id, f"{start_station}->{finish_station}")
            update_user_data(message.chat.id, [5], [None])

            draw_favorite_trips_menu(message)

    # Отрисовка меню выбора сохранённого пути для удаления
    elif data == "draw_remove_favorite_trip_menu":
        update_user_data(message.chat.id, [7], [None])
        draw_remove_favorite_trip_menu(message)

    # Кнопка возврата на главную страницу меню
    elif data == "back_to_first_station_menu":
        update_user_data(message.chat.id, [5], [None])
        redraw_first_station_menu(message)


def get_favorite_trips_marcup(message, add_to_callback) -> types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с избранными маршрутами.

    :param message: Объект сообщения от пользователя
    :param add_to_callback: строка для добавления к данным callback
    :return: объект InlineKeyboardMarkup
    """
    favorite_trips = get_favorite_trips(message.chat.id)

    markup = types.InlineKeyboardMarkup()
    for trip in favorite_trips:
        name = f"{station_button_names.get(trip.split('->')[0])} ➜ {station_button_names.get(trip.split('->')[1])}"
        callback = f"{add_to_callback}{'->'.join(trip.split('->'))}"
        markup.add(types.InlineKeyboardButton(name, callback_data=callback))

    return markup


def get_first_station_marcup(add_to_callback) -> types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для выбора первой станции.

    :param add_to_callback: Строка для добавления к данным callback
    :return: объект InlineKeyboardMarkup
    """
    markup = types.InlineKeyboardMarkup()

    buttons = [
        types.InlineKeyboardButton(name, callback_data=f"{add_to_callback}{callback}")
        for callback, name in station_button_names.items()
    ]

    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i + 3])

    return markup


def get_second_station_marcup(add_to_callback, selected_station: str) -> types.InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для выбора второй станции.

    :param add_to_callback: Строка для добавления к данным callback
    :param selected_station: выбранная пользователем первая станция
    :return: объект InlineKeyboardMarkup
    """
    markup = types.InlineKeyboardMarkup()

    buttons = []
    for callback, name in station_button_names.items():
        if callback == selected_station:
            name = f"✅ {name[name.index(' ') + 1:]}"
            callback = "pass"
        buttons.append(types.InlineKeyboardButton(name, callback_data=f"{add_to_callback}{callback}"))

    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i + 3])

    return markup


def send_first_station_menu(message):
    """
    Отправляет меню для выбора первой станции.

    :param message: Объект сообщения от пользователя
    """
    markup = get_first_station_marcup("start_")

    favorite_trips_menu_button = types.InlineKeyboardButton("✨ Избранные маршруты ✨",
                                                            callback_data="go_to_favorite_trips_menu")
    markup.add(favorite_trips_menu_button)

    main_bot.send_message(message.chat.id, "С какой станции планируете уехать? 🗺",
                          reply_markup=markup)


def redraw_first_station_menu(message):
    """
    Перерисовывает меню для выбора первой станции.

    :param message: Объект сообщения от пользователя
    """
    markup = get_first_station_marcup("start_")

    favorite_trips_menu_button = types.InlineKeyboardButton("✨ Избранные маршруты ✨",
                                                            callback_data="go_to_favorite_trips_menu")
    markup.add(favorite_trips_menu_button)

    main_bot.edit_message_text("С какой станции планируете уехать? 🗺", message.chat.id, message.message_id,
                               reply_markup=markup)


def draw_second_station_menu(message, selected_station: str):
    """
    Рисует меню для выбора второй станции.

    :param message: Объект сообщения от пользователя
    :param selected_station: выбранная пользователем первая станция
    """
    markup = get_second_station_marcup("finish_", selected_station)

    back_button = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_first_station_menu")
    markup.add(back_button)

    main_bot.edit_message_text("На какую станцию планируете попасть? ⛔", message.chat.id, message.message_id,
                               reply_markup=markup)


def draw_favorite_trips_menu(message):
    """
    Рисует меню избранных маршрутов.

    :param message: Объект сообщения от пользователя
    """
    markup = get_favorite_trips_marcup(message, "favorite_")

    add_favorite_trip_button = types.InlineKeyboardButton("➕ Добавить маршрут",
                                                          callback_data="draw_add_favorite_trip_menu_step_one")
    remove_favorite_trip_button = types.InlineKeyboardButton("➖ Удалить маршрут",
                                                             callback_data="draw_remove_favorite_trip_menu")

    back_button = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_first_station_menu")
    markup.row(remove_favorite_trip_button, add_favorite_trip_button)
    markup.add(back_button)

    favorite_station_message = "📝 Список ваших любимых маршрутов:"

    main_bot.edit_message_text(favorite_station_message, message.chat.id, message.message_id, reply_markup=markup)


def draw_add_favorite_trip_menu_step_one(message):
    """
    Рисует меню для добавления избранного маршрута (шаг 1).

    :param message: Объект сообщения от пользователя
    """
    markup = get_first_station_marcup("select_")
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="go_to_favorite_trips_menu"))

    main_bot.edit_message_text("Выберите начальную станцию: ", message.chat.id, message.message_id, reply_markup=markup)


def draw_add_favorite_trip_menu_step_two(message, selected_station: str):
    """
    Рисует меню для добавления избранного маршрута (шаг 2).

    :param message: Объект сообщения от пользователя
    :param selected_station: выбранная пользователем начальная станция
    """
    markup = get_second_station_marcup("add_", selected_station)
    back_button = types.InlineKeyboardButton("🔙 Назад", callback_data="draw_add_favorite_trip_menu_step_one")
    markup.add(back_button)

    main_bot.edit_message_text("Выберите конечную станцию: ", message.chat.id, message.message_id,
                               reply_markup=markup)


def draw_remove_favorite_trip_menu(message):
    """
    Рисует меню для удаления избранного маршрута.

    :param message: Объект сообщения от пользователя
    """
    markup = get_favorite_trips_marcup(message, "remove_")
    back_button = types.InlineKeyboardButton("🔙 Назад", callback_data="go_to_favorite_trips_menu")
    markup.add(back_button)

    remove_favorite_trip_message = "Выберите маршрут для удаления❌"
    main_bot.edit_message_text(remove_favorite_trip_message, message.chat.id, message.message_id, reply_markup=markup)


def draw_confirm_remove_trip_menu(message):
    """
    Рисует меню для подтверждения удаления маршрута.

    :param message: Объект сообщения от пользователя
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="confirm_delete"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="draw_remove_favorite_trip_menu"))

    trip_to_remove = get_current_user(message.chat.id).get("selected_trip_to_remove")

    confirm_remove_trip_message = ("⁉ Вы уверены, что хотите удалить этот маршрут:\n"
                                   f"{station_button_names.get(trip_to_remove.split('->')[0])} ➜ "
                                   f"{station_button_names.get(trip_to_remove.split('->')[1])}")

    main_bot.edit_message_text(confirm_remove_trip_message, message.chat.id, message.message_id, reply_markup=markup)


if __name__ == '__main__':
    if datetime.date.today().day == 1:
        update_all_links()

    if datetime.date.today().weekday() == 0:
        update_schedule_pages()
        update_schedule_json()

    main_bot.infinity_polling()
