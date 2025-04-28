import logging
import sys

def setup_logger():
    # Настраиваем логгер
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Обработчик для вывода в консоль
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Форматируем вывод логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Добавляем обработчик к логгеру
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()