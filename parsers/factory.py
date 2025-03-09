from parsers.balluff_parser import BalluffParser
from parsers.base_parser import BaseParser
from parsers.beskonta_ru_parser_new import BeskontaRuNewParser
from parsers.megak_ru_parser_new import MegakRuNewParser
from parsers.sensor_com_ru_parser import SensorComRuParser
from parsers.sensoren_parser_new import SensorenNewParser
from parsers.teko_com_ru_parser import TekoParser


def get_parser(site_name: str, driver) -> BaseParser:
    parsers = {
        "sensor-com.ru": SensorComRuParser,
        "teko-com.ru": TekoParser,
        "mega-k.com": MegakRuNewParser,
        "beskonta.ru": BeskontaRuNewParser,
        "balluff-rus.ru": BalluffParser,
        "sensoren.ru": SensorenNewParser,
    }

    if site_name not in parsers:
        raise Exception("Нет ключа в массиве")

    return parsers[site_name](driver)
