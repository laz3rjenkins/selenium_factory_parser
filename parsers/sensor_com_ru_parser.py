import csv
import os
import re

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from parsers.base_parser import BaseParser


class SensorComRuParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.max_page = 1
        self.products = []

    def show_maximum_products_count(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/section[3]/div/div[2]/div[2]/div[2]/div[1]"))
            )

            self.driver.execute_script(
                '$(".nativejs-select__placeholder")[1].click();$(".nativejs-select__option")[5].click();')
            time.sleep(.5)
        except Exception as e:
            return

    def calculate_max_page_count(self):
        try:
            last_page_button = self.driver.find_element(By.XPATH, '//*[@id="pager-app"]/div/ul/li[7]/a')
            max_page = last_page_button.text.strip()

            return int(max_page)
        except Exception as e:
            print(e)
            return 1

    def collect_product_data(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "subcatalog-page__products-list"))
            )
            time.sleep(.5)
            products = self.driver.find_elements(By.CLASS_NAME, "product-box")
            for product in products:
                try:

                    product_title = product.find_element(By.CLASS_NAME, "product-box__title")
                    try:
                        product_tag_a = product_title.find_element(By.TAG_NAME, "a")
                        product_name = product_tag_a.text.strip()
                        product_link = product_tag_a.get_attribute('href').strip()

                        product_information_text = product.find_element(By.CLASS_NAME,
                                                                        'product-box__intro').text.strip()
                        try:
                            product_box_available_div = product.find_element(By.CLASS_NAME,
                                                                             'product-box__available')
                            is_product_available = product_box_available_div.text.strip()
                        except Exception as exception:
                            product_box_available_div = product.find_element(By.CLASS_NAME,
                                                                             'product-box__notavailable')
                            is_product_available = product_box_available_div.text.strip()

                        product_price = product.find_element(By.CLASS_NAME, 'product-box__price').text.strip()
                    except Exception as exc:
                        continue

                    self.products.append({
                        'name': product_name,
                        'link': product_link,
                        'info': product_information_text,
                        'is_available': is_product_available,
                        'price': product_price,
                    })

                except Exception as e:
                    print(f"Ошибка при обработке товара: {e}")
        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")

    def parse(self):
        catalog_links = [
            # "https://sensor-com.ru/catalog/datchiki-pozitsionirovaniya-i-nalichiya-obyektov/induktivnyie/",
            # "https://sensor-com.ru/catalog/datchiki-pozitsionirovaniya-i-nalichiya-obyektov/opticheskie/",
            "https://sensor-com.ru/catalog/datchiki-pozitsionirovaniya-i-nalichiya-obyektov/ultrazvukovyie/",
            "https://sensor-com.ru/catalog/datchiki-pozitsionirovaniya-i-nalichiya-obyektov/emkostnyie-2/",
        ]
        self.driver.delete_all_cookies()

        for catalog_link in catalog_links:
            self.driver.get(catalog_link)
            time.sleep(3)
            print(f"начал парсинг по ссылке {catalog_link}")

            self.show_maximum_products_count()
            time.sleep(2)

            self.products = []
            self.current_page = 1
            self.max_page = self.calculate_max_page_count()
            title = self.driver.find_element(By.CLASS_NAME, "title-h1").text.strip()
            while True:
                print(f"Парсинг {self.current_page} страницы")
                self.collect_product_data()

                if self.current_page >= self.max_page:
                    break

                self.current_page += 1
                self.go_to_the_next_page()

            print(f"{title} has {len(self.products)} elements")
            self.save_to_csv(title)

    def save_to_csv(self, filename):
        """Сохранение данных в CSV."""

        filename = os.path.join("files", "sensor_com", f"sensor_com_data_{sanitize_filename(filename)}.csv")

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

    def go_to_the_next_page(self):
        pagination_input = self.driver.find_element(By.CLASS_NAME, "pagination-block__pagination-input")
        pagination_input.clear()
        pagination_input.send_keys(str(self.current_page))
        pagination_input.send_keys(Keys.ENTER)
        time.sleep(1)


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
