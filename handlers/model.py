from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from core.openai_client import OpenAIClient
from core.config import USD_TO_RUB
from utils.logger import logger

# Создаем роутер для обработки сообщений
router = Router()
openai_client = OpenAIClient()

@router.message(Command("model"))
async def model_command_handler(message: Message):
    """Обработчик команды /model"""
    markup = create_model_keyboard()
    
    # Получаем текущую модель пользователя
    user_id = message.from_user.id
    current_model = openai_client.get_user_model(user_id)
    
    await message.answer(
        f"🤖 Выбери модель для общения:\n\n"
        f"Текущая модель: <b>{current_model['name']}</b>\n"
        f"Стоимость на 1000 токенов:\n"
        f"- Ввод: ${current_model['input_price']:.2f}\n"
        f"- Вывод: ${current_model['output_price']:.2f}",
        reply_markup=markup
    )
    logger.info(f"Пользователь {message.from_user.id} запросил выбор модели")

def create_model_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с доступными моделями"""
    models = openai_client.get_available_models()
    keyboard = []
    
    for key, model in models.items():
        button_text = f"{model['name']} (${model['input_price']/1000:.2f}/${model['output_price']/1000:.2f} за 1K)"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"model:{key}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data.startswith("model:"))
async def model_callback_handler(callback: CallbackQuery):
    """Обработчик выбора модели"""
    user_id = callback.from_user.id
    model_key = callback.data.split(":")[1]
    
    if openai_client.set_user_model(user_id, model_key):
        model_info = openai_client.get_user_model(user_id)
        await callback.message.edit_text(
            f"✅ Модель изменена на <b>{model_info['name']}</b>\n\n"
            f"Стоимость на 1000 токенов:\n"
            f"- Ввод: ${model_info['input_price']/1000:.4f} (₽{model_info['input_price']*USD_TO_RUB/1000:.2f})"
            f"- Вывод: ${model_info['output_price']/1000:.4f} (₽{model_info['output_price']*USD_TO_RUB/1000:.2f})"
        )
        
        # Сбрасываем историю диалога при смене модели
        openai_client.reset_conversation(user_id)
        logger.info(f"Пользователь {user_id} изменил модель на {model_key}")
    else:
        await callback.message.edit_text("❌ Ошибка при выборе модели")
        logger.error(f"Ошибка при выборе модели {model_key} для пользователя {user_id}")
    
    await callback.answer()