from abc import ABC, abstractmethod
from selenium import webdriver


class BaseParser(ABC):
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    @abstractmethod
    def parse(self) -> list[dict]:
        """
        Метод, который должен реализовать каждый парсер.
        Возвращает список словарей с данными.
        """
        pass

    def close(self):
        self.driver.quit()
