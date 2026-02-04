# 🚀 Инструкция по деплою Telegram Analytics

## 📋 Требования

- Ubuntu 20.04+ (или любой Linux)
- Python 3.9+
- 2GB RAM минимум
- Доступ к Supabase

## 🛠️ Шаг 1: Подготовка VPS сервера

### 1.1 Подключение к серверу

```bash
ssh root@your-server-ip
```

### 1.2 Обновление системы

```bash
apt update && apt upgrade -y
```

### 1.3 Установка Python и зависимостей

```bash
apt install -y python3 python3-pip python3-venv git
```

## 📦 Шаг 2: Клонирование репозитория

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/telegram-analytics.git
cd telegram-analytics
```

## 🔧 Шаг 3: Настройка окружения

### 3.1 Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.2 Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3.3 Создание .env файла

```bash
cp .env.example .env
nano .env
```

Заполните данные:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
LOG_LEVEL=INFO
```

## 📊 Шаг 4: Настройка Supabase

### 4.1 Создание таблиц

1. Зайдите в Supabase Dashboard
2. SQL Editor
3. Скопируйте содержимое `database/schema.sql`
4. Выполните запрос

### 4.2 Проверка подключения

```bash
python scripts/test_supabase.py
```

## 👥 Шаг 5: Добавление менеджеров

### 5.1 Добавление первого менеджера

```bash
python scripts/add_manager.py
```

Следуйте инструкциям на экране.

### 5.2 Проверка статуса

```bash
python scripts/status.py
```

## 🚀 Шаг 6: Запуск как системный сервис

### 6.1 Создание systemd service

```bash
nano /etc/systemd/system/telegram-analytics.service
```

Вставьте:

```ini
[Unit]
Description=Telegram Analytics Userbot System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-analytics
Environment="PATH=/opt/telegram-analytics/venv/bin"
ExecStart=/opt/telegram-analytics/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.2 Запуск сервиса

```bash
systemctl daemon-reload
systemctl enable telegram-analytics
systemctl start telegram-analytics
```

### 6.3 Проверка статуса

```bash
systemctl status telegram-analytics
```

### 6.4 Просмотр логов

```bash
journalctl -u telegram-analytics -f
```

## 🔄 Шаг 7: Обновление системы

### 7.1 Создание скрипта обновления

```bash
nano /opt/telegram-analytics/update.sh
chmod +x /opt/telegram-analytics/update.sh
```

Содержимое:

```bash
#!/bin/bash
cd /opt/telegram-analytics
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart telegram-analytics
echo "✅ Система обновлена и перезапущена"
```

### 7.2 Использование

```bash
cd /opt/telegram-analytics
./update.sh
```

## 🔒 Шаг 8: Безопасность

### 8.1 Настройка firewall

```bash
ufw allow ssh
ufw allow 443
ufw enable
```

### 8.2 Создание отдельного пользователя (рекомендуется)

```bash
adduser telegrambot
usermod -aG sudo telegrambot

# Переместите проект
mv /opt/telegram-analytics /home/telegrambot/
chown -R telegrambot:telegrambot /home/telegrambot/telegram-analytics

# Обновите service файл
nano /etc/systemd/system/telegram-analytics.service
# Измените User=root на User=telegrambot
# Измените WorkingDirectory на /home/telegrambot/telegram-analytics
```

## 📊 Шаг 9: Мониторинг

### 9.1 Проверка логов

```bash
# Системные логи
tail -f logs/main.log

# Логи конкретного менеджера
tail -f logs/userbot_MANAGER_NAME.log
```

### 9.2 Статус всех userbot'ов

```bash
python scripts/status.py
```

### 9.3 Live статистика

```bash
python scripts/live_stats.py
```

## 🐛 Troubleshooting

### Userbot не подключается

```bash
# Проверьте логи
journalctl -u telegram-analytics -n 100

# Проверьте session файлы
ls -la managers/sessions/

# Переавторизуйте менеджера
python scripts/add_manager.py
```

### Нет данных в Supabase

```bash
# Проверьте подключение
python scripts/test_supabase.py

# Проверьте .env файл
cat .env
```

### Высокое использование CPU/RAM

```bash
# Проверьте процессы
top

# Перезапустите сервис
systemctl restart telegram-analytics
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи
2. Проверьте .env конфигурацию
3. Убедитесь что все зависимости установлены
4. Проверьте доступ к Supabase

## 🔄 Backup

### Автоматический backup session файлов

```bash
# Создайте cron задачу
crontab -e

# Добавьте строку (backup каждые 6 часов)
0 */6 * * * rsync -a /opt/telegram-analytics/managers/sessions/ /opt/telegram-analytics/backups/sessions-$(date +\%Y\%m\%d-\%H\%M)/
```

## ✅ Проверка успешного деплоя

1. Сервис запущен: `systemctl status telegram-analytics`
2. Userbot'ы онлайн: `python scripts/status.py`
3. Данные поступают в Supabase
4. CRM показывает статистику

Готово! 🎉
