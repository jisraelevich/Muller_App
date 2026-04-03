-- Migration: Create oradores table
-- Date: 2026-04-03
-- Purpose: Store guest speakers/lecturers information

CREATE TABLE IF NOT EXISTS oradores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    email VARCHAR(255),
    telefono VARCHAR(20),
    especialidad VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
