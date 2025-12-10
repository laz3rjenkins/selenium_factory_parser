from colorama import init, Fore, Back, Style
import datetime
import pytz

init()

def get_datetime():
    return datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime('%d-%m-%Y %H:%M:%S')

def write_to_file(text: str) -> None:
    file_name = 'logs/log.txt'

    with open(file_name, 'a', encoding='utf-8') as file:
        file.write(text + "\n\n")

def warn(text: str) -> None:
    text = f"WARNING ({get_datetime()}): {text}"
    print(Fore.YELLOW + Style.BRIGHT + text + Style.RESET_ALL)

    write_to_file(text)

def error(text: str) -> None:
    text = f"ERROR ({get_datetime()}): {text}"
    print(Fore.RED + Style.BRIGHT + text + Style.RESET_ALL)

    write_to_file(text)



# print(Fore.RED + 'Красный текст')
# print(Fore.GREEN + 'Зеленый текст')
# print(Back.YELLOW + Fore.BLUE + 'Синий текст на желтом фоне' + Style.RESET_ALL) # Сброс стиля
# print("Обычный текст снова")
