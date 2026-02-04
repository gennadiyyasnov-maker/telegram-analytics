#!/usr/bin/env python3
"""
Скрипт для добавления нового менеджера в систему
"""

import asyncio
import json
import sys
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Добавляем корневую папку в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR

async def add_manager():
    """Интерактивное добавление менеджера"""
    print("=" * 60)
    print("🤖 ДОБАВЛЕНИЕ НОВОГО МЕНЕДЖЕРА")
    print("=" * 60)
    print()

    # Собираем данные
    print("📋 Введите данные менеджера:")
    print()

    manager_id = input("ID менеджера (латиница, например 'ivan'): ").strip().lower()
    manager_name = input("Имя менеджера (например 'Иван'): ").strip()

    print()
    print("📱 Telegram API credentials (получить на https://my.telegram.org):")
    api_id = input("API ID: ").strip()
    api_hash = input("API Hash: ").strip()
    phone = input("Номер телефона (например +79991234567): ").strip()

    print()
    print(f"✅ Данные менеджера:")
    print(f"   ID: {manager_id}")
    print(f"   Имя: {manager_name}")
    print(f"   Телефон: {phone}")
    print()

    confirm = input("Продолжить? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Отменено")
        return

    # Авторизация в Telegram
    print()
    print("🔐 Авторизация в Telegram...")

    session_file = DATA_DIR / f"{manager_id}.session"
    client = TelegramClient(str(session_file), int(api_id), api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print(f"📱 Отправляем код на {phone}...")
            await client.send_code_request(phone)

            code = input("Введите код из Telegram: ").strip()

            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Введите пароль 2FA: ").strip()
                await client.sign_in(password=password)

        # Проверяем успешность
        me = await client.get_me()
        print(f"✅ Успешно авторизован как: {me.first_name} (@{me.username})")

        await client.disconnect()

        # Сохраняем в конфиг
        config_file = Path("managers/config.json")

        # Загружаем существующий конфиг или создаем новый
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = []

        # Добавляем нового менеджера
        manager_data = {
            'id': manager_id,
            'name': manager_name,
            'api_id': int(api_id),
            'api_hash': api_hash,
            'phone': phone,
            'username': me.username or '',
            'added_at': str(asyncio.get_event_loop().time())
        }

        # Проверяем, нет ли уже такого ID
        existing_ids = [m['id'] for m in config]
        if manager_id in existing_ids:
            print(f"⚠️ Менеджер с ID '{manager_id}' уже существует. Обновляем...")
            config = [m for m in config if m['id'] != manager_id]

        config.append(manager_data)

        # Сохраняем
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 60)
        print(f"✅ Менеджер '{manager_name}' успешно добавлен!")
        print("=" * 60)
        print()
        print("💡 Следующие шаги:")
        print("   1. Запустите систему: python main.py")
        print("   2. Или проверьте статус: python scripts/status.py")
        print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print()
        print("💡 Возможные причины:")
        print("   - Неверный API ID/Hash (проверьте на https://my.telegram.org)")
        print("   - Неверный номер телефона")
        print("   - Проблемы с сетью")

        # Удаляем session файл при ошибке
        if session_file.exists():
            session_file.unlink()

if __name__ == "__main__":
    asyncio.run(add_manager())
