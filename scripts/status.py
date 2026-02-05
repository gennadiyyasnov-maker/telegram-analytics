#!/usr/bin/env python3
"""
Проверка статуса всех userbot'ов
"""

import asyncio
import sys
from pathlib import Path
from tabulate import tabulate
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.userbot_manager import UserbotOrchestrator
import json

async def check_status():
    """Проверить статус всех менеджеров"""
    print("🔍 Проверка статуса userbot'ов...")
    print()

    # Загружаем конфиг
    config_file = Path("managers/config.json")
    if not config_file.exists():
        print("❌ Файл managers/config.json не найден")
        print("💡 Добавьте менеджеров через: python scripts/add_manager.py")
        return

    with open(config_file, 'r') as f:
        managers = json.load(f)

    if not managers:
        print("❌ Нет добавленных менеджеров")
        return

    # Создаем оркестратор
    orchestrator = UserbotOrchestrator()

    # Добавляем всех менеджеров
    for manager in managers:
        orchestrator.add_userbot(
            manager_id=manager['id'],
            manager_name=manager['name'],
            api_id=manager['api_id'],
            api_hash=manager['api_hash'],
            phone=manager['phone']
        )

    # Получаем статусы
    statuses = await orchestrator.get_all_statuses()

    # Формируем таблицу
    table_data = []
    for status in statuses:
        last_activity = status.get('last_activity')
        if last_activity:
            last_activity = f"{int((asyncio.get_event_loop().time() - last_activity) / 60)} мин назад"
        else:
            last_activity = "Нет данных"

        status_emoji = {
            'online': '🟢',
            'offline': '🔴',
            'error': '⚠️'
        }.get(status.get('status'), '❓')

        table_data.append([
            status_emoji,
            status.get('manager_name', 'N/A'),
            status.get('status', 'unknown').upper(),
            status.get('active_chats', 'N/A'),
            last_activity
        ])

    print(tabulate(
        table_data,
        headers=['', 'Менеджер', 'Статус', 'Активных чатов', 'Последняя активность'],
        tablefmt='rounded_grid'
    ))

    print()
    print(f"📊 Всего менеджеров: {len(statuses)}")
    online = sum(1 for s in statuses if s.get('status') == 'online')
    print(f"🟢 Онлайн: {online}")
    print(f"🔴 Оффлайн: {len(statuses) - online}")

if __name__ == "__main__":
    asyncio.run(check_status())
