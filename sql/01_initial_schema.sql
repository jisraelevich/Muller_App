-- ============================================================================
-- MULLER_APP - PostgreSQL Schema
-- Database: Neon (PostgreSQL)
-- Purpose: Replace JSON file storage with proper relational database
-- ============================================================================

-- Table: users (Google OAuth - 3 admin users only)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    nombre VARCHAR(100),
    is_admin BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);

-- Table: miembros (Miembros/Estudiantes)
CREATE TABLE miembros (
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

CREATE INDEX idx_miembros_tipo_asistencia ON miembros(tipo_asistencia);
CREATE INDEX idx_miembros_estado ON miembros(estado);

-- Table: clases (Classes)
CREATE TABLE clases (
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

CREATE INDEX idx_clases_fecha ON clases(fecha);
CREATE INDEX idx_clases_estado ON clases(estado);

-- Table: asistencia (Attendance tracking)
CREATE TABLE asistencia (
    id SERIAL PRIMARY KEY,
    miembro_id INTEGER NOT NULL,
    clase_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    asistio BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE,
    FOREIGN KEY (clase_id) REFERENCES clases(id) ON DELETE CASCADE
);

CREATE INDEX idx_asistencia_miembro_id ON asistencia(miembro_id);
CREATE INDEX idx_asistencia_clase_id ON asistencia(clase_id);
CREATE INDEX idx_asistencia_fecha ON asistencia(fecha);
CREATE UNIQUE INDEX idx_asistencia_unique ON asistencia(miembro_id, clase_id, fecha);

-- Table: pagos (Payment tracking)
CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    miembro_id INTEGER NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha DATE NOT NULL,
    mes VARCHAR(20), -- 'Marzo', 'Abril', 'Mayo', etc.
    tipo_pago VARCHAR(50) DEFAULT 'Cuota', -- 'Cuota', 'Matrícula', 'Libro', 'Donación'
    descripcion VARCHAR(255),
    metodo_pago VARCHAR(50), -- 'Efectivo', 'Transferencia', 'PayPal', etc.
    estado VARCHAR(50) DEFAULT 'Completado', -- 'Completado', 'Pendiente', 'Cancelado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
);

CREATE INDEX idx_pagos_miembro_id ON pagos(miembro_id);
CREATE INDEX idx_pagos_fecha ON pagos(fecha);
CREATE INDEX idx_pagos_mes ON pagos(mes);
CREATE INDEX idx_pagos_estado ON pagos(estado);

-- Table: retiros (Withdrawals/Refunds)
CREATE TABLE retiros (
    id SERIAL PRIMARY KEY,
    miembro_id INTEGER NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha DATE NOT NULL,
    razon TEXT,
    tipo_retiro VARCHAR(50), -- 'Reembolso', 'Crédito', etc.
    estado VARCHAR(50) DEFAULT 'Completado', -- 'Completado', 'Pendiente', 'Rechazado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
);

CREATE INDEX idx_retiros_miembro_id ON retiros(miembro_id);
CREATE INDEX idx_retiros_fecha ON retiros(fecha);
CREATE INDEX idx_retiros_estado ON retiros(estado);

-- Table: oradores (Speakers/Guests)
CREATE TABLE oradores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    email VARCHAR(255),
    telefono VARCHAR(20),
    especialidad VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: examenes (Exams - kept for reference, not shown in reports)
CREATE TABLE examenes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    fecha DATE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_examenes_fecha ON examenes(fecha);

-- Table: configuracion (App configuration)
CREATE TABLE configuracion (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    tipo VARCHAR(50), -- 'string', 'integer', 'boolean', 'json'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE users IS 'Google OAuth users - max 3 admin users';
COMMENT ON TABLE miembros IS 'Students/Members with attendance type tracking';
COMMENT ON TABLE clases IS 'Classes with dates, modality (Meet/Presencial), and status';
COMMENT ON TABLE asistencia IS 'Attendance records linking members to classes';
COMMENT ON TABLE pagos IS 'Payment records with monthly tracking';
COMMENT ON TABLE retiros IS 'Refund/withdrawal records';
COMMENT ON TABLE oradores IS 'Guest speakers/lecturers';
COMMENT ON TABLE examenes IS 'Exam records (for reference, not in reports)';
COMMENT ON TABLE configuracion IS 'App configuration settings stored in database';
