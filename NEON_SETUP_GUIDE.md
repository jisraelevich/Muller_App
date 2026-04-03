# Neon PostgreSQL Setup - Step by Step

## Step 1: Create Neon Account & Database

### 1.1 Go to Neon Console
```
https://console.neon.tech
```

### 1.2 Sign Up or Login
- Click "Sign up" or "Login"
- Use GitHub, Google, or email
- Verify email

### 1.3 Create Project
1. Click "New Project"
2. Set project name: `muller-app`
3. Choose region: 
   - If users in USA → `us-east-1`
   - If users in South America → `sa-east-1` (São Paulo)
   - Otherwise → default
4. Click "Create project"

Wait 1-2 minutes for setup...

### 1.4 Get Connection String
1. In Neon console, click your project
2. Go to "Connection" tab
3. Select "psycopg2" driver (Python)
4. Copy the full connection string (looks like):
   ```
   postgresql://neon_user:password@ep-xyz.region.neon.tech/muller_app?sslmode=require
   ```

---

## Step 2: Update .env File

### 2.1 Open `.env.example`
Already created with template

### 2.2 Create Local `.env` File
DO NOT COMMIT THIS FILE - it contains passwords!

```bash
# Copy .env.example to .env
cp .env.example .env
```

### 2.3 Edit `.env` with Your Connection String
```env
# From Neon console
DATABASE_URL=postgresql://neon_user:your_password@ep-xyz.region.neon.tech/muller_app?sslmode=require

# Google OAuth (we'll set up next)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Admin emails (3 users max)
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com

# Flask Config
FLASK_ENV=production
SECRET_KEY=your_secret_key_change_this_in_production
```

### 2.4 Keep .env Secret
Add to `.gitignore`:
```
.env
*.env
```

---

## Step 3: Install Python Dependencies

### 3.1 Open Terminal in VS Code
```powershell
cd "c:\joelsla apps\Muller_App\Muller_App"
```

### 3.2 Update requirements.txt
```bash
pip install psycopg2-binary python-dotenv flask flask-cors
pip freeze > requirements.txt
```

Or manually add to `requirements.txt`:
```
psycopg2-binary==2.9.9
python-dotenv==1.0.0
Flask==2.3.3
Flask-CORS==4.0.0
```

### 3.3 Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Step 4: Deploy PostgreSQL Schema to Neon

### 4.1 Install psql Client (PostgreSQL CLI)
**Windows:**
```powershell
# Option 1: Download from https://www.postgresql.org/download/windows/
# Option 2: Using Chocolatey
choco install postgresql

# Verify installation
psql --version
```

**Alternative: Use Python to deploy schema**
```bash
# If psql not available, I'll create a Python script
```

### 4.2 Deploy Schema (Using psql)
```bash
# Get connection string from .env
$env:DATABASE_URL = "your_connection_string_here"

# Deploy initial schema
psql $env:DATABASE_URL -f sql/01_initial_schema.sql

# Deploy stored procedures
psql $env:DATABASE_URL -f sql/02_stored_procedures.sql

# Deploy seed data (optional - for testing)
psql $env:DATABASE_URL -f sql/03_seed_data.sql
```

### 4.3 Verify Schema Was Deployed
```bash
# Check tables exist
psql $env:DATABASE_URL -c "\dt"

# Should show:
# users
# miembros
# clases
# asistencia
# pagos
# retiros
# oradores
# examenes
# configuracion
```

---

## Step 5: Python Script to Deploy (If psql Not Available)

Create `deploy_schema.py`:

```python
#!/usr/bin/env python3
"""
Deploy PostgreSQL schema from SQL files to Neon database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get connection string
connection_string = os.getenv('DATABASE_URL')
if not connection_string:
    print("❌ ERROR: DATABASE_URL not found in .env")
    exit(1)

print(f"Connecting to database...")

try:
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    print("✓ Connected to Neon database")
    
    # Files to deploy in order
    sql_files = [
        'sql/01_initial_schema.sql',
        'sql/02_stored_procedures.sql',
        'sql/03_seed_data.sql'
    ]
    
    for sql_file in sql_files:
        if not os.path.exists(sql_file):
            print(f"⚠ Warning: {sql_file} not found, skipping...")
            continue
        
        print(f"\nDeploying: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            cursor.execute(sql_content)
        
        conn.commit()
        print(f"✓ {sql_file} deployed successfully")
    
    # Verify tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"\n✓ Database schema deployed!")
    print(f"\nTables created ({len(tables)}):")
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"❌ Database Error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n✓ Schema deployment complete!")
```

**Run it:**
```bash
python deploy_schema.py
```

---

## Step 6: Test Connection from Python

### 6.1 Create Test Script
Create `test_db.py`:

```python
#!/usr/bin/env python3
"""
Test database connection and basic operations
"""

import os
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

try:
    # Initialize database
    db = Database()
    print("✓ Connected to database")
    
    # Test 1: Get miembros
    miembros = db.get_miembros()
    print(f"\n✓ Retrieved {len(miembros)} members")
    for m in miembros[:3]:
        print(f"  - {m['nombre']} {m['apellido']} ({m['tipo_asistencia']})")
    
    # Test 2: Get clases
    clases = db.get_clases_hoy()
    print(f"\n✓ Retrieved {len(clases)} classes")
    for c in clases:
        print(f"  - {c['tipo']}: {c['nombre']} ({c['fecha']})")
    
    # Test 3: Get payment report
    reporte = db.get_reporte_pagos_por_mes()
    print(f"\n✓ Retrieved payment report for {len(reporte)} students")
    
    print("\n✓✓✓ All tests passed! Database connection working! ✓✓✓")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
```

**Run it:**
```bash
python test_db.py
```

---

## Step 7: Verify Everything Works

### Checklist:
- [ ] Neon account created
- [ ] Project created in Neon console
- [ ] Connection string copied to `.env` file
- [ ] `.env` file added to `.gitignore`
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Schema deployed (`python deploy_schema.py`)
- [ ] Connection test passed (`python test_db.py`)
- [ ] Tables visible in Neon console

---

## Step 8: Setup Google OAuth (Next)

Once database is verified, we'll add Google login so only 3 people can access.

---

## Troubleshooting

### "psycopg2: Connection refused"
**Cause:** Wrong connection string or Neon project not created
**Fix:** 
1. Copy connection string again from Neon console
2. Check no typos in `.env` file
3. Try pasting directly: `psql "your_connection_string"`

### "psycopg2: password authentication failed"
**Cause:** Wrong password in connection string
**Fix:**
1. Go to Neon console → Connection
2. Click "Show password" button
3. Copy full string again, paste to `.env`

### "relation 'miembros' does not exist"
**Cause:** Schema files weren't deployed
**Fix:**
1. Run: `python deploy_schema.py`
2. Wait for success message
3. Run: `python test_db.py`

### "ModuleNotFoundError: No module named 'psycopg2'"
**Cause:** Dependencies not installed
**Fix:**
```bash
pip install -r requirements.txt
```

### Neon Database Connection Shows 0 Connections
**Cause:** Connection string not used yet
**Fix:** Run any Python script that uses database.py

---

## Next After This:

1. ✅ Database setup (you are here)
2. ⬜ Update Flask app (`app.py`)
3. ⬜ Google OAuth login
4. ⬜ Deploy to Vercel
5. ⬜ Test all features

**Ready to proceed?** Let me know when schema is deployed! 🚀
