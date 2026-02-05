-- =====================================================
-- TELEGRAM ANALYTICS - УПРОЩЕННАЯ СХЕМА БД
-- =====================================================
-- Скопируй и выполни этот SQL в Supabase → SQL Editor

-- Главная таблица переписок
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
CREATE INDEX IF NOT EXISTS idx_conversations_is_new ON telegram_conversations(is_new_client);

-- Отключить RLS (Row Level Security) для упрощения
ALTER TABLE telegram_conversations DISABLE ROW LEVEL SECURITY;

-- Права доступа (открыть для всех - только для разработки!)
GRANT ALL ON telegram_conversations TO anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE telegram_conversations_id_seq TO anon, authenticated;
