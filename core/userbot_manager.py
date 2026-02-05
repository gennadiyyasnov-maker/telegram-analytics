import logging
import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from core.message_analyzer import MessageAnalyzer
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

class UserbotManager:
    """Менеджер для управления userbot'ом одного менеджера"""

    def __init__(self, manager_id: str, manager_name: str, api_id: int, api_hash: str, phone: str):
        self.manager_id = manager_id
        self.manager_name = manager_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone

        # Путь к session файлу
        session_file = DATA_DIR / f"{manager_id}.session"

        # Создаем клиента
        self.client = TelegramClient(str(session_file), api_id, api_hash)

        # Анализатор сообщений (передаем client для проверки истории)
        self.analyzer = MessageAnalyzer(manager_id, manager_name, self.client)

        # Статус
        self.is_running = False
        self.last_activity = None

    async def start(self):
        """Запустить userbot"""
        try:
            logger.info(f"🚀 Запуск userbot для {self.manager_name}...")

            # Подключаемся
            await self.client.connect()

            # Проверяем авторизацию
            if not await self.client.is_user_authorized():
                logger.warning(f"⚠️ {self.manager_name} не авторизован. Требуется код.")
                # В production это будет обработано через add_manager.py
                return False

            # Получаем информацию о себе
            me = await self.client.get_me()
            logger.info(f"✅ {self.manager_name} подключен как @{me.username}")

            # Регистрируем обработчики событий
            self._register_handlers()

            self.is_running = True
            logger.info(f"✅ Userbot {self.manager_name} успешно запущен")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка запуска userbot {self.manager_name}: {e}")
            return False

    def _register_handlers(self):
        """Регистрация обработчиков событий Telegram"""

        @self.client.on(events.NewMessage(incoming=True, outgoing=False))
        async def handle_incoming(event):
            """Обработка входящих сообщений"""
            # Игнорируем сообщения от ботов и каналов
            if event.is_channel or event.is_group:
                return

            self.last_activity = asyncio.get_event_loop().time()
            await self.analyzer.analyze_incoming_message(event)

        @self.client.on(events.NewMessage(incoming=False, outgoing=True))
        async def handle_outgoing(event):
            """Обработка исходящих сообщений"""
            # Только личные чаты
            if event.is_channel or event.is_group:
                return

            self.last_activity = asyncio.get_event_loop().time()
            await self.analyzer.analyze_outgoing_message(event)

    async def stop(self):
        """Остановить userbot"""
        try:
            self.is_running = False
            await self.client.disconnect()
            logger.info(f"🛑 Userbot {self.manager_name} остановлен")
        except Exception as e:
            logger.error(f"Ошибка остановки userbot: {e}")

    async def get_status(self) -> dict:
        """Получить статус userbot"""
        try:
            if not self.is_running:
                return {
                    'manager_id': self.manager_id,
                    'manager_name': self.manager_name,
                    'status': 'offline',
                    'last_activity': self.last_activity
                }

            # Получаем количество активных диалогов
            dialogs = await self.client.get_dialogs(limit=100)
            private_chats = len([d for d in dialogs if d.is_user and not d.entity.bot])

            return {
                'manager_id': self.manager_id,
                'manager_name': self.manager_name,
                'status': 'online',
                'active_chats': private_chats,
                'last_activity': self.last_activity
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {
                'manager_id': self.manager_id,
                'manager_name': self.manager_name,
                'status': 'error',
                'error': str(e)
            }


class UserbotOrchestrator:
    """Оркестратор для управления всеми userbot'ами"""

    def __init__(self):
        self.userbots: dict[str, UserbotManager] = {}

    def add_userbot(self, manager_id: str, manager_name: str, api_id: int, api_hash: str, phone: str):
        """Добавить userbot"""
        userbot = UserbotManager(manager_id, manager_name, api_id, api_hash, phone)
        self.userbots[manager_id] = userbot
        logger.info(f"➕ Добавлен userbot для {manager_name}")

    async def start_all(self):
        """Запустить все userbot'ы"""
        logger.info(f"🚀 Запуск {len(self.userbots)} userbot'ов...")

        tasks = []
        for userbot in self.userbots.values():
            tasks.append(userbot.start())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(f"✅ Успешно запущено: {success_count}/{len(self.userbots)}")

    async def stop_all(self):
        """Остановить все userbot'ы"""
        logger.info("🛑 Остановка всех userbot'ов...")

        tasks = []
        for userbot in self.userbots.values():
            tasks.append(userbot.stop())

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ Все userbot'ы остановлены")

    async def get_all_statuses(self) -> list[dict]:
        """Получить статус всех userbot'ов"""
        tasks = []
        for userbot in self.userbots.values():
            tasks.append(userbot.get_status())

        statuses = await asyncio.gather(*tasks, return_exceptions=True)
        return [s for s in statuses if isinstance(s, dict)]

    async def run_forever(self):
        """Запустить все userbot'ы и держать работающими"""
        await self.start_all()

        logger.info("♾️ Система работает. Нажмите Ctrl+C для остановки.")

        try:
            # Держим процесс живым
            while True:
                await asyncio.sleep(60)

                # Периодически проверяем статус
                statuses = await self.get_all_statuses()
                online = sum(1 for s in statuses if s.get('status') == 'online')
                logger.debug(f"💚 Онлайн: {online}/{len(statuses)}")

        except KeyboardInterrupt:
            logger.info("⚠️ Получен сигнал остановки")
        finally:
            await self.stop_all()
