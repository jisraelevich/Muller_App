#!/usr/bin/env python3
"""Quick script to fully migrate classes and speakers from JSON"""

import json
from database import Database

db = Database()

print("\n" + "="*60)
print("FULL DATA MIGRATION")
print("="*60 + "\n")

# 1. Speakers
print("[1] Speakers:")
print(f"    In DB: {len(db.get_oradores())}")
with open('data/oradores.json', 'r', encoding='utf-8-sig') as f:
    oradores = json.load(f)
print(f"    In JSON: {len(oradores)}")

# 2. Classes  
print("\n[2] Classes:")
print(f"    In DB: {len(db.get_clases())}")
with open('data/clases.json', 'r', encoding='utf-8-sig') as f:
    clases_json = json.load(f)
print(f"    In JSON: {len(clases_json)}")

# Clear and migrate classes
if len(db.get_clases()) < len(clases_json):
    print("\n    Migrating classes...")
    
    with db.get_cursor() as cursor:
        cursor.execute("DELETE FROM clases")
    
    count = 0
    for c in clases_json:
        try:
            fecha_str = c.get('fecha', '')
            fecha = None
            if fecha_str:
                if len(fecha_str) == 10 and fecha_str.count('-') == 2:
                    fecha = fecha_str
                elif '/' in fecha_str:
                    parts = fecha_str.split('/')
                    fecha = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            
            with db.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO clases (nombre, descripcion, fecha, modalidad, link_meet, estado) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (c.get('tema', 'Clase'), c.get('orador', ''), fecha, 
                     c.get('modalidad', 'Presencial'), c.get('link_meet', ''), 
                     c.get('estado', 'Programada'))
                )
            count += 1
        except:
            pass
    
    print(f"    Migrated: {count}/{len(clases_json)} classes")
    final = len(db.get_clases())
    print(f"    Total in DB: {final}")

print("\n" + "="*60)
print("DONE!")
print("="*60 + "\n")
