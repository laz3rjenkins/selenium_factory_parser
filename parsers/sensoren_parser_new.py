import csv
import os
import re

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

from parsers.base_parser import BaseParser
from utils import logger

NEEDED_KEYS = [
    "Размер резьбы корпуса:",
    "Размер цилиндрического корпуса, мм:",
    "Размер прямоугольного корпуса, мм:",
    "Расстояние срабатывания, мм:",
    "Функция переключения:",
    "Монтаж:",
    "Температура эксплуатации Min, °C:",
    "Температура эксплуатации Max, °C:",
    "Длина кабеля, м:",
    "Материал корпуса:",
    "Напряжение питания, В:",
    "Тип выходного сигнала:",
    "Соединение:",
]

def sanitize_filename(filename: str) -> str:
    '''
    Метод для обработки строки, чтобы создать валидный csv файл
    :param filename:
    :return:
    '''
    sanitized = re.sub(r'[\/:*?"<>|]', '_', filename)
    sanitized = sanitized.strip()
    sanitized = re.sub(r'_+', '_', sanitized)

    return sanitized

def parse_product_info(characteristics: str) -> dict:
    parts = characteristics.split(";")
    temp_dict = {}

    for i in range(0, len(parts) - 1, 2):
        key = parts[i].strip()
        value = parts[i + 1].strip()
        temp_dict[key] = value

    parsed = {key: temp_dict.get(key, "") for key in NEEDED_KEYS}

    return parsed

class SensorenNewParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.limit = 64
        self.products = []

    def get_url(self, catalog_link):
        return f"{catalog_link}?PAGEN_2={self.current_page}&show={self.limit}"

    def has_content(self):
        try:
            content = self.driver.find_element(By.CLASS_NAME, "catalog-items")

            if content:
                return True
            else:
                return False
        except selenium.common.exceptions.NoSuchElementException as exc:
            logger.warn(exc.msg)
            return False

    def open_new_tab(self):
        self.driver.execute_script("window.open('about:blank','secondtab');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(.5)

    def close_current_tab(self):
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(.2)

    def collect_product_data(self):
        """Сбор данных о товарах на текущей странице."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "catalog-items"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "catalog-element")
            product_links = []
            for product in products:
                product_tag_a = product.find_element(By.TAG_NAME, "a")
                product_link = product_tag_a.get_attribute('href').strip()
                product_links.append(product_link)

            self.open_new_tab()
            for link in product_links:
                try:
                    product_info_dict = {}
                    self.driver.get(link)
                    time.sleep(1)

                    product_title_element = self.driver.find_element(By.CLASS_NAME, "product-info-name")
                    product_name = product_title_element.text.strip()
                    product_link = link

                    try:
                        try:
                            self.driver.execute_script("window.scrollBy(0, 500);")
                            time.sleep(.3)
                        except Exception as exception:
                            logger.error(str(exception))
                        product_options = self.driver.find_element(By.CLASS_NAME, "characteristics-all")
                        product_info = product_options.text.strip()
                        product_info = product_info.replace("\n", ";")
                        product_info = parse_product_info(product_info)
                        product_info_dict = product_info
                        product_info = json.dumps(product_info, ensure_ascii=False, indent=None)
                    except Exception as e:
                        product_info = "Характеристики отсутствуют или не удалось получить"

                    product_price = ""
                    try:
                        price_block = self.driver.find_element(By.CLASS_NAME, "product-info__all-order")
                        product_price = price_block.find_element(By.CLASS_NAME, "price").text.strip()
                    except Exception as exception:
                        logger.warn(str(exception))
                        logger.warn(f"не удалось получить цену у {product_name}")


                    self.products.append({
                        'name': product_name,
                        'link': product_link,
                        # 'info': product_info,
                        'price': product_price,
                        **product_info_dict,
                    })

                    log = {
                        'name': product_name,
                        'link': product_link,
                        # 'info': product_info,
                        'price': product_price,
                        **product_info_dict,
                        'page': self.current_page
                    }

                    log_path = os.path.join(os.getcwd(), "log.txt")

                    try:
                        with open(log_path, "w", encoding="utf-8") as file:
                            json.dump(log, file, ensure_ascii=False, indent=4)
                            # file.write("\n")
                    except Exception as e:
                        logger.error(f"Ошибка при записи log.txt: {e}")

                except Exception as e:
                    logger.error(f"Ошибка при обработке товара: {e}")

            self.close_current_tab()

        except Exception as e:
            logger.error(f"Ошибка при загрузке товаров: {e}")

        logger.warn(f"Обработана страница {self.current_page}")

    def parse(self):
        catalog_links = [
            "https://sensoren.ru/catalog/datchiki-peremeshcheniy-i-rasstoyaniya/",  # 72
            "https://sensoren.ru/catalog/datchiki-fizicheskikh-velichin/",  # 181
            "https://sensoren.ru/catalog/opticheskie-datchiki-dlya-spetsialnykh-zadach/",  # 108
            "https://sensoren.ru/catalog/beskontaktnye-datchiki-polozheniya-obekta/",  # 761
            "https://sensoren.ru/catalog/promyshlennaya_bezopasnost/",  # 408
            "https://sensoren.ru/catalog/datchiki_urovnya/",  # 49 # 171
            "https://sensoren.ru/catalog/shchelevye_datchiki/",  # 21 # 44
        ]

        self.driver.delete_all_cookies()

        for catalog_link in catalog_links:
            logger.warn(f"начал парсинг по ссылке {catalog_link}")

            self.products = []
            self.current_page = 1
            title = ""
            while True:
                self.driver.get(self.get_url(catalog_link))
                time.sleep(1)

                print(f"current page {self.current_page}, catalog: {catalog_link}")
                if self.current_page == 1:
                    title = self.driver.find_element(By.CLASS_NAME, "title-block").text.strip().lower()

                if not self.has_content():
                    break

                self.collect_product_data()
                self.current_page += 1

                if self.current_page % 100 == 0:
                    self.save_to_csv(f"{self.current_page}_{title}")
                    self.products = []

            logger.warn(f"{title} has {len(self.products)} elements")
            self.save_to_csv(title)

    def save_to_csv(self, filename):
        """Сохранение данных в CSV."""

        logger.warn(f"saving to file {filename}")
        filename = os.path.join("files", "sensoren_new", f"new_sensoren_data_{sanitize_filename(filename)}.csv")
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        if not self.products:
            logger.warn("Нет данных для сохранения")
            return

        fieldnames = list(self.products[0].keys())

        with open(filename, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()

            for product in self.products:
                row = {key: product.get(key, "") for key in fieldnames}
                if "info" in row:
                    row["info"] = row["info"].replace("\n", "; ")
                writer.writerow(row)

