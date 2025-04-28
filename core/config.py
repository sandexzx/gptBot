import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токены и ключи
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройки OpenAI
MAX_TOKENS = 5000  # Максимальное количество токенов в ответе

# Настройки бота
ADMINS = [165879072, 5237388776, 415595998]  # Список ID администраторов бота

# Словарь с моделями и их стоимостью на 1 млн токенов (в долларах)
MODELS = {
    "gpt-4.1": {"name": "gpt-4.1", "input_price": 2.00, "output_price": 8.00},
    "gpt-4.1-mini": {"name": "gpt-4.1-mini", "input_price": 0.40, "output_price": 1.60},
    "gpt-4.1-nano": {"name": "gpt-4.1-nano", "input_price": 0.10, "output_price": 0.40},
    "gpt-4o": {"name": "gpt-4o", "input_price": 2.50, "output_price": 10.00},
    "gpt-4o-mini": {"name": "gpt-4o-mini", "input_price": 0.15, "output_price": 0.60},
    "o4-mini": {"name": "o4-mini", "input_price": 1.10, "output_price": 4.40},
}

# Курс доллара к рублю
USD_TO_RUB = 107.0

# Модель по умолчанию
DEFAULT_MODEL = "gpt-4.1-nano"