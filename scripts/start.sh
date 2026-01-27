#!/bin/bash

pm2 describe selen_parser >/dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "Parser already running"
  exit 0
fi

cd /home/selenium_factory_parser || exit 1

pm2 start ecosystem.config.js
