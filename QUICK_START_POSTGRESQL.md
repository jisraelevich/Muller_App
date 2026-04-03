# 🚀 PostgreSQL Migration - Quick Start

## Prerequisites
- Windows/Mac/Linux
- Python 3.8+
- VS Code or terminal
- Neon account (free tier is fine)

---

## 🔴 STEP 1: Create Neon Database (5 minutes)

1. Go to https://console.neon.tech
2. Sign up (GitHub, Google, or email)
3. Create new project:
   - Name: `muller-app`
   - Region: Choose closest to you
4. copy connection string from **"Connection"** tab

**Save this string!**

---

## 🟠 STEP 2: Configure .env File (2 minutes)

```bash
# In terminal:
cd "c:\joelsla apps\Muller_App\Muller_App"

# Copy template
cp .env.example .env
```

Edit `.env` file with:
```env
DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/muller_app?sslmode=require
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
```

**Important:** Add to `.gitignore`:
```
.env
*.env
```

---

## 🟡 STEP 3: Install Python Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

**What gets installed:**
- `psycopg2-binary` - PostgreSQL driver
- `python-dotenv` - Load .env variables
- `Flask`, `Werkzeug`, `Flask-CORS`

---

## 🟢 STEP 4: Deploy PostgreSQL Schema (3 minutes)

Run the deployment script:
```bash
python deploy_schema.py
```

**What it does:**
1. Connects to Neon database
2. Creates all tables (9 tables)
3. Creates stored procedures (7 functions)
4. Loads sample data
5. Verifies everything works

**Expected output:**
```
✓ Connected to Neon database
✓ Deployed successfully (01_initial_schema.sql)
✓ Deployed successfully (02_stored_procedures.sql)
✓ Deployed successfully (03_seed_data.sql)
✓ Tables created (9):
  1. users
  2. miembros
  3. clases
  4. asistencia
  5. pagos
  6. retiros
  7. oradores
  8. examenes
  9. configuracion
✓✓✓ SCHEMA DEPLOYMENT COMPLETE ✓✓✓
```

---

## 🔵 STEP 5: Test Database Connection (1 minute)

```bash
python test_db.py
```

**Expected output:**
```
✓ Connected to database
✓ Retrieved X total members
✓ Retrieved today's classes info
✓ Retrieved X attendance records
✓ Retrieved payment report
✓✓✓ ALL TESTS PASSED ✓✓✓
```

---

## 🟣 STEP 6: Verify in Neon Console (1 minute)

1. Go to https://console.neon.tech
2. Click your project
3. Go to **"Query Editor"**
4. Run:
   ```sql
   SELECT * FROM miembros;
   ```
5. Should see test data ✓

---

## Next Steps

After this:
1. ⬜ Update `app.py` to use `database.py`
2. ⬜ Add Google OAuth login
3. ⬜ Test locally
4. ⬜ Deploy to Vercel

---

## 📋 Files Created

| File | Purpose |
|------|---------|
| `sql/01_initial_schema.sql` | Tables & indexes |
| `sql/02_stored_procedures.sql` | Query functions |
| `sql/03_seed_data.sql` | Sample test data |
| `database.py` | Python connection module |
| `deploy_schema.py` | Deployment script (run this!) |
| `test_db.py` | Test script (run this!) |
| `.env.example` | Configuration template |
| `.env` | Your secret config (don't commit!) |

---

## 🆘 Troubleshooting

### Error: "DATABASE_URL not found"
- [ ] Created `.env` file?
- [ ] Added CONNECTION STRING to `.env`?
- [ ] Saved `.env` file?

### Error: "Connection refused"
- [ ] Go to Neon console
- [ ] Try **"Test connection"** button
- [ ] Copy CONNECTION STRING again (fresh copy)
- [ ] Paste into `.env`

### Error: "authentication failed"
- [ ] In Neon: Click **"Show password"** button
- [ ] Copy full string including password
- [ ] Replace in `.env`

### Error: "ModuleNotFoundError: psycopg2"
```bash
pip install -r requirements.txt
```

### Error: "relation 'miembros' does not exist"
```bash
python deploy_schema.py
```

---

## Done! ✓✓✓

When all tests pass, you have:
- ✓ PostgreSQL database on Neon
- ✓ 9 tables with relationships
- ✓ 7 stored procedures for reports
- ✓ Python connection module ready
- ✓ Sample data loaded

**Ready to update your Flask app to use it!**

For details, see:
- `NEON_SETUP_GUIDE.md` - Full step-by-step guide
- `POSTGRESQL_SETUP.md` - Technical overview
- `sql/README.md` - Database documentation
- `sql/MIGRATION_GUIDE.md` - Migration path

---

Questions? Check the `/sql/` folder documentation! 🚀
