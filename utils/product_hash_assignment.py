import asyncio
import httpx
import utils.logger as logger
from bs4 import BeautifulSoup
import hashlib

# PRODUCT_INFO_SELECTOR = ".product-info-name, .characteristics-all, .product-info__all-order"
PRODUCT_INFO_SELECTOR = ".product, .product-tab-items"

async def check_for_update_by_hash(link: str, cached_hash: str | None) -> str | None:
    """
    Отправляет GET-запрос, извлекает полезную нагрузку и возвращает
    новый хеш, если данные изменились.
    Возвращает None, если хеши совпадают.
    """
    semaphore = asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        async with semaphore:
            try:
                response = await http_client.get(link)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                target_content = ""
                for selector in PRODUCT_INFO_SELECTOR.split(', '):
                    element = soup.select_one(selector)
                    if element:
                        target_content += element.prettify()

                if not target_content:
                    logger.error(f"Не удалось найти целевой контент по селекторам для {link}")
                    return None

                normalized_content = "".join(target_content.split())
                new_hash = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()

                print(new_hash)

                if cached_hash and new_hash == cached_hash:
                    logger.warn(f"Хеш совпадает: {link}")
                    return None  # Нет изменений

                logger.warn(f"Хеш изменился или новый товар: {link}")
                return new_hash

            except httpx.RequestError as e:
                logger.error(f"Ошибка запроса {link}: {e}")
                return None

if __name__ == "__main__":
    # OLD_HASH = "fce3ad98b143b57cb7e6b6577c4b8b248059026f0666ed1e62dacf1c8c336a6a"
    OLD_HASH = "bbc35c6622ae965a2631fbeb7a6237ecbc2b3be1867d7f4c75d0574b1a125fa6"
    asyncio.run(check_for_update_by_hash("https://sensoren.ru/product/opticheskiy_datchik_rasstoyaniya_ifm_electronic_o1d100/", OLD_HASH))
