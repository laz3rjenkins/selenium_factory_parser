import csv
import os
import re

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from parsers.base_parser import BaseParser


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


class SensorenParser(BaseParser):
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
            content = self.driver.find_element(By.CLASS_NAME, "catalog-list")

            if content:
                return True
            else:
                return False
        except selenium.common.exceptions.NoSuchElementException as exc:
            print(exc.msg)
            return False

    def collect_product_data(self):
        """Сбор данных о товарах на текущей странице."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "catalog-list"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "catalog-item")
            for product in products:
                try:
                    product_title_element = product.find_element(By.CLASS_NAME, "catalog-item__title")
                    product_tag_a = product_title_element.find_element(By.TAG_NAME, "a")
                    product_link = product_tag_a.get_attribute('href').strip()
                    product_name = product_tag_a.text.strip()

                    try:
                        product_options = product.find_element(By.CLASS_NAME, "catalog-item__options")
                        product_info = product_options.text.strip()
                    except Exception as e:
                        product_info = "Характеристики отсутствуют или не удалось получить"

                    product_price = product.find_element(By.CLASS_NAME, "catalog-item__price").text.strip()

                    is_available = product.find_element(By.CLASS_NAME, "catalog-item__status").text.strip()

                    self.products.append({
                        'name': product_name,
                        'link': product_link,
                        'info': product_info,
                        'price': product_price,
                        'is_available': is_available,
                    })



                except Exception as e:
                    print(f"Ошибка при обработке товара: {e}")
        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")

        print(f"Обработана страница {self.current_page}")

    def parse(self):
        catalog_links = [
            "https://sensoren.ru/catalog/datchiki-peremeshcheniy-i-rasstoyaniya/", # 72
            "https://sensoren.ru/catalog/datchiki-fizicheskikh-velichin/",  # 181
            "https://sensoren.ru/catalog/opticheskie-datchiki-dlya-spetsialnykh-zadach/",  # 108
            "https://sensoren.ru/catalog/beskontaktnye-datchiki-polozheniya-obekta/",  # 761
            "https://sensoren.ru/catalog/promyshlennaya_bezopasnost/",  # 408
            "https://sensoren.ru/catalog/datchiki_urovnya/",  # 49
            "https://sensoren.ru/catalog/shchelevye_datchiki/",  # 21
        ]

        self.driver.delete_all_cookies()

        for catalog_link in catalog_links:
            print(f"начал парсинг по ссылке {catalog_link}")

            self.products = []
            self.current_page = 1
            title = "title stub"
            while True:
                self.driver.get(self.get_url(catalog_link))
                time.sleep(3)

                if self.current_page == 1:
                    breadcrumbs = self.driver.find_element(By.CLASS_NAME, "ajax_breadcrumbs")
                    title = breadcrumbs.find_element(By.TAG_NAME, "h1").text.strip()
                    self.set_item_limit()

                if not self.has_content():
                    break

                self.collect_product_data()
                self.current_page += 1

            print(f"{title} has {len(self.products)} elements")
            self.save_to_csv(title)

    def set_item_limit(self):
        select = self.driver.find_element(By.CLASS_NAME, "selectric-count_sort")
        select.click()
        time.sleep(.2)

        select.find_element(By.CLASS_NAME, "last").click()
        time.sleep(1)

    def save_to_csv(self, filename):
        """Сохранение данных в CSV."""

        filename = f"files\\sensoren\\sensoren_data_{sanitize_filename(filename)}.csv"

        with open(filename, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=["name", "price", "info", "link", "is_available"])
            writer.writeheader()
            for product in self.products:
                writer.writerow({
                    "name": product["name"],
                    "price": product["price"],
                    "info": product["info"].replace('\n', '; '),
                    "link": product["link"],
                    "is_available": product["is_available"],
                })
