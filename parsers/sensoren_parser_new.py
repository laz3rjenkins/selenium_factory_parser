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
            content = self.driver.find_element(By.CLASS_NAME, "catalog-list")

            if content:
                return True
            else:
                return False
        except selenium.common.exceptions.NoSuchElementException as exc:
            print(exc.msg)
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
                EC.presence_of_element_located((By.CLASS_NAME, "catalog-list"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "catalog-item")
            product_links = []
            for product in products:
                product_img = product.find_element(By.CLASS_NAME, "catalog-item__img")
                product_tag_a = product_img.find_element(By.TAG_NAME, "a")

                product_link = product_tag_a.get_attribute('href').strip()

                product_links.append(product_link)

            self.open_new_tab()
            for link in product_links:
                try:
                    self.driver.get(link)
                    time.sleep(3)

                    product_title_element = self.driver.find_element(By.XPATH, "/html/body/div[5]/div[1]/h1")
                    product_link = link
                    product_name = product_title_element.text.strip()

                    try:
                        try:
                            self.driver.execute_script("window.scrollBy(0, 500);")
                            time.sleep(.3)
                        except Exception as exception:
                            print(exception)
                        product_options = self.driver.find_element(By.CLASS_NAME, "product-page__center-info-data")
                        product_info = product_options.text.strip()
                        product_info = product_info.replace("\n", ";")
                    except Exception as e:
                        product_info = "Характеристики отсутствуют или не удалось получить"

                    product_price = self.driver.find_element(By.CLASS_NAME, "product-price-count-actual").text.strip()

                    self.products.append({
                        'name': product_name,
                        'link': product_link,
                        'info': product_info,
                        'price': product_price,
                    })

                    log = {
                        'name': product_name,
                        'link': product_link,
                        'info': product_info,
                        'price': product_price,
                        'page': self.current_page
                    }

                    log_path = os.path.join(os.getcwd(), "log.txt")

                    try:
                        with open(log_path, "w", encoding="utf-8") as file:
                            json.dump(log, file, ensure_ascii=False, indent=4)
                            # file.write("\n")
                    except Exception as e:
                        print(f"Ошибка при записи log.txt: {e}")

                except Exception as e:
                    print(f"Ошибка при обработке товара: {e}")

            self.close_current_tab()

        except Exception as e:
            print(f"Ошибка при загрузке товаров: {e}")

        print(f"Обработана страница {self.current_page}")

    def parse(self):
        catalog_links = [
            "https://sensoren.ru/catalog/datchiki-peremeshcheniy-i-rasstoyaniya/",  # 72
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

                print(f"current page {self.current_page}, catalog: {catalog_link}")
                if self.current_page == 1:
                    breadcrumbs = self.driver.find_element(By.CLASS_NAME, "ajax_breadcrumbs")
                    title = breadcrumbs.find_element(By.TAG_NAME, "h1").text.strip()
                    self.set_item_limit()

                if not self.has_content():
                    break

                self.collect_product_data()
                self.current_page += 1

                if self.current_page % 100 == 0:
                    self.save_to_csv(f"{self.current_page}_{title}")
                    self.products = []

            print(f"{title} has {len(self.products)} elements")
            self.save_to_csv(title)

    def set_item_limit(self):
        select = self.driver.find_element(By.CLASS_NAME, "selectric-count_sort")
        select.click()
        time.sleep(.2)

        select.find_element(By.CLASS_NAME, "last").click()
        time.sleep(2)

    def save_to_csv(self, filename):
        """Сохранение данных в CSV."""

        filename = os.path.join("files", "sensoren_new", f"new_sensoren_data_{sanitize_filename(filename)}.csv")

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
