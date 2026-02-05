from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY
import logging

logger = logging.getLogger(__name__)

# Создаем клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def test_connection():
    """Проверка подключения к Supabase"""
    try:
        result = supabase.table('telegram_conversations').select("count", count='exact').limit(1).execute()
        logger.info(f"✅ Supabase подключен успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Supabase: {e}")
        return False

async def save_conversation(data: dict):
    """Сохранить данные о переписке"""
    try:
        result = supabase.table('telegram_conversations').insert(data).execute()
        return result.data
    except Exception as e:
        logger.error(f"Ошибка сохранения переписки: {e}")
        return None

async def save_daily_stats(data: dict):
    """Сохранить дневную статистику"""
    try:
        # Проверяем, есть ли уже запись за этот день для этого менеджера
        existing = supabase.table('telegram_daily_stats').select('*').eq(
            'manager_id', data['manager_id']
        ).eq('date', data['date']).execute()

        if existing.data:
            # Обновляем существующую запись
            result = supabase.table('telegram_daily_stats').update(data).eq(
                'id', existing.data[0]['id']
            ).execute()
        else:
            # Создаем новую запись
            result = supabase.table('telegram_daily_stats').insert(data).execute()

        return result.data
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")
        return None

async def get_client_history(client_telegram_id: int, manager_id: str):
    """Получить историю переписок с клиентом"""
    try:
        result = supabase.table('telegram_conversations').select('*').eq(
            'client_telegram_id', client_telegram_id
        ).eq('manager_id', manager_id).order('message_time', desc=True).execute()

        return result.data
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return []

async def is_new_client(client_telegram_id: int, manager_id: str, hours: int = 24, telegram_client=None):
    """
    Проверить, новый ли это клиент

    ПРАВИЛЬНАЯ ЛОГИКА:
    1. Проверяем реальную историю переписок в Telegram
    2. Если есть хоть одно сообщение в истории (кроме текущего) - это ПОВТОРНЫЙ клиент
    3. Если история пустая или только одно сообщение - это НОВЫЙ клиент

    Параметры:
    - client_telegram_id: ID клиента
    - manager_id: ID менеджера (не используется для Telegram, но для логов)
    - hours: не используется в новой логике
    - telegram_client: клиент Telethon для проверки истории
    """
    try:
        if not telegram_client:
            logger.warning("⚠️ Telegram client не передан, проверяем по БД")
            # Fallback на старую логику если клиент не передан
            result = supabase.table('telegram_conversations').select('id').eq(
                'client_telegram_id', client_telegram_id
            ).eq('manager_id', manager_id).limit(1).execute()
            is_new = len(result.data) == 0
        else:
            # НОВАЯ ЛОГИКА: Проверяем реальную историю в Telegram
            try:
                # Получаем последние 2 сообщения из чата с этим клиентом
                messages = await telegram_client.get_messages(client_telegram_id, limit=2)

                # Если сообщений меньше 2 (только текущее или вообще нет) - новый клиент
                # Если 2 или больше - уже была переписка, значит повторный
                is_new = len(messages) < 2

                if is_new:
                    logger.info(f"🆕 Новый клиент {client_telegram_id}: только {len(messages)} сообщение(й) в истории")
                else:
                    logger.info(f"🔄 Повторный клиент {client_telegram_id}: {len(messages)}+ сообщений в истории")

            except Exception as telegram_error:
                logger.warning(f"⚠️ Не удалось получить историю из Telegram для {client_telegram_id}: {telegram_error}")
                # Fallback на проверку по БД
                result = supabase.table('telegram_conversations').select('id').eq(
                    'client_telegram_id', client_telegram_id
                ).eq('manager_id', manager_id).limit(1).execute()
                is_new = len(result.data) == 0

        return is_new
    except Exception as e:
        logger.error(f"Ошибка проверки клиента: {e}")
        return True  # По умолчанию считаем новым

logger.info("✅ Supabase клиент инициализирован")
