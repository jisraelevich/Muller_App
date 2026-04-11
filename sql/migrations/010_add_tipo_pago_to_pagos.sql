-- Add tipo_pago column to pagos table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'pagos' AND column_name = 'tipo_pago') THEN
        ALTER TABLE pagos ADD COLUMN tipo_pago VARCHAR(50) DEFAULT 'Cuota';
    END IF;
END $$;
