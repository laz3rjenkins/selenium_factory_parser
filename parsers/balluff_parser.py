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


class BalluffParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.products = []

    def get_url(self, catalog_link):
        return f"{catalog_link}?view=list&PAGEN_1={self.current_page}"

    def save_to_csv(self, filename):
        """Сохранение данных в CSV."""

        filename = os.path.join("files", "balluff_rus", f"balluff_data_{sanitize_filename(filename)}.csv")
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=["name", "price", "info", "link"],
                                    delimiter=";")
            writer.writeheader()
            for product in self.products:
                writer.writerow({
                    "name": product["name"],
                    "price": product["price"],
                    "info": product["info"].replace('\n', '; '),
                    "link": product["link"],
                })

    def is_available_element(self, find_by, value):
        try:
            element = self.driver.find_element(find_by, value)
            if element:
                return True
            return False
        except:
            return False

    def has_content(self):
        try:
            is_pagination_available = self.is_available_element(By.CLASS_NAME, "system-pagenavigation-items")

            if not is_pagination_available and self.current_page > 1:
                return False
            if not is_pagination_available and self.current_page == 1:
                return True

            active_page = self.driver.find_element(By.CLASS_NAME, "system-pagenavigation-item-active").text.strip()
            active_page = int(active_page)

            if self.current_page != active_page:
                return False

            return True
        except Exception as exception:
            print(exception)
            return False

    def collect_product_data(self):
        """Сбор данных о товарах на текущей странице."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "catalog-section-items"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "catalog-section-item")
            for product in products:
                try:
                    product_tag_a = product.find_element(By.CLASS_NAME, "catalog-section-item-name-wrapper")
                    product_link = product_tag_a.get_attribute('href').strip()
                    product_name = product_tag_a.text.strip()

                    product_info = product.find_element(By.CLASS_NAME, "props_list").text.strip()
                    product_price = product.find_element(By.CLASS_NAME, "intec-ui-part-content").text.strip()

                    self.products.append({
                        'name': product_name,
                        'link': product_link,
                        'info': product_info,
                        'price': product_price,
                    })

                except Exception as e:
                    print(f"Ошибка при обработке товара: {e}")
        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")

    def parse(self):
        catalog_links = [
            "https://balluff-rus.ru/catalog/2d_datchiki/",
            "https://balluff-rus.ru/catalog/lazernye_datchiki_rasstoyaniya/",
            "https://balluff-rus.ru/catalog/induktivnye_datchiki_rasstoyaniya/",
            "https://balluff-rus.ru/catalog/datchiki_davleniya/",
            "https://balluff-rus.ru/catalog/datchiki_temperatury/",
            "https://balluff-rus.ru/catalog/emkostnye_datchiki/",
        ]

        # self.driver.delete_all_cookies()

        for catalog_link in catalog_links:
            self.driver.get(self.get_url(catalog_link))
            time.sleep(3)
            print(f"начал парсинг по ссылке {catalog_link}")

            title = self.driver.find_element(By.ID, "pagetitle").text.strip()

            self.products = []
            self.current_page = 1
            while True:
                self.driver.get(self.get_url(catalog_link))
                time.sleep(3)

                if not self.has_content():
                    break

                self.collect_product_data()
                self.current_page += 1

            self.save_to_csv(title)
