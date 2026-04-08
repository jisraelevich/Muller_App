#!/usr/bin/env python3
"""
Deploy PostgreSQL schema from SQL files to Neon database
Run this script once to create all tables and functions

Usage:
    python deploy_schema.py
"""

import os
import sys
from dotenv import load_dotenv

# Try to import psycopg (v3) first, fall back to psycopg2
try:
    import psycopg
    USE_PSYCOPG3 = True
except ImportError:
    try:
        import psycopg2
        USE_PSYCOPG3 = False
    except ImportError:
        print("❌ ERROR: Neither psycopg nor psycopg2 installed")
        print("Install with: pip install 'psycopg[binary]'")
        sys.exit(1)

# Load .env file
load_dotenv()

def deploy_schema():
    """Deploy PostgreSQL schema and stored procedures"""
    
    # Get connection string
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        print("[ERROR] DATABASE_URL not found in .env file")
        print("\nPlease add your Neon connection string to .env:")
        print("  DATABASE_URL=postgresql://user:password@host/database")
        return False
    
    print("=" * 70)
    print("MULLER APP - PostgreSQL Schema Deployment")
    print("=" * 70)
    print(f"\nConnecting to database...")
    
    try:
        if USE_PSYCOPG3:
            conn = psycopg.connect(connection_string)
        else:
            conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        print("[OK] Connected to Neon database")
        
        # Files to deploy in order
        sql_files = [
            ('sql/01_initial_schema.sql', 'Initial Schema (Tables & Indexes)'),
            ('sql/02_stored_procedures.sql', 'Stored Procedures (Functions)'),
            ('sql/03_seed_data.sql', 'Seed Data (Test Data)')
        ]
        
        for sql_file, description in sql_files:
            if not os.path.exists(sql_file):
                print(f"\n[WARN] {sql_file} not found, skipping...")
                continue
            
            print(f"\n{'-' * 70}")
            print(f"Deploying: {description}")
            print(f"File: {sql_file}")
            print(f"{'-' * 70}")
            
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Execute SQL file
                cursor.execute(sql_content)
                conn.commit()
                print(f"[OK] Deployed successfully")
                
            except Exception as e:
                print(f"[ERROR] Error in {sql_file}:")
                print(f"   {str(e)[:100]}")
                conn.rollback()
                return False
        
        # Verify tables exist
        print(f"\n{'-' * 70}")
        print("Verifying Database Schema")
        print(f"{'-' * 70}")
        
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n[OK] Tables created ({len(tables)}):")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table[0]}")
        else:
            print("[WARN] No tables found - deployment may have failed")
            return False
        
        # Check stored procedures
        cursor.execute("""
            SELECT routine_name FROM information_schema.routines 
            WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)
        
        functions = cursor.fetchall()
        if functions:
            print(f"\n[OK] Functions created ({len(functions)}):")
            for i, func in enumerate(functions, 1):
                # Skip system generated functions
                if not func[0].startswith('_'):
                    print(f"  {i}. {func[0]}()")
        
        cursor.close()
        conn.close()
        
        print(f"\n{'=' * 70}")
        print("[SUCCESS] SCHEMA DEPLOYMENT COMPLETE")
        print(f"{'=' * 70}\n")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"\n[ERROR] Error: {error_str[:100]}")
        
        if 'connection' in error_str.lower() or 'operational' in error_str.lower():
            print("\nPossible causes:")
            print("  1. Wrong connection string in .env")
            print("  2. Neon database not created yet")
            print("  3. Network/firewall issues")
        return False


def test_database_connection():
    """Test if database connection works"""
    print("\n" + "=" * 70)
    print("Testing Database Connection")
    print("=" * 70 + "\n")
    
    try:
        from database import Database
        
        print("Initializing Database class...")
        db = Database()
        print("✓ Database class initialized")
        
        print("\nTesting basic queries...")
        
        # Test 1: Get miembros
        miembros = db.get_miembros()
        print(f"✓ Retrieved {len(miembros)} members")
        
        # Test 2: Get clases
        clases = db.get_clases_hoy()
        print(f"✓ Retrieved class info")
        
        # Test 3: Get payment report
        reporte = db.get_reporte_pagos_por_mes()
        print(f"✓ Retrieved payment report")
        
        print("\n" + "=" * 70)
        print("✓ All database connections working!")
        print("=" * 70 + "\n")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Step 1: Deploy schema
    success = deploy_schema()
    
    if success:
        # Step 2: Test connection
        test_success = test_database_connection()
        
        if test_success:
            print("\n🎉 Database is ready to use!\n")
            print("Next steps:")
            print("1. Update app.py to use database.py instead of JSON files")
            print("2. Configure Google OAuth for authentication")
            print("3. Test the app locally")
            print("4. Deploy to Vercel\n")
        else:
            print("\n⚠ Schema deployed but connection test failed")
    else:
        print("\n❌ Deployment failed - see errors above")
        sys.exit(1)
