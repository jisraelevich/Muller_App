-- ============================================================================
-- MULLER_APP - PostgreSQL Database Schema Documentation
-- ============================================================================
-- Database: Neon (PostgreSQL on Vercel)
-- Purpose: Replace JSON file storage with relational database
-- Status: Production-ready schema
-- ============================================================================

-- ============================================================================
-- TABLE RELATIONSHIPS (Entity Relationship Diagram)
-- ============================================================================
/*
    users
    ├── (Admin users via Google OAuth - max 3)

    miembros (Students)
    ├── asistencia (Attendance → clases)
    ├── pagos (Payments)
    └── retiros (Refunds)

    clases (Classes)
    ├── asistencia (Attendance records)

    oradores (Guest speakers)

    examenes (Exams - reference only)

    configuracion (Settings)
*/

-- ============================================================================
-- TABLE: users
-- ============================================================================
-- Purpose: Google OAuth authentication (max 3 admin users)
-- Fields:
--   - id: Primary key
--   - email: Unique email for login whitelist
--   - google_id: Google OAuth ID from authentication
--   - nombre: User's name
--   - is_admin: All users are admins by default
--   - created_at, last_login: Timestamps for audit
-- 
-- Usage:
--   - Check if email exists before allowing login
--   - Update last_login on each authentication
--   - Only allow 3 emails total

-- ============================================================================
-- TABLE: miembros
-- ============================================================================
-- Purpose: Student/member record management
-- Key Fields:
--   - tipo_asistencia: 'Regular' or 'Oyente' (Guest)
--   - estado: 'Activo', 'Inactivo', 'Retirado'
--   - matricula: Unique student ID number
--
-- Related: asistencia, pagos, retiros

-- ============================================================================
-- TABLE: clases
-- ============================================================================
-- Purpose: Class/lecture scheduling
-- Key Fields:
--   - fecha: Date of the class
--   - hora_inicio, hora_fin: Times
--   - modalidad: 'Meet' (Google Meet) or 'Presencial' (In-person)
--   - link_meet: Google Meet URL if online
--   - estado: 'Programada', 'Realizada', 'Cancelada'
--
-- Related: asistencia (attendance records)

-- ============================================================================
-- TABLE: asistencia
-- ============================================================================
-- Purpose: Attendance tracking for each class
-- Key Fields:
--   - miembro_id: Reference to student
--   - clase_id: Reference to class
--   - fecha: Date attended
--   - asistio: Boolean (true/false)
--
-- Unique Constraint: One record per (miembro, clase, fecha)
-- Related: miembros, clases

-- ============================================================================
-- TABLE: pagos
-- ============================================================================
-- Purpose: Payment/fee tracking
-- Key Fields:
--   - monto: Amount paid (DECIMAL for currency)
--   - fecha: Payment date
--   - mes: Month ('Marzo', 'Abril', ..., 'Noviembre')
--   - metodo_pago: 'Efectivo', 'Transferencia', etc.
--   - estado: 'Completado', 'Pendiente', 'Cancelado'
--
-- Note: User wanted JSON storage for payments too
-- Report: Payment status by month for each student
-- Related: miembros

-- ============================================================================
-- TABLE: retiros
-- ============================================================================
-- Purpose: Refund/withdrawal tracking
-- Key Fields:
--   - monto: Amount withdrawn
--   - fecha: Date of withdrawal
--   - tipo_retiro: 'Reembolso' (refund) or 'Crédito' (credit)
--   - razon: Reason for withdrawal
--
-- Related: miembros

-- ============================================================================
-- TABLE: oradores
-- ============================================================================
-- Purpose: Guest speakers/lecturers database
-- Fields: Name, specialization, contact info
-- Status: Reference table, not heavily used in reports

-- ============================================================================
-- TABLE: examenes
-- ============================================================================
-- Purpose: Exam records
-- Note: User requested to exclude from reports
-- Status: Kept for reference, NOT shown in app reports

-- ============================================================================
-- TABLE: configuracion
-- ============================================================================
-- Purpose: Application settings stored in database
-- Examples:
--   - mes_inicio_pagos: 'Marzo'
--   - mes_fin_pagos: 'Noviembre'
--   - cuota_regular: '500' (monthly fee for regular students)
--   - idioma: 'es' (Spanish)

-- ============================================================================
-- KEY QUERIES / FUNCTIONS
-- ============================================================================
/*
1. obtener_reporte_pagos_por_mes()
   - Returns: Students with payment status by month (Mar-Nov)
   - Used for: Payment report printout
   - Filters: tipo_asistencia = 'Regular' only

2. obtener_reporte_asistencia(date_start, date_end)
   - Returns: Attendance records with percentages
   - Used for: Attendance report

3. obtener_resumen_pagos(date_start, date_end)
   - Returns: Total payments per student
   - Used for: Payment summary

4. obtener_clases_hoy()
   - Returns: Last class, today's class, next class
   - Used for: Dashboard display

5. marcar_clase_realizada(clase_id)
   - Updates class status from 'Programada' to 'Realizada'
   - Used for: Class management

6. cambiar_tipo_asistencia(miembro_id, nuevo_tipo)
   - Updates student type between 'Regular' and 'Oyente'
   - Used for: Member management

7. eliminar_pago(pago_id)
   - Deletes a payment record
   - Used for: Payment correction/deletion
*/

-- ============================================================================
-- INDEXES (Performance Optimization)
-- ============================================================================
/*
Indexes improve query speed for commonly filtered columns:
- users: email, google_id (frequent lookups)
- miembros: tipo_asistencia, estado (frequent filtering)
- clases: fecha, estado
- asistencia: miembro_id, clase_id, fecha (join operations)
- pagos: miembro_id, fecha, mes (report generation)
- retiros: miembro_id, fecha
*/

-- ============================================================================
-- DEPLOYMENT STEPS
-- ============================================================================
/*
1. Create Neon database at https://console.neon.tech
2. Copy connection string to .env file
3. Install Python dependencies:
   pip install psycopg2-binary (or asyncpg for async)
4. Run migrations:
   - Execute 01_initial_schema.sql (OR run migrations 001-009)
   - Execute 02_stored_procedures.sql
   - Execute 03_seed_data.sql
5. Verify connection in Python app
6. Update Flask/Python app to use database instead of JSON files
*/

-- ============================================================================
-- MIGRATION PATH FROM JSON TO SQL
-- ============================================================================
/*
Data migration script (pseudocode):
1. Read JSON files from /data/ folder
2. Parse each JSON object
3. Insert into corresponding PostgreSQL tables
4. Verify record counts match
5. Update Python app to query database
6. Keep JSON files as backup until verified working
7. Remove JSON file operations from code
*/
