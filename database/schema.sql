-- =====================================================
-- TELEGRAM ANALYTICS - DATABASE SCHEMA
-- =====================================================
-- Создать эти таблицы в вашей Supabase БД

-- 1. Таблица переписок (детальная информация о каждом сообщении)
CREATE TABLE IF NOT EXISTS telegram_conversations (
  id BIGSERIAL PRIMARY KEY,
  manager_id TEXT NOT NULL,
  manager_name TEXT NOT NULL,
  client_telegram_id BIGINT NOT NULL,
  message_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  message_type TEXT NOT NULL CHECK (message_type IN ('incoming', 'outgoing')),
  is_new_client BOOLEAN DEFAULT FALSE,
  channel_source TEXT,
  response_time_minutes NUMERIC(10, 2),
  message_text TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрых запросов
CREATE INDEX IF NOT EXISTS idx_conversations_manager_id ON telegram_conversations(manager_id);
CREATE INDEX IF NOT EXISTS idx_conversations_client_id ON telegram_conversations(client_telegram_id);
CREATE INDEX IF NOT EXISTS idx_conversations_message_time ON telegram_conversations(message_time);
CREATE INDEX IF NOT EXISTS idx_conversations_manager_client ON telegram_conversations(manager_id, client_telegram_id);

-- 2. Таблица дневной статистики (агрегированные данные за день)
CREATE TABLE IF NOT EXISTS telegram_daily_stats (
  id BIGSERIAL PRIMARY KEY,
  manager_id TEXT NOT NULL,
  date DATE NOT NULL,
  new_clients INTEGER DEFAULT 0,
  returning_clients INTEGER DEFAULT 0,
  total_conversations INTEGER DEFAULT 0,
  messages_sent INTEGER DEFAULT 0,
  messages_received INTEGER DEFAULT 0,
  avg_response_time_minutes NUMERIC(10, 2),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(manager_id, date)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_daily_stats_manager_id ON telegram_daily_stats(manager_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON telegram_daily_stats(date);

-- 3. Таблица метрик менеджеров (расширенная аналитика)
CREATE TABLE IF NOT EXISTS telegram_manager_metrics (
  id BIGSERIAL PRIMARY KEY,
  manager_id TEXT NOT NULL,
  manager_name TEXT NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  total_new_clients INTEGER DEFAULT 0,
  total_returning_clients INTEGER DEFAULT 0,
  total_messages_sent INTEGER DEFAULT 0,
  total_messages_received INTEGER DEFAULT 0,
  avg_response_time_minutes NUMERIC(10, 2),
  fastest_response_seconds INTEGER,
  slowest_response_minutes INTEGER,
  conversion_rate NUMERIC(5, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_manager_metrics_manager_id ON telegram_manager_metrics(manager_id);
CREATE INDEX IF NOT EXISTS idx_manager_metrics_period ON telegram_manager_metrics(period_start, period_end);

-- 4. Таблица источников (каналов)
CREATE TABLE IF NOT EXISTS telegram_channel_sources (
  id BIGSERIAL PRIMARY KEY,
  channel_name TEXT NOT NULL UNIQUE,
  channel_username TEXT,
  total_clients INTEGER DEFAULT 0,
  conversion_rate NUMERIC(5, 2),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- VIEWS (представления для удобных запросов)
-- =====================================================

-- Статистика по менеджерам за сегодня
CREATE OR REPLACE VIEW v_today_manager_stats AS
SELECT
  manager_id,
  SUM(CASE WHEN is_new_client THEN 1 ELSE 0 END) as new_clients,
  SUM(CASE WHEN NOT is_new_client THEN 1 ELSE 0 END) as returning_clients,
  SUM(CASE WHEN message_type = 'outgoing' THEN 1 ELSE 0 END) as messages_sent,
  SUM(CASE WHEN message_type = 'incoming' THEN 1 ELSE 0 END) as messages_received,
  AVG(response_time_minutes) as avg_response_time
FROM telegram_conversations
WHERE DATE(message_time) = CURRENT_DATE
GROUP BY manager_id;

-- Топ каналов по количеству клиентов
CREATE OR REPLACE VIEW v_top_channels AS
SELECT
  channel_source,
  COUNT(DISTINCT client_telegram_id) as unique_clients,
  COUNT(*) as total_messages
FROM telegram_conversations
WHERE is_new_client = TRUE
  AND channel_source IS NOT NULL
  AND channel_source != 'unknown'
GROUP BY channel_source
ORDER BY unique_clients DESC;

-- =====================================================
-- FUNCTIONS (триггеры и функции)
-- =====================================================

-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_telegram_daily_stats_updated_at
BEFORE UPDATE ON telegram_daily_stats
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- RLS (Row Level Security) - опционально
-- =====================================================

-- Включить RLS если нужна безопасность на уровне строк
-- ALTER TABLE telegram_conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE telegram_daily_stats ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- SAMPLE QUERIES (примеры запросов)
-- =====================================================

-- Статистика конкретного менеджера за последние 7 дней
/*
SELECT * FROM telegram_daily_stats
WHERE manager_id = 'ivan'
  AND date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC;
*/

-- Топ менеджеров по количеству новых клиентов за сегодня
/*
SELECT manager_name, COUNT(*) as new_clients
FROM telegram_conversations
WHERE is_new_client = TRUE
  AND DATE(message_time) = CURRENT_DATE
GROUP BY manager_name
ORDER BY new_clients DESC
LIMIT 10;
*/

-- Средн время ответа по всем менеджерам
/*
SELECT
  manager_name,
  AVG(response_time_minutes) as avg_response,
  COUNT(*) as total_responses
FROM telegram_conversations
WHERE response_time_minutes IS NOT NULL
  AND DATE(message_time) = CURRENT_DATE
GROUP BY manager_name
ORDER BY avg_response ASC;
*/
