"""
Database Connection Handler for Muller App
Uses Neon PostgreSQL with psycopg2
"""

import os
import psycopg2
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

class DatabaseError(Exception):
    """Custom database error"""
    pass

class Database:
    """Handle PostgreSQL database operations"""
    
    def __init__(self, connection_string=None):
        """Initialize database connection"""
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise DatabaseError("DATABASE_URL not found in environment variables")
        self.conn = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        try:
            conn = psycopg2.connect(self.connection_string)
            yield conn
            conn.commit()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
            finally:
                cursor.close()
    
    # ========================================================================
    # MIEMBROS (Students/Members) Operations
    # ========================================================================
    
    def get_miembros(self, tipo_asistencia=None, estado='Activo'):
        """Get all members, optionally filtered"""
        with self.get_cursor() as cursor:
            if tipo_asistencia:
                cursor.execute(
                    "SELECT * FROM miembros WHERE tipo_asistencia=%s AND estado=%s ORDER BY nombre",
                    (tipo_asistencia, estado)
                )
            else:
                cursor.execute(
                    "SELECT * FROM miembros WHERE estado=%s ORDER BY nombre",
                    (estado,)
                )
            return cursor.fetchall()
    
    def get_miembro(self, miembro_id):
        """Get single member by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM miembros WHERE id=%s", (miembro_id,))
            return cursor.fetchone()
    
    def add_miembro(self, nombre, apellido, email, tipo_asistencia, matricula=None):
        """Add new member"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO miembros (nombre, apellido, email, tipo_asistencia, matricula) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (nombre, apellido, email, tipo_asistencia, matricula)
            )
            return cursor.fetchone()['id']
    
    def update_miembro_tipo(self, miembro_id, nuevo_tipo):
        """Change member type (Regular/Oyente)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE miembros SET tipo_asistencia=%s, updated_at=NOW() WHERE id=%s",
                (nuevo_tipo, miembro_id)
            )
    
    # ========================================================================
    # CLASES (Classes) Operations
    # ========================================================================
    
    def get_clases_hoy(self):
        """Get last class, today's class, next class"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM obtener_clases_hoy()")
            return cursor.fetchall()
    
    def get_clase(self, clase_id):
        """Get single class"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM clases WHERE id=%s", (clase_id,))
            return cursor.fetchone()
    
    def add_clase(self, nombre, fecha, hora_inicio, modalidad, link_meet=None):
        """Add new class"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO clases (nombre, fecha, hora_inicio, modalidad, link_meet) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (nombre, fecha, hora_inicio, modalidad, link_meet)
            )
            return cursor.fetchone()['id']
    
    def update_clase_estado(self, clase_id, nuevo_estado):
        """Update class status (Programada/Realizada/Cancelada)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE clases SET estado=%s, updated_at=NOW() WHERE id=%s",
                (nuevo_estado, clase_id)
            )
    
    # ========================================================================
    # ASISTENCIA (Attendance) Operations
    # ========================================================================
    
    def get_asistencia_fecha(self, fecha):
        """Get attendance records for specific date"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT a.*, m.nombre, m.apellido FROM asistencia a "
                "JOIN miembros m ON a.miembro_id = m.id "
                "WHERE a.fecha=%s ORDER BY m.nombre",
                (fecha,)
            )
            return cursor.fetchall()
    
    def add_asistencia(self, miembro_id, clase_id, fecha, asistio):
        """Record attendance"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO asistencia (miembro_id, clase_id, fecha, asistio) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (miembro_id, clase_id, fecha) "
                "DO UPDATE SET asistio=%s, updated_at=NOW()",
                (miembro_id, clase_id, fecha, asistio, asistio)
            )
    
    # ========================================================================
    # PAGOS (Payments) Operations
    # ========================================================================
    
    def get_pagos_miembro(self, miembro_id):
        """Get all payments for a member"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM pagos WHERE miembro_id=%s ORDER BY fecha DESC",
                (miembro_id,)
            )
            return cursor.fetchall()
    
    def add_pago(self, miembro_id, monto, fecha, mes, descripcion=None, metodo_pago='Efectivo'):
        """Add payment record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO pagos (miembro_id, monto, fecha, mes, descripcion, metodo_pago) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (miembro_id, monto, fecha, mes, descripcion, metodo_pago)
            )
            return cursor.fetchone()['id']
    
    def delete_pago(self, pago_id):
        """Delete/remove a payment"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM pagos WHERE id=%s", (pago_id,))
    
    def update_pago(self, pago_id, monto, fecha, mes, descripcion=None, metodo_pago='Efectivo'):
        """Update payment record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE pagos SET monto=%s, fecha=%s, mes=%s, descripcion=%s, metodo_pago=%s, updated_at=NOW() "
                "WHERE id=%s",
                (monto, fecha, mes, descripcion, metodo_pago, pago_id)
            )
    
    # ========================================================================
    # RETIROS (Refunds) Operations
    # ========================================================================
    
    def add_retiro(self, miembro_id, monto, fecha, razon=None, tipo_retiro='Reembolso'):
        """Add refund/withdrawal record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO retiros (miembro_id, monto, fecha, razon, tipo_retiro) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (miembro_id, monto, fecha, razon, tipo_retiro)
            )
            return cursor.fetchone()['id']
    
    def get_retiros_miembro(self, miembro_id):
        """Get all refunds for a member"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM retiros WHERE miembro_id=%s ORDER BY fecha DESC",
                (miembro_id,)
            )
            return cursor.fetchall()
    
    # ========================================================================
    # REPORTS / QUERIES
    # ========================================================================
    
    def get_reporte_pagos_por_mes(self):
        """Get payment report: students with payment status by month"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM obtener_reporte_pagos_por_mes()")
            return cursor.fetchall()
    
    def get_reporte_asistencia(self, fecha_inicio, fecha_fin):
        """Get attendance report for date range"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM obtener_reporte_asistencia(%s, %s)",
                (fecha_inicio, fecha_fin)
            )
            return cursor.fetchall()
    
    def get_resumen_pagos(self, fecha_inicio, fecha_fin):
        """Get payment summary by student"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM obtener_resumen_pagos(%s, %s)",
                (fecha_inicio, fecha_fin)
            )
            return cursor.fetchall()
    
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    def check_admin_email(self, email):
        """Check if email is authorized admin"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email=%s AND is_admin=true",
                (email,)
            )
            return cursor.fetchone()
    
    def add_user_oauth(self, email, google_id, nombre):
        """Add user from Google OAuth"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (email, google_id, nombre) VALUES (%s, %s, %s) "
                "ON CONFLICT (email) DO UPDATE SET last_login=NOW() RETURNING id",
                (email, google_id, nombre)
            )
            return cursor.fetchone()['id']
    
    def update_last_login(self, email):
        """Update user's last login timestamp"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET last_login=NOW() WHERE email=%s",
                (email,)
            )


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Initialize database
    db = Database()
    
    # Example 1: Get all regular members
    miembros = db.get_miembros(tipo_asistencia='Regular')
    print(f"Regular members: {len(miembros)}")
    
    # Example 2: Get today's classes
    clases = db.get_clases_hoy()
    print(f"Today's classes: {clases}")
    
    # Example 3: Get payment report
    reporte = db.get_reporte_pagos_por_mes()
    for row in reporte:
        print(row)
    
    # Example 4: Add attendance record
    db.add_asistencia(miembro_id=1, clase_id=1, fecha=date.today(), asistio=True)
    print("Attendance recorded")
