import csv

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

from parsers.base_parser import BaseParser


class TekoParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.base_url = "https://teko-com.ru/katalog/"
        self.current_page = 1
        self.limit = 100
        self.products = []

    def get_url(self):
        return f'{self.base_url}?limit={self.limit}&page={self.current_page}'

    def collect_product_data(self):
        """Сбор данных о товарах на текущей странице."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-layout"))
            )
            products = self.driver.find_elements(By.CLASS_NAME, "product-layout")
            self.driver.execute_script('$(".showatr").click()')

            for product in products:
                try:
                    product_link = product.find_element(By.CSS_SELECTOR, ".tovarszg a").get_attribute("href")
                    product_name = product.find_element(By.CLASS_NAME, "tovarszg").text.strip()

                    try:
                        product_price = product.find_element(By.CLASS_NAME, "category-price-test").text.strip()
                    except Exception:
                        product_price = "Цена не указана"

                    availability = product.find_element(By.CLASS_NAME, "pricersc").text.strip()
                    delivery_deadline = product.find_element(By.CLASS_NAME, "pricers").text.strip()
                    technical_specs = product.find_element(By.CLASS_NAME, "description_atr").text.strip()

                    self.products.append({
                        "name": product_name,
                        "price": product_price,
                        "availability": availability,
                        "delivery_deadline": delivery_deadline,
                        "technical_specs": technical_specs,
                        "link": product_link,
                    })
                except Exception as e:
                    print(f"Ошибка при обработке товара: {e}")
        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")

    def save_to_csv(self):
        """Сохранение данных в CSV."""

        filename = os.path.join("files", "teco_com", "products.csv")

        with open(filename, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=["name", "price", "availability", "delivery_deadline", "technical_specs",
                                                "link"])
            writer.writeheader()
            for product in self.products:
                writer.writerow({
                    "name": product["name"],
                    "price": product["price"],
                    "availability": product["availability"],
                    "delivery_deadline": product["delivery_deadline"],
                    "technical_specs": product['technical_specs'].replace('\n', '; '),
                    "link": product["link"],
                })

    def has_content(self):
        try:
            content = self.driver.find_element(By.ID, "osnovsoderj")

            if content:
                return True
            else:
                return False
        except selenium.common.exceptions.NoSuchElementException:
            return False

    def parse(self):
        """Основной метод парсинга."""
        self.driver.delete_all_cookies()
        while True:
            self.driver.get(self.get_url())
            time.sleep(3)

            if not self.has_content():
                break

            self.collect_product_data()
            self.current_page += 1

        self.save_to_csv()
