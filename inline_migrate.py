#!/usr/bin/env python3
"""Auto-migrate and sync data from JSON files on startup"""

import json

def migrate_from_json(db):
    """Migrate and sync miembros, oradores, clases, and asistencia from JSON"""
    
    print("    Syncing data from JSON files...")
    
    # 1. Migrate speakers (oradores) if needed
    try:
        with open('data/oradores.json', 'r', encoding='utf-8-sig') as f:
            oradores = json.load(f)
        
        if len(db.get_oradores()) == 0:
            print(f"      Adding {len(oradores)} speakers...")
            for o in oradores:
                try:
                    db.add_orador(
                        nombre=o.get('nombre', '').strip(),
                        apellido=o.get('apellido', '').strip(),
                        email=o.get('email', '').strip(),
                        telefono=o.get('telefono', '').strip()
                    )
                except:
                    pass
    except:
        pass
    
    # 2. Sync classes (clases) with ID preservation
    try:
        with open('data/clases.json', 'r', encoding='utf-8-sig') as f:
            clases_json = json.load(f)
        
        current_count = len(db.get_clases())
        
        # Reload if count doesn't match or if attendance needs classes
        if current_count != len(clases_json):
            print(f"      Syncing classes: {current_count} -> {len(clases_json)}...")
            
            # Clear attendance and classes due to FK constraint
            with db.get_cursor() as cursor:
                cursor.execute("DELETE FROM asistencia")
                cursor.execute("DELETE FROM clases")
            
            # Reload with ID preservation
            count = 0
            for i, c in enumerate(clases_json, 1):
                try:
                    # Parse fecha
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
                            "INSERT INTO clases (id, nombre, descripcion, fecha, modalidad, link_meet, estado) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (i,
                             c.get('tema', 'Clase'), 
                             c.get('orador', ''), 
                             fecha, 
                             c.get('modalidad', 'Presencial'), 
                             c.get('link_meet', ''), 
                             c.get('estado', 'Programada'))
                        )
                    count += 1
                except:
                    pass
            
            print(f"      Loaded {count} classes")
    except:
        pass
    
    # 3. Migrate attendance
    try:
        with open('data/asistencia.json', 'r', encoding='utf-8-sig') as f:
            asistencia_json = json.load(f)
        
        current_asistencia = len(db.get_asistencia())
        
        if current_asistencia == 0 and len(asistencia_json) > 0:
            print(f"      Loading {len(asistencia_json)} attendance records...")
            count = 0
            for registro in asistencia_json:
                try:
                    fecha_clase = registro.get('fecha_clase')
                    id_clase = registro.get('id_clase')
                    asistencias = registro.get('asistencias', [])
                    
                    for asistencia in asistencias:
                        try:
                            miembro_id = asistencia.get('id_miembro')
                            presente = asistencia.get('presente', True)
                            
                            if miembro_id and fecha_clase and id_clase:
                                db.add_asistencia(miembro_id, id_clase, fecha_clase, presente)
                                count += 1
                        except:
                            pass
                except:
                    pass
            print(f"      Loaded {count} attendance records")
    except:
        pass
    
    # 4. Summary
    try:
        miembros_count = len(db.get_miembros())
        oradores_count = len(db.get_oradores())
        clases_count = len(db.get_clases())
        asistencia_count = len(db.get_asistencia())
        print(f"      Total: {miembros_count} students, {oradores_count} speakers, {clases_count} classes, {asistencia_count} attendance")
    except:
        pass

if __name__ == '__main__':
    from database import Database
    db = Database()
    migrate_from_json(db)
    print("    Data sync complete!")

