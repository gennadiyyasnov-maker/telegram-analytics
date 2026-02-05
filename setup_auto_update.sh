#!/bin/bash

echo "======================================"
echo "🚀 Настройка автообновления userbot"
echo "======================================"

# Переходим в папку проекта
cd ~/telegram-analytics || exit 1

echo ""
echo "📥 Обновляем код до последней версии..."
git pull origin main

echo ""
echo "🔄 Перезапускаем userbot с новым кодом..."
sudo systemctl restart telegram-analytics

echo ""
echo "✅ Userbot перезапущен с новой логикой!"
echo ""

# Создаем скрипт автообновления
cat > ~/auto_update_telegram.sh << 'SCRIPT'
#!/bin/bash
cd ~/telegram-analytics
git pull origin main > /dev/null 2>&1
if [ $? -eq 0 ]; then
    sudo systemctl restart telegram-analytics
    echo "$(date): Код обновлен и userbot перезапущен" >> ~/telegram_updates.log
fi
SCRIPT

chmod +x ~/auto_update_telegram.sh

echo "📝 Создан скрипт автообновления: ~/auto_update_telegram.sh"
echo ""

# Добавляем в cron (каждые 15 минут)
(crontab -l 2>/dev/null | grep -v "auto_update_telegram.sh"; echo "*/15 * * * * ~/auto_update_telegram.sh") | crontab -

echo "⏰ Автообновление настроено! Будет запускаться каждые 15 минут"
echo ""
echo "======================================"
echo "✅ ГОТОВО!"
echo "======================================"
echo ""
echo "Userbot теперь:"
echo "  ✅ Работает с НОВОЙ логикой is_new_client"
echo "  ✅ Автоматически обновляется каждые 15 минут"
echo "  ✅ Новый клиент = пишет ПЕРВЫЙ РАЗ вообще"
echo "  ✅ Повторный = уже есть история"
echo ""
echo "📊 Проверь логи:"
echo "   sudo journalctl -u telegram-analytics -n 50"
echo ""
