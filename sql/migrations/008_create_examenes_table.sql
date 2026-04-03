-- Migration: Create examenes table
-- Date: 2026-04-03
-- Purpose: Store exam records (for reference, not shown in reports per user request)

CREATE TABLE IF NOT EXISTS examenes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    fecha DATE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_examenes_fecha ON examenes(fecha);
