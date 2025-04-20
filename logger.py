import logging
from logging.handlers import RotatingFileHandler

# Настройка логгера
logger = logging.getLogger("event_logger")
logger.setLevel(logging.INFO)

# Обработчик с ротацией логов
handler = RotatingFileHandler("event.log", maxBytes=5_000_000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
