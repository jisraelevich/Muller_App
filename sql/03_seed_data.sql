-- ============================================================================
-- Seed Data: Initial data for the application
-- ============================================================================

-- Insert 3 admin users (whitelist for Google OAuth)
INSERT INTO users (email, nombre, is_admin) VALUES
('admin1@gmail.com', 'Admin User 1', true),
('admin2@gmail.com', 'Admin User 2', true),
('admin3@gmail.com', 'Admin User 3', true)
ON CONFLICT (email) DO NOTHING;

-- Sample miembros (for testing)
INSERT INTO miembros (nombre, apellido, email, tipo_asistencia, matricula, estado) VALUES
('Juan', 'Pérez', 'juan@example.com', 'Regular', 'MAT001', 'Activo'),
('María', 'González', 'maria@example.com', 'Regular', 'MAT002', 'Activo'),
('Pedro', 'López', 'pedro@example.com', 'Oyente', 'MAT003', 'Activo'),
('Ana', 'Martínez', 'ana@example.com', 'Regular', 'MAT004', 'Activo'),
('Carlos', 'Rodríguez', 'carlos@example.com', 'Regular', 'MAT005', 'Activo')
ON CONFLICT (matricula) DO NOTHING;

-- Sample clases
INSERT INTO clases (nombre, descripcion, fecha, hora_inicio, hora_fin, modalidad, estado) VALUES
('Clase de Hoy - Neumatología', 'Clase sobre Neumatología', CURRENT_DATE, '10:00', '11:30', 'Meet', 'Programada'),
('Clase Anterior - Cardiología', 'Clase sobre Cardiología', CURRENT_DATE - INTERVAL '7 days', '10:00', '11:30', 'Meet', 'Realizada'),
('Próxima Clase - Gastroenterología', 'Clase sobre Gastroenterología', CURRENT_DATE + INTERVAL '7 days', '10:00', '11:30', 'Meet', 'Programada')
ON CONFLICT DO NOTHING;

-- Sample asistencia
INSERT INTO asistencia (miembro_id, clase_id, fecha, asistio) VALUES
(1, 2, CURRENT_DATE - INTERVAL '7 days', true),
(2, 2, CURRENT_DATE - INTERVAL '7 days', true),
(3, 2, CURRENT_DATE - INTERVAL '7 days', false),
(1, 1, CURRENT_DATE, true),
(2, 1, CURRENT_DATE, true)
ON CONFLICT (miembro_id, clase_id, fecha) DO NOTHING;

-- Sample pagos (multiple months for payment report)
INSERT INTO pagos (miembro_id, monto, fecha, mes, descripcion, metodo_pago, estado) VALUES
(1, 500.00, '2025-03-15', 'Marzo', 'Cuota Marzo', 'Transferencia', 'Completado'),
(1, 500.00, '2025-04-15', 'Abril', 'Cuota Abril', 'Transferencia', 'Completado'),
(1, 500.00, '2025-05-15', 'Mayo', 'Cuota Mayo', 'Efectivo', 'Completado'),
(2, 500.00, '2025-03-20', 'Marzo', 'Cuota Marzo', 'Efectivo', 'Completado'),
(2, 500.00, '2025-04-20', 'Abril', 'Cuota Abril', 'Transferencia', 'Completado'),
(4, 500.00, '2025-03-25', 'Marzo', 'Cuota Marzo', 'Transferencia', 'Completado'),
(5, 500.00, '2025-03-30', 'Marzo', 'Cuota Marzo', 'Efectivo', 'Completado')
ON CONFLICT DO NOTHING;

-- Sample retiros
INSERT INTO retiros (miembro_id, monto, fecha, razon, tipo_retiro, estado) VALUES
(3, 250.00, '2025-04-10', 'Retiro de fondos excedentes', 'Reembolso', 'Completado')
ON CONFLICT DO NOTHING;

-- Configuration settings
INSERT INTO configuracion (clave, valor, tipo) VALUES
('mes_inicio_pagos', 'Marzo', 'string'),
('mes_fin_pagos', 'Noviembre', 'string'),
('cuota_regular', '500', 'integer'),
('idioma', 'es', 'string')
ON CONFLICT (clave) DO NOTHING;
