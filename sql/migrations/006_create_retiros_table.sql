-- Migration: Create retiros table
-- Date: 2026-04-03
-- Purpose: Track refund/withdrawal records

CREATE TABLE IF NOT EXISTS retiros (
    id SERIAL PRIMARY KEY,
    miembro_id INTEGER NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha DATE NOT NULL,
    razon TEXT,
    tipo_retiro VARCHAR(50), -- 'Reembolso', 'Crédito', etc.
    estado VARCHAR(50) DEFAULT 'Completado', -- 'Completado', 'Pendiente', 'Rechazado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_retiros_miembro FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_retiros_miembro_id ON retiros(miembro_id);
CREATE INDEX IF NOT EXISTS idx_retiros_fecha ON retiros(fecha);
CREATE INDEX IF NOT EXISTS idx_retiros_estado ON retiros(estado);
