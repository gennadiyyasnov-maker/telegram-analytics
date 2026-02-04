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

async def is_new_client(client_telegram_id: int, manager_id: str, hours: int = 24):
    """Проверить, новый ли это клиент (не писал более N часов)"""
    try:
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        result = supabase.table('telegram_conversations').select('*').eq(
            'client_telegram_id', client_telegram_id
        ).eq('manager_id', manager_id).gte(
            'message_time', cutoff_time.isoformat()
        ).execute()

        return len(result.data) == 0
    except Exception as e:
        logger.error(f"Ошибка проверки клиента: {e}")
        return True  # По умолчанию считаем новым

logger.info("✅ Supabase клиент инициализирован")
