# Muller App - PostgreSQL Migration Guide

## Overview
This directory contains the complete PostgreSQL schema for replacing JSON file storage with a relational database on Neon.

## Files Structure

### Core Schema Files
- **`01_initial_schema.sql`** - Complete schema with all tables, indexes, and constraints (all-in-one)
- **`02_stored_procedures.sql`** - Functions for complex queries and business logic
- **`03_seed_data.sql`** - Sample data for testing (optional)

### Migration Files (Alternative approach)
- **`migrations/001_create_users_table.sql`** - Google OAuth users (3 admins)
- **`migrations/002_create_miembros_table.sql`** - Students/members
- **`migrations/003_create_clases_table.sql`** - Classes
- **`migrations/004_create_asistencia_table.sql`** - Attendance records
- **`migrations/005_create_pagos_table.sql`** - Payment tracking
- **`migrations/006_create_retiros_table.sql`** - Refunds/withdrawals
- **`migrations/007_create_oradores_table.sql`** - Guest speakers
- **`migrations/008_create_examenes_table.sql`** - Exams (reference only)
- **`migrations/009_create_configuracion_table.sql`** - Configuration settings

## Quick Start

### 1. Create Neon Database
```bash
# Go to console.neon.tech
# Create new project
# Save connection string to .env file
```

### 2. Deploy Schema (choose one method)

**Method A: Single Script (Recommended for new setup)**
```bash
# Using psql client
psql "your_connection_string" -f sql/01_initial_schema.sql
psql "your_connection_string" -f sql/02_stored_procedures.sql
psql "your_connection_string" -f sql/03_seed_data.sql
```

**Method B: Individual Migrations**
```bash
# For git-tracked migrations
for file in sql/migrations/*.sql; do
  psql "your_connection_string" -f "$file"
done
```

### 3. Update Python App
See `../app.py` for database connection example:
```python
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
```

## Database Tables

| Table | Purpose | Rows | Related |
|-------|---------|------|---------|
| `users` | Google OAuth admins (max 3) | ~3 | - |
| `miembros` | Students/members | ~100+ | asistencia, pagos, retiros |
| `clases` | Classes with dates & modality | ~50+ | asistencia |
| `asistencia` | Attendance records | ~500+ | miembros, clases |
| `pagos` | Payment tracking (Mar-Nov) | ~200+ | miembros |
| `retiros` | Refunds/withdrawals | ~20+ | miembros |
| `oradores` | Guest speakers | ~10+ | - |
| `examenes` | Exam records (reference) | ~20+ | - |
| `configuracion` | App settings | ~10 | - |

## Key Functions

### Payment Report (by Month)
```sql
SELECT * FROM obtener_reporte_pagos_por_mes();
```
Shows payment status for each regular student (Jan-Nov)

### Today's Classes
```sql
SELECT * FROM obtener_clases_hoy();
```
Returns: last class, today's class, next class

### Attendance Report
```sql
SELECT * FROM obtener_reporte_asistencia('2025-03-01'::DATE, '2025-11-30'::DATE);
```

### Change Member Type
```sql
SELECT cambiar_tipo_asistencia(miembro_id, 'Oyente');
```

## Fixes This Solves

| Issue | Solution |
|-------|----------|
| Read-only file system errors | Direct database writes ✓ |
| Can't load previous data | SQL queries with filters ✓ |
| Edit/delete payments impossible | `UPDATE`/`DELETE` with UI ✓ |
| Editing classes has no effect | Direct database updates ✓ |
| Connection timeouts on Vercel | Optimized queries + indexes ✓ |
| Can't view payment reports | Stored procedures generate instantly ✓ |
| Reports in file system only | Database queries exported to PDF/Excel ✓ |

## Authentication

**Google OAuth Flow:**
1. User clicks "Login with Google"
2. System checks if email in `users` table
3. If yes → login allowed
4. If no → "Not authorized" error

**Setup:**
```bash
# Add 3 admin emails to .env
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com
```

## Performance Indexes

Indexes on frequently queried columns:
- `users.email` - Login lookups
- `miembros.tipo_asistencia` - Filter by Regular/Oyente
- `pagos.fecha`, `pagos.mes` - Report generation
- `asistencia.miembro_id`, `asistencia.clase_id` - Join operations
- `clases.fecha`, `clases.estado` - Dashboard queries

## Data Types Reference

| Column | Type | Notes |
|--------|------|-------|
| IDs | `SERIAL PRIMARY KEY` | Auto-incrementing integers |
| Names | `VARCHAR(100)` | Up to 100 characters |
| Money | `DECIMAL(10,2)` | Currency: e.g., 500.00 |
| Dates | `DATE` | YYYY-MM-DD format |
| Booleans | `BOOLEAN` | true/false for attendance |
| Timestamps | `TIMESTAMP` | Auto-filled on create/update |

## Backup & Restore

```bash
# Backup entire database
pg_dump "your_connection_string" > backup.sql

# Restore from backup
psql "your_connection_string" < backup.sql
```

## Support

For Neon-specific issues: https://docs.neon.tech/
For PostgreSQL docs: https://www.postgresql.org/docs/
