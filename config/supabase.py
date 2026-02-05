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

    ГИБРИДНЫЙ ПОДХОД (БД + Telegram):
    1. Проверяем таблицу telegram_client_first_seen (primary source)
    2. Если есть запись - сравниваем дату первого контакта с сегодня
    3. Если нет записи - проверяем Telegram API и создаем запись
    4. Fallback на старую логику если всё недоступно

    Параметры:
    - client_telegram_id: ID клиента
    - manager_id: ID менеджера
    - hours: не используется
    - telegram_client: клиент Telethon для проверки истории
    """
    try:
        from datetime import datetime, time

        today = datetime.now().date().isoformat()
        today_start = datetime.combine(datetime.now().date(), time.min)

        # ШАГ 1: Проверяем БД (быстро и надежно)
        first_seen = await get_first_seen(client_telegram_id, manager_id)

        if first_seen:
            # Уже есть запись в БД - это источник истины
            first_date = first_seen['first_seen_date']
            is_new = (first_date == today)

            logger.info(f"📦 БД: клиент {client_telegram_id} впервые писал {first_date}, сегодня {today} → {'НОВЫЙ' if is_new else 'ПОВТОРНЫЙ'}")
            return is_new

        # ШАГ 2: Нет в БД - первый раз видим этого клиента
        logger.info(f"🔍 Первая встреча с клиентом {client_telegram_id}, проверяем Telegram историю...")

        if not telegram_client:
            logger.warning("⚠️ Telegram client не передан, считаем новым")
            # Сохраняем в БД как нового
            await save_first_seen(client_telegram_id, manager_id, datetime.now())
            return True

        # ШАГ 3: Проверяем реальную историю в Telegram
        try:
            # Получаем последние 100 сообщений из истории (увеличили лимит)
            all_messages = await telegram_client.get_messages(client_telegram_id, limit=100)

            if len(all_messages) == 0:
                # Нет истории вообще - точно новый
                logger.info(f"🆕 Новый клиент {client_telegram_id}: история пустая")
                await save_first_seen(client_telegram_id, manager_id, datetime.now())
                return True

            # Фильтруем сообщения ДО сегодняшнего дня
            messages_before_today = [
                msg for msg in all_messages
                if msg.date.replace(tzinfo=None) < today_start
            ]

            # Определяем статус
            is_new = len(messages_before_today) == 0

            # Определяем дату первого контакта
            if is_new:
                # Все сообщения сегодняшние - первый контакт сегодня
                first_contact_time = datetime.now()
                logger.info(f"🆕 Новый клиент {client_telegram_id}: нет сообщений до {today_start}, всего: {len(all_messages)}")
            else:
                # Есть старые сообщения - первый контакт был раньше
                # Берем самое старое сообщение как дату первого контакта
                oldest_message = all_messages[-1]  # Последнее в списке = самое старое
                first_contact_time = oldest_message.date.replace(tzinfo=None)
                logger.info(f"🔄 Повторный клиент {client_telegram_id}: найдено {len(messages_before_today)} сообщений до {today_start}, первый контакт: {first_contact_time.date()}")

            # ВАЖНО: Сохраняем в БД для будущих проверок
            await save_first_seen(client_telegram_id, manager_id, first_contact_time)

            return is_new

        except Exception as telegram_error:
            logger.warning(f"⚠️ Не удалось получить историю из Telegram для {client_telegram_id}: {telegram_error}")
            # Не можем проверить - считаем новым и сохраняем
            await save_first_seen(client_telegram_id, manager_id, datetime.now())
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка проверки клиента: {e}")
        import traceback
        traceback.print_exc()
        return True  # По умолчанию считаем новым

logger.info("✅ Supabase клиент инициализирован")
