module.exports = {
  apps: [
    {
      name: "selen_parser",
      script: "main.py",
      interpreter: "python3",
      cwd: "/home/selenium_factory_parser",
      watch: false,
      autorestart: true,
      max_restarts: 10,
      env: {
        PYTHONUNBUFFERED: "1",
        DISPLAY: "",
        QT_QPA_PLATFORM: "offscreen"
      }
    }
  ]
}
