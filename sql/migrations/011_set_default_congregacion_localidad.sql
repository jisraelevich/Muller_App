-- Migración: Establecer valores por defecto para congregación y localidad
-- Actualiza registros NULL con valores por defecto

UPDATE miembros 
SET congregacion = 'ICE Fco Arias' 
WHERE congregacion IS NULL OR congregacion = '';

UPDATE miembros 
SET localidad = 'Salta Capital' 
WHERE localidad IS NULL OR localidad = '';
