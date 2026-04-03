# Complete PostgreSQL Migration Pipeline

## Full Workflow (Start to Finish)

This document shows the complete sequence to migrate your Muller App from JSON to PostgreSQL.

---

## Phase 1: Setup (Do Once)

### 1️⃣ Create Neon Database
```
https://console.neon.tech
Create project → Copy connection string
```

### 2️⃣ Create `.env` File
```bash
cp .env.example .env
# Edit .env with your Neon connection string
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Deploy PostgreSQL Schema
```bash
python deploy_schema.py

# Output should show:
# ✓ Connected to Neon database
# ✓ Deployed successfully (01_initial_schema.sql)
# ✓ Deployed successfully (02_stored_procedures.sql)
# ✓ Tables created (9): users, miembros, clases, ...
# ✓✓✓ SCHEMA DEPLOYMENT COMPLETE ✓✓✓
```

### 5️⃣ Test Database Connection
```bash
python test_db.py

# Output should show:
# ✓ Connected to database
# ✓ Retrieved X members
# ✓ Retrieved payment report
# ✓✓✓ ALL TESTS PASSED ✓✓✓
```

---

## Phase 2: Data Migration (One Time)

### 6️⃣ Backup JSON Files
```bash
xcopy data data_backup /E /I /Y
```

### 7️⃣ Migrate Data
```bash
python migrate_json_to_postgres.py

# Output should show:
# 📌 Migrating MIEMBROS (Members)...
#    ✓ Migrated X members
# 📌 Migrating PAGOS (Payments)...
#    ✓ Migrated X payments
# ... etc
# ✓✓✓ Migration complete!
```

### 8️⃣ Verify Migration
```bash
# Option 1: Query database directly
python test_db.py

# Option 2: Check in Neon console
https://console.neon.tech → Query Editor
SELECT COUNT(*) FROM miembros;
SELECT COUNT(*) FROM pagos;
```

---

## Phase 3: Local Testing

### 9️⃣ Run Flask App
```bash
python app.py

# Output should show:
# ✅ Base de datos conectada
# ✅ Servidor iniciado en: http://localhost:5000
```

### 🔟 Test Each Tab
Visit http://localhost:5000 and test:

- **Dashboard** ✓ Shows migrated stats
- **Asistencia** ✓ Can load/save attendance
- **Pagos** ✓ Lists payments from DB, can add/edit/delete
- **Miembros** ✓ Shows all members, can change type
- **Clases** ✓ Can edit class status
- **Reportes** ✓ Payment report by month works
- **Retiros** ✓ Can save/view withdrawals
- **Export** ✓ Excel export includes DB data

### 1️⃣1️⃣ Test New Operations
```
Try these actions:
- Register new payment
- Edit existing payment
- Delete a payment
- Change member type
- Record attendance
- Export to Excel
```

---

## Phase 4: Production Deployment

### 1️⃣2️⃣ Prepare for Vercel

**Update files:**
- `requirements.txt` — Already updated ✓
- `app.py` — Already updated ✓
- `.env.example` — Already created ✓
- `database.py` — Already created ✓

**Create `vercel.json`:**
```json
{
  "buildCommand": "pip install -r requirements.txt",
  "outputDirectory": ".",
  "env": {
    "DATABASE_URL": "@database_url"
  },
  "public": false,
  "functions": {
    "app.py": {
      "maxDuration": 60,
      "memory": 1024
    }
  }
}
```

### 1️⃣3️⃣ Commit to Git
```bash
git add .
git commit -m "Migrate to PostgreSQL (Neon) with Flask app updates"
git push origin main
```

### 1️⃣4️⃣ Deploy to Vercel
**Option A: Using git push**
```bash
# If Vercel connected to GitHub, auto-deploys on push
git push origin main
```

**Option B: Using Vercel CLI**
```bash
npm install -g vercel
vercel

# Follow prompts:
# - Link to project?
# - Set DATABASE_URL secret
# - Deploy
```

### 1️⃣5️⃣ Add Environment Variables in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings → Environment Variables**
4. Add `DATABASE_URL`:
   - Value: `postgresql://user:password@host/database`
   - Scope: Production

5. Redeploy to apply

### 1️⃣6️⃣ Test in Production
```
https://your-app.vercel.app/

Test same operations as local:
- Dashboard loads
- Can view members
- Can add/edit payments
- Export works
- Reports generate
```

---

## Phase 5: Cleanup (Optional)

### 1️⃣7️⃣ Delete Original JSON Files
```bash
# After 1+ week of testing in production
rm -r data

# OR just archive them
mkdir data_archived_20260403
move data\* data_archived_20260403\
```

---

## Testing Checklist

Before declaring success:

### Backend Operations
- [ ] Dashboard displays correct statistics
- [ ] Miembros tab loads all members
- [ ] Can create new payment
- [ ] Can edit existing payment
- [ ] Can delete payment
- [ ] Can save attendance
- [ ] Can load attendance for past date
- [ ] Can update member type (Regular/Oyente)
- [ ] Can save refund/retiro
- [ ] Export to Excel works

### Report Functions
- [ ] Payment report by month generates
- [ ] Attendance report calculates percentages
- [ ] Payment summary shows total by student
- [ ] Today's classes (última/hoy/próxima) shows correctly

### Error Handling
- [ ] Shows error if DB not available
- [ ] Shows message on connection failure
- [ ] Doesn't crash on invalid data

### API Endpoints
```bash
# Test with curl or Postman
curl http://localhost:5000/api/miembros/all
curl http://localhost:5000/api/reportes/pagos-por-mes
curl http://localhost:5000/api/reportes/asistencia?inicio=2025-03-01&fin=2025-04-30
```

---

## Rollback Instructions

If something breaks:

### Quick Rollback
```bash
# Revert Flask app to use JSON
git checkout HEAD~1 app.py

# Restart
python app.py
```

### Full Rollback
```bash
# Delete data in Neon (in console)
# Restore from JSON backup
git checkout HEAD~2  # Revert commits
python app.py  # Will use JSON again
```

---

## File Summary

### New Files Created
| File | Purpose |
|------|---------|
| `database.py` | PostgreSQL connection module |
| `deploy_schema.py` | Deploy SQL schema |
| `test_db.py` | Test database connection |
| `migrate_json_to_postgres.py` | Migrate JSON data to DB |
| `.env.example` | Environment template |
| `sql/` | SQL schema files |
| `/sql/migrations/` | Individual migrations |

### Files Modified
| File | Changes |
|------|---------|
| `app.py` | Replace JSON ops with DB calls |
| `requirements.txt` | Added psycopg2, python-dotenv |

### Files Kept As-Is
| File | Reason |
|------|--------|
| `templates/` | HTML templates |
| `static/` | CSS/JS files |
| `data/` | Keep as backup (optional delete later) |

---

## Expected Results

### Before Migration (Local with JSON)
```
Local: ✓ (fast)
Vercel: ✗ (read-only file system errors)
```

### After Migration (PostgreSQL)
```
Local: ✓ (fast, reliable)
Vercel: ✓ (works perfectly)
```

---

## Support References

| Issue | Reference |
|-------|-----------|
| Schema errors | `/sql/README.md` |
| Neon setup | `NEON_SETUP_GUIDE.md` |
| PostgreSQL docs | https://www.postgresql.org/docs/ |
| Flask docs | https://flask.palletsprojects.com/ |
| Vercel docs | https://vercel.com/docs |

---

## Timeline

| Phase | Duration | Task |
|-------|----------|------|
| Phase 1 | 15 min | Setup Neon & schema |
| Phase 2 | 5 min | Migrate data |
| Phase 3 | 30 min | Test locally |
| Phase 4 | 15 min | Deploy to Vercel |
| Phase 5 | Optional | Cleanup |

**Total: ~1 hour to full production! ⏱️**

---

## Success Indicators

✅ You're done when:
- Flask app runs locally without JSON errors
- All operations work (create, read, update, delete)
- Vercel deployment shows no file system errors
- Reports generate instantly (no timeouts)
- Payment/attendance data persists correctly
- Export to Excel works on both local & Vercel

**Congratulations! 🎉 Your app is now scalable and production-ready!**
