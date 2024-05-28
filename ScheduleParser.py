from os import sep

import requests
from bs4 import BeautifulSoup
import json

names_saved_pages = ["MainPage", "Kosmonavtov_Avenue", "Uralmash", "Mashinostroiteley", "Uralskaya", "Dinamo",
                     "Square_of_1905", "Geologicheskaya", "Chkalovskaya", "Botanicheskaya"]


def save_page_html(name: str, src: str):
    """
    Функция сохраняет страницу в файл .html
    :param name: Имя файла
    :param src: html код страницы
    """
    with open(f"ScheduleDB{sep}AllPages{sep}{name}.html", "w", encoding="utf-8") as file:
        file.write(src)


def get_src_link(url: str) -> str:
    """
    Функция возвращает html код страницы по её ссылке
    :param url: Ссылка на страницу
    :return: html код страницы
    """
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/121.0.0.0Safari/537.36 OPR/107.0.0.0 (Edition Yx GX)"
    }

    req = requests.get(url, headers=headers)
    return req.text


def get_src_file(name: str) -> str:
    """
    Функция возвращает html код страницы из файла по имени
    :param name: Имя файла
    :return: html код страницы
    """
    with open(f"ScheduleDB{sep}AllPages{sep}{name}.html", "r", encoding="utf-8") as file:
        return file.read()


def update_main_page(url: str):
    """
    Функция обновляет код основной страницы
    :param url: Ссылка на главную страницу
    """
    save_page_html("MainPage", get_src_link(url))


def update_all_links():
    """
    Функция обновляет ссылки на нужные страницы в файле station_links.json
    """
    soup = BeautifulSoup(get_src_file(names_saved_pages[0]), "lxml")
    ul_element = soup.find(class_="detail_schedule")
    li_items = ul_element.find_all("li")

    links_dict = {}
    for item in li_items:
        item_text = item.text
        item_links = item.find("a")["href"]

        links_dict[item_text] = item_links

    with open(f"ScheduleDB{sep}AllPages{sep}station_links.json", "w") as file:
        json.dump(links_dict, file, indent=4, ensure_ascii=False)


def update_schedule_pages():
    """
    Функция обновляет сохранённые страницы с подробным расписанием поездов для всех станций
    """
    with open(f"ScheduleDB{sep}AllPages{sep}station_links.json") as file:
        links_dict = json.load(file)

    name_number = 1
    for name, link in links_dict.items():
        save_page_html(names_saved_pages[name_number], get_src_link(link))
        name_number += 1


def update_schedule_json():
    """
    Функция записывает расписание поездов для каждой станции в файл "ScheduleDB/schedule.json"
    """

    schedule = {}

    def update_schedule(start_station: str, day: str, way: str, train_times: list):
        """
        Функция добавляет в словарь необходимый массив с расписанием поездов
        :param start_station: Название начальной станции
        :param day: Тип дня (выходной или рабочий)
        :param way: Название конечной станции (Проспект Космонавтов или Ботаническая)
        :param train_times: Массив с временами отправления поездов со станции
        """
        if start_station not in schedule:
            schedule[start_station] = {}
        if day not in schedule[start_station]:
            schedule[start_station][day] = {}
        schedule[start_station][day][way] = train_times

    for name in names_saved_pages:

        soup = BeautifulSoup(get_src_file(name), "lxml")

        tables = soup.find_all('table', class_='uss_table_black10')

        for table in tables:
            label = table.find_previous_sibling('p').text.strip()

            day_type, direction = label.split(" дни ")[0], label.split('"')[1]

            trains = []
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all('td')

                hour = int(cells[0].text.strip())
                if hour == 0:
                    hour = 24

                minutes_str = cells[1].text.strip()
                if minutes_str[-1] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                    minutes = [int(item) for item in cells[1].text.strip().split(";")]
                else:
                    minutes = [int(item) for item in cells[1].text.strip()[:-1].split(";")]

                for minute in minutes:
                    trains.append(hour * 60 + minute)

            update_schedule(name, day_type, direction, trains)

    with open(f"ScheduleDB{sep}schedule.json", 'w', encoding='utf-8') as file:
        json.dump(schedule, file, ensure_ascii=False, indent=4)
