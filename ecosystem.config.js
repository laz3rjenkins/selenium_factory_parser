module.exports = {
  apps: [
    {
      name: "selen_parser",
      script: "main.py",
      interpreter: "/home/selenium_factory_parser/venv/bin/python",
      cwd: "/home/selenium_factory_parser",
      watch: false,
      autorestart: false,
      max_restarts: 10,
      env: {
        PYTHONUNBUFFERED: "1",
        DISPLAY: "",
        QT_QPA_PLATFORM: "offscreen"
      }
    }
  ]
}
