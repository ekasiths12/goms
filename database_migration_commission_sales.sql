-- Database Migration: Add Commission Sales Support
-- This script adds the necessary columns to support commission sales functionality

-- Add commission sale fields to invoice_lines table
ALTER TABLE invoice_lines 
ADD COLUMN is_commission_sale BOOLEAN DEFAULT FALSE,
ADD COLUMN commission_yards DECIMAL(10,2) DEFAULT 0,
ADD COLUMN commission_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN commission_date DATE;

-- Add indexes for better performance
CREATE INDEX idx_invoice_lines_commission_sale ON invoice_lines(is_commission_sale);
CREATE INDEX idx_invoice_lines_commission_date ON invoice_lines(commission_date);

-- Update existing data to ensure consistency
UPDATE invoice_lines SET is_commission_sale = FALSE WHERE is_commission_sale IS NULL;
UPDATE invoice_lines SET commission_yards = 0 WHERE commission_yards IS NULL;
UPDATE invoice_lines SET commission_amount = 0 WHERE commission_amount IS NULL;

-- Verify the changes
SELECT 'Migration completed successfully' as status;
