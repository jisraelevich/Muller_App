-- Add mes_inicio, mes_fin, and estado_pago columns to pagos table
-- These allow tracking multi-month payments and payment status (puntual/atrasado/adelantado)

DO $$ 
BEGIN
    -- Add mes_inicio (month payment starts covering)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'pagos' AND column_name = 'mes_inicio') THEN
        ALTER TABLE pagos ADD COLUMN mes_inicio INTEGER DEFAULT NULL;
    END IF;
    
    -- Add mes_fin (month payment ends covering)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'pagos' AND column_name = 'mes_fin') THEN
        ALTER TABLE pagos ADD COLUMN mes_fin INTEGER DEFAULT NULL;
    END IF;
    
    -- Add estado_pago (Puntual, Adelantado, Atrasado)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'pagos' AND column_name = 'estado_pago') THEN
        ALTER TABLE pagos ADD COLUMN estado_pago VARCHAR(20) DEFAULT 'Puntual';
    END IF;
    
    -- Add CHECK constraint for valid months
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'pagos' AND constraint_name = 'pagos_months_valid'
    ) THEN
        ALTER TABLE pagos 
        ADD CONSTRAINT pagos_months_valid 
        CHECK (mes_inicio IS NULL OR (mes_inicio >= 1 AND mes_inicio <= 12));
    END IF;
    
    -- Add CHECK constraint for mes_fin
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'pagos' AND constraint_name = 'pagos_mes_fin_valid'
    ) THEN
        ALTER TABLE pagos 
        ADD CONSTRAINT pagos_mes_fin_valid 
        CHECK (mes_fin IS NULL OR (mes_fin >= 1 AND mes_fin <= 12));
    END IF;

END $$;
