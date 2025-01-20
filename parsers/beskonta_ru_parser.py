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


def get_url(page=1, page_size=45, view_as="list"):
    return f"https://beskonta.ru/catalog/all/?pageSize={page_size}&viewAs={view_as}&p={page}"


class BeskontaRuParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.limit = 45
        self.products = []

    def has_content(self):
        current_url = self.driver.current_url

        return "p=" in current_url

    def collect_product_data(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "row-products"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "item-card")
            for product in products:
                product_tag_a = product.find_element(By.CLASS_NAME, "card-href")
                product_link = product_tag_a.get_attribute('href')
                product_name = product_tag_a.text
                product_info = product.find_element(By.CLASS_NAME, "card-characteristic").text.strip()

                product_price = product.find_element(By.CLASS_NAME, "card-price").text.strip()
                self.products.append({
                    'link': product_link,
                    'name': product_name,
                    'info': product_info,
                    'price': product_price,
                })
        except Exception as exception:
            print(exception)

    def save_to_csv(self, filename="files\\beskonta_ru\\beskonta_data.csv"):
        """Сохранение данных в CSV."""
        with open(filename, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=["name", "price", "info", "link"])
            writer.writeheader()
            for product in self.products:
                writer.writerow({
                    "name": product["name"],
                    "price": product["price"],
                    "info": product["info"].replace('\n', '; '),
                    "link": product["link"],
                })

    def parse(self):
        self.driver.delete_all_cookies()
        while True:
            self.driver.get(get_url(page_size=45, page=self.current_page))
            time.sleep(3)

            if not self.has_content():
                break

            self.collect_product_data()
            self.current_page += 1

        self.save_to_csv()
