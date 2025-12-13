from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
import os

from parsers.factory import get_parser
from utils import logger


def get_driver(headless: bool = False) -> webdriver.Chrome:
    options = Options()

    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--enable-automation")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


def is_driver_alive(driver):
    if driver is None:
        return False
    try:
        driver.title
        return True
    except (InvalidSessionIdException, WebDriverException):
        return False


def ensure_driver(driver, headless=False):
    if driver is None or not is_driver_alive(driver):
        driver = get_driver(headless)
    return driver


def run():
    # todo в .env вынести названия сайтов и выбор хедлесса
    site_names = [
        "sensor-com.ru",
        "mega-k.com",
        "beskonta.ru",
        "balluff-rus.ru",
        "sensoren.ru",
        # "teko-com.ru",
    ]

    for site in site_names:
        driver = None
        try:
            driver = get_driver(headless=True)

            logger.warn(f"started parse {site}")
            parser = get_parser(site, driver)
            parser.parse()
        except Exception as exc:
            print(f"\nОшибка при парсинге {site}: {exc}")
            traceback.print_exc()
        finally:
            if driver:
                driver.quit()


if __name__ == "__main__":
    run()
