import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.openai_client import OpenAIClient
from utils.logger import logger

# Создаем роутер для обработки сообщений
router = Router()
openai_client = OpenAIClient()

# Определяем состояния для FSM (машина состояний)
class SystemPromptStates(StatesGroup):
    waiting_for_prompt = State()

@router.message(Command("start"))
async def start_handler(message: Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name
    await message.answer(
        f"Йоу, {user_name}! 🤖\n\n"
        "Я твой бот с интеграцией GPT-4.1-nano. Просто отправь мне сообщение, "
        "и я перешлю его в нейронку для обработки!\n\n"
        "Чтобы очистить историю, используй /reset"
        "Для установки системного промпта используй /system\n"
        "Для сброса системного промпта используй /reset_system"
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

@router.message(Command("reset"))
async def reset_handler(message: Message):
    """Обработчик команды /reset (можно добавить сброс контекста, если нужно)"""
    user_id = message.from_user.id
    openai_client.reset_conversation(user_id)
    await message.answer("История сброшена! Начинаем с чистого листа 🧠")
    logger.info(f"Пользователь {message.from_user.id} сбросил историю")

@router.message(Command("system"))
async def system_prompt_handler(message: Message, state: FSMContext):
    """Обработчик команды /system для установки системного промпта"""
    await message.answer(
        "Отправь мне системный промпт, который будет использоваться для OpenAI.\n\n"
        "Например: 'Ты — эксперт по Python, который всегда отвечает кодом'"
    )
    await state.set_state(SystemPromptStates.waiting_for_prompt)
    logger.info(f"Пользователь {message.from_user.id} запросил установку системного промпта")

@router.message(SystemPromptStates.waiting_for_prompt)
async def process_system_prompt(message: Message, state: FSMContext):
    """Обработчик для сохранения системного промпта"""
    user_id = message.from_user.id
    system_prompt = message.text
    
    # Устанавливаем системный промпт
    openai_client.set_system_prompt(user_id, system_prompt)
    
    # Сбрасываем историю диалога, чтобы новый системный промпт применился сразу
    openai_client.reset_conversation(user_id)
    
    await message.answer(
        "✅ Системный промпт установлен! История диалога сброшена.\n\n"
        f"Установленный промпт: <i>{system_prompt}</i>"
    )
    
    # Сбрасываем состояние FSM
    await state.clear()
    logger.info(f"Пользователь {message.from_user.id} установил новый системный промпт")

@router.message(Command("reset_system"))
async def reset_system_prompt_handler(message: Message):
    """Обработчик команды /reset_system для сброса системного промпта"""
    user_id = message.from_user.id
    openai_client.reset_system_prompt(user_id)
    openai_client.reset_conversation(user_id)
    
    await message.answer(
        "✅ Системный промпт сброшен до значения по умолчанию! История диалога также сброшена."
    )
    logger.info(f"Пользователь {message.from_user.id} сбросил системный промпт")

@router.message(F.text)
async def process_message(message: Message):
    """Обработчик всех текстовых сообщений"""
    user_id = message.from_user.id
    user_message = message.text
    
    # Отправляем индикатор набора текста
    await message.bot.send_chat_action(chat_id=user_id, action="typing")
    
    logger.info(f"Получен запрос от пользователя {user_id}: {user_message[:20]}...")
    
    # Получаем ответ от OpenAI
    response, prompt_tokens, completion_tokens = await openai_client.get_completion(user_id, user_message)
    
    # Добавляем информацию о токенах
    token_info = f"\n\n📊 Токены: отправлено {prompt_tokens}, получено {completion_tokens}, всего {prompt_tokens + completion_tokens}"
    response_with_tokens = response + token_info
    
    # Обрабатываем длинные ответы (если они превышают лимит Telegram в 4096 символов)
    if len(response_with_tokens) <= 4000:
        await message.answer(response_with_tokens)
    else:
        # Разбиваем ответ на части без информации о токенах
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for i, part in enumerate(parts):
            if i > 0:
                # Небольшая задержка между отправкой частей
                await asyncio.sleep(0.5)
            
            # Добавляем информацию о токенах только к последней части
            part_text = part
            if i == len(parts) - 1:
                part_text += token_info
                
            await message.answer(f"{part_text}\n\n[Часть {i+1}/{len(parts)}]")
    
    logger.info(f"Отправлен ответ пользователю {user_id}")