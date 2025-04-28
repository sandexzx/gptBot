import asyncio
from openai import AsyncOpenAI
from core.config import OPENAI_API_KEY, MAX_TOKENS, MODELS, DEFAULT_MODEL, USD_TO_RUB
from tiktoken import encoding_for_model
from typing import List, Dict, Any

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.models = MODELS
        self.user_models = {}
        self.conversations = {}  # Словарь для хранения истории диалогов по user_id
        self.system_prompts = {}  # Системные промпты для каждого пользователя
        
        # Дефолтный системный промпт
        self.default_system_prompt = (
            "Ты — полезный ассистент, который отвечает на русском языке. "
            "Твои ответы должны быть информативными и полезными."
        )
        
    def _count_tokens(self, messages, model_name):
        """
        Подсчитывает количество токенов в сообщениях
        
        Args:
            messages: Список сообщений для подсчета токенов
            model_name: Название модели для токенизации
            
        Returns:
            Количество токенов
        """
        try:
            # Попытка получить подходящую модель токенизации
            base_model = model_name.split('-')[0] + "-" + model_name.split('-')[1]
            enc = encoding_for_model(base_model)
        except KeyError:
            # Если точной модели нет, используем cl100k_base как дефолтную
            enc = encoding_for_model("gpt-4")
            
        token_count = 0
        for message in messages:
            # Учитываем токены для роли и контента
            token_count += 4  # Примерно 4 токена на структуру сообщения
            token_count += len(enc.encode(message["content"]))
        
        return token_count

    async def get_completion(self, user_id: int, prompt: str) -> tuple:
        """
        Асинхронно получает ответ от OpenAI API
        
        Args:
            prompt: Текст запроса к модели
            
        Returns:
            Кортеж (текстовый ответ от модели, токены запроса, токены ответа, стоимость запроса, стоимость ответа)
        """
        try:
            # Инициализация истории диалога для нового пользователя
            if user_id not in self.conversations:
                self.conversations[user_id] = []

            # Получаем модель для данного пользователя
            model_info = self.get_user_model(user_id)
            model_name = model_info["name"]

            # Получаем системный промпт для данного пользователя или используем дефолтный
            system_prompt = self.system_prompts.get(user_id, self.default_system_prompt)
            
            # Формируем все сообщения с системным промптом в начале
            messages = [{"role": "system", "content": system_prompt}]
            
            # Добавляем сообщение пользователя в историю
            self.conversations[user_id].append({"role": "user", "content": prompt})
            
            # Ограничиваем историю до последних 10 сообщений для экономии токенов
            if len(self.conversations[user_id]) > 20:
                self.conversations[user_id] = self.conversations[user_id][-20:]

            # Добавляем историю диалога к сообщениям
            messages.extend(self.conversations[user_id])

            # Подсчитываем токены запроса
            prompt_tokens = self._count_tokens(messages, model_name)

            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=MAX_TOKENS,
            )
            # Получаем ответ и добавляем его в историю
            assistant_response = response.choices[0].message.content.strip()
            self.conversations[user_id].append({"role": "assistant", "content": assistant_response})
            
            completion_tokens = response.usage.completion_tokens
            # Рассчитываем стоимость
            input_cost = (prompt_tokens / 1000000) * model_info["input_price"]
            output_cost = (completion_tokens / 1000000) * model_info["output_price"]
            # Рассчитываем стоимость в рублях
            input_cost_rub = input_cost * USD_TO_RUB
            output_cost_rub = output_cost * USD_TO_RUB
            total_cost_rub = input_cost_rub + output_cost_rub
            
            return assistant_response, prompt_tokens, completion_tokens, input_cost, output_cost, input_cost_rub, output_cost_rub, total_cost_rub
        except Exception as e:
            return f"Упс, что-то сломалось: {str(e)}", 0, 0, 0, 0, 0, 0, 0
        
    def reset_conversation(self, user_id: int) -> None:
        """
        Сбрасывает историю диалога для указанного пользователя
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.conversations:
            self.conversations[user_id] = []

    def set_system_prompt(self, user_id: int, prompt: str) -> None:
        """
        Устанавливает системный промпт для указанного пользователя
        
        Args:
            user_id: ID пользователя
            prompt: Системный промпт
        """
        self.system_prompts[user_id] = prompt
        
    def reset_system_prompt(self, user_id: int) -> None:
        """
        Сбрасывает системный промпт для указанного пользователя
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.system_prompts:
            del self.system_prompts[user_id]

    def get_user_model(self, user_id: int) -> Dict[str, Any]:
        """
        Получает модель, выбранную пользователем, или модель по умолчанию
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с информацией о модели
        """
        model_key = self.user_models.get(user_id, DEFAULT_MODEL)
        return self.models[model_key]

    def set_user_model(self, user_id: int, model_key: str) -> bool:
        """
        Устанавливает модель для пользователя
        
        Args:
            user_id: ID пользователя
            model_key: Ключ модели
            
        Returns:
            True, если модель успешно установлена, иначе False
        """
        if model_key in self.models:
            self.user_models[user_id] = model_key
            return True
        return False

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает словарь с доступными моделями
        
        Returns:
            Словарь с моделями
        """
        return self.models