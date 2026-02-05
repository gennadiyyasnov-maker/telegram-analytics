import logging
from datetime import datetime
from typing import Optional, Dict
from config.supabase import save_conversation, is_new_client, get_client_history
from config.settings import NEW_CLIENT_HOURS

logger = logging.getLogger(__name__)

class MessageAnalyzer:
    """Анализатор входящих и исходящих сообщений"""

    def __init__(self, manager_id: str, manager_name: str, telegram_client):
        self.manager_id = manager_id
        self.manager_name = manager_name
        self.telegram_client = telegram_client
        self.response_times = {}  # client_id -> last_client_message_time

    async def analyze_incoming_message(self, event):
        """Анализ входящего сообщения от клиента"""
        try:
            client_id = event.sender_id
            message_time = datetime.now()

            # Определяем, новый ли это клиент (проверяем реальную историю в Telegram)
            is_new = await is_new_client(client_id, self.manager_id, NEW_CLIENT_HOURS, self.telegram_client)

            # Получаем историю для определения источника
            history = await get_client_history(client_id, self.manager_id)
            channel_source = await self._detect_channel_source(event, history)

            # Сохраняем время сообщения для расчета времени ответа
            self.response_times[client_id] = message_time

            # Сохраняем в базу
            data = {
                'manager_id': self.manager_id,
                'manager_name': self.manager_name,
                'client_telegram_id': client_id,
                'message_time': message_time.isoformat(),
                'message_type': 'incoming',
                'is_new_client': is_new,
                'channel_source': channel_source,
                'message_text': event.message.text[:200] if event.message and event.message.text else None
            }

            await save_conversation(data)

            logger.info(f"📩 [{self.manager_name}] Входящее от клиента {client_id} (новый: {is_new})")

        except Exception as e:
            logger.error(f"Ошибка анализа входящего сообщения: {e}")

    async def analyze_outgoing_message(self, event):
        """Анализ исходящего сообщения менеджера"""
        try:
            # Получаем ID клиента из чата
            if event.is_private:
                client_id = event.chat_id
            else:
                return  # Игнорируем групповые чаты

            message_time = datetime.now()

            # Получаем последнее входящее сообщение от этого клиента
            # чтобы узнать был ли он новым
            history = await get_client_history(client_id, self.manager_id)
            is_new_for_stats = False

            # Ищем последнее входящее сообщение
            for msg in history:
                if msg.get('message_type') == 'incoming':
                    is_new_for_stats = msg.get('is_new_client', False)
                    break

            # Рассчитываем время ответа
            response_time_minutes = None
            if client_id in self.response_times:
                delta = message_time - self.response_times[client_id]
                response_time_minutes = delta.total_seconds() / 60
                del self.response_times[client_id]  # Убираем из очереди

            # Сохраняем в базу
            data = {
                'manager_id': self.manager_id,
                'manager_name': self.manager_name,
                'client_telegram_id': client_id,
                'message_time': message_time.isoformat(),
                'message_type': 'outgoing',
                'is_new_client': is_new_for_stats,  # Берем из последнего входящего
                'response_time_minutes': response_time_minutes,
                'message_text': event.message.text[:200] if event.message and event.message.text else None
            }

            await save_conversation(data)

            response_info = f"{response_time_minutes:.1f} мин" if response_time_minutes else "нет данных"
            client_type = "новый" if is_new_for_stats else "повторный"
            logger.info(f"📤 [{self.manager_name}] Исходящее клиенту {client_id} ({client_type}, время ответа: {response_info})")

        except Exception as e:
            logger.error(f"Ошибка анализа исходящего сообщения: {e}")

    async def _detect_channel_source(self, event, history: list) -> Optional[str]:
        """Определить источник клиента (канал)"""
        try:
            # Метод 1: Проверяем текст первого сообщения на упоминание канала
            if event.message and event.message.text:
                text = event.message.text.lower()
                # Ищем упоминания каналов (@channel_name)
                import re
                channels = re.findall(r'@(\w+)', text)
                if channels:
                    return channels[0]

            # Метод 2: Проверяем историю (если уже есть записи)
            if history and len(history) > 0:
                return history[0].get('channel_source')

            # Метод 3: Можно расширить - проверять общие группы/каналы с клиентом
            # Это требует дополнительных API вызовов

            return 'unknown'

        except Exception as e:
            logger.error(f"Ошибка определения канала: {e}")
            return 'unknown'
