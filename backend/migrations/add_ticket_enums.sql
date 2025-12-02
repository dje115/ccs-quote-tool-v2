-- Migration: Add Ticket Priority and Type Enums
-- Purpose: Create enum types for ticket priority and ticket type
-- Date: 2025-12-02

-- Create ticketpriority enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ticketpriority') THEN
        CREATE TYPE ticketpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT');
    END IF;
END $$;

-- Create tickettype enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tickettype') THEN
        CREATE TYPE tickettype AS ENUM ('SUPPORT', 'BUG', 'FEATURE_REQUEST', 'BILLING', 'TECHNICAL');
    END IF;
END $$;

