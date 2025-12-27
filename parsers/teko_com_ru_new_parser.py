import csv

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

from utils import logger
from parsers.base_parser import BaseParser

NEEDED_KEYS = [
    "Размер прямоугольного корпуса, мм",
    "Диаметр резьбового корпуса",
    "Расстояние срабатывания, мм",
    "Функция переключения",
    "Монтажное исполнение",
    "Минимальная рабочая температура, °С",
    "Максимальная рабочая температура, °С",
    "Длина кабеля, м",
    "Материал корпуса",
    "Напряжение питания, В",
    "Структура выхода",
    "Способ подключения",
]

#todo: вынести метод в utils
def parse_product_info(characteristics: str) -> dict:
    parts = characteristics.split("%;%")
    temp_dict = {}

    for i in range(0, len(parts) - 1, 2):
        key = parts[i].strip()
        value = parts[i + 1].strip()
        temp_dict[key] = value

    return {key: temp_dict.get(key, "") for key in NEEDED_KEYS}

class TekoParserNew(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.max_page_count = None
        self.products = []

    def open_next_page(self, link: str):
        self.driver.get(f"{link}?PAGEN_3={self.current_page}")

    def get_data_from_page(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "products-list_pk"))
        )
        products = self.driver.find_elements(By.CLASS_NAME, "product-item-container")
        product_links = []
        for product in products:
            try:
                product_link = product.find_element(By.CSS_SELECTOR, "a.products-slider-name")
                product_links.append(product_link.get_attribute("href").strip())
            except selenium.common.exceptions.NoSuchElementException:
                continue

        logger.warn(f"на странице обнаружено {len(product_links)} товаров")
        logger.warn(f"teco.com страница {self.current_page}")

        for link in product_links:
            self.driver.get(link)
            time.sleep(.5)
            self.collect_product_data()

    def collect_product_data(self):
        """Сбор данных о товарах на текущей странице."""
        try:
            product_link = self.driver.current_url
            product_name = self.driver.find_element(By.CLASS_NAME, "catalog-detail-name").text.strip()
            product_model = self.driver.find_element(By.CLASS_NAME, "catalog-detail-model").text.strip()
            product_name += " " + product_model
            try:
                price_block = self.driver.find_element(By.CLASS_NAME, "catalog-detail-price")
                price_div = price_block.find_element(By.TAG_NAME, "div")
                product_price = price_div.text.strip()
                product_price = "".join(char for char in product_price if char.isdigit())
            except Exception:
                product_price = ""

            availability = self.driver.find_element(By.CLASS_NAME, "catalog-detail-stock").text.strip()
            properties_div = self.driver.find_element(By.CLASS_NAME, "product-item-detail-properties")
            properties = properties_div.find_elements(By.CLASS_NAME, "one_prop")

            info = ""
            divider = ""
            for propertie in properties:
                prop_name = propertie.find_element(By.CLASS_NAME, "name").text.strip()
                prop_value = propertie.find_element(By.CLASS_NAME, "value").text.strip()

                if len(info) != 0:
                    divider = "%;%"

                info += f"{divider}{prop_name}%;%{prop_value}"

            product_info_dict = parse_product_info(info)

            self.products.append({
                "name": product_name,
                # "model": product_model,
                "price": product_price,
                "availability": availability,
                # "info": info,
                "link": product_link,
                **product_info_dict,
            })

        except Exception as e:
            logger.error(f"Ошибка при загрузке товаров: {str(e)}")

    def save_to_csv(self, page_title: str):
        """Сохранение данных в CSV."""

        filename = os.path.join("files", "teco_com", f"teco_{page_title}.csv")
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        if not self.products:
            logger.warn("Нет данных для сохранения")
            return

        fieldnames = list(self.products[0].keys())
        logger.warn(f"{page_title} has {len(self.products)} items")

        with open(filename, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()

            for product in self.products:
                row = {key: product.get(key, "") for key in fieldnames}
                if "info" in row:
                    row["info"] = row["info"].replace("\n", "; ")
                writer.writerow(row)
        logger.warn(f"file {page_title} was saved for teco_com")

    def get_max_page_count(self):
        try:
            ul = self.driver.find_element(By.CLASS_NAME, "pgn")
            lis = ul.find_elements(By.TAG_NAME, "li")

            pages_count = lis[-2].text.strip()
            if pages_count.isdigit():
                return int(pages_count)

            return 1
        except Exception as e:
            return 1

    def parse(self):
        """Основной метод парсинга."""
        self.driver.delete_all_cookies()
        catalog = [
            {'link': 'https://teko-com.ru/catalog/emkostnye-datchiki/', 'name': 'Емкостные датчики'},
            {'link': 'https://teko-com.ru/catalog/magnitochuvstvitelnye-datchiki-polozheniya/',
             'name': 'Магниточувствительные датчики положения'},
            {'link': 'https://teko-com.ru/catalog/magnitochuvstvitelnye-datchiki-urovnya/',
             'name': 'Магниточувствительные датчики уровня'},
            {'link': 'https://teko-com.ru/catalog/ultrazvukovye-datchiki/', 'name': 'Ультразвуковые датчики'},
            {'link': 'https://teko-com.ru/catalog/datchik-vlazhnosti-i-temperatury-vozdukha/',
             'name': 'Датчики влажности и температуры воздуха'},
            {'link': 'https://teko-com.ru/catalog/magnitochuvstvitelnye-datchiki-skorosti/',
             'name': 'Магниточувствительные датчики скорости'},
            {'link': 'https://teko-com.ru/catalog/datchik-diferentsialnogo-davleniya-vozdukha/',
             'name': 'Датчики дифференциального давления воздуха'},
            {'link': 'https://teko-com.ru/catalog/datchiki-uglekislogo-gaza/',
             'name': 'Датчики углекислого газа'},
            {'link': 'https://teko-com.ru/catalog/emkostno-chastotnye-datchiki/',
             'name': 'Емкостно-частотные датчики'},
            {'link': 'https://teko-com.ru/catalog/inklinometry/', 'name': 'Инклинометры'},
            {'link': 'https://teko-com.ru/catalog/lazernye-datchiki-rasstoyaniya/',
             'name': 'Лазерные датчики расстояния'},
            # {'link': 'https://teko-com.ru/catalog/radarnye-datchiki-dvizheniya/',
            #  'name': 'Радарные датчики движения'}, тут 0 товаров, не забыть обработать
            {'link': 'https://teko-com.ru/catalog/rotatsionnye-datchiki/', 'name': 'Ротационные датчики'},
            {'link': 'https://teko-com.ru/catalog/vibratsionnyy-datchiki/', 'name': 'Вибрационные датчики'},
            {'link': 'https://teko-com.ru/catalog/enkodery/', 'name': 'Энкодеры'},
            {'link': 'https://teko-com.ru/catalog/kontsevye-vyklyuchateli/', 'name': 'Концевые выключатели'},
            {'link': 'https://teko-com.ru/catalog/datchiki-temperatury/', 'name': 'Датчики температуры'},
            {'link': 'https://teko-com.ru/catalog/datchiki-davleniya/', 'name': 'Датчики давления'},
            {'link': 'https://teko-com.ru/catalog/opticheskie-datchiki/', 'name': 'Оптические датчики'},
            {'link': 'https://teko-com.ru/catalog/induktivnye-datchiki/', 'name': 'Индуктивные датчики'},
        ]

        for link in catalog:
            self.driver.get(link['link'])
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(.5)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "products-list_pk"))
            )

            self.max_page_count = self.get_max_page_count()
            self.products = []
            self.current_page = 1
            self.driver.delete_cookie("PHPSESSID")
            self.driver.delete_all_cookies()
            logger.warn(f"Начал парсинг {link['link']}")
            logger.warn(f"по ссылке {self.max_page_count} страниц")

            while True:
                try:
                    time.sleep(1)

                    if self.current_page > self.max_page_count:
                        break

                    # чистим куки каждые 25 страниц
                    if self.current_page % 25 == 0:
                        logger.warn(f"удалил все куки на странице {self.current_page}")
                        self.driver.delete_cookie("PHPSESSID")
                        self.driver.delete_all_cookies()

                    self.get_data_from_page()
                    self.current_page += 1
                    self.open_next_page(link['link'])
                except Exception as e:
                    self.driver.delete_cookie("PHPSESSID")
                    self.driver.delete_all_cookies()
                    self.current_page += 1
                    logger.error(str(e))

            link['name'] = link['name'].lower().replace(" ", "_")
            self.save_to_csv(link['name'])

        logger.warn("TECO COM succeed")
