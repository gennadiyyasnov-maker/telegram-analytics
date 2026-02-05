#!/usr/bin/env python3
"""
Telegram Analytics Userbot System
Главная точка входа для запуска всех userbot'ов
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from core.userbot_manager import UserbotOrchestrator
from core.statistics import StatisticsCalculator
from config.supabase import test_connection
from config.settings import STATS_UPDATE_INTERVAL

# Глобальный оркестратор
orchestrator = UserbotOrchestrator()

async def load_managers():
    """Загрузить список менеджеров из конфига"""
    # TODO: В реальной версии загружать из файла managers/config.json
    # Для примера добавляю вручную

    logger.info("📋 Загрузка списка менеджеров...")

    # Пример (в реальности будет из файла):
    # orchestrator.add_userbot(
    #     manager_id="ivan",
    #     manager_name="Иван",
    #     api_id=12345678,
    #     api_hash="abc123...",
    #     phone="+79991234567"
    # )

    # Загружаем из managers/config.json
    config_file = Path("managers/config.json")
    if config_file.exists():
        import json
        with open(config_file, 'r') as f:
            managers = json.load(f)

        for manager in managers:
            orchestrator.add_userbot(
                manager_id=manager['id'],
                manager_name=manager['name'],
                api_id=manager['api_id'],
                api_hash=manager['api_hash'],
                phone=manager['phone']
            )

        logger.info(f"✅ Загружено {len(managers)} менеджеров")
    else:
        logger.warning("⚠️ Файл managers/config.json не найден")
        logger.info("ℹ️ Используйте `python scripts/add_manager.py` для добавления менеджеров")

async def periodic_stats_update():
    """Периодическое обновление статистики"""
    while True:
        try:
            await asyncio.sleep(STATS_UPDATE_INTERVAL)

            logger.info("📊 Обновление ежедневной статистики...")

            # Получаем список всех менеджеров
            for manager_id in orchestrator.userbots.keys():
                await StatisticsCalculator.calculate_daily_stats(manager_id)

            logger.info("✅ Статистика обновлена")

        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")

async def main():
    """Главная функция"""
    logger.info("=" * 60)
    logger.info("🤖 TELEGRAM ANALYTICS USERBOT SYSTEM")
    logger.info("=" * 60)

    # Проверяем подключение к Supabase
    logger.info("🔍 Проверка подключения к Supabase...")
    if not await test_connection():
        logger.error("❌ Не удалось подключиться к Supabase. Проверьте .env файл")
        return

    # Загружаем менеджеров
    await load_managers()

    if not orchestrator.userbots:
        logger.error("❌ Нет менеджеров для запуска")
        logger.info("ℹ️ Добавьте менеджеров через: python scripts/add_manager.py")
        return

    # Запускаем периодическое обновление статистики
    asyncio.create_task(periodic_stats_update())

    # Запускаем все userbot'ы
    await orchestrator.run_forever()

def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info("⚠️ Получен сигнал остановки")
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Завершение работы...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
