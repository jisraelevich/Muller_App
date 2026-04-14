"""
Database Connection Handler for Muller App
Uses Neon PostgreSQL with psycopg
"""

import os
from contextlib import contextmanager
from datetime import datetime, date
from dotenv import load_dotenv
import time
from functools import wraps

# Load environment variables
load_dotenv()

# Try to import psycopg3, fall back to psycopg2
try:
    import psycopg
    from psycopg.rows import dict_row
    USE_PSYCOPG3 = True
except ImportError:
    try:
        import psycopg2
        import psycopg2.extras
        USE_PSYCOPG3 = False
    except ImportError:
        psycopg = None
        psycopg2 = None
        USE_PSYCOPG3 = None

class DatabaseError(Exception):
    """Custom database error"""
    pass

# Simple cache decorator - expires after N seconds
# Store cache objects globally so we can clear them
_cache_store = {}

def cache_result(timeout=300, cache_key=None):
    """Cache decorator with timeout (in seconds) and ability to clear cache"""
    def decorator(func):
        actual_key = cache_key or func.__name__
        cache = {'result': None, 'timestamp': 0}
        _cache_store[actual_key] = cache  # Store reference globally
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - cache['timestamp'] > timeout:
                cache['result'] = func(*args, **kwargs)
                cache['timestamp'] = now
            return cache['result']
        
        return wrapper
    return decorator

def clear_cache(cache_key=None):
    """Clear specific cache or all caches"""
    if cache_key:
        if cache_key in _cache_store:
            _cache_store[cache_key]['timestamp'] = 0
    else:
        # Clear all caches
        for cache in _cache_store.values():
            cache['timestamp'] = 0

class Database:
    """Handle PostgreSQL database operations"""
    
    def __init__(self, connection_string=None):
        """Initialize database connection"""
        if USE_PSYCOPG3 is None:
            raise DatabaseError("Neither psycopg nor psycopg2 installed. Install with: pip install psycopg[binary]")
        
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise DatabaseError("DATABASE_URL not found in environment variables")
        self.conn = None
        self.use_psycopg3 = USE_PSYCOPG3
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            if self.use_psycopg3:
                conn = psycopg.connect(self.connection_string)
            else:
                conn = psycopg2.connect(self.connection_string)
            yield conn
            conn.commit()
        except Exception as e:
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
            if USE_PSYCOPG3:
                # psycopg3 - use dict_row factory to return dicts instead of tuples
                cursor = conn.cursor(row_factory=dict_row)
            else:
                # psycopg2 - use RealDictCursor
                cursor = psycopg2.extras.RealDictCursor(conn)
            try:
                yield cursor
            finally:
                cursor.close()
    
    # ========================================================================
    # MIEMBROS (Students/Members) Operations
    # ========================================================================
    
    @cache_result(timeout=300, cache_key='get_miembros')  # Cache for 5 minutes
    def get_miembros(self, tipo_asistencia=None, estado='Activo'):
        """Get all members, optionally filtered - cached for 5 minutes"""
        with self.get_cursor() as cursor:
            if tipo_asistencia:
                cursor.execute(
                    "SELECT id, nombre, apellido, email, telefono, tipo_asistencia, estado, congregacion, localidad, matricula FROM miembros "
                    "WHERE tipo_asistencia=%s AND estado=%s ORDER BY nombre LIMIT 200",
                    (tipo_asistencia, estado)
                )
            else:
                cursor.execute(
                    "SELECT id, nombre, apellido, email, telefono, tipo_asistencia, estado, congregacion, localidad, matricula FROM miembros "
                    "WHERE estado=%s ORDER BY nombre LIMIT 200",
                    (estado,)
                )
            return cursor.fetchall()
    
    def get_miembros_inactivos(self):
        """Get all inactive members"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, apellido, email, telefono, tipo_asistencia, estado, congregacion, localidad, matricula FROM miembros "
                "WHERE estado='Inactivo' ORDER BY nombre LIMIT 200"
            )
            return cursor.fetchall()
    
    def get_miembros_fresh(self, estado='Activo'):
        """Get members WITHOUT cache - for reports"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, apellido, email, telefono, tipo_asistencia, estado, congregacion, localidad, matricula FROM miembros "
                "WHERE estado=%s ORDER BY nombre LIMIT 200",
                (estado,)
            )
            return cursor.fetchall()
    
    def reactivar_miembro(self, miembro_id):
        """Reactivate an inactive member"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE miembros SET estado='Activo', updated_at=NOW() WHERE id=%s AND estado='Inactivo'",
                (miembro_id,)
            )
    
    def get_miembro(self, miembro_id):
        """Get single member by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM miembros WHERE id=%s", (miembro_id,))
            return cursor.fetchone()
    
    def add_miembro(self, nombre, apellido, email, tipo_asistencia, matricula=None, congregacion=None, localidad=None):
        """Add new member"""
        # Usar valores por defecto si no se proporcionan
        if not congregacion:
            congregacion = 'ICE Fco Arias'
        if not localidad:
            localidad = 'Salta Capital'
            
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO miembros (nombre, apellido, email, tipo_asistencia, matricula, congregacion, localidad) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (nombre, apellido, email, tipo_asistencia, matricula, congregacion, localidad)
            )
            result = cursor.fetchone()
            # Handle both tuple and dict returns
            if isinstance(result, tuple):
                return result[0]
            return result.get('id') if hasattr(result, 'get') else result[0]
    
    def update_miembro_tipo(self, miembro_id, nuevo_tipo):
        """Change member type (Regular/Oyente)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE miembros SET tipo_asistencia=%s, updated_at=NOW() WHERE id=%s",
                (nuevo_tipo, miembro_id)
            )
    
    def update_miembro_datos(self, miembro_id, nombre, apellido, email, congregacion=None, localidad=None, tipo_asistencia=None):
        """Update member personal data (name, apellido, email, congregacion, localidad, tipo_asistencia)"""
        with self.get_cursor() as cursor:
            update_fields = ["nombre=%s", "apellido=%s", "email=%s"]
            values = [nombre, apellido, email]
            
            if congregacion:
                update_fields.append("congregacion=%s")
                values.append(congregacion)
            
            if localidad:
                update_fields.append("localidad=%s")
                values.append(localidad)
            
            # SIEMPRE actualiza tipo_asistencia si se proporciona (no solo si es truthy)
            if tipo_asistencia is not None:
                update_fields.append("tipo_asistencia=%s")
                values.append(tipo_asistencia)
            
            update_fields.append("updated_at=NOW()")
            values.append(miembro_id)
            
            query = f"UPDATE miembros SET {', '.join(update_fields)} WHERE id=%s"
            cursor.execute(query, values)
    
    def inactivar_miembro(self, miembro_id):
        """Mark a member as Inactive (NEVER delete data)"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE miembros SET estado='Inactivo', updated_at=NOW() WHERE id=%s",
                (miembro_id,)
            )
            return {"status": "success", "message": "Miembro inactivado"}
    
    def delete_miembro(self, miembro_id):
        """Alias for inactivar_miembro for backward compatibility"""
        return self.inactivar_miembro(miembro_id)
    
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
    
    @cache_result(timeout=300, cache_key='get_clases')  # Cache for 5 minutes
    def asignar_oradores_automatico(self):
        """Migración SQL puro: Busca oradores en descripción y asigna orador_id a clases
        Retorna dict con resumen de la migración"""
        resultado = {
            'status': 'error',
            'total_clases': 0,
            'asignados': 0,
            'no_encontrados': 0,
            'detalles': []
        }
        
        try:
            with self.get_cursor() as cursor:
                # 1. Contar clases sin orador
                cursor.execute(
                    "SELECT COUNT(*) as count FROM clases WHERE orador_id IS NULL OR orador_id = 0"
                )
                row = cursor.fetchone()
                total_sin_orador = row['count'] if isinstance(row, dict) else row[0]
                resultado['total_clases'] = total_sin_orador
                
                if total_sin_orador == 0:
                    resultado['status'] = 'success'
                    resultado['detalles'].append("✅ No hay clases sin orador que actualizar")
                    print("✅ No hay clases sin orador que actualizar")
                    return resultado
                
                print(f"🔍 Migrando {total_sin_orador} clases sin orador asignado...\n")
                
                # 2. UPDATE SQL: Buscar apellido en descripción, asignar orador_id
                # Prioridad: 1) Apellido del orador en descripción, 2) Nombre del orador
                update_apellido_sql = """
                UPDATE clases c
                SET orador_id = (
                    SELECT id FROM oradores o
                    WHERE LOWER(o.apellido) != ''
                    AND LOWER(c.descripcion) LIKE CONCAT('%', LOWER(o.apellido), '%')
                    ORDER BY LENGTH(o.apellido) DESC
                    LIMIT 1
                )
                WHERE (c.orador_id IS NULL OR c.orador_id = 0)
                AND EXISTS (
                    SELECT 1 FROM oradores o
                    WHERE LOWER(o.apellido) != ''
                    AND LOWER(c.descripcion) LIKE CONCAT('%', LOWER(o.apellido), '%')
                )
                """
                
                cursor.execute(update_apellido_sql)
                asignados_apellido = cursor.rowcount
                print(f"✓ {asignados_apellido} clases asignadas por APELLIDO\n")
                resultado['asignados'] += asignados_apellido
                
                # 3. UPDATE SQL: Buscar nombre en descripción
                update_nombre_sql = """
                UPDATE clases c
                SET orador_id = (
                    SELECT id FROM oradores o
                    WHERE LOWER(o.nombre) != ''
                    AND LOWER(c.descripcion) LIKE CONCAT('%', LOWER(o.nombre), '%')
                    ORDER BY LENGTH(o.nombre) DESC
                    LIMIT 1
                )
                WHERE (c.orador_id IS NULL OR c.orador_id = 0)
                AND EXISTS (
                    SELECT 1 FROM oradores o
                    WHERE LOWER(o.nombre) != ''
                    AND LOWER(c.descripcion) LIKE CONCAT('%', LOWER(o.nombre), '%')
                )
                """
                
                cursor.execute(update_nombre_sql)
                asignados_nombre = cursor.rowcount
                print(f"✓ {asignados_nombre} clases asignadas por NOMBRE\n")
                resultado['asignados'] += asignados_nombre
                
                # 4. Reporte detallado - solo contar clases actualizadas
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM clases c
                    WHERE c.orador_id IS NOT NULL AND c.orador_id != 0
                """)
                row = cursor.fetchone()
                total_con_orador = row.get('total', 0) if isinstance(row, dict) else row[0]
                
                print(f"=== CLASES ACTUALIZADAS ({total_con_orador} total) ===\n")
                
                # 5. Contar clases que quedaron sin orador
                cursor.execute(
                    "SELECT COUNT(*) as count FROM clases WHERE orador_id IS NULL OR orador_id = 0"
                )
                row = cursor.fetchone()
                no_encontrados = row['count'] if isinstance(row, dict) else row[0]
                resultado['no_encontrados'] = no_encontrados
                
                resultado['status'] = 'success'
                resumen = f"\n✅ MIGRACIÓN COMPLETADA:\n   • Total iniciales: {total_sin_orador}\n   • Asignadas: {resultado['asignados']}\n   • Sin asignar: {no_encontrados}"
                print(resumen)
                resultado['detalles'].append(resumen)
                
        except Exception as e:
            print(f"❌ Error en migración SQL: {e}")
            import traceback
            traceback.print_exc()
            resultado['detalles'].append(f"❌ Error: {str(e)}")
        
        return resultado

    def actualizar_hora_clases(self, hora='21:00'):
        """Actualizar todas las clases a una hora específica (default 21:00 = 9:00 PM)"""
        resultado = {'status': 'error', 'actualizadas': 0}
        
        try:
            with self.get_cursor() as cursor:
                # Contar clases actuales
                cursor.execute("SELECT COUNT(*) as count FROM clases")
                row = cursor.fetchone()
                total_clases = row['count'] if isinstance(row, dict) else row[0]
                
                # Actualizar todas a la hora especificada
                cursor.execute(
                    "UPDATE clases SET hora_inicio = %s WHERE 1=1",
                    (hora,)
                )
                actualizadas = cursor.rowcount
                
                resultado['status'] = 'success'
                resultado['actualizadas'] = actualizadas
                resultado['total'] = total_clases
                resultado['hora'] = hora
                
                print(f"✅ ACTUALIZACIÓN DE HORA COMPLETADA:")
                print(f"   • Total clases: {total_clases}")
                print(f"   • Actualizadas a {hora}: {actualizadas}")
                
        except Exception as e:
            print(f"❌ Error actualizando hora de clases: {e}")
            resultado['error'] = str(e)
        
        return resultado

    def get_clases(self):
        """Get all classes - cached for 5 minutes, limited to 100, ordered ascending by date"""
        with self.get_cursor() as cursor:
            try:
                # Intenta con el JOIN si existe la columna orador_id
                cursor.execute(
                    "SELECT c.id, c.nombre, c.descripcion, c.fecha, c.hora_inicio, c.modalidad, c.estado, c.link_meet, "
                    "c.orador_id, "
                    "COALESCE(o.nombre, '') as orador_nombre, COALESCE(o.apellido, '') as orador_apellido "
                    "FROM clases c "
                    "LEFT JOIN oradores o ON c.orador_id = o.id "
                    "ORDER BY c.fecha ASC LIMIT 100"
                )
                return cursor.fetchall()
            except:
                # Si falla (columna no existe), usa query simple
                cursor.execute(
                    "SELECT id, nombre, descripcion, fecha, hora_inicio, modalidad, estado, link_meet "
                    "FROM clases ORDER BY fecha ASC LIMIT 100"
                )
                return cursor.fetchall()
    
    def add_clase(self, nombre, fecha, hora_inicio, modalidad, link_meet=None, orador_id=None):
        """Add new class"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO clases (nombre, fecha, hora_inicio, modalidad, link_meet, orador_id) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (nombre, fecha, hora_inicio, modalidad, link_meet, orador_id)
            )
            result = cursor.fetchone()
            if isinstance(result, tuple):
                return result[0]
            return result.get('id') if hasattr(result, 'get') else result[0]
    
    def update_clase_estado(self, clase_id, nuevo_estado, modalidad=None):
        """Update class status (Programada/Realizada/Cancelada) and optionally modalidad"""
        with self.get_cursor() as cursor:
            if modalidad:
                cursor.execute(
                    "UPDATE clases SET estado=%s, modalidad=%s, updated_at=NOW() WHERE id=%s",
                    (nuevo_estado, modalidad, clase_id)
                )
            else:
                cursor.execute(
                    "UPDATE clases SET estado=%s, updated_at=NOW() WHERE id=%s",
                    (nuevo_estado, clase_id)
                )
        # Clear cache after updating
        clear_cache('get_clases')
    
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
    
    def get_asistencia(self):
        """Get recent attendance records - limited to 500 most recent"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT a.id, a.miembro_id, a.clase_id, a.fecha, a.asistio, "
                "CONCAT(m.nombre, ' ', m.apellido) as miembro_nombre, "
                "c.nombre as clase_nombre "
                "FROM asistencia a "
                "JOIN miembros m ON a.miembro_id = m.id "
                "LEFT JOIN clases c ON a.clase_id = c.id "
                "ORDER BY a.fecha DESC, m.nombre LIMIT 500"
            )
            return cursor.fetchall()
    
    def add_asistencia(self, miembro_id, clase_id, fecha, asistio):
        """Record attendance - PostgreSQL compatible with update on duplicate"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO asistencia (miembro_id, clase_id, fecha, asistio) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (miembro_id, clase_id, fecha) DO UPDATE SET asistio=EXCLUDED.asistio, updated_at=NOW()",
                (miembro_id, clase_id, fecha, asistio)
            )
    
    # ========================================================================
    # PAGOS (Payments) Operations
    # ========================================================================
    
    def get_pagos_miembro(self, miembro_id):
        """Get payments for a member - limited to last 20 most recent"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, miembro_id, monto, fecha, mes, tipo_pago, descripcion, metodo_pago, mes_inicio, mes_fin FROM pagos WHERE miembro_id=%s ORDER BY fecha DESC LIMIT 20",
                (miembro_id,)
            )
            return cursor.fetchall()
    
    def get_pagos(self):
        """Get recent payments - limited to 300 most recent"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT p.id, p.miembro_id, p.monto, p.fecha, p.mes, p.descripcion, p.metodo_pago, p.tipo_pago, p.mes_inicio, p.mes_fin, "
                "CONCAT(m.nombre, ' ', m.apellido) as miembro_nombre "
                "FROM pagos p "
                "LEFT JOIN miembros m ON p.miembro_id = m.id "
                "ORDER BY p.fecha DESC LIMIT 300"
            )
            return cursor.fetchall()
    
    def add_pago(self, miembro_id, monto, fecha, mes, descripcion=None, metodo_pago='Efectivo', tipo_pago='Cuota', mes_inicio=None, mes_fin=None, estado_pago='Puntual'):
        """Add payment record with optional multi-month coverage and payment status"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO pagos (miembro_id, monto, fecha, mes, descripcion, metodo_pago, tipo_pago, mes_inicio, mes_fin, estado_pago) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (miembro_id, monto, fecha, mes, descripcion, metodo_pago, tipo_pago, mes_inicio, mes_fin, estado_pago)
            )
            result = cursor.fetchone()
            if isinstance(result, tuple):
                return result[0]
            return result.get('id') if hasattr(result, 'get') else result[0]
    
    def delete_pago(self, pago_id):
        """Delete/remove a payment"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM pagos WHERE id=%s", (pago_id,))
    
    def update_pago(self, pago_id, monto, fecha, mes, tipo_pago=None, descripcion=None, metodo_pago='Efectivo'):
        """Update payment record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE pagos SET monto=%s, fecha=%s, mes=%s, tipo_pago=%s, descripcion=%s, metodo_pago=%s, updated_at=NOW() "
                "WHERE id=%s",
                (monto, fecha, mes, tipo_pago, descripcion, metodo_pago, pago_id)
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
            result = cursor.fetchone()
            if isinstance(result, tuple):
                return result[0]
            return result.get('id') if hasattr(result, 'get') else result[0]
    
    def get_retiros_miembro(self, miembro_id):
        """Get all refunds for a member"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM retiros WHERE miembro_id=%s ORDER BY fecha DESC",
                (miembro_id,)
            )
            return cursor.fetchall()
    
    def get_retiros(self):
        """Get recent refunds - limited to 200 most recent"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, miembro_id, monto, fecha, razon, tipo_retiro FROM retiros "
                "ORDER BY fecha DESC LIMIT 200"
            )
            return cursor.fetchall()
    
    def delete_retiro(self, retiro_id):
        """Delete a refund record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM retiros WHERE id=%s",
                (retiro_id,)
            )
    
    def update_retiro(self, retiro_id, concepto, monto, fecha, metodo, notas):
        """Update a refund record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE retiros SET tipo_retiro=%s, monto=%s, fecha=%s, razon=%s "
                "WHERE id=%s",
                (concepto, monto, fecha, f"{metodo} | {notas}" if notas else metodo, retiro_id)
            )
    
    @cache_result(timeout=600, cache_key='get_oradores')  # Cache for 10 minutes
    def get_oradores(self):
        """Get all speakers - cached for 10 minutes"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, apellido, email, telefono, especialidad FROM oradores "
                "ORDER BY apellido, nombre LIMIT 50"
            )
            return cursor.fetchall()
    
    def add_orador(self, nombre, apellido='', email='', telefono='', especialidad=''):
        """Add a speaker"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO oradores (nombre, apellido, email, telefono, especialidad) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (nombre, apellido, email, telefono, especialidad)
            )
            result = cursor.fetchone()
            if isinstance(result, tuple):
                return result[0]
            return result.get('id') if hasattr(result, 'get') else result[0]
    
    def update_orador(self, id_orador, nombre, apellido='', email='', telefono='', especialidad=''):
        """Update a speaker"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "UPDATE oradores SET nombre=%s, apellido=%s, email=%s, telefono=%s, especialidad=%s "
                "WHERE id=%s",
                (nombre, apellido, email, telefono, especialidad, id_orador)
            )
            return cursor.rowcount > 0
    
    def delete_orador(self, id_orador):
        """Delete a speaker"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM oradores WHERE id=%s", (id_orador,))
            return cursor.rowcount > 0
    
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
            result = cursor.fetchone()
            if isinstance(result, tuple):
                return result[0]
            return result.get('id') if hasattr(result, 'get') else result[0]
    
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
