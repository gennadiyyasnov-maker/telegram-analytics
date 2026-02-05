import logging
from datetime import datetime, date, timedelta
from typing import Dict, List
from config.supabase import supabase, save_daily_stats

logger = logging.getLogger(__name__)

class StatisticsCalculator:
    """Расчет статистики по переписках"""

    @staticmethod
    async def calculate_daily_stats(manager_id: str, target_date: date = None) -> Dict:
        """Рассчитать статистику за день для менеджера"""
        try:
            if target_date is None:
                target_date = date.today()

            # Получаем все переписки за день
            start_time = datetime.combine(target_date, datetime.min.time()).isoformat()
            end_time = datetime.combine(target_date, datetime.max.time()).isoformat()

            result = supabase.table('telegram_conversations').select('*').eq(
                'manager_id', manager_id
            ).gte('message_time', start_time).lte('message_time', end_time).execute()

            conversations = result.data

            if not conversations:
                return {
                    'manager_id': manager_id,
                    'date': target_date.isoformat(),
                    'new_clients': 0,
                    'returning_clients': 0,
                    'total_conversations': 0,
                    'messages_sent': 0,
                    'messages_received': 0,
                    'avg_response_time_minutes': None
                }

            # Подсчет метрик
            new_clients = set()
            returning_clients = set()
            messages_sent = 0
            messages_received = 0
            response_times = []

            for conv in conversations:
                client_id = conv['client_telegram_id']

                # Определяем новых/повторных клиентов
                if conv.get('is_new_client'):
                    new_clients.add(client_id)
                else:
                    returning_clients.add(client_id)

                # Считаем сообщения
                if conv['message_type'] == 'outgoing':
                    messages_sent += 1

                    # Собираем время ответа
                    if conv.get('response_time_minutes'):
                        response_times.append(conv['response_time_minutes'])
                else:
                    messages_received += 1

            # Рассчитываем среднее время ответа
            avg_response_time = None
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)

            stats = {
                'manager_id': manager_id,
                'date': target_date.isoformat(),
                'new_clients': len(new_clients),
                'returning_clients': len(returning_clients),
                'total_conversations': len(new_clients) + len(returning_clients),
                'messages_sent': messages_sent,
                'messages_received': messages_received,
                'avg_response_time_minutes': round(avg_response_time, 1) if avg_response_time else None
            }

            # Сохраняем в базу
            await save_daily_stats(stats)

            logger.info(f"📊 Статистика за {target_date} для {manager_id}: "
                       f"новых={stats['new_clients']}, повторных={stats['returning_clients']}")

            return stats

        except Exception as e:
            logger.error(f"Ошибка расчета статистики: {e}")
            return {}

    @staticmethod
    async def calculate_weekly_stats(manager_id: str) -> Dict:
        """Рассчитать статистику за неделю"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            result = supabase.table('telegram_daily_stats').select('*').eq(
                'manager_id', manager_id
            ).gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).execute()

            daily_stats = result.data

            if not daily_stats:
                return {}

            # Агрегируем данные
            total_new = sum(s.get('new_clients', 0) for s in daily_stats)
            total_returning = sum(s.get('returning_clients', 0) for s in daily_stats)
            total_messages_sent = sum(s.get('messages_sent', 0) for s in daily_stats)
            total_messages_received = sum(s.get('messages_received', 0) for s in daily_stats)

            # Среднее время ответа
            response_times = [s.get('avg_response_time_minutes') for s in daily_stats
                            if s.get('avg_response_time_minutes') is not None]
            avg_response = sum(response_times) / len(response_times) if response_times else None

            return {
                'manager_id': manager_id,
                'period': f"{start_date} - {end_date}",
                'total_new_clients': total_new,
                'total_returning_clients': total_returning,
                'total_messages_sent': total_messages_sent,
                'total_messages_received': total_messages_received,
                'avg_response_time_minutes': round(avg_response, 1) if avg_response else None,
                'days_active': len(daily_stats)
            }

        except Exception as e:
            logger.error(f"Ошибка расчета недельной статистики: {e}")
            return {}

    @staticmethod
    async def get_channel_stats(target_date: date = None) -> List[Dict]:
        """Получить статистику по каналам"""
        try:
            if target_date is None:
                target_date = date.today()

            start_time = datetime.combine(target_date, datetime.min.time()).isoformat()
            end_time = datetime.combine(target_date, datetime.max.time()).isoformat()

            result = supabase.table('telegram_conversations').select('*').gte(
                'message_time', start_time
            ).lte('message_time', end_time).eq('is_new_client', True).execute()

            conversations = result.data

            # Группируем по каналам
            channel_stats = {}
            for conv in conversations:
                channel = conv.get('channel_source', 'unknown')
                if channel not in channel_stats:
                    channel_stats[channel] = {
                        'channel': channel,
                        'new_clients': 0,
                        'managers': set()
                    }

                channel_stats[channel]['new_clients'] += 1
                channel_stats[channel]['managers'].add(conv['manager_id'])

            # Конвертируем в список
            result = []
            for channel, stats in channel_stats.items():
                result.append({
                    'channel': channel,
                    'new_clients': stats['new_clients'],
                    'managers_count': len(stats['managers'])
                })

            # Сортируем по количеству клиентов
            result.sort(key=lambda x: x['new_clients'], reverse=True)

            return result

        except Exception as e:
            logger.error(f"Ошибка получения статистики каналов: {e}")
            return []
