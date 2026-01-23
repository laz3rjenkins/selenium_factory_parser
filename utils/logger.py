from colorama import init, Fore, Back, Style
import datetime
import pytz

init()

def get_datetime():
    return datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime('%d-%m-%Y %H:%M:%S')

def write_to_file(text: str) -> None:
    #todo: создавать новый файл лога при запуске
    file_name = 'logs/log.txt'

    with open(file_name, 'a', encoding='utf-8') as file:
        file.write(text + "\n\n")

def ready(site_name: str) -> None:
    file_name = 'logs/is_ready.txt'

    with open(file_name, 'a', encoding='utf-8') as file:
        file.write(site_name + f" is ready ({get_datetime()})\n\n")

def warn(text: str) -> None:
    text = f"WARNING ({get_datetime()}): {text}"
    print(Fore.YELLOW + Style.BRIGHT + text + Style.RESET_ALL)

    write_to_file(text)

def error(text: str) -> None:
    text = f"ERROR ({get_datetime()}): {text}"
    print(Fore.RED + Style.BRIGHT + text + Style.RESET_ALL)

    write_to_file(text)
