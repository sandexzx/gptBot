import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токены и ключи
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройки OpenAI
OPENAI_MODEL = "gpt-4.1-nano"  # Модель, которую будем использовать
MAX_TOKENS = 5000  # Максимальное количество токенов в ответе

# Настройки бота
ADMINS = [165879072, 5237388776]  # Список ID администраторов бота