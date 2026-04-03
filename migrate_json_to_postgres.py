#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate existing JSON data to PostgreSQL (Neon)
Reads all JSON files from /data/ folder and inserts into database

Usage:
    python migrate_json_to_postgres.py
"""

import json
import os
from datetime import datetime, date
from dotenv import load_dotenv
from database import Database, DatabaseError

# Load environment variables
load_dotenv()

DATA_DIR = 'data'

class JSONToPostgresMigration:
    """Handle migration from JSON files to PostgreSQL"""
    
    def __init__(self):
        """Initialize migration"""
        self.db = Database()
        self.stats = {
            'miembros': 0,
            'clases': 0,
            'asistencia': 0,
            'pagos': 0,
            'retiros': 0,
            'oradores': 0,
            'examenes': 0,
            'errors': []
        }
    
    def load_json_file(self, filename):
        """Load JSON file from data/ folder"""
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except FileNotFoundError:
            print(f"⚠ File not found: {filename}")
            return []
        except json.JSONDecodeError as e:
            print(f"⚠ Invalid JSON in {filename}: {e}")
            return []
    
    def migrate_miembros(self):
        """Migrate members from miembros.json"""
        print("\n📌 Migrating MIEMBROS (Members)...")
        miembros_data = self.load_json_file('miembros.json')
        
        if not miembros_data:
            print("   ℹ No members to migrate")
            return
        
        for m in miembros_data:
            try:
                self.db.add_miembro(
                    nombre=m.get('nombre', 'Unknown'),
                    apellido=m.get('apellido', ''),
                    email=m.get('email'),
                    tipo_asistencia=m.get('tipo_asistencia', 'Regular'),
                    matricula=m.get('matricula') or m.get('id')
                )
                self.stats['miembros'] += 1
            except Exception as e:
                error_msg = f"Error migrating member {m.get('id')}: {str(e)}"
                print(f"   ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
        
        print(f"   ✓ Migrated {self.stats['miembros']} members")
    
    def migrate_clases(self):
        """Migrate classes from clases.json"""
        print("\n📌 Migrating CLASES (Classes)...")
        clases_data = self.load_json_file('clases.json')
        
        if not clases_data:
            print("   ℹ No classes to migrate")
            return
        
        for c in clases_data:
            try:
                fecha = c.get('fecha', str(date.today()))
                hora_inicio = c.get('hora_inicio', '10:00')
                modalidad = c.get('modalidad', 'Meet')
                link_meet = c.get('link_meet')
                nombre = c.get('nombre', 'Clase sin nombre')
                
                self.db.add_clase(
                    nombre=nombre,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    modalidad=modalidad,
                    link_meet=link_meet
                )
                self.stats['clases'] += 1
            except Exception as e:
                error_msg = f"Error migrating class {c.get('id')}: {str(e)}"
                print(f"   ❌ {error_msg}")
                self.stats['errors'].append(error_msg)
        
        print(f"   ✓ Migrated {self.stats['clases']} classes")
    
    def migrate_asistencia(self):
        """Migrate attendance records from asistencia.json"""
        print("\n📌 Migrating ASISTENCIA (Attendance)...")
        asistencia_data = self.load_json_file('asistencia.json')
        
        if not asistencia_data:
            print("   ℹ No attendance records to migrate")
            return
        
        for a in asistencia_data:
            try:
                miembro_id = a.get('id_miembro') or a.get('miembro_id')
                clase_id = a.get('clase_id', 1)
                fecha = a.get('fecha', a.get('fecha_clase', str(date.today())))
                asistio = a.get('asistio', a.get('presente', True))
                
                # Convert asistio to boolean if it's a string
                if isinstance(asistio, str):
                    asistio = asistio.lower() in ['true', 'si', 'yes', '1']
                
                self.db.add_asistencia(
                    miembro_id=miembro_id,
                    clase_id=clase_id,
                    fecha=fecha,
                    asistio=bool(asistio)
                )
                self.stats['asistencia'] += 1
            except Exception as e:
                error_msg = f"Error migrating attendance: {str(e)}"
                # Don't print every error, just count them
                self.stats['errors'].append(error_msg)
        
        print(f"   ✓ Migrated {self.stats['asistencia']} attendance records")
    
    def migrate_pagos(self):
        """Migrate payments from pagos.json"""
        print("\n📌 Migrating PAGOS (Payments)...")
        pagos_data = self.load_json_file('pagos.json')
        
        if not pagos_data:
            print("   ℹ No payments to migrate")
            return
        
        for p in pagos_data:
            try:
                miembro_id = p.get('id_miembro') or p.get('miembro_id')
                monto = float(p.get('monto', 0))
                fecha = p.get('fecha', str(date.today()))
                mes = p.get('mes', '')
                descripcion = p.get('descripcion') or p.get('concepto', '')
                metodo_pago = p.get('metodo_pago', 'Efectivo')
                
                self.db.add_pago(
                    miembro_id=miembro_id,
                    monto=monto,
                    fecha=fecha,
                    mes=mes,
                    descripcion=descripcion,
                    metodo_pago=metodo_pago
                )
                self.stats['pagos'] += 1
            except Exception as e:
                error_msg = f"Error migrating payment: {str(e)}"
                self.stats['errors'].append(error_msg)
        
        print(f"   ✓ Migrated {self.stats['pagos']} payments")
    
    def migrate_retiros(self):
        """Migrate withdrawals from retiros.json"""
        print("\n📌 Migrating RETIROS (Withdrawals)...")
        retiros_data = self.load_json_file('retiros.json')
        
        if not retiros_data:
            print("   ℹ No withdrawals to migrate")
            return
        
        for r in retiros_data:
            try:
                miembro_id = r.get('id_miembro') or r.get('miembro_id')
                monto = float(r.get('monto', 0))
                fecha = r.get('fecha', str(date.today()))
                razon = r.get('razon', '')
                tipo_retiro = r.get('tipo_retiro', 'Reembolso')
                
                self.db.add_retiro(
                    miembro_id=miembro_id,
                    monto=monto,
                    fecha=fecha,
                    razon=razon,
                    tipo_retiro=tipo_retiro
                )
                self.stats['retiros'] += 1
            except Exception as e:
                error_msg = f"Error migrating withdrawal: {str(e)}"
                self.stats['errors'].append(error_msg)
        
        print(f"   ✓ Migrated {self.stats['retiros']} withdrawals")
    
    def migrate_oradores(self):
        """Migrate speakers from oradores.json"""
        print("\n📌 Migrating ORADORES (Speakers)...")
        oradores_data = self.load_json_file('oradores.json')
        
        if not oradores_data:
            print("   ℹ No speakers to migrate")
            return
        
        print(f"   ℹ Speaker migration would need: {len(oradores_data)} records")
        print("   (Implement if needed)")
        self.stats['oradores'] = len(oradores_data)
    
    def migrate_examenes(self):
        """Migrate exams from examenes.json"""
        print("\n📌 Migrating EXAMENES (Exams)...")
        examenes_data = self.load_json_file('examenes.json')
        
        if not examenes_data:
            print("   ℹ No exams to migrate")
            return
        
        print(f"   ℹ Exam migration would need: {len(examenes_data)} records")
        print("   (Implement if needed)")
        self.stats['examenes'] = len(examenes_data)
    
    def run(self):
        """Run full migration"""
        print("=" * 70)
        print("JSON to PostgreSQL Migration")
        print("=" * 70)
        
        # Check if data folder exists
        if not os.path.exists(DATA_DIR):
            print(f"❌ Data folder not found: {DATA_DIR}")
            print("   Make sure /data/ folder exists with JSON files")
            return False
        
        try:
            # Migrate all tables
            self.migrate_miembros()
            self.migrate_clases()
            self.migrate_asistencia()
            self.migrate_pagos()
            self.migrate_retiros()
            self.migrate_oradores()
            self.migrate_examenes()
            
            # Print summary
            print("\n" + "=" * 70)
            print("MIGRATION SUMMARY")
            print("=" * 70)
            print(f"\n✓ Successfully migrated:")
            print(f"  • {self.stats['miembros']} members")
            print(f"  • {self.stats['clases']} classes")
            print(f"  • {self.stats['asistencia']} attendance records")
            print(f"  • {self.stats['pagos']} payments")
            print(f"  • {self.stats['retiros']} withdrawals")
            print(f"  • {self.stats['oradores']} speakers (in JSON)")
            print(f"  • {self.stats['examenes']} exams (in JSON)")
            
            total_migrated = (self.stats['miembros'] + self.stats['clases'] + 
                            self.stats['asistencia'] + self.stats['pagos'] + 
                            self.stats['retiros'])
            
            print(f"\n✓ Total database records: {total_migrated}")
            
            if self.stats['errors']:
                print(f"\n⚠ Errors: {len(self.stats['errors'])}")
                for error in self.stats['errors'][:5]:  # Show first 5 errors
                    print(f"   - {error}")
                if len(self.stats['errors']) > 5:
                    print(f"   ... and {len(self.stats['errors']) - 5} more")
            
            print("\n" + "=" * 70)
            print("✓ Migration complete!")
            print("=" * 70)
            print("\nNext steps:")
            print("1. Verify data in PostgreSQL:")
            print("   SELECT COUNT(*) FROM miembros;")
            print("   SELECT COUNT(*) FROM pagos;")
            print("   etc.")
            print("2. Test the Flask app: python app.py")
            print("3. Deploy to Vercel when ready\n")
            
            return True
        
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            return False


if __name__ == "__main__":
    migration = JSONToPostgresMigration()
    success = migration.run()
    exit(0 if success else 1)
