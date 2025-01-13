from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from parsers.factory import get_parser


def get_driver(headless: bool = False):
    """
       Создает экземпляр Selenium WebDriver с заданными настройками.

       :param headless: Если True, запускает Selenium в фоновом режиме (без интерфейса браузера).
       :return: Экземпляр WebDriver.
       """
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def run():
    site_names = [
        "sensor-com.ru",
        # "https://teko-com.ru",
        # "https://mega-k.com",
        # "https://beskonta.ru",
        # "https://balluff-rus.ru",
        # "https://sensoren.ru"
    ]
    driver = get_driver(False)

    parser = get_parser(site_names[0], driver)

    parser.parse()


if __name__ == "__main__":
    run()
