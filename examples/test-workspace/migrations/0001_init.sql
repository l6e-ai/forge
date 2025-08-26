-- Create schema and tables for conversation/message persistence
create schema if not exists forge;

create table if not exists forge.conversations (
  conversation_id uuid primary key,
  agent_id text,
  user_id text,
  started_at timestamptz default now(),
  last_activity timestamptz default now(),
  message_count integer default 0
);

create table if not exists forge.messages (
  message_id uuid primary key,
  conversation_id uuid not null references forge.conversations(conversation_id) on delete cascade,
  role text not null,
  content text not null,
  timestamp timestamptz not null default now(),
  metadata jsonb default '{}'::jsonb
);

create index if not exists idx_messages_conversation_ts on forge.messages (conversation_id, timestamp desc);
