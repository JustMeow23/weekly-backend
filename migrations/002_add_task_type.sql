-- Add type column to tasks table ("task" | "reminder")
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS "type" VARCHAR(50) NOT NULL DEFAULT 'task';