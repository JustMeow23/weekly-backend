-- Add referralCode column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS "referralCode" VARCHAR(100) DEFAULT NULL;