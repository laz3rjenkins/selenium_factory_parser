import csv
from datetime import datetime


def write_to_csv(data: list[dict], filename: str):
    if not data:
        return

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(data)
