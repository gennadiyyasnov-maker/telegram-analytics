import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "managers" / "sessions"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"

# Создаем папки если не существуют
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Система
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
STATS_UPDATE_INTERVAL = int(os.getenv("STATS_UPDATE_INTERVAL", 300))
BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", 21600))
NEW_CLIENT_HOURS = int(os.getenv("NEW_CLIENT_HOURS", 24))

# Уведомления
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"

# Проверка обязательных настроек
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL и SUPABASE_KEY обязательны в .env файле")

print(f"✅ Настройки загружены")
print(f"📁 DATA_DIR: {DATA_DIR}")
print(f"📊 LOG_DIR: {LOG_DIR}")
