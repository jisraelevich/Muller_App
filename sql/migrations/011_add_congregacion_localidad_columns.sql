-- Migración: Agregar columnas congregación y localidad a tabla miembros

ALTER TABLE miembros 
ADD COLUMN IF NOT EXISTS congregacion VARCHAR(255) DEFAULT 'ICE Fco Arias',
ADD COLUMN IF NOT EXISTS localidad VARCHAR(255) DEFAULT 'Salta Capital';

-- Actualizar registros existentes con valores NULL
UPDATE miembros 
SET congregacion = 'ICE Fco Arias' 
WHERE congregacion IS NULL OR congregacion = '';

UPDATE miembros 
SET localidad = 'Salta Capital' 
WHERE localidad IS NULL OR localidad = '';
