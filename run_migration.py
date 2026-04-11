#!/usr/bin/env python3
"""
Script para ejecutar migraciones SQL
"""
import os
import sys
from database import Database

def run_migrations():
    """Ejecutar todas las migraciones pendientes"""
    db = Database()
    
    migration_dir = 'sql/migrations'
    migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])
    
    for migration_file in migration_files:
        filepath = os.path.join(migration_dir, migration_file)
        print(f"\n[EJECUTANDO] {migration_file}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Ejecutar cada statement
            with db.get_cursor() as cursor:
                cursor.execute(sql_content)
            
            print(f"[✓ OK] {migration_file} ejecutada correctamente")
        except Exception as e:
            print(f"[✗ ERROR] {migration_file}: {str(e)}")
            # No detenemos, continuamos con las siguientes

if __name__ == '__main__':
    print("Iniciando migraciones...")
    run_migrations()
    print("\n✅ Migraciones completadas")
