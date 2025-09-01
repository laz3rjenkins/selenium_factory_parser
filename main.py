from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import traceback
import os

from parsers.factory import get_parser


def get_driver(headless: bool = False):
    """
       Создает экземпляр Selenium WebDriver с заданными настройками.

       :param headless: Если True, запускает Selenium в фоновом режиме (без интерфейса браузера).
       :return: Экземпляр WebDriver.
       """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--enable-automation")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def run():
    site_names = [
        "sensor-com.ru",
        "teko-com.ru",
        "mega-k.com",
        "beskonta.ru",
        "balluff-rus.ru",
        "sensoren.ru"
    ]
    driver = get_driver(True)

    for site in site_names:
        try:
            parser = get_parser(site, driver)
            parser.parse()
        except Exception as exc:
            print(f"\nОшибка при парсинге {site}: {exc}")
            traceback.print_exc()


if __name__ == "__main__":
    run()
