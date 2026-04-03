# JSON to PostgreSQL Migration Guide

## Overview
This guide walks you through migrating your existing JSON data to the new PostgreSQL database on Neon.

---

## Prerequisites

✅ PostgreSQL schema deployed (`python deploy_schema.py` completed)
✅ Database connection tested (`python test_db.py` passed)
✅ `.env` file configured with `DATABASE_URL`

---

## Step 1: Backup Your JSON Data

**Important:** Always backup before migrating!

```bash
# Create backup
xcopy data data_backup /E /I /Y
```

Now you have:
- `data/` — Original JSON files (unchanged)
- `data_backup/` — Safe backup copy

---

## Step 2: Run Migration Script

```bash
python migrate_json_to_postgres.py
```

**Expected output:**
```
======================================================================
JSON to PostgreSQL Migration
======================================================================

📌 Migrating MIEMBROS (Members)...
   ✓ Migrated 5 members

📌 Migrating CLASES (Classes)...
   ✓ Migrated 3 classes

📌 Migrating ASISTENCIA (Attendance)...
   ✓ Migrated 12 attendance records

📌 Migrating PAGOS (Payments)...
   ✓ Migrated 8 payments

📌 Migrating RETIROS (Withdrawals)...
   ✓ Migrated 2 withdrawals

======================================================================
MIGRATION SUMMARY
======================================================================

✓ Successfully migrated:
  • 5 members
  • 3 classes
  • 12 attendance records
  • 8 payments
  • 2 withdrawals

✓ Total database records: 30

======================================================================
✓ Migration complete!
======================================================================
```

---

## Step 3: Verify Migration

### Option A: Using Neon Console (Web)

1. Go to https://console.neon.tech
2. Click your project
3. Go to **"Query Editor"**
4. Run queries:

```sql
SELECT COUNT(*) FROM miembros;
SELECT COUNT(*) FROM clases;
SELECT COUNT(*) FROM asistencia;
SELECT COUNT(*) FROM pagos;
SELECT COUNT(*) FROM retiros;
```

### Option B: Using Python Script

```python
from database import Database

db = Database()

# Check counts
miembros = db.get_miembros()
print(f"Members: {len(miembros)}")

# Check payment report
reporte = db.get_reporte_pagos_por_mes()
print(f"Unique payers: {len(reporte)}")

# Check attendance
asistencia = db.get_asistencia_fecha('2025-04-03')
print(f"Today's attendance: {len(asistencia)}")
```

### Option C: Using psql CLI

```bash
psql "your_connection_string" -c "SELECT COUNT(*) FROM miembros;"
```

---

## Step 4: Test Flask App with Migrated Data

```bash
python app.py
```

Visit: http://localhost:5000

Check each tab:
- **Dashboard** — Shows migrated stats
- **Asistencia** — Shows attendance records from DB
- **Pagos** — Lists migrated payments
- **Miembros** — Shows all migrated members
- **Reportes** — Generate reports from DB

---

## Step 5: Keep or Delete JSON Files

### Option 1: Keep JSON (Safer)
Keep `/data/` folder as backup while you verify

### Option 2: Delete JSON (Cleaner)
After verification, you can delete:
```bash
rmdir /s /q data
```

**Recommendation:** Keep for 1 week while testing, then delete.

---

## Troubleshooting

### "ERROR: DATABASE_URL not found"
**Fix:**
```bash
# Check .env file exists
type .env

# Should show DATABASE_URL=postgresql://...
```

### Migration fails with "relation does not exist"
**Fix:**
```bash
# Redeploy schema
python deploy_schema.py

# Then retry
python migrate_json_to_postgres.py
```

### No data appears after migration
**Check:**
```bash
# Run test script
python test_db.py

# Should show migrated counts

# If empty, check JSON files
dir data\*.json
```

### "Unique constraint violation"
**Cause:** Running migration twice on same DB
**Fix:**
```bash
# Delete and recreate database in Neon console
# OR reset schema
python deploy_schema.py  # This overwrites
python migrate_json_to_postgres.py  # Retry
```

---

## Data Mapping Reference

### MIEMBROS (Members)
| JSON Field | DB Column | Type |
|------------|-----------|------|
| id/matricula | matricula | VARCHAR |
| nombre | nombre | VARCHAR |
| apellido | apellido | VARCHAR |
| email | email | VARCHAR |
| tipo_asistencia | tipo_asistencia | VARCHAR |

### CLASES (Classes)
| JSON Field | DB Column | Type |
|------------|-----------|------|
| id | id | SERIAL |
| nombre | nombre | VARCHAR |
| fecha | fecha | DATE |
| hora_inicio | hora_inicio | TIME |
| modalidad | modalidad | VARCHAR |
| link_meet | link_meet | VARCHAR |
| estado | estado | VARCHAR |

### PAGOS (Payments)
| JSON Field | DB Column | Type |
|------------|-----------|------|
| id | id | SERIAL |
| id_miembro | miembro_id | INTEGER |
| monto | monto | DECIMAL |
| fecha | fecha | DATE |
| mes | mes | VARCHAR |
| concepto | descripcion | VARCHAR |

### ASISTENCIA (Attendance)
| JSON Field | DB Column | Type |
|------------|-----------|------|
| id_miembro | miembro_id | INTEGER |
| clase_id | clase_id | INTEGER |
| fecha | fecha | DATE |
| presente/asistio | asistio | BOOLEAN |

### RETIROS (Withdrawals)
| JSON Field | DB Column | Type |
|------------|-----------|------|
| id | id | SERIAL |
| id_miembro | miembro_id | INTEGER |
| monto | monto | DECIMAL |
| fecha | fecha | DATE |

---

## What Happens During Migration

### 1. Data is READ from
```
data/miembros.json
data/clases.json
data/asistencia.json
data/pagos.json
data/retiros.json
```

### 2. Data is TRANSFORMED
- Dates validated/standardized (YYYY-MM-DD)
- Booleans normalized (true/false)
- IDs mapped to correct tables
- Nulls handled gracefully

### 3. Data is WRITTEN to
```
PostgreSQL Database (Neon)
├─ miembros table
├─ clases table
├─ asistencia table
├─ pagos table
└─ retiros table
```

### 4. Original JSON files
- REMAIN UNTOUCHED
- Can be deleted after verification
- Kept as backup for recovery

---

## Verification Checklist

After migration, verify:

- [ ] `python migrate_json_to_postgres.py` completed without errors
- [ ] Dashboard shows correct member count
- [ ] Payment report shows all payments by month
- [ ] Attendance records are displayable
- [ ] Can create NEW payments in database (not JSON)
- [ ] Can edit/delete payments successfully
- [ ] Export to Excel works
- [ ] All tabs show database data correctly

---

## Next Steps

Once migration is complete:

1. **Test locally** — Ensure Flask app works with migrated data
2. **Update templates** — Some JS might reference JSON, update to use DB APIs
3. **Test all operations** — Add, edit, delete, export
4. **Deploy to Vercel** — Push code with DATABASE_URL
5. **Delete JSON** (optional) — Once verified working for 1+ week

---

## Rollback Plan

If something goes wrong:

1. **Stop using new database** — Don't add more data
2. **Keep JSON files** — They still exist in `data/`
3. **Revert Flask** — Use git to checkout old version
4. **Restore JSON ops** — Downgrade `app.py` to use JSON
5. **Start over** — Plan better migration, retry

---

## Questions?

- **Schema issues?** See `/sql/README.md`
- **Connection problems?** See `NEON_SETUP_GUIDE.md`
- **Data mapping?** See reference table above
- **Database errors?** Check Neon console for connection logs

**Happy migrating!** 🚀
