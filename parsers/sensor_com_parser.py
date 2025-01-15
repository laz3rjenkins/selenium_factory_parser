import os
import time
import csv

import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from parsers.base_parser import BaseParser


def write_to_csv(data):
    filename = data['category_name'].replace(" ", "_") + ".csv"

    filepath = os.path.join("files\\sensor_com", filename)

    # Определяем заголовки
    headers = ['Название', 'Ссылка', 'Описание', 'Наличие', 'Цена']

    # Сохраняем данные в CSV-файл
    # encoding='utf-8'
    with open(filepath, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        # Заполняем строки из данных
        for item in data['data']:
            writer.writerow([
                item['name'],
                item['link'],
                item['info'].replace('\n', '; '),
                item['is_available'],
                item['price']
            ])
    print(f"Данные сохранены в файл: {filepath}")


class SensorComParser(BaseParser):
    def get_page_count(self):
        try:
            last_page_button = self.driver.find_element(By.XPATH, '//*[@id="pager-app"]/div/ul/li[7]/a')
            max_page = last_page_button.text.strip()
            return int(max_page)
        except selenium.common.exceptions.NoSuchElementException:
            try:
                while True:
                    show_more_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="pager-app"]/div/button'))
                    )

                    show_more_button.click()
                    print('ждемс')
                    time.sleep(4)
            except selenium.common.exceptions.ElementClickInterceptedException:
                print('ElementClickInterceptedException')
                return 1
            except selenium.common.exceptions.TimeoutException:
                print('TimeoutException')
                return 1
            except selenium.common.exceptions.NoSuchElementException:
                print('NoSuchElementException')
                return 1
            return 1

    def show_maximum_products_count(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/section[3]/div/div[2]/div[2]/div[2]/div[1]"))
        )

        self.driver.execute_script(
            '$(".nativejs-select__placeholder")[1].click();$(".nativejs-select__option")[5].click();')
        time.sleep(2)

    def accept_cookie(self):
        try:
            close_button = self.driver.find_element(By.CLASS_NAME, "jsCookieClose")
            close_button.click()
        except:
            return

    def parse(self) -> list[dict]:
        self.driver.delete_all_cookies()
        self.driver.get("https://sensor-com.ru/catalog")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/section[3]/div/div[1]/aside/div/ul"))
        )
        self.accept_cookie()

        # собираем список категорий
        categories = self.driver.find_element(By.XPATH, "/html/body/section[3]/div/div[1]/aside/div/ul")
        list_items = categories.find_elements(By.TAG_NAME, "li")

        categories_info = []
        for item in list_items:
            categories_info.append({
                'category_name': item.find_element(By.TAG_NAME, 'a').text,
                'category_link': item.find_element(By.TAG_NAME, 'a').get_attribute('href')
            })

        # TODO ВРЕМЕННОЕ РЕШЕНИЕ, ПОТОМ БРАТЬ
        categories_info.pop(1)
        categories_info.pop(1)
        categories_info.pop(1)
        categories_info.pop(1)
        categories_info.pop(1)

        # проходим по списку категорий и берем из них ссылки
        for item in categories_info:
            if not item:
                break

            product_info = {
                'category_name': item['category_name'],  # название категории
                'category_url': item['category_link'],  # ссылка на категорию
            }

            # переходим по ссылке в категорию
            self.driver.get(item['category_link'])

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "subcatalog-page__products-list"))
            )

            self.show_maximum_products_count()

            page_count = self.get_page_count()
            current_page = 1

            category_product_info = []

            # Цикл для учета пагинации
            while current_page <= page_count:
                # собираем со страницы товары и начинаем парсить все товары, которые сейчас видны на странице
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "subcatalog-page__products-list"))
                )
                time.sleep(2)
                product_boxes = self.driver.find_elements(By.CLASS_NAME, "product-box")
                for product_box in product_boxes:
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "product-box__title"))
                        )

                        title_div = product_box.find_element(By.CLASS_NAME, 'product-box__title')
                        product_box_a = title_div.find_element(By.TAG_NAME, 'a')
                        product_name = product_box_a.text.replace("\n", " ").strip()
                        product_link = product_box_a.get_attribute("href")

                        product_box_intro_div = product_box.find_element(By.CLASS_NAME, 'product-box__intro')
                        product_information_text = product_box_intro_div.text.strip()

                        try:
                            product_box_available_div = product_box.find_element(By.CLASS_NAME,
                                                                                 'product-box__available')
                            is_product_available = product_box_available_div.text.strip()
                        except Exception as exception:
                            product_box_available_div = product_box.find_element(By.CLASS_NAME,
                                                                                 'product-box__notavailable')
                            is_product_available = product_box_available_div.text.strip()

                        product_box_price_div = product_box.find_element(By.CLASS_NAME, 'product-box__price')
                        product_price = product_box_price_div.text.strip()

                        category_product_info.append({
                            'name': product_name,
                            'link': product_link,
                            'info': product_information_text,
                            'is_available': is_product_available,
                            'price': product_price,
                        })

                    except selenium.common.exceptions.NoSuchElementException as e:
                        print(127, e.msg)

                # переходим на следующую страницу
                try:
                    current_page += 1
                    pagination_input = self.driver.find_element(By.CLASS_NAME, "pagination-block__pagination-input")
                    pagination_input.clear()
                    pagination_input.send_keys(str(current_page))
                    pagination_input.send_keys(Keys.ENTER)
                    time.sleep(.5)
                except selenium.common.exceptions.TimeoutException as exc:
                    print(exc.msg)
                    print("Не удалось перейти на следущую страниццу.")
                    break
                except selenium.common.exceptions.NoSuchElementException as no_element_exception:
                    print(no_element_exception.msg)
                    print("В категории 1 страница")
                    break

            product_info['data'] = category_product_info

            write_to_csv(product_info)

        return []
