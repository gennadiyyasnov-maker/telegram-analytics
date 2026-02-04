#!/usr/bin/env python3
"""
Тест подключения к Supabase
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.supabase import supabase, test_connection

async def main():
    """Тестирование подключения"""
    print("🔍 Тестирование подключения к Supabase...")
    print()

    if await test_connection():
        print("✅ Подключение успешно!")
        print()

        # Проверяем таблицы
        print("📊 Проверка таблиц...")

        tables = ['telegram_conversations', 'telegram_daily_stats', 'telegram_manager_metrics']

        for table in tables:
            try:
                result = supabase.table(table).select("count", count='exact').limit(1).execute()
                print(f"   ✅ {table}: OK (записей: {result.count})")
            except Exception as e:
                print(f"   ❌ {table}: ОШИБКА - {e}")

        print()
        print("🎉 Все проверки пройдены!")

    else:
        print("❌ Не удалось подключиться к Supabase")
        print()
        print("💡 Проверьте:")
        print("   1. .env файл существует")
        print("   2. SUPABASE_URL и SUPABASE_KEY заполнены")
        print("   3. Таблицы созданы (см. database/schema.sql)")

if __name__ == "__main__":
    asyncio.run(main())
