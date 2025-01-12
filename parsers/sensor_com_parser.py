import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from parsers.base_parser import BaseParser


class SensorComParser(BaseParser):
    def parse(self) -> list[dict]:
        self.driver.get("https://sensor-com.ru/catalog")
        products = []

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/section[3]/div/div[1]/aside/div/ul"))
        )

        categories = self.driver.find_element(By.XPATH, "/html/body/section[3]/div/div[1]/aside/div/ul")
        list_items = categories.find_elements(By.TAG_NAME, "li")

        for item in list_items:
            link = item.find_element(By.TAG_NAME, "a")
            href = link.get_attribute("href")
            text = link.text

            product_info = {
                'category_name': text,
                'category_url': href,

            }

            self.driver.get(href)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "catalog__main"))
            )

            product_boxes = self.driver.find_elements(By.CLASS_NAME, "product-box")
            product_info = []
            for product_box in product_boxes:
                try:
                    class_name_div = product_box.find_element(By.CLASS_NAME, 'product-box__title')
                    product_box_a = class_name_div.find_element(By.TAG_NAME, 'a')

                    print(f'link: {product_box_a.get_attribute("href")}, name: {product_box_a.text}')
                except selenium.common.exceptions.NoSuchElementException as e:
                    print(e.msg)


            exit(1)

        return products
