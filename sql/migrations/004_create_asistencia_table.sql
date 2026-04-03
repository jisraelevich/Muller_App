-- Migration: Create asistencia table
-- Date: 2026-04-03
-- Purpose: Track attendance records linking members to classes

CREATE TABLE IF NOT EXISTS asistencia (
    id SERIAL PRIMARY KEY,
    miembro_id INTEGER NOT NULL,
    clase_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    asistio BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_asistencia_miembro FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE,
    CONSTRAINT fk_asistencia_clase FOREIGN KEY (clase_id) REFERENCES clases(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_asistencia_miembro_id ON asistencia(miembro_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_clase_id ON asistencia(clase_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_fecha ON asistencia(fecha);
CREATE UNIQUE INDEX IF NOT EXISTS idx_asistencia_unique ON asistencia(miembro_id, clase_id, fecha);
