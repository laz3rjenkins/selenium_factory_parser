import mysql.connector
import json

import utils.logger as logger
import datetime
import pytz

class DatabaseHandler:
    def __init__(self):
        #todo: вынести в .env
        config = {
            'host': '127.0.0.1',
            'user': 'lazer',
            'password': 'lazer',
            'database': 'ais_db',
            'port': 3306,
        }
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor(dictionary=True)

    def get_mappings(self, site):
        # Получаем маппинги и id характеристик
        query = "SELECT remote_key, characteristic_id, id FROM characteristic_key_mappings WHERE site = %s"
        self.cursor.execute(query, (site,))
        rows = self.cursor.fetchall()

        mappings = {r['remote_key']: r['characteristic_id'] for r in rows}
        mapping_ids = {r['remote_key']: r['id'] for r in rows}

        # Получаем все существующие характеристики для поиска по прямому ключу
        self.cursor.execute("SELECT id, `key` FROM characteristics")
        chars = {r['key']: r['id'] for r in self.cursor.fetchall()}

        return mappings, mapping_ids, chars

    def save_product(self, site, data, mappings, mapping_ids, chars):
        try:
            name = data.get('name', '').strip()
            if not name:
                return

            price = data.get('price')
            link = data.get('link')
            # В PHP коде info сохраняется как JSON, если пришло в массиве
            # В твоем словаре характеристики лежат в корне, поэтому для колонки info
            # мы можем либо оставить пустоту, либо собрать все данные
            info_json = "null" #json.dumps(data, ensure_ascii=False)

            # 1. Ищем или создаем продукт
            self.cursor.execute(
                "SELECT id, price, link, info FROM products WHERE source_site = %s AND name = %s",
                (site, name)
            )
            product = self.cursor.fetchone()
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if not product:
                # INSERT
                query = """INSERT INTO products (source_site, name, price, link, info, created_at, updated_at) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.cursor.execute(query, (site, name, price, link, info_json, now, now))
                product_id = self.cursor.lastrowid
                logger.warn(f"Создан новый товар: {name}")
            else:
                product_id = product['id']
                # UPDATE если изменились данные (имитация dirty в Laravel)
                if product['price'] != price or product['link'] != link:
                    query = """UPDATE products SET price=%s, link=%s, info=%s, updated_at=%s WHERE id=%s"""
                    self.cursor.execute(query, (price, link, info_json, now, product_id))
                    logger.warn(f"Обновлен товар: {name}")
                else:
                    logger.warn(f"Товар {name} не изменился")

            # 2. Обработка характеристик
            excluded_keys = ['name', 'price', 'availability', 'link', 'parsed_at']

            for key, value in data.items():
                val_str = str(value).strip()
                if key in excluded_keys or not val_str:
                    continue

                char_id = mappings.get(key) or chars.get(key)
                mapping_id = mapping_ids.get(key)

                if char_id:
                    # UpdateOrCreate для product_characteristic_values
                    val_query = """
                        INSERT INTO product_characteristic_values 
                        (product_id, characteristic_id, characteristic_key_mapping_id, value, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE value = VALUES(value), updated_at = VALUES(updated_at)
                    """
                    self.cursor.execute(val_query, (product_id, char_id, mapping_id, val_str, now, now))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"DB Error: {e}")