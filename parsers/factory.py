from parsers.balluff_parser import BalluffParser
from parsers.base_parser import BaseParser
from parsers.beskonta_ru_parser import BeskontaRuParser
from parsers.megak_ru_parser import MegakRuParser
from parsers.sensor_com_parser import SensorComParser
from parsers.teko_com_ru_parser import TekoParser


def get_parser(site_name: str, driver) -> BaseParser:
    parsers = {
        "sensor-com.ru": SensorComParser,
        "teko-com.ru": TekoParser,
        "mega-k.com": MegakRuParser,
        "beskonta.ru": BeskontaRuParser,
        "balluff-rus.ru": BalluffParser,
    }

    if site_name not in parsers:
        raise Exception("Нет ключа в массиве")

    return parsers[site_name](driver)
