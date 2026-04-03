-- ============================================================================
-- Stored Procedures and Functions
-- ============================================================================

-- ============================================================================
-- PAYMENT REPORT: Students with payment status by month
-- This powers the payment report showing which students paid each month
-- ============================================================================
CREATE OR REPLACE FUNCTION obtener_reporte_pagos_por_mes()
RETURNS TABLE (
    miembro_id INTEGER,
    nombre VARCHAR,
    apellido VARCHAR,
    matricula VARCHAR,
    marzo BIGINT,
    abril BIGINT,
    mayo BIGINT,
    junio BIGINT,
    julio BIGINT,
    agosto BIGINT,
    septiembre BIGINT,
    octubre BIGINT,
    noviembre BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.nombre,
        m.apellido,
        m.matricula,
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 3 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 4 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 5 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 6 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 7 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 8 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 9 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 10 AND p.estado = 'Completado' THEN 1 END),
        COUNT(CASE WHEN EXTRACT(MONTH FROM p.fecha) = 11 AND p.estado = 'Completado' THEN 1 END)
    FROM miembros m
    LEFT JOIN pagos p ON m.id = p.miembro_id 
    WHERE m.tipo_asistencia = 'Regular' AND m.estado = 'Activo'
    GROUP BY m.id, m.nombre, m.apellido, m.matricula
    ORDER BY m.nombre, m.apellido;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ATTENDANCE REPORT: Students attendance by class
-- ============================================================================
CREATE OR REPLACE FUNCTION obtener_reporte_asistencia(p_fecha_inicio DATE, p_fecha_fin DATE)
RETURNS TABLE (
    miembro_id INTEGER,
    nombre VARCHAR,
    apellido VARCHAR,
    total_clases BIGINT,
    clases_asistidas BIGINT,
    clases_no_asistidas BIGINT,
    porcentaje_asistencia NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.nombre,
        m.apellido,
        COUNT(DISTINCT a.clase_id),
        COUNT(CASE WHEN a.asistio = true THEN 1 END),
        COUNT(CASE WHEN a.asistio = false THEN 1 END),
        ROUND(
            CAST(COUNT(CASE WHEN a.asistio = true THEN 1 END) AS NUMERIC) / 
            NULLIF(COUNT(DISTINCT a.clase_id), 0) * 100, 
            2
        )
    FROM miembros m
    LEFT JOIN asistencia a ON m.id = a.miembro_id 
    WHERE a.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
    GROUP BY m.id, m.nombre, m.apellido
    ORDER BY porcentaje_asistencia DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PAYMENT SUMMARY: Total payments by student for a date range
-- ============================================================================
CREATE OR REPLACE FUNCTION obtener_resumen_pagos(p_fecha_inicio DATE, p_fecha_fin DATE)
RETURNS TABLE (
    miembro_id INTEGER,
    nombre VARCHAR,
    apellido VARCHAR,
    total_pagos DECIMAL,
    cantidad_pagos BIGINT,
    ultimo_pago DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.nombre,
        m.apellido,
        SUM(p.monto)::DECIMAL,
        COUNT(p.id),
        MAX(p.fecha)
    FROM miembros m
    LEFT JOIN pagos p ON m.id = p.miembro_id AND p.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
    WHERE m.estado = 'Activo'
    GROUP BY m.id, m.nombre, m.apellido
    ORDER BY m.nombre, m.apellido;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GET TODAY'S CLASS INFO: Last class, today's class, next class
-- ============================================================================
CREATE OR REPLACE FUNCTION obtener_clases_hoy()
RETURNS TABLE (
    tipo VARCHAR,
    clase_id INTEGER,
    nombre VARCHAR,
    descripcion TEXT,
    fecha DATE,
    hora_inicio TIME,
    hora_fin TIME,
    modalidad VARCHAR,
    link_meet VARCHAR,
    estado VARCHAR
) AS $$
BEGIN
    -- Last class
    RETURN QUERY
    SELECT 'anterior'::VARCHAR, id, nombre, descripcion, fecha, hora_inicio, hora_fin, modalidad, link_meet, estado
    FROM clases
    WHERE fecha < CURRENT_DATE AND estado = 'Realizada'
    ORDER BY fecha DESC
    LIMIT 1;
    
    -- Today's class
    RETURN QUERY
    SELECT 'hoy'::VARCHAR, id, nombre, descripcion, fecha, hora_inicio, hora_fin, modalidad, link_meet, estado
    FROM clases
    WHERE fecha = CURRENT_DATE
    ORDER BY hora_inicio ASC
    LIMIT 1;
    
    -- Next class
    RETURN QUERY
    SELECT 'proxima'::VARCHAR, id, nombre, descripcion, fecha, hora_inicio, hora_fin, modalidad, link_meet, estado
    FROM clases
    WHERE fecha > CURRENT_DATE AND estado = 'Programada'
    ORDER BY fecha ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- UPDATE STATUS: Mark class as completed
-- ============================================================================
CREATE OR REPLACE FUNCTION marcar_clase_realizada(p_clase_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE clases
    SET estado = 'Realizada', updated_at = CURRENT_TIMESTAMP
    WHERE id = p_clase_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- DELETE PAYMENT: Remove a payment by ID
-- ============================================================================
CREATE OR REPLACE FUNCTION eliminar_pago(p_pago_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM pagos WHERE id = p_pago_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- UPDATE MEMBER TYPE: Change between Regular/Oyente
-- ============================================================================
CREATE OR REPLACE FUNCTION cambiar_tipo_asistencia(p_miembro_id INTEGER, p_nuevo_tipo VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE miembros
    SET tipo_asistencia = p_nuevo_tipo, updated_at = CURRENT_TIMESTAMP
    WHERE id = p_miembro_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;
