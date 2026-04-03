-- Migration: Create clases table
-- Date: 2026-04-03
-- Purpose: Store class information with dates, modality, and status

CREATE TABLE IF NOT EXISTS clases (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha DATE NOT NULL,
    hora_inicio TIME,
    hora_fin TIME,
    modalidad VARCHAR(50), -- 'Meet', 'Presencial', etc.
    link_meet VARCHAR(500),
    estado VARCHAR(50) DEFAULT 'Programada', -- 'Programada', 'Realizada', 'Cancelada'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clases_fecha ON clases(fecha);
CREATE INDEX IF NOT EXISTS idx_clases_estado ON clases(estado);
