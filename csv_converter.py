import pandas as pd
from pathlib import Path

input_folder = "files\\megak_ru_new"
output_folder = "files\\megak_ru_new_converted"

Path(output_folder).mkdir(exist_ok=True)

for file in Path(input_folder).glob("*.csv"):
    try:
        df = pd.read_csv(file, encoding="windows-1251", delimiter=",")
        df.to_csv(Path(output_folder) / file.name, index=False, encoding="UTF-8", sep=";")
        print(f"✔ Конвертирован: {file.name}")
    except Exception as e:
        print(f"❌ Ошибка в {file.name}: {e}")
