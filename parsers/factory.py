# from parsers.sensor_com_parser import SensorComParser
# from parsers.teko_com_parser import TekoComParser
from parsers.base_parser import BaseParser
from parsers.sensor_com_parser import SensorComParser


def get_parser(site_name: str, driver) -> BaseParser:
    parsers = {
        "sensor-com.ru": SensorComParser,
        # "teko-com.ru": TekoComParser,
    }

    if site_name not in parsers:
        raise Exception("Нет ключа в массиве")

    return parsers[site_name](driver)
