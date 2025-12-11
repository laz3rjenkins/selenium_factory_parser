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
from utils import logger


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


class MegakRuNewParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.limit = 100
        self.products = []

    def get_subcategories_links(self):
        subcategories = self.driver.find_elements(By.CLASS_NAME, "product-categories-item-slim")

        subcategory_info = []
        for subcategory in subcategories:
            tag_a = subcategory.find_element(By.TAG_NAME, "a")
            href = tag_a.get_attribute('href').strip()
            category_name = tag_a.text.lower().strip()

            subcategory_info.append({
                "name": category_name,
                "link": href
            })

        return subcategory_info

    def get_second_lvl_category_links(self, subcategory):
        self.driver.get(subcategory['link'])
        time.sleep(3)

        second_lvl_categories_links = self.get_subcategories_links()

        return second_lvl_categories_links

    def has_content(self):
        try:
            content = self.driver.find_element(By.CLASS_NAME, "products-view-block")

            if content:
                return True
            else:
                return False
        except selenium.common.exceptions.NoSuchElementException:
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
                EC.presence_of_element_located((By.CLASS_NAME, "products-view"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "products-view-block")
            product_links = []
            for product in products:
                product_name_tag = product.find_element(By.CLASS_NAME, "products-view-name-link")
                product_link = product_name_tag.get_attribute('href').strip()

                product_links.append(product_link)

            self.open_new_tab()
            for link in product_links:
                try:
                    self.driver.get(link)
                    time.sleep(3)

                    product_name = self.driver.find_element(By.CLASS_NAME, "page-title").text.strip()
                    description = self.driver.find_element(By.CLASS_NAME, "details-tabs-deacription").text.strip()

                    try:
                        self.driver.execute_script("window.scrollBy(0, 500);")
                        time.sleep(.2)
                        self.driver.find_element(By.ID, 'tabOptions').click()
                        time.sleep(.3)
                    except Exception as exception:
                        logger.error(str(exception))

                    specs = self.driver.find_elements(By.CLASS_NAME, "properties-item")
                    specs_with_separator = ""
                    for spec in specs:
                        specs_with_separator += spec.text.strip() + ";"

                    product_price = self.driver.find_element(By.CLASS_NAME, "price").text.strip()

                    self.products.append({
                        "name": product_name,
                        "price": product_price,
                        "description": description,
                        "info": specs_with_separator,
                        "link": link,
                    })

                except Exception as e:
                    logger.error(str(f"Ошибка при обработке товара: {e}"))

            self.close_current_tab()

        except Exception as e:
            logger.error(str(f"Ошибка при загрузке товаров: {e}"))

    def get_data_from_category(self, category_info):
        self.current_page = 1
        self.products = []
        while True:
            self.driver.get(f"{category_info['link']}?page={self.current_page}")
            time.sleep(3)

            if not self.has_content():
                break

            self.collect_product_data()
            self.current_page += 1

    def parse(self):
        """Основной метод парсинга."""
        self.driver.delete_all_cookies()

        sensor_links = [
            {
                'link': "https://mega-k.com/categories/datchiki-polozheniya",
                'name': "Датчики положения",
            }, {
                'link': "https://mega-k.com/categories/datchiki-proportsionalnye",
                'name': "Датчики пропорциональные",
            },
            {
                'link': "https://mega-k.com/categories/datchiki-chastoty",
                'name': "Датчики частоты",
            },
        ]

        for link in sensor_links:
            self.driver.get(link['link'])
            time.sleep(3)
            logger.warn(f"started parse {link['link']}")

            subcategories_links = self.get_subcategories_links()
            filename = ""
            for subcategory in subcategories_links:
                try:
                    second_lvl_categories = self.get_second_lvl_category_links(subcategory)

                    if len(second_lvl_categories) == 0:
                        logger.warn(f"В подкатегории {subcategory['name']} нет дополнительных категорий, начинаю парсить")
                        self.get_data_from_category(subcategory)
                        filename = sanitize_filename(f"{link['name']}_{subcategory['name']}.csv")
                        logger.warn(f"Загрузка данных в файл {filename}")
                        save_to_csv(self.products, filename)
                    else:
                        for second_subcategory in second_lvl_categories:
                            logger.warn(f"Парсинг подкатегории {second_subcategory['name']}")
                            filename = sanitize_filename(
                                f"{link['name']}_{second_subcategory['name']} ({subcategory['name']}).csv".replace(" ",
                                                                                                                   "_"))
                            self.get_data_from_category(second_subcategory)
                            logger.warn(f"Загрузка данных в файл {filename}")
                            save_to_csv(self.products, filename)
                except Exception as e:
                    logger.error(f"Не удалось получить данные из {subcategory['link']}: {str(e)}")


def save_to_csv(data, filename):
    filename = filename.replace(" ", "_")

    filepath = os.path.join("files", "megak_ru_new", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file,
                                fieldnames=['name', 'price', 'description', 'info', 'link'],
                                delimiter=";")
        writer.writeheader()
        for item in data:
            writer.writerow({
                "name": item['name'],
                "price": item['price'],
                "description": item['description'],
                "info": item['info'].replace('\n', '; '),
                "link": item['link'],
            })
    logger.warn(f"Данные сохранены в файл: {filepath}")
