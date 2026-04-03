-- Migration: Create pagos table
-- Date: 2026-04-03
-- Purpose: Track payment records with monthly tracking

CREATE TABLE IF NOT EXISTS pagos (
    id SERIAL PRIMARY KEY,
    miembro_id INTEGER NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha DATE NOT NULL,
    mes VARCHAR(20), -- 'Marzo', 'Abril', 'Mayo', etc.
    descripcion VARCHAR(255),
    metodo_pago VARCHAR(50), -- 'Efectivo', 'Transferencia', 'PayPal', etc.
    estado VARCHAR(50) DEFAULT 'Completado', -- 'Completado', 'Pendiente', 'Cancelado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pagos_miembro FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pagos_miembro_id ON pagos(miembro_id);
CREATE INDEX IF NOT EXISTS idx_pagos_fecha ON pagos(fecha);
CREATE INDEX IF NOT EXISTS idx_pagos_mes ON pagos(mes);
CREATE INDEX IF NOT EXISTS idx_pagos_estado ON pagos(estado);
