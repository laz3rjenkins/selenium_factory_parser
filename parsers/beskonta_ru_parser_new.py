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


class BeskontaRuNewParser(BaseParser):
    def __init__(self, driver: webdriver.Chrome):
        super().__init__(driver)

        self.driver = driver
        self.current_page = 1
        self.limit = 45
        self.products = []

    def has_content(self):
        current_url = self.driver.current_url

        return "p=" in current_url

    def open_new_tab(self):
        self.driver.execute_script("window.open('about:blank','secondtab');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(.5)

    def close_current_tab(self):
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(.2)

    def collect_product_data(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "row-products"))
            )

            products = self.driver.find_elements(By.CLASS_NAME, "item-card")
            product_links = []
            for product in products:
                product_tag_a = product.find_element(By.CLASS_NAME, "card-href")
                product_link = product_tag_a.get_attribute('href').strip()

                product_links.append(product_link)

            self.open_new_tab()
            for link in product_links:
                try:
                    self.driver.get(link)
                    time.sleep(3)

                    item_container = self.driver.find_element(By.CLASS_NAME, "p-p-info")

                    product_link = link
                    product_name = item_container.find_element(By.TAG_NAME, "h1").text.strip()
                    specs_with_separator = ""
                    try:
                        self.driver.find_element(By.CLASS_NAME, "to-all-characteristic").click()
                        time.sleep(.2)

                        tabs_content = self.driver.find_element(By.CLASS_NAME, "p-p-tabs-content")
                        table_mini = tabs_content.find_elements(By.CLASS_NAME, "p-p-table-mini-h")

                        index = 1
                        for table_mini_item in table_mini:
                            if index == 1:
                                specs = table_mini_item.find_elements(By.CLASS_NAME, "tab-content_table_character-text")
                            elif index > 2:
                                break
                            else:
                                specs = table_mini_item.find_elements(By.TAG_NAME, "td")

                            index2 = 1
                            for spec in specs:
                                if index2 == 1 and index == 2:
                                    index2 += 1
                                    continue
                                if spec.text.strip().replace("\n", "") == "":
                                    continue
                                specs_with_separator += spec.text.strip().replace("\n", ";") + ";"

                            index += 1

                    except Exception as price_exc:
                        print(price_exc)

                    product_price = self.driver.find_element(By.CLASS_NAME, "p-p-price").text.strip()
                    self.products.append({
                        'link': product_link,
                        'name': product_name,
                        'info': specs_with_separator,
                        'price': product_price,
                    })

                    print({
                        'link': product_link,
                        'name': product_name,
                        'info': specs_with_separator,
                        'price': product_price,
                    })

                except Exception as exc:
                    print(f"Ошибка при обработке товара: {e}")

            self.close_current_tab()
        except Exception as exception:
            print(exception)

    def save_to_csv(self, filename="files\\beskonta_ru_new\\beskonta_data.csv"):
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
            print(f"current page: {self.current_page}")
            self.driver.get(get_url(page_size=45, page=self.current_page))
            time.sleep(3)

            if not self.has_content():
                break

            self.collect_product_data()
            self.current_page += 1

        self.save_to_csv()
