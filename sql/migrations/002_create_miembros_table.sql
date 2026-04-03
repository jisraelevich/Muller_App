-- Migration: Create miembros table
-- Date: 2026-04-03
-- Purpose: Store student/member information with attendance type tracking

CREATE TABLE IF NOT EXISTS miembros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(20),
    tipo_asistencia VARCHAR(50) NOT NULL, -- 'Regular' o 'Oyente'
    matricula VARCHAR(50) UNIQUE,
    fecha_ingreso DATE,
    estado VARCHAR(50) DEFAULT 'Activo', -- 'Activo', 'Inactivo', 'Retirado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_miembros_tipo_asistencia ON miembros(tipo_asistencia);
CREATE INDEX IF NOT EXISTS idx_miembros_estado ON miembros(estado);
