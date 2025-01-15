from parsers.base_parser import BaseParser
from parsers.sensor_com_parser import SensorComParser
from parsers.teko_com_ru_parser import TekoParser


def get_parser(site_name: str, driver) -> BaseParser:
    parsers = {
        "sensor-com.ru": SensorComParser,
        "teko-com.ru": TekoParser,
    }

    if site_name not in parsers:
        raise Exception("Нет ключа в массиве")

    return parsers[site_name](driver)
