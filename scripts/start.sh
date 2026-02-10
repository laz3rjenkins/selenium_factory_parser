#!/bin/bash

# Указываем полный путь к PM2 (замени на свой из шага 1)
PM2=/usr/local/bin/pm2

# Проверяем статус, используя полный путь
$PM2 describe selen_parser >/dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "Parser already running"
  exit 0
fi

# Переходим в директорию проекта
cd /home/selenium_factory_parser || exit 1

# Запускаем через конфиг
$PM2 start ecosystem.config.js