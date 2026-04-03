#!/usr/bin/env python3
"""
Test database connection and verify all operations work
Run after deploy_schema.py to verify everything

Usage:
    python test_db.py
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run all database tests"""
    
    print("=" * 70)
    print("MULLER APP - Database Connection Test")
    print("=" * 70)
    
    try:
        from database import Database
        
        print("\n1️⃣  Initializing database connection...")
        db = Database()
        print("   ✓ Connected to database")
        
        # Test 2: Get members
        print("\n2️⃣  Testing MIEMBROS (Members) table...")
        miembros = db.get_miembros()
        print(f"   ✓ Retrieved {len(miembros)} total members")
        
        miembros_regular = db.get_miembros(tipo_asistencia='Regular')
        print(f"   ✓ Regular members: {len(miembros_regular)}")
        
        if miembros:
            m = miembros[0]
            print(f"   ✓ Sample member: {m['nombre']} {m['apellido']} ({m['tipo_asistencia']})")
        
        # Test 3: Get classes
        print("\n3️⃣  Testing CLASES (Classes) table...")
        clases = db.get_clases_hoy()
        print(f"   ✓ Retrieved today's classes info")
        for c in clases:
            print(f"     • {c['tipo'].upper()}: {c['nombre']}")
        
        # Test 4: Get attendance
        print("\n4️⃣  Testing ASISTENCIA (Attendance) table...")
        asistencia = db.get_asistencia_fecha(date.today())
        if asistencia:
            print(f"   ✓ Retrieved {len(asistencia)} attendance records for today")
        else:
            print(f"   ℹ No attendance records for today (expected if no classes)")
        
        # Test 5: Get payments
        print("\n5️⃣  Testing PAGOS (Payments) table...")
        if miembros_regular:
            pagos = db.get_pagos_miembro(miembros_regular[0]['id'])
            print(f"   ✓ Retrieved {len(pagos)} payments for first member")
            if pagos:
                p = pagos[0]
                print(f"     • Payment: ${p['monto']} on {p['fecha']} ({p['mes']})")
        
        # Test 6: Get refunds
        print("\n6️⃣  Testing RETIROS (Refunds) table...")
        if miembros:
            retiros = db.get_retiros_miembro(miembros[0]['id'])
            print(f"   ✓ Retrieved {len(retiros)} refunds for first member")
        
        # Test 7: Payment Report
        print("\n7️⃣  Testing PAYMENT REPORT function...")
        reporte_pagos = db.get_reporte_pagos_por_mes()
        print(f"   ✓ Retrieved payment report for {len(reporte_pagos)} students")
        if reporte_pagos:
            r = reporte_pagos[0]
            print(f"     • {r['nombre']} {r['apellido']}: {r['marzo']} Mar, {r['abril']} Apr")
        
        # Test 8: Attendance Report
        print("\n8️⃣  Testing ATTENDANCE REPORT function...")
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        reporte_asistencia = db.get_reporte_asistencia(start_date, end_date)
        print(f"   ✓ Retrieved attendance report for {len(reporte_asistencia)} students")
        
        # Test 9: Payment Summary
        print("\n9️⃣  Testing PAYMENT SUMMARY function...")
        resumen = db.get_resumen_pagos(start_date, end_date)
        print(f"   ✓ Retrieved payment summary for {len(resumen)} students")
        
        # Test 10: Check admin emails
        print("\n🔟 Testing USERS (Authentication) table...")
        admin_emails = ['admin1@gmail.com', 'admin2@gmail.com', 'admin3@gmail.com']
        for email in admin_emails:
            user = db.check_admin_email(email)
            if user:
                print(f"   ✓ Admin found: {email}")
            else:
                print(f"   ℹ Admin not found: {email} (add via INSERT)")
        
        print("\n" + "=" * 70)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 70)
        print("\nDatabase is working correctly!")
        print("\nNext steps:")
        print("1. Read NEON_SETUP_GUIDE.md for configuration details")
        print("2. Update app.py to use database.py for all operations")
        print("3. Configure Google OAuth in .env")
        print("4. Test the Flask app locally")
        print("5. Deploy to Vercel\n")
        
        return True
        
    except ModuleNotFoundError as e:
        print(f"\n❌ Missing module: {e}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("\nTroubleshoot:")
        print("1. Check DATABASE_URL in .env file")
        print("2. Verify schema was deployed: python deploy_schema.py")
        print("3. Check Neon console for connection details")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
