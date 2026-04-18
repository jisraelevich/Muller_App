#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instituto Jorge Müller - Sistema de Gestión
Servidor Flask con PostgreSQL (Neon)
Reemplaza operaciones de archivos JSON con base de datos
"""

from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, session
import os
from datetime import datetime, date, timedelta
import io
from dotenv import load_dotenv
from xlsxwriter import Workbook
import time
from functools import wraps
import unicodedata

# Cargar variables de entorno
load_dotenv()

# Importar autenticación OAuth
from auth import GoogleOAuth, login_required, GOOGLE_CLIENT_ID, ADMIN_EMAILS

# Importar módulo de base de datos (opcional - para testing sin DB)
try:
    from database import Database, DatabaseError, clear_cache
    db_available = True
except ImportError as e:
    print(f"⚠️  Módulo database no disponible: {e}")
    db_available = False
    db = None

# Simple HTTP response cache decorator for API endpoints
_api_cache_store = {}

def cache_route(timeout=60, cache_key=None):
    """Cache JSON responses from endpoints for specified seconds"""
    def decorator(f):
        actual_key = cache_key or f.__name__
        cache = {'response': None, 'timestamp': 0}
        _api_cache_store[actual_key] = cache
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Don't cache if user is logged in or if it's a POST request
            if request.method == 'POST' or session.get('user_email'):
                return f(*args, **kwargs)
            
            now = time.time()
            if now - cache['timestamp'] > timeout:
                cache['response'] = f(*args, **kwargs)
                cache['timestamp'] = now
            return cache['response']
        
        return decorated_function
    return decorator

def clear_api_cache(cache_key=None):
    """Clear specific API cache or all API caches"""
    if cache_key:
        if cache_key in _api_cache_store:
            _api_cache_store[cache_key]['timestamp'] = 0
    else:
        for cache in _api_cache_store.values():
            cache['timestamp'] = 0

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.permanent_session_lifetime = timedelta(days=7)

# Inicializar base de datos si está disponible
if db_available:
    try:
        db = Database()
        print("[OK] Conexion a base de datos establecida")
        
        # Auto-migrate data from JSON if needed (disabled for performance)
        # Uncomment only if you need to reset data
        # try:
        #     from inline_migrate import migrate_from_json
        #     migrate_from_json(db)
        # except Exception as e:
        #     print(f"  ! Migration warning: {str(e)[:50]}")
            
    except Exception as e:
        print(f"[ERROR] Error de conexion: {e}")
        db = None
else:
    db = None
    print("[WARN] Base de datos deshabilitada para testing")
    
# Mostrar estado de la app
print("\n[OK] APP INICIADA")
print(f"   Google OAuth: {'OK' if GOOGLE_CLIENT_ID else 'ERROR'}")
print(f"   Base de datos: {'OK' if db else 'ERROR'}\n")

# ========== CONFIGURACIÓN TABS ==========
TABS = {
    0: {"id": "tab_0", "label": "Inicio", "icon": "Home", "route": "dashboard"},
    1: {"id": "tab_1", "label": "Asistencia", "icon": "Check", "route": "asistencia"},
    2: {"id": "tab_2", "label": "Pagos", "icon": "Money", "route": "pagos"},
    3: {"id": "tab_3", "label": "Miembros", "icon": "Users", "route": "miembros"},
    4: {"id": "tab_4", "label": "Clases", "icon": "Book", "route": "clases"},
    5: {"id": "tab_5", "label": "Reportes", "icon": "BarChart", "route": "reportes"},
    6: {"id": "tab_6", "label": "Retiros", "icon": "TrendingUp", "route": "retiros"},
    7: {"id": "tab_7", "label": "Pagos (Calendario)", "icon": "Calendar", "route": "reportes_pagos"}
}

# ========== FUNCIONES AUXILIARES ==========

def check_db():
    """Verificar que la base de datos está disponible (aviso solo, no bloquea)"""
    if not db:
        print("⚠️  Aviso: Base de datos NO disponible")
        return None, None, None  # No bloquear, solo devolver None
    return db, None, None

def get_clase_hoy():
    """Obtener última clase, clase de hoy y próxima clase"""
    try:
        clases = db.get_clases_hoy()
        return clases if clases else []
    except DatabaseError as e:
        print(f"Error al obtener clases: {e}")
        return []

# ========== RUTAS DE AUTENTICACIÓN ==========

@app.route('/auth/login', methods=['GET'])
def login():
    """Mostrar página de login"""
    return render_template('login.html', GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID)

@app.route('/auth/google', methods=['POST'])
def auth_google():
    """Procesar token de Google OAuth"""
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({"status": "error", "message": "Token no proporcionado"}), 400
        
        # Verificar token de Google
        user_info = GoogleOAuth.verify_token(token)
        
        if not user_info:
            return jsonify({"status": "error", "message": "Token inválido"}), 401
        
        # Verificar si email está en lista de admins
        if not GoogleOAuth.is_admin(user_info['email']):
            return jsonify({
                "status": "error", 
                "message": f"Email {user_info['email']} no autorizado. Contacta al administrador."
            }), 403
        
        # Guardar en sesión
        GoogleOAuth.set_session(user_info)
        
        # Log en base de datos (si disponible)
        if db and hasattr(db, 'update_last_login'):
            try:
                db.update_last_login(user_info['email'])
            except:
                pass  # No crítico si DB no está disponible
        
        return jsonify({"status": "success", "message": "Sesión iniciada"})
    
    except Exception as e:
        print(f"Error en auth_google: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/auth/logout', methods=['GET'])
def logout():
    """Cerrar sesión"""
    GoogleOAuth.clear_session()
    return redirect(url_for('login'))

# ========== RUTAS PRINCIPALES ==========

@app.route('/')
@login_required
def index():
    """Dashboard principal"""
    try:
        # Obtener usuario actual
        current_user = GoogleOAuth.get_session_user()
        
        if db:
            # Si hay base de datos, obtener datos reales
            try:
                # Obtener miembros ACTIVOS e INACTIVOS separados
                miembros_activos = db.get_miembros()  # Solo activos (estado='Activo' por defecto)
                miembros_inactivos = db.get_miembros_inactivos()
                miembros_total = miembros_activos + miembros_inactivos
                
                miembros_regulares = db.get_miembros(tipo_asistencia='Regular')
                clases = db.get_clases()
                
                # Debug: mostrar estados de las clases
                print("[DEBUG CLASES] Estados en BD:")
                for c in clases[:10]:  # Mostrar primeras 10
                    print(f"  - {c.get('nombre', 'Sin nombre')}: estado='{c.get('estado', 'NULL')}'")
                
                # Contar clases realizadas (estado = "Realizada")
                # Más flexible: busca "realizada" en cualquier posición o si tiene checkmark
                clases_realizadas = sum(1 for c in clases if c.get('estado') and ('realizada' in str(c.get('estado', '')).lower() or '✓' in str(c.get('estado', ''))))
                
                print(f"[DEBUG CLASES] Total: {len(clases)}, Realizadas: {clases_realizadas}")
                print(f"[DEBUG MIEMBROS] Activos: {len(miembros_activos)}, Inactivos: {len(miembros_inactivos)}, Total: {len(miembros_total)}")
                
                # Debug: mostrar miembros inactivos si existen
                if miembros_inactivos:
                    print("[DEBUG MIEMBROS INACTIVOS]:")
                    for m in miembros_inactivos:
                        print(f"  - {m.get('nombre', '')} {m.get('apellido', '')}: estado='{m.get('estado', 'NULL')}'")
                else:
                    print("[DEBUG MIEMBROS INACTIVOS] No hay miembros inactivos")
                
                # Obtener pagos este mes
                start_date = date(date.today().year, date.today().month, 1)
                if date.today().month == 12:
                    end_date = date(date.today().year + 1, 1, 1)
                else:
                    end_date = date(date.today().year, date.today().month + 1, 1)
                
                # Pagos este mes
                pagos_mes = db.get_pagos()
                total_pagos = sum(float(p['monto']) for p in pagos_mes if p.get('monto'))
                
                # Retiros
                retiros = db.get_retiros()
                total_retiros = sum(float(r['monto']) for r in retiros if r.get('monto')) if retiros else 0
                
                # Total esperado (miembros regulares * cuota mensual $30,000)
                total_esperado = len(miembros_regulares) * 30000
                
                stats = {
                    'miembros_activos': len(miembros_activos),
                    'miembros_inactivos': len(miembros_inactivos),
                    'miembros': len(miembros_total),
                    'miembros_regulares': len(miembros_regulares),
                    'miembros_oyentes': len(miembros_activos) - len(miembros_regulares),
                    'clases': len(clases),
                    'clases_realizadas': clases_realizadas,
                    'pagos': total_pagos,
                    'pagos_esperado': total_esperado,
                    'pagos_porcentaje': int((total_pagos / total_esperado * 100) if total_esperado > 0 else 0),
                    'retiros': total_retiros
                }
            except Exception as e:
                print(f"Error obteniendo datos: {e}")
                stats = {'error': 'No se pudieron obtener datos de la base de datos'}
        else:
            # Sin base de datos - mostrar mensaje de prueba
            stats = {
                'miembros_activos': 0,
                'miembros_inactivos': 0,
                'miembros': 0,
                'miembros_regulares': 0,
                'miembros_oyentes': 0,
                'clases': 0,
                'clases_realizadas': 0,
                'pagos': 0,
                'pagos_esperado': 0,
                'pagos_porcentaje': 0,
                'retiros': 0,
                'info': '⚠️ Base de datos no disponible - Modo testing'
            }
        
        return render_template('tab_0_dashboard.html',
                             tabs=TABS,
                             active_tab=0,
                             current_user=current_user,
                             stats=stats,
                             clases_hoy=[])
    
    except Exception as e:
        print(f"Error en dashboard: {e}")
        current_user = GoogleOAuth.get_session_user()
        return render_template('tab_0_dashboard.html',
                             tabs=TABS,
                             active_tab=0,
                             current_user=current_user,
                             stats={'error': str(e)},
                             clases_hoy=[])

@app.route('/tab/<int:tab_id>')
@login_required
def render_tab(tab_id):
    """Renderizar tab específico"""
    if tab_id not in TABS:
        return jsonify({"status": "error", "message": "Tab no encontrado"}), 404
    
    try:
        current_user = GoogleOAuth.get_session_user()
        tab_info = TABS[tab_id]
        template = f"tab_{tab_id}_{tab_info['route']}.html"
        
        # Cargar datos según el tab desde base de datos
        data = {}
        
        if db:
            # Si base de datos está disponible, obtener datos reales
            try:
                if tab_id == 1:  # Asistencia
                    data['miembros'] = db.get_miembros()
                    data['clases'] = db.get_clases()
                    data['asistencia'] = db.get_asistencia()
                    data['clases_hoy'] = get_clase_hoy()
                
                elif tab_id == 2:  # Pagos
                    data['miembros'] = db.get_miembros(tipo_asistencia='Regular')
                    data['pagos'] = db.get_pagos()
                
                elif tab_id == 3:  # Miembros
                    data['miembros'] = db.get_miembros()
                
                elif tab_id == 4:  # Clases
                    # Nota: Migración SQL de oradores ejecutada manualmente via /api/admin/migrate-oradores
                    data['clases'] = db.get_clases()
                    data['oradores'] = db.get_oradores()
                
                elif tab_id == 5:  # Reportes
                    data['miembros'] = db.get_miembros(tipo_asistencia='Regular')
                    data['reporte_pagos'] = db.get_reporte_pagos_por_mes()
                    data['asistencia'] = db.get_asistencia()
                    data['pagos'] = db.get_pagos()
                
                elif tab_id == 6:  # Retiros
                    data['retiros'] = db.get_retiros()
            except Exception as e:
                print(f"Error obteniendo datos: {e}")
                data['error'] = f"Error obteniendo datos: {str(e)}"
        else:
            # Sin base de datos - mostrar mensaje de prueba
            data['miembros'] = []
            data['clases'] = []
            data['asistencia'] = []
            data['pagos'] = []
            data['retiros'] = []
            data['error'] = "⚠️ Base de datos no disponible - Modo testing (solo autenticación)"
        
        return render_template(template,
                             tabs=TABS,
                             active_tab=tab_id,
                             current_user=current_user,
                             **data)
    
    except Exception as e:
        print(f"Error al cargar tab {tab_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/tab/3-5')
@login_required
def render_oradores():
    """Renderizar tab de Oradores"""
    try:
        current_user = GoogleOAuth.get_session_user()
        
        data = {}
        if db:
            try:
                data['oradores'] = db.get_oradores()
            except Exception as e:
                print(f"Error obteniendo oradores: {e}")
                data['oradores'] = []
                data['error'] = f"Error obteniendo oradores: {str(e)}"
        else:
            data['oradores'] = []
            data['error'] = "⚠️ Base de datos no disponible"
        
        return render_template('tab_3-5_oradores.html',
                             tabs=TABS,
                             active_tab='3-5',
                             current_user=current_user,
                             **data)
    
    except Exception as e:
        print(f"Error al cargar tab oradores: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - ASISTENCIA ==========

@app.route('/api/asistencia/save', methods=['POST'])
def save_asistencia():
    """Guardar asistencia en la base de datos - soporta múltiples registros"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        datos = request.json
        
        # Check if it's an array of attendance records (from UI)
        if isinstance(datos, list):
            # Multiple attendance records
            for asistencia in datos:
                miembro_id = asistencia.get('id_miembro')
                fecha = asistencia.get('fecha', str(date.today()))
                asistio = asistencia.get('asistio', asistencia.get('presente', True))
                clase_id = asistencia.get('clase_id', 1)
                
                if miembro_id:
                    db.add_asistencia(miembro_id, clase_id, fecha, asistio)
        
        # Check if it's the new format with fecha_clase and asistencias array
        elif 'asistencias' in datos:
            fecha_clase = datos.get('fecha_clase', str(date.today()))
            clase_id = datos.get('id_clase', 1)
            asistencias = datos.get('asistencias', [])
            
            for asistencia in asistencias:
                miembro_id = asistencia.get('id_miembro')
                presente = asistencia.get('presente', True)
                
                if miembro_id:
                    db.add_asistencia(miembro_id, clase_id, fecha_clase, presente)
        
        # Old format - single record
        else:
            miembro_id = datos.get('id_miembro')
            fecha = datos.get('fecha', str(date.today()))
            asistio = datos.get('asistio', True)
            clase_id = datos.get('clase_id', 1)
            
            if miembro_id:
                db.add_asistencia(miembro_id, clase_id, fecha, asistio)
        
        return jsonify({"status": "success", "message": "Asistencia guardada correctamente"})
    
    except Exception as e:
        print(f"Error al guardar asistencia: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/asistencia/por-fecha/<fecha>', methods=['GET'])
def get_asistencia_fecha(fecha):
    """Obtener asistencia para una fecha específica"""
    try:
        if db:
            asistencia = db.get_asistencia_fecha(fecha)
            return jsonify({"status": "success", "asistencia": [dict(a) for a in asistencia]})
        else:
            return jsonify({"status": "success", "asistencia": []})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "success", "asistencia": []})

@app.route('/api/asistencia/obtain/<clase_id>', methods=['GET'])
def get_asistencia_clase(clase_id):
    """Obtener asistencia guardada para una clase específica de HOY - todos los registros"""
    try:
        from datetime import date
        hoy = str(date.today())
        
        if db:
            # Usar el objeto db existente que ya está conectado a PostgreSQL
            with db.get_cursor() as cursor:
                query = """
                    SELECT a.miembro_id, a.asistio, a.fecha,
                           m.nombre || ' ' || m.apellido as nombre_completo
                    FROM asistencia a
                    JOIN miembros m ON a.miembro_id = m.id
                    WHERE a.clase_id = %s AND DATE(a.fecha) = %s
                    ORDER BY m.nombre
                """
                cursor.execute(query, (int(clase_id), hoy))
                registros = cursor.fetchall()
            
            # Convertir a formato esperado por el frontend
            datos_procesados = [
                {
                    'id_miembro': registro['miembro_id'],
                    'nombre_completo': registro['nombre_completo'],
                    'presente': bool(registro['asistio'])  # True si asistio=1, False si asistio=0
                }
                for registro in registros
            ]
            
            return jsonify({"status": "success", "data": datos_procesados})
        else:
            return jsonify({"status": "success", "data": []})
    except Exception as e:
        print(f"Error al obtener asistencia de clase {clase_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "data": [], "message": str(e)})

# ========== API ENDPOINTS - CLASES ==========

@app.route('/api/clases/todas', methods=['GET'])
@cache_route(timeout=120, cache_key='get_todas_clases')  # Cache for 2 minutes
def get_todas_clases():
    """Obtener TODAS las clases disponibles"""
    try:
        if db:
            # Limit to 50 most recent classes for performance
            clases = db.get_clases()[:50]  
            # Convert to expected format for frontend
            clases_formatted = []
            for c in clases:
                c_dict = dict(c) if hasattr(c, 'items') else c
                clases_formatted.append({
                    'id': c_dict.get('id'),
                    'fecha': str(c_dict.get('fecha', '')),
                    'tema': c_dict.get('nombre', ''),  # Map nombre to tema
                    'orador': c_dict.get('descripcion', ''),  # Map descripcion to orador
                    'modalidad': c_dict.get('modalidad', ''),
                    'estado': c_dict.get('estado', ''),
                    'link_meet': c_dict.get('link_meet', '')
                })
            return jsonify({"status": "success", "clases": clases_formatted})
        else:
            # Sin base de datos - devolver ejemplo vacío
            return jsonify({"status": "success", "clases": []})
    except Exception as e:
        print(f"Error en /api/clases/todas: {e}")
        return jsonify({"status": "success", "clases": []})  # Devolver vacío en error

@app.route('/api/clases/por-fecha/<fecha>', methods=['GET'])
def get_clase_por_fecha(fecha):
    """Obtener clase para una fecha específica"""
    try:
        if db:
            clase = db.get_clase(1)  # Implementar búsqueda por fecha
            if clase:
                return jsonify({"status": "success", "clase": dict(clase)})
            else:
                return jsonify({"status": "success", "clase": None})
        else:
            return jsonify({"status": "success", "clase": None})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "success", "clase": None})

@app.route('/api/clases/hoy', methods=['GET'])
@cache_route(timeout=60, cache_key='get_clases_hoy')  # Cache for 1 minute
def get_clases_hoy_api():
    """Obtener clases de hoy (última, hoy, próxima)"""
    try:
        if db:
            clases = get_clase_hoy()
            return jsonify({"status": "success", "clases": [dict(c) for c in clases]})
        else:
            return jsonify({"status": "success", "clases": []})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "success", "clases": []})

@app.route('/api/clases/update', methods=['POST'])
def update_clase():
    """Actualizar clase (nombre, descripcion, fecha, estado, modalidad, hora, orador)"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        datos = request.json
        clase_id = int(datos.get('id'))  # Asegurar que es int
        nombre = datos.get('nombre', '').strip()
        descripcion = datos.get('descripcion', '').strip()
        fecha = datos.get('fecha', '').strip()
        nuevo_estado = datos.get('estado', '').strip()
        modalidad = datos.get('modalidad', '').strip()
        hora_inicio = datos.get('hora_inicio', '21:00').strip() or '21:00'  # Default 21:00 = 9:00 PM
        orador_id = datos.get('orador_id')
        
        # Validar datos
        if not clase_id or not nuevo_estado:
            return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        
        if nuevo_estado not in ['Programada', 'Realizada', 'Cancelada']:
            return jsonify({"status": "error", "message": "Estado inválido"}), 400
        
        print(f"[UPDATE] Clase ID: {clase_id}, Nombre: {nombre}, Desc: {descripcion}, Fecha: {fecha}, Estado: {nuevo_estado}, Modalidad: {modalidad}, Hora: {hora_inicio}, Orador ID: {orador_id}")
        
        # Actualizar con los nuevos campos
        with db.get_cursor() as cursor:
            query = "UPDATE clases SET estado=%s, updated_at=NOW()"
            params = [nuevo_estado]
            
            if nombre:
                query += ", nombre=%s"
                params.append(nombre)
            
            if descripcion:
                query += ", descripcion=%s"
                params.append(descripcion)
            
            if fecha:
                query += ", fecha=%s"
                params.append(fecha)
            
            if modalidad:
                query += ", modalidad=%s"
                params.append(modalidad)
            
            # Siempre guardar hora_inicio
            query += ", hora_inicio=%s"
            params.append(hora_inicio)
            
            if orador_id:
                query += ", orador_id=%s"
                params.append(orador_id)
            
            query += " WHERE id=%s"
            params.append(clase_id)
            
            cursor.execute(query, params)
        
        # Clear caches so next request gets fresh data
        clear_cache('get_clases')  # Database cache
        clear_api_cache('get_todas_clases')  # API response cache
        clear_api_cache('get_clases_hoy')  # API response cache
        
        # Fetch updated class data to return to frontend
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT c.id, c.nombre, c.descripcion, c.fecha, c.hora_inicio, c.modalidad, c.estado, c.link_meet, "
                "c.orador_id, "
                "COALESCE(o.nombre, '') as orador_nombre, COALESCE(o.apellido, '') as orador_apellido "
                "FROM clases c "
                "LEFT JOIN oradores o ON c.orador_id = o.id "
                "WHERE c.id = %s",
                (clase_id,)
            )
            clase_actualizada = cursor.fetchone()
        
        clase_dict = dict(clase_actualizada) if hasattr(clase_actualizada, 'items') else clase_actualizada
        
        print(f"[SUCCESS] Clase {clase_id} actualizada")
        return jsonify({
            "status": "success", 
            "message": "Clase actualizada correctamente",
            "clase": {
                'id': clase_dict.get('id'),
                'nombre': clase_dict.get('nombre'),
                'descripcion': clase_dict.get('descripcion'),
                'fecha': str(clase_dict.get('fecha')),
                'hora_inicio': str(clase_dict.get('hora_inicio')) if clase_dict.get('hora_inicio') else '',
                'modalidad': clase_dict.get('modalidad'),
                'estado': clase_dict.get('estado'),
                'orador_id': clase_dict.get('orador_id'),
                'orador_nombre': clase_dict.get('orador_nombre', ''),
                'orador_apellido': clase_dict.get('orador_apellido', '')
            }
        })
    except ValueError as e:
        print(f"[ERROR] Valor inválido: {e}")
        return jsonify({"status": "error", "message": f"Valor inválido: {str(e)}"}), 400
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/oradores/all', methods=['GET'])
def get_all_oradores():
    """Obtener lista de todos los oradores"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, apellido FROM oradores ORDER BY nombre ASC"
            )
            oradores = cursor.fetchall()
        
        return jsonify({"status": "success", "data": oradores})
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/oradores/todos', methods=['GET'])
def get_oradores_todos():
    """Obtener lista de todos los oradores"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        oradores = db.get_oradores()
        return jsonify({"status": "success", "data": oradores})
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/oradores/add', methods=['POST'])
def add_orador_endpoint():
    """Agregar nuevo orador"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        datos = request.json
        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        email = datos.get('email', '').strip()
        telefono = datos.get('telefono', '').strip()
        especialidad = datos.get('especialidad', '').strip()
        
        if not nombre or not apellido:
            return jsonify({"status": "error", "message": "Nombre y apellido son requeridos"}), 400
        
        orador_id = db.add_orador(nombre, apellido, email, telefono, especialidad)
        
        if orador_id:
            return jsonify({"status": "success", "message": "Orador agregado correctamente", "id": orador_id})
        else:
            return jsonify({"status": "error", "message": "Error al agregar orador"}), 500
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/oradores/update/<int:id_orador>', methods=['POST'])
def update_orador_endpoint(id_orador):
    """Actualizar datos de un orador"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        datos = request.json
        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        email = datos.get('email', '').strip()
        telefono = datos.get('telefono', '').strip()
        especialidad = datos.get('especialidad', '').strip()
        
        if not nombre or not apellido:
            return jsonify({"status": "error", "message": "Nombre y apellido son requeridos"}), 400
        
        success = db.update_orador(id_orador, nombre, apellido, email, telefono, especialidad)
        
        if success:
            return jsonify({"status": "success", "message": "Orador actualizado correctamente"})
        else:
            return jsonify({"status": "error", "message": "Orador no encontrado"}), 404
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/oradores/delete/<int:id_orador>', methods=['DELETE'])
def delete_orador_endpoint(id_orador):
    """Eliminar un orador"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        success = db.delete_orador(id_orador)
        
        if success:
            return jsonify({"status": "success", "message": "Orador eliminado correctamente"})
        else:
            return jsonify({"status": "error", "message": "Orador no encontrado"}), 404
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/migrate-012', methods=['POST'])
def migrate_012():
    """Ejecutar migración 012 (agregar orador_id a clases)"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        print("[MIGRACIÓN 012] Iniciando...")
        
        with db.get_cursor() as cursor:
            # Agregar columna orador_id
            cursor.execute(
                "ALTER TABLE clases ADD COLUMN IF NOT EXISTS orador_id INTEGER REFERENCES oradores(id) ON DELETE SET NULL"
            )
            print("[MIGRACIÓN 012] Columna orador_id agregada")
            
            # Crear índice
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_clases_orador_id ON clases(orador_id)"
            )
            print("[MIGRACIÓN 012] Índice creado")
        
        # Limpiar caché
        clear_cache('get_clases')
        
        print("[MIGRACIÓN 012] ✓ Completada")
        return jsonify({"status": "success", "message": "Migración 012 ejecutada correctamente"})
    except Exception as e:
        print(f"[ERROR MIGRACIÓN 012] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/migrate-oradores', methods=['POST'])
def migrate_oradores():
    """Migrar datos: buscar y asignar oradores a todas las clases sin orador
    Este proceso busca el orador en la BD basándose en la descripción de la clase"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        # Verificar que sea admin (opcional - descomenta si quieres verificar)
        # current_user = GoogleOAuth.get_session_user()
        # if current_user['email'] not in ADMIN_EMAILS:
        #     return jsonify({"status": "error", "message": "No tienes permisos para realizar esta acción"}), 403
        
        print("\n" + "="*60)
        print("🚀 INICIANDO MIGRACIÓN: ASIGNACIÓN DE ORADORES")
        print("="*60)
        
        # Ejecutar la migración
        resultado = db.asignar_oradores_automatico()
        
        print("\n" + "="*60)
        print("RESUMEN DE LA MIGRACIÓN:")
        print("="*60)
        print(f"Total de clases sin orador: {resultado['total_clases']}")
        print(f"Oradores asignados: {resultado['asignados']}")
        print(f"No encontrados: {resultado['no_encontrados']}")
        print("="*60 + "\n")
        
        # Limpiar caché para refrescar datos
        clear_cache('get_clases')
        clear_api_cache('get_todas_clases')
        clear_api_cache('get_clases_hoy')
        
        return jsonify(resultado)
    except Exception as e:
        print(f"[ERROR MIGRACIÓN ORADORES] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": str(e),
            "total_clases": 0,
            "asignados": 0,
            "no_encontrados": 0
        }), 500

@app.route('/api/clases/crear', methods=['POST'])
def crear_clase():
    """Crear nueva clase en la base de datos"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        datos = request.json
        nombre = datos.get('nombre', '').strip()
        descripcion = datos.get('descripcion', '').strip()
        fecha = datos.get('fecha', '').strip()
        hora_inicio = datos.get('hora_inicio', '21:00').strip() or '21:00'  # Default 21:00 = 9:00 PM
        modalidad = datos.get('modalidad', 'Presencial').strip()
        orador_id = datos.get('orador_id')
        
        # Validar datos requeridos
        if not nombre or not fecha:
            return jsonify({"status": "error", "message": "Nombre y fecha son requeridos"}), 400
        
        # Validar modalidad
        if modalidad not in ['Presencial', 'Meet']:
            return jsonify({"status": "error", "message": "Modalidad inválida"}), 400
        
        print(f"[CREAR CLASE] Nombre: {nombre}, Fecha: {fecha}, Hora: {hora_inicio}, Modalidad: {modalidad}, Orador ID: {orador_id}")
        
        # Crear clase en la base de datos
        clase_id = db.add_clase(nombre, fecha, hora_inicio, modalidad, link_meet=None, orador_id=orador_id)
        
        # Si la clase tiene descripción, actualizar la columna descripcion (si existe)
        if descripcion:
            try:
                with db.get_cursor() as cursor:
                    cursor.execute(
                        "UPDATE clases SET descripcion=%s WHERE id=%s",
                        (descripcion, clase_id)
                    )
            except Exception as e:
                print(f"[ADVERTENCIA] No se pudo guardar descripción: {e}")
        
        # Clear caches
        clear_cache('get_clases')
        clear_api_cache('get_todas_clases')
        clear_api_cache('get_clases_hoy')
        
        print(f"[SUCCESS] Nueva clase creada con ID: {clase_id}")
        return jsonify({"status": "success", "message": "Clase creada correctamente", "id": clase_id})
    except Exception as e:
        print(f"[ERROR] Exception al crear clase: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clases/delete', methods=['DELETE', 'POST'])
def delete_clase():
    """Eliminar una clase de la base de datos"""
    try:
        if not db:
            return jsonify({"status": "error", "message": "Base de datos no disponible"}), 503
        
        datos = request.json
        clase_id = int(datos.get('id'))  # Asegurar que es int
        
        if not clase_id:
            return jsonify({"status": "error", "message": "ID de clase requerido"}), 400
        
        print(f"[DELETE CLASE] Eliminando clase ID: {clase_id}")
        
        # Eliminar la clase
        with db.get_cursor() as cursor:
            cursor.execute("DELETE FROM clases WHERE id=%s", (clase_id,))
        
        # Clear caches so next request gets fresh data
        clear_cache('get_clases')
        clear_api_cache('get_todas_clases')
        clear_api_cache('get_clases_hoy')
        
        print(f"[SUCCESS] Clase {clase_id} eliminada")
        return jsonify({"status": "success", "message": "Clase eliminada correctamente"})
    except ValueError as e:
        print(f"[ERROR] Valor inválido: {e}")
        return jsonify({"status": "error", "message": f"Valor inválido: {str(e)}"}), 400
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - PAGOS ==========

@app.route('/api/pagos/save', methods=['POST'])
def save_pago():
    """Guardar pago en la base de datos"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        print(f"[PAGOS] Datos recibidos: {datos}")
        
        # Parámetros del pago
        miembro_id = datos.get('miembro_id') or datos.get('id_miembro')
        monto = float(datos.get('monto', 0))
        fecha = datos.get('fecha', str(date.today()))
        mes = datos.get('mes', '')
        tipo_pago = datos.get('tipo_pago', 'Cuota')  
        metodo_pago = datos.get('metodo_pago', 'Efectivo')
        descripcion = datos.get('descripcion', '')  # Notas del pago
        
        # Nuevos parámetros para multi-mes y estado
        meses_seleccionados = datos.get('meses_seleccionados', [])
        estado_pago = 'Puntual'  # Default value, no se envía desde el frontend
        
        if not miembro_id:
            return jsonify({"status": "error", "message": "ID de miembro es requerido"}), 400
        
        if monto <= 0:
            return jsonify({"status": "error", "message": "Monto debe ser mayor a 0"}), 400
        
        # Calcular mes_inicio y mes_fin si hay meses seleccionados
        mes_inicio = None
        mes_fin = None
        if tipo_pago == 'Cuota' and meses_seleccionados:
            mes_inicio = min(meses_seleccionados)
            mes_fin = max(meses_seleccionados)
        
        print(f"[PAGOS] Guardando pago: miembro_id={miembro_id}, monto={monto}, fecha={fecha}, tipo={tipo_pago}, metodo={metodo_pago}, notas={descripcion}, meses={meses_seleccionados}, estado={estado_pago}")
        
        # Pasar nuevos parámetros a la BD
        pago_id = db.add_pago(miembro_id, monto, fecha, mes, descripcion, metodo_pago, tipo_pago, mes_inicio, mes_fin, estado_pago)
        
        print(f"[PAGOS] Pago guardado exitosamente con ID: {pago_id}")
        return jsonify({"status": "success", "message": "Pago registrado correctamente", "id": pago_id})
    
    except ValueError as e:
        print(f"[ERROR] Valor inválido: {e}")
        return jsonify({"status": "error", "message": f"Valor inválido: {str(e)}"}), 400
    except DatabaseError as e:
        print(f"[ERROR] Error de BD: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/miembro/<int:miembro_id>', methods=['GET'])
def get_pagos_miembro(miembro_id):
    """Obtener pagos de un miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        pagos = db.get_pagos_miembro(miembro_id)
        pagos_list = []
        
        for p in pagos:
            pago_dict = dict(p)
            # Convertir fecha a string en formato YYYY-MM-DD
            if pago_dict.get('fecha'):
                fecha = pago_dict['fecha']
                if hasattr(fecha, 'isoformat'):
                    pago_dict['fecha'] = fecha.isoformat().split('T')[0]
                else:
                    pago_dict['fecha'] = str(fecha)
            # Convertir monto a int
            if pago_dict.get('monto'):
                pago_dict['monto'] = int(pago_dict['monto'])
            pagos_list.append(pago_dict)
        
        return jsonify({"status": "success", "pagos": pagos_list})
    except Exception as e:
        print(f"[ERROR PAGOS] Error al obtener pagos del miembro {miembro_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/delete/<int:pago_id>', methods=['DELETE'])
def delete_pago(pago_id):
    """Eliminar un pago"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        print(f"[PAGOS DELETE] Eliminando pago {pago_id}")
        db.delete_pago(pago_id)
        print(f"[PAGOS DELETE] Pago {pago_id} eliminado exitosamente")
        return jsonify({"status": "success", "message": "Pago eliminado correctamente"})
    except DatabaseError as e:
        print(f"[ERROR] Error de BD al eliminar pago {pago_id}: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception al eliminar pago {pago_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/update/<int:pago_id>', methods=['POST'])
def update_pago(pago_id):
    """Actualizar un pago"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        print(f"[PAGOS UPDATE] Datos recibidos para pago {pago_id}: {datos}")
        
        monto = float(datos.get('monto'))
        fecha = datos.get('fecha', str(date.today()))
        mes = datos.get('mes', '')
        tipo_pago = datos.get('tipo_pago', 'Cuota')
        metodo_pago = datos.get('metodo_pago', 'Efectivo')
        descripcion = datos.get('descripcion', '')  # Notas del pago
        mes_inicio = datos.get('mes_inicio')  # Para Cuota: mes inicial del rango
        mes_fin = datos.get('mes_fin')  # Para Cuota: mes final del rango
        
        print(f"[PAGOS UPDATE] Actualizando pago {pago_id}: monto={monto}, fecha={fecha}, tipo={tipo_pago}, mes_inicio={mes_inicio}, mes_fin={mes_fin}, notas={descripcion}")
        
        db.update_pago(pago_id, monto, fecha, mes, tipo_pago, descripcion, metodo_pago, mes_inicio, mes_fin)
        
        print(f"[PAGOS UPDATE] Pago {pago_id} actualizado exitosamente")
        return jsonify({"status": "success", "message": "Pago actualizado correctamente"})
    except ValueError as e:
        print(f"[ERROR] Valor inválido: {e}")
        return jsonify({"status": "error", "message": f"Valor inválido: {str(e)}"}), 400
    except DatabaseError as e:
        print(f"[ERROR] Error de BD: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - RETIROS ==========

@app.route('/api/retiros/save', methods=['POST'])
def save_retiro():
    """Guardar retiro en la base de datos"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        print(f"[RETIROS] Datos recibidos: {datos}")
        
        concepto = datos.get('concepto', '')
        monto = float(datos.get('monto', 0))
        fecha = datos.get('fecha', str(date.today()))
        metodo = datos.get('metodo', 'Efectivo')
        notas = datos.get('notas', '')
        
        if monto <= 0:
            return jsonify({"status": "error", "message": "Monto debe ser mayor a 0"}), 400
        
        print(f"[RETIROS] Guardando retiro: concepto={concepto}, monto={monto}, fecha={fecha}")
        
        # Usar miembro_id=None para retiros generales (no vinculados a miembro)
        razon = f"{metodo}" + (f" | {notas}" if notas else "")
        retiro_id = db.add_retiro(miembro_id=None, monto=monto, fecha=fecha, razon=razon, tipo_retiro=concepto)
        
        print(f"[RETIROS] Retiro guardado exitosamente con ID: {retiro_id}")
        return jsonify({"status": "success", "message": "Retiro registrado correctamente", "id": retiro_id})
    
    except ValueError as e:
        print(f"[ERROR] Valor inválido: {e}")
        return jsonify({"status": "error", "message": f"Valor inválido: {str(e)}"}), 400
    except DatabaseError as e:
        print(f"[ERROR] Error de BD: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/retiros/todos', methods=['GET'])
def get_todos_retiros():
    """Obtener todos los retiros"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        retiros = db.get_retiros()
        retiros_list = []
        
        for r in retiros:
            retiro_dict = dict(r)
            
            # Mapeo de campos para el frontend
            # La DB guarda: tipo_retiro=concepto, razon=metodo|notas
            # El frontend espera: concepto, metodo, notas
            retiro_mapped = {
                'id': retiro_dict.get('id'),
                'concepto': retiro_dict.get('tipo_retiro', ''),
                'monto': int(retiro_dict.get('monto', 0)) if retiro_dict.get('monto') else 0,
                'fecha': retiro_dict.get('fecha'),
                'metodo': '',
                'notas': '',
                'miembro_id': retiro_dict.get('miembro_id')
            }
            
            # Convertir fecha a string en formato YYYY-MM-DD
            if retiro_mapped['fecha']:
                fecha = retiro_mapped['fecha']
                if hasattr(fecha, 'isoformat'):
                    retiro_mapped['fecha'] = fecha.isoformat().split('T')[0]
                else:
                    retiro_mapped['fecha'] = str(fecha)
            
            # Extraer metodo y notas del campo razon (formato: "metodo | notas")
            razon = retiro_dict.get('razon', '')
            if razon and '|' in razon:
                parts = razon.split('|', 1)
                retiro_mapped['metodo'] = parts[0].strip()
                retiro_mapped['notas'] = parts[1].strip() if len(parts) > 1 else ''
            elif razon:
                retiro_mapped['metodo'] = razon.strip()
            
            retiros_list.append(retiro_mapped)
        
        return jsonify({"status": "success", "retiros": retiros_list})
    except Exception as e:
        print(f"[ERROR] Error al obtener retiros: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/retiros/delete/<int:retiro_id>', methods=['DELETE'])
def delete_retiro(retiro_id):
    """Eliminar un retiro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        print(f"[RETIROS DELETE] Eliminando retiro {retiro_id}")
        db.delete_retiro(retiro_id)
        print(f"[RETIROS DELETE] Retiro {retiro_id} eliminado exitosamente")
        return jsonify({"status": "success", "message": "Retiro eliminado correctamente"})
    except DatabaseError as e:
        print(f"[ERROR] Error de BD al eliminar retiro {retiro_id}: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception al eliminar retiro {retiro_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/retiros/update/<int:retiro_id>', methods=['POST'])
def update_retiro(retiro_id):
    """Actualizar un retiro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        print(f"[RETIROS UPDATE] Datos recibidos para retiro {retiro_id}: {datos}")
        
        concepto = datos.get('concepto', '')
        monto = float(datos.get('monto'))
        fecha = datos.get('fecha', str(date.today()))
        metodo = datos.get('metodo', 'Efectivo')
        notas = datos.get('notas', '')
        
        print(f"[RETIROS UPDATE] Actualizando retiro {retiro_id}: concepto={concepto}, monto={monto}, fecha={fecha}")
        
        db.update_retiro(retiro_id, concepto, monto, fecha, metodo, notas)
        
        print(f"[RETIROS UPDATE] Retiro {retiro_id} actualizado exitosamente")
        return jsonify({"status": "success", "message": "Retiro actualizado correctamente"})
    except ValueError as e:
        print(f"[ERROR] Valor inválido: {e}")
        return jsonify({"status": "error", "message": f"Valor inválido: {str(e)}"}), 400
    except DatabaseError as e:
        print(f"[ERROR] Error de BD: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/retiros/miembro/<int:miembro_id>', methods=['GET'])
def get_retiros_miembro(miembro_id):
    """Obtener retiros de un miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        retiros = db.get_retiros_miembro(miembro_id)
        return jsonify({"status": "success", "retiros": [dict(r) for r in retiros]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - MIEMBROS ==========

@app.route('/api/miembros/all', methods=['GET'])
@cache_route(timeout=300, cache_key='get_all_miembros')  # Cache for 5 minutes
def get_all_miembros():
    """Obtener todos los miembros - cached for 5 min"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        miembros = db.get_miembros()
        return jsonify({"status": "success", "miembros": [dict(m) for m in miembros]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/crear', methods=['POST'])
def crear_miembro():
    """Crear nuevo miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        email = datos.get('email', '').strip()
        congregacion = datos.get('congregacion') or 'ICE Fco Arias'
        localidad = datos.get('localidad') or 'Salta Capital'
        tipo_asistencia = datos.get('tipo_asistencia', 'Regular')
        
        if not nombre or not apellido:
            return jsonify({"status": "error", "message": "Nombre y apellido son requeridos"}), 400
        
        miembro_id = db.add_miembro(nombre, apellido, email, tipo_asistencia, 
                                    congregacion=congregacion, localidad=localidad)
        
        # Clear cache so next GET reflects the changes
        clear_cache()
        clear_api_cache()
        
        return jsonify({
            "status": "success", 
            "message": "Miembro creado correctamente",
            "id": miembro_id
        })
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/update', methods=['POST'])
def update_miembro():
    """Actualizar tipo de asistencia de un miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        miembro_id = datos.get('id_miembro')
        nuevo_tipo = datos.get('tipo_asistencia')
        
        db.update_miembro_tipo(miembro_id, nuevo_tipo)
        
        # Clear cache so next GET reflects the changes
        clear_cache()
        clear_api_cache()
        
        return jsonify({"status": "success", "message": "Miembro actualizado correctamente"})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/<int:miembro_id>', methods=['GET'])
def get_miembro_endpoint(miembro_id):
    """Obtener datos completos de un miembro específico"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        miembro = db.get_miembro(miembro_id)
        if miembro:
            return jsonify({"status": "success", "miembro": dict(miembro)})
        else:
            return jsonify({"status": "error", "message": "Miembro no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/update-datos', methods=['POST'])
def update_miembro_datos():
    """Actualizar datos personales de un miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        miembro_id = datos.get('id_miembro')
        nombre = datos.get('nombre')
        apellido = datos.get('apellido')
        email = datos.get('email')
        congregacion = datos.get('congregacion')
        localidad = datos.get('localidad')
        tipo_asistencia = datos.get('tipo_asistencia')
        
        if not miembro_id or not nombre or not apellido:
            return jsonify({"status": "error", "message": "Faltan datos requeridos"}), 400
        
        db.update_miembro_datos(miembro_id, nombre, apellido, email, congregacion, localidad, tipo_asistencia)
        
        # Clear cache so next GET reflects the changes
        clear_cache()
        clear_api_cache()
        
        return jsonify({"status": "success", "message": "Datos actualizados correctamente"})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/delete', methods=['POST'])
def delete_miembro():
    """Eliminar o deshabilitar un miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        miembro_id = datos.get('id_miembro')
        
        if not miembro_id:
            return jsonify({"status": "error", "message": "ID de miembro requerido"}), 400
        
        result = db.delete_miembro(miembro_id)
        
        # Clear cache so next GET reflects the changes
        clear_cache()
        clear_api_cache()
        
        return jsonify({
            "status": "success", 
            "message": result.get("message"),
            "deleted": result.get("deleted")
        })
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/inactivos', methods=['GET'])
def get_miembros_inactivos():
    """Obtener todos los miembros inactivos"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        miembros = db.get_miembros_inactivos()
        return jsonify({"status": "success", "data": [dict(m) for m in miembros]})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/reactivar', methods=['POST'])
def reactivar_miembro():
    """Reactivar un miembro inactivo"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        miembro_id = datos.get('id_miembro')
        
        if not miembro_id:
            return jsonify({"status": "error", "message": "ID de miembro requerido"}), 400
        
        db.reactivar_miembro(miembro_id)
        
        # Clear cache so next GET reflects the changes
        clear_cache()
        clear_api_cache()
        
        return jsonify({"status": "success", "message": "Miembro reactivado correctamente"})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - REPORTES ==========

@app.route('/api/reportes/pagos-por-mes', methods=['GET'])
def get_reporte_pagos():
    """Obtener reporte de pagos por mes"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        reporte = db.get_reporte_pagos_por_mes()
        return jsonify({"status": "success", "reporte": [dict(r) for r in reporte]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reportes/asistencia', methods=['GET'])
def get_reporte_asistencia():
    """Obtener reporte de asistencia"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        fecha_inicio = request.args.get('inicio', '2025-03-01')
        fecha_fin = request.args.get('fin', str(date.today()))
        
        reporte = db.get_reporte_asistencia(fecha_inicio, fecha_fin)
        return jsonify({"status": "success", "reporte": [dict(r) for r in reporte]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reportes/pagos-resumen', methods=['GET'])
def get_resumen_pagos():
    """Obtener resumen de pagos"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        fecha_inicio = request.args.get('inicio', '2025-03-01')
        fecha_fin = request.args.get('fin', str(date.today()))
        
        resumen = db.get_resumen_pagos(fecha_inicio, fecha_fin)
        return jsonify({"status": "success", "resumen": [dict(r) for r in resumen]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - REPORTES CALENDARIO ==========

@app.route('/api/reportes/pagos-calendario', methods=['GET'])
def reportes_pagos_calendario():
    """Reporte de pagos por mes (tabla pivot: alumnos × meses)"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        # Parámetro para filtrar solo regulares
        solo_regulares = request.args.get('solo_regulares', 'true').lower() == 'true'
        
        # Obtener miembros SIN CACHE para asegurar datos frescos
        miembros = db.get_miembros_fresh(estado='Activo')
        
        # Filtrar solo regulares si se solicita
        if solo_regulares:
            miembros = [m for m in miembros if dict(m).get('tipo_asistencia') == 'Regular']
        
        # Obtener todos los pagos
        pagos = db.get_pagos()
        
        # Obtener todos los pagos
        pagos = db.get_pagos()
        
        # Crear reporte pivot
        reporte = []
        
        for miembro in miembros:
            miembro_dict = dict(miembro)
            row = {
                'miembro_id': miembro_dict.get('id'),
                'nombre': miembro_dict.get('nombre', ''),
                'apellido': miembro_dict.get('apellido', ''),
                'matricula_monto': 0,  # Monto total pagado por matrícula
                'libro': 0,  # Monto total pagado por libro
                'estado': miembro_dict.get('estado', 'Activo'),
                'meses': {}
            }
            
            # Inicializar 12 meses con 0
            for mes in range(1, 13):
                row['meses'][f'{mes:02d}'] = 0
            
            # Llenar con pagos del miembro
            for pago in pagos:
                pago_dict = dict(pago)
                if pago_dict.get('miembro_id') == miembro_dict.get('id'):
                    monto = float(pago_dict.get('monto', 0))
                    tipo_pago = pago_dict.get('tipo_pago', '')
                    
                    # Si es pago de Matrícula, agregarlo separately
                    # Normalizar comparación sin acentos
                    tipo_normalized = unicodedata.normalize('NFD', tipo_pago.lower()).encode('ascii', 'ignore').decode() if tipo_pago else ''
                    if tipo_normalized == 'matricula':
                        row['matricula_monto'] += int(monto)
                    elif tipo_normalized == 'libro':
                        row['libro'] += int(monto)
                    else:
                        # Si es cuota mensual, verificar si tiene mes_inicio y mes_fin
                        mes_inicio = pago_dict.get('mes_inicio')
                        mes_fin = pago_dict.get('mes_fin')
                        
                        if mes_inicio and mes_fin:
                            # Distribuir el monto entre los meses del rango
                            cantidad_meses = mes_fin - mes_inicio + 1
                            monto_por_mes = int(monto / cantidad_meses) if cantidad_meses > 0 else int(monto)
                            
                            for mes in range(mes_inicio, mes_fin + 1):
                                mes_key = f'{mes:02d}'
                                row['meses'][mes_key] += monto_por_mes
                        else:
                            # Usar el mes de la fecha (comportamiento anterior)
                            if pago_dict.get('fecha'):
                                fecha = pago_dict['fecha']
                                if hasattr(fecha, 'month'):
                                    mes_key = f"{fecha.month:02d}"
                                else:
                                    # Parsear string
                                    from datetime import datetime as dt
                                    fecha_obj = dt.strptime(str(fecha), '%Y-%m-%d')
                                    mes_key = f"{fecha_obj.month:02d}"
                                
                                row['meses'][mes_key] += int(monto)
            
            reporte.append(row)
        
        # Ordenar por apellido, nombre
        reporte.sort(key=lambda x: (x['apellido'].lower(), x['nombre'].lower()))
        
        return jsonify({
            "status": "success",
            "reporte": reporte,
            "meses": ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        })
    except Exception as e:
        print(f"[ERROR] Error en reportes_pagos_calendario: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reportes/pagos-calendario/excel', methods=['POST'])
def export_pagos_calendario_excel():
    """Exportar reporte de pagos - Excel SIN COLORES - COMO EN LA APP"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json or {}
        solo_regulares = datos.get('solo_regulares', True)
        miembros = db.get_miembros_fresh(estado='Activo')
        
        if solo_regulares:
            miembros = [m for m in miembros if dict(m).get('tipo_asistencia') == 'Regular']
        
        pagos = db.get_pagos()
        
        # Construir reporte
        reporte = []
        for miembro in miembros:
            md = dict(miembro)
            row = {
                'nombre': md.get('nombre', ''),
                'matricula_monto': 0.0,
                'libro': 0.0,
                'meses': {f'{i:02d}': 0.0 for i in range(1, 13)}
            }
            
            for pago in pagos:
                if dict(pago).get('miembro_id') == md.get('id'):
                    pd = dict(pago)
                    monto = float(pd.get('monto', 0))
                    tipo = unicodedata.normalize('NFD', pd.get('tipo_pago', '').lower()).encode('ascii', 'ignore').decode() if pd.get('tipo_pago') else ''
                    
                    if tipo == 'matricula':
                        row['matricula_monto'] += monto
                    elif tipo == 'libro':
                        row['libro'] += monto
                    else:
                        mes_key = f"{int(pd.get('mes', 0)):02d}" if pd.get('mes') else ''
                        if mes_key in row['meses']:
                            row['meses'][mes_key] += monto
            
            reporte.append(row)
        
        # Crear Excel con xlsxwriter
        output = io.BytesIO()
        workbook = Workbook(output)
        worksheet = workbook.add_worksheet("Pagos por Mes")
        
        # Formatos - TODO BLANCO, SIN COLORES
        header_fmt = workbook.add_format({
            'bg_color': '#FFFFFF',
            'font_color': '#000000',
            'bold': True,
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        cell_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        number_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        total_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'left',
            'valign': 'vcenter',
            'bold': True,
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        total_number_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'right',
            'valign': 'vcenter',
            'bold': True,
            'num_format': '#,##0',
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        # Headers - SIN EMOJIS, COMO EN LA APP
        meses = [3, 4, 5, 6, 7, 8, 9, 10, 11]
        meses_nombres = {3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV'}
        
        headers = ['Alumno', 'Matricula'] + [f'{m:02d} {meses_nombres[m]}' for m in meses] + ['Libro', 'TOTAL']
        
        for col, h in enumerate(headers):
            worksheet.write(0, col, h, header_fmt)
        
        # Ancho de columnas
        worksheet.set_column(0, 0, 22)
        worksheet.set_column(1, 1, 13)
        for i in range(2, 12):
            worksheet.set_column(i, i, 11)
        worksheet.set_column(12, 12, 14)
        
        # Datos de alumnos
        totales_mes = {m: 0.0 for m in meses}
        total_mat = 0.0
        total_lib = 0.0
        
        for idx, alumno in enumerate(reporte, 1):
            worksheet.write(idx, 0, alumno['nombre'], cell_fmt)
            
            mat = alumno['matricula_monto']
            worksheet.write_number(idx, 1, mat, number_fmt)
            total_mat += mat
            
            total_row = mat
            for i, m in enumerate(meses):
                col = 2 + i
                monto = alumno['meses'][f'{m:02d}']
                total_row += monto
                totales_mes[m] += monto
                worksheet.write_number(idx, col, monto, number_fmt)
            
            lib = alumno['libro']
            worksheet.write_number(idx, 11, lib, number_fmt)
            total_row += lib
            total_lib += lib
            
            worksheet.write_number(idx, 12, total_row, number_fmt)
        
        # Fila TOTALES al final
        total_row_num = len(reporte) + 1
        worksheet.write(total_row_num, 0, 'TOTALES', total_fmt)
        worksheet.write_number(total_row_num, 1, total_mat, total_number_fmt)
        
        for i, m in enumerate(meses):
            worksheet.write_number(total_row_num, 2 + i, totales_mes[m], total_number_fmt)
        
        worksheet.write_number(total_row_num, 11, total_lib, total_number_fmt)
        total_general = total_mat + sum(totales_mes.values()) + total_lib
        worksheet.write_number(total_row_num, 12, total_general, total_number_fmt)
        
        worksheet.freeze_panes(1, 0)
        workbook.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'Reporte_Pagos_{datetime.now().strftime("%d%m%Y_%H%M%S")}.xlsx'
        )
    except Exception as e:
        print(f"[ERROR] Error exportando: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    """Exportar reporte de pagos por calendario a Excel con openpyxl"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        # Obtener parámetro del request
        datos = request.json or {}
        solo_regulares = datos.get('solo_regulares', True)
        
        # Obtener miembros activos
        miembros = db.get_miembros_fresh(estado='Activo')
        
        # Filtrar solo regulares si se solicita
        if solo_regulares:
            miembros = [m for m in miembros if dict(m).get('tipo_asistencia') == 'Regular']
        
        # Obtener todos los pagos
        pagos = db.get_pagos()
        
        # Crear reporte pivot
        reporte = []
        for miembro in miembros:
            miembro_dict = dict(miembro)
            row = {
                'miembro_id': miembro_dict.get('id'),
                'nombre': miembro_dict.get('nombre', ''),
                'apellido': miembro_dict.get('apellido', ''),
                'matricula_monto': 0.0,
                'libro': 0.0,
                'estado': miembro_dict.get('estado', 'Activo'),
                'meses': {}
            }
            
            # Inicializar 12 meses con 0
            for mes in range(1, 13):
                row['meses'][f'{mes:02d}'] = 0.0
            
            # Llenar con pagos del miembro
            for pago in pagos:
                pago_dict = dict(pago)
                if pago_dict.get('miembro_id') == miembro_dict.get('id'):
                    monto = float(pago_dict.get('monto', 0))
                    tipo_pago = pago_dict.get('tipo_pago', '')
                    
                    tipo_normalized = unicodedata.normalize('NFD', tipo_pago.lower()).encode('ascii', 'ignore').decode() if tipo_pago else ''
                    if tipo_normalized == 'matricula':
                        row['matricula_monto'] += monto
                    elif tipo_normalized == 'libro':
                        row['libro'] += monto
                    else:
                        mes_pago = pago_dict.get('mes', '')
                        if mes_pago:
                            # Asegurar formato '03' no '3'
                            mes_pago_padded = f'{int(mes_pago):02d}' if mes_pago else ''
                            if mes_pago_padded in row['meses']:
                                row['meses'][mes_pago_padded] += monto
            
            reporte.append(row)
        
        # Crear workbook openpyxl
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Pagos por Mes"
        
        # Estilos
        border = Border(
            left=Side(style='thin', color='CCCCCC'),
            right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'),
            bottom=Side(style='thin', color='CCCCCC')
        )
        
        header_fill = PatternFill(start_color='E8E8E8', end_color='E8E8E8', fill_type='solid')
        header_font = Font(name='Calibri', size=10, bold=True, color='333333')
        
        cell_font = Font(name='Calibri', size=10, color='333333')
        
        # Formato de dinero SIN centavos
        dinero_format = '#,##0'
        
        verde_fill = PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid')
        verde_font = Font(name='Calibri', size=10, color='1B5E20', bold=True)
        
        amarillo_fill = PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid')
        amarillo_font = Font(name='Calibri', size=10, color='856404')
        
        azul_fill = PatternFill(start_color='E3F2FD', end_color='E3F2FD', fill_type='solid')
        azul_font = Font(name='Calibri', size=10, color='0D47A1', bold=True)
        
        center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
        right_alignment = Alignment(horizontal='right', vertical='center')
        left_alignment = Alignment(horizontal='left', vertical='center')
        
        # Headers
        meses_mostrar = [3, 4, 5, 6, 7, 8, 9, 10, 11]
        meses_nombres = {
            3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL',
            8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV'
        }
        
        # Escribir headers SIN emojis
        headers = ['Alumno', 'Matricula']
        for mes in meses_mostrar:
            headers.append(f'{mes:02d} {meses_nombres[mes]}')
        headers.extend(['Libro', 'TOTAL'])
        
        for col_num, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = center_alignment
        
        # Anchos de columnas
        worksheet.column_dimensions['A'].width = 22
        worksheet.column_dimensions['B'].width = 13
        for i in range(len(meses_mostrar)):
            col_letter = get_column_letter(3 + i)
            worksheet.column_dimensions[col_letter].width = 11
        worksheet.column_dimensions['L'].width = 11
        worksheet.column_dimensions['M'].width = 14
        
        # Datos
        totales_por_mes = {mes: 0.0 for mes in meses_mostrar}
        total_matriculas = 0.0
        total_libros = 0.0
        
        for idx, alumno in enumerate(reporte, 2):
            # Nombre
            cell = worksheet.cell(row=idx, column=1)
            cell.value = alumno['nombre']
            cell.font = cell_font
            cell.border = border
            cell.alignment = left_alignment
            
            # Matrícula
            matricula = alumno['matricula_monto']
            cell = worksheet.cell(row=idx, column=2)
            cell.value = matricula
            cell.number_format = dinero_format
            cell.border = border
            cell.alignment = right_alignment
            if matricula > 0:
                cell.fill = verde_fill
                cell.font = verde_font
            else:
                cell.font = cell_font
            total_matriculas += matricula
            
            # Meses
            total_alumno = matricula
            for col_idx, mes in enumerate(meses_mostrar, 3):
                mes_key = f'{mes:02d}'
                monto = alumno['meses'].get(mes_key, 0.0)
                total_alumno += monto
                totales_por_mes[mes] += monto
                
                cell = worksheet.cell(row=idx, column=col_idx)
                cell.value = monto if monto > 0 else None
                cell.number_format = dinero_format
                cell.border = border
                cell.alignment = right_alignment
                
                if monto >= 1000:
                    cell.fill = verde_fill
                    cell.font = verde_font
                elif monto > 0:
                    cell.fill = amarillo_fill
                    cell.font = amarillo_font
                else:
                    cell.font = cell_font
            
            # Libro
            libro = alumno['libro']
            cell = worksheet.cell(row=idx, column=12)  # L
            cell.value = libro if libro > 0 else None
            cell.number_format = dinero_format
            cell.border = border
            cell.alignment = right_alignment
            if libro > 0:
                cell.fill = verde_fill
                cell.font = verde_font
            else:
                cell.font = cell_font
            total_alumno += libro
            total_libros += libro
            
            # Total
            cell = worksheet.cell(row=idx, column=13)  # M
            cell.value = total_alumno
            cell.number_format = dinero_format
            cell.fill = azul_fill
            cell.font = azul_font
            cell.border = border
            cell.alignment = right_alignment
        
        # Fila de totales
        total_row = len(reporte) + 2
        cell = worksheet.cell(row=total_row, column=1)
        cell.value = 'TOTALES'
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = center_alignment
        
        cell = worksheet.cell(row=total_row, column=2)
        cell.value = total_matriculas
        cell.number_format = dinero_format
        cell.fill = verde_fill
        cell.font = verde_font
        cell.border = border
        cell.alignment = right_alignment
        
        for col_idx, mes in enumerate(meses_mostrar, 3):
            cell = worksheet.cell(row=total_row, column=col_idx)
            cell.value = totales_por_mes[mes]
            cell.number_format = dinero_format
            cell.fill = verde_fill
            cell.font = verde_font
            cell.border = border
            cell.alignment = right_alignment
        
        cell = worksheet.cell(row=total_row, column=12)
        cell.value = total_libros
        cell.number_format = dinero_format
        cell.fill = verde_fill
        cell.font = verde_font
        cell.border = border
        cell.alignment = right_alignment
        
        total_general = total_matriculas + sum(totales_por_mes.values()) + total_libros
        cell = worksheet.cell(row=total_row, column=13)
        cell.value = total_general
        cell.number_format = dinero_format
        cell.fill = verde_fill
        cell.font = verde_font
        cell.border = border
        cell.alignment = right_alignment
        
        # Congelar primera fila
        worksheet.freeze_panes = 'A2'
        
        # Enviar archivo
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'Reporte_Pagos_{datetime.now().strftime("%d%m%Y_%H%M%S")}.xlsx'
        )
    except Exception as e:
        print(f"[ERROR] Error exportando Excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - LISTADOS PARA REPORTES ==========

@app.route('/api/pagos/todos', methods=['GET'])
def get_todos_pagos():
    """Obtener todos los pagos para el reporte"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        pagos = db.get_pagos()
        pagos_list = []
        
        for p in pagos:
            pago_dict = dict(p)
            # Formato de fecha
            if pago_dict.get('fecha'):
                fecha = pago_dict['fecha']
                if hasattr(fecha, 'isoformat'):
                    pago_dict['fecha'] = fecha.isoformat().split('T')[0]
                else:
                    pago_dict['fecha'] = str(fecha)
            pagos_list.append(pago_dict)
        
        return jsonify({"status": "success", "pagos": pagos_list})
    except Exception as e:
        print(f"[ERROR] Error al obtener pagos: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/asistencia/todos', methods=['GET'])
def get_todos_asistencia():
    """Obtener todos los registros de asistencia"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        asistencias = db.get_asistencia()
        asist_list = []
        
        for a in asistencias:
            asist_dict = dict(a)
            if asist_dict.get('fecha'):
                fecha = asist_dict['fecha']
                if hasattr(fecha, 'isoformat'):
                    asist_dict['fecha'] = fecha.isoformat().split('T')[0]
                else:
                    asist_dict['fecha'] = str(fecha)
            # Convertir asistio a estado
            asist_dict['estado'] = 'Presente' if asist_dict.get('asistio') else 'Ausente'
            asist_list.append(asist_dict)
        
        return jsonify({"status": "success", "asistencias": asist_list})
    except Exception as e:
        print(f"[ERROR] Error al obtener asistencia: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/todos', methods=['GET'])
def get_todos_miembros():
    """Obtener todos los miembros"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        miembros = db.get_miembros()
        miembros_list = [dict(m) for m in miembros]
        return jsonify({"status": "success", "miembros": miembros_list})
    except Exception as e:
        print(f"[ERROR] Error al obtener miembros: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - EXPORTACIÓN ==========

@app.route('/api/export/excel/<tipo>', methods=['GET'])
def export_excel(tipo):
    """Exportar datos a Excel - CLON EXACTO DEL DISEÑO WEB"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Colores y estilos que clonan exactamente el web
        header_bg = '#CCCCCC'
        header_border = '#666666'
        
        header_fmt = workbook.add_format({
            'bg_color': header_bg,
            'border': 2,
            'border_color': header_border,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 11,
            'font_color': '#000',
            'bold': True,
        })
        
        cell_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 10,
            'font_color': '#333',
        })
        
        cell_right_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'right',
            'valign': 'vcenter',
            'font_size': 10,
            'font_color': '#333',
        })
        
        money_fmt = workbook.add_format({
            'border': 1,
            'border_color': '#CCCCCC',
            'align': 'right',
            'valign': 'vcenter',
            'font_size': 10,
            'num_format': '$#,##0',
        })
        
        if tipo == 'miembros':
            worksheet.name = 'Miembros'
            headers = ['Nombre', 'Email', 'Teléfono', 'Estado', 'Tipo']
            
            # Escribir headers
            for col, header in enumerate(headers):
                worksheet.set_column(col, col, 20)
                worksheet.write(0, col, header, header_fmt)
            
            # Ordenar y escribir datos
            miembros = db.get_miembros()
            miembros_list = [dict(m) for m in miembros]
            miembros_list.sort(key=lambda x: (x.get('apellido', '').lower(), x.get('nombre', '').lower()))
            
            for row, m in enumerate(miembros_list, 1):
                nombre = f"{m['apellido']}, {m['nombre']}"
                worksheet.write(row, 0, nombre, cell_fmt)
                worksheet.write(row, 1, m.get('email', '-'), cell_fmt)
                worksheet.write(row, 2, m.get('telefono', '-'), cell_fmt)
                worksheet.write(row, 3, m.get('estado', 'Activo'), cell_fmt)
                worksheet.write(row, 4, m.get('tipo_asistencia', '-'), cell_fmt)
        
        elif tipo == 'pagos':
            worksheet.name = 'Pagos'
            headers = ['Alumno', 'Monto', 'Fecha', 'Tipo', 'Método']
            
            for col, header in enumerate(headers):
                worksheet.set_column(col, col, 20)
                worksheet.write(0, col, header, header_fmt)
            
            pagos = db.get_pagos()
            pagos_list = [dict(p) for p in pagos]
            
            # Ordenar por apellido, nombre
            pagos_list.sort(key=lambda x: (x.get('apellido', '').lower(), x.get('nombre', '').lower()))
            
            meses_nombres = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            for row, p in enumerate(pagos_list, 1):
                nombre = f"{p.get('apellido', '')}, {p.get('nombre', '')}"
                worksheet.write(row, 0, nombre, cell_fmt)
                worksheet.write_number(row, 1, p['monto'], money_fmt)
                
                # Fecha formateada
                fecha = p.get('fecha', '')
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime('%d/%m/%Y')
                worksheet.write(row, 2, fecha, cell_fmt)
                
                # Tipo: si es Cuota, mostrar "Cuota: Mes"
                tipo_display = p.get('tipo_pago', '-')
                if p.get('tipo_pago') == 'Cuota' and p.get('mes_inicio'):
                    mes_inicio = int(p['mes_inicio'])
                    if p.get('mes_fin') and p['mes_fin'] != p['mes_inicio']:
                        mes_fin = int(p['mes_fin'])
                        tipo_display = f"Cuota: {meses_nombres.get(mes_inicio, '')}-{meses_nombres.get(mes_fin, '')}"
                    else:
                        tipo_display = f"Cuota: {meses_nombres.get(mes_inicio, '')}"
                
                worksheet.write(row, 3, tipo_display, cell_fmt)
                worksheet.write(row, 4, p.get('metodo_pago', '-'), cell_fmt)
        
        elif tipo == 'asistencia':
            worksheet.name = 'Asistencia'
            headers = ['Alumno', 'Clase', 'Fecha', 'Estado']
            
            for col, header in enumerate(headers):
                worksheet.set_column(col, col, 20)
                worksheet.write(0, col, header, header_fmt)
            
            asistencias = db.get_asistencia()
            asist_list = [dict(a) for a in asistencias]
            
            # Ordenar por apellido, nombre
            asist_list.sort(key=lambda x: (x.get('apellido', '').lower(), x.get('nombre', '').lower()))
            
            for row, a in enumerate(asist_list, 1):
                nombre = f"{a.get('apellido', '')}, {a.get('nombre', '')}"
                worksheet.write(row, 0, nombre, cell_fmt)
                worksheet.write(row, 1, a.get('clase_nombre', '-'), cell_fmt)
                
                # Fecha formateada
                fecha = a.get('fecha', '')
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime('%d/%m/%Y')
                worksheet.write(row, 2, fecha, cell_fmt)
                
                estado = 'Presente' if a.get('asistio') else 'Ausente'
                worksheet.write(row, 3, estado, cell_fmt)
        
        workbook.close()
        output.seek(0)
        
        filename = f"{tipo}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"[ERROR] Error exportando Excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    """Manejar rutas no encontradas"""
    return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404

@app.errorhandler(500)
def server_error(error):
    """Manejar errores del servidor"""
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

# ========== INICIAR SERVIDOR ==========

if __name__ == '__main__':
    print("=" * 70)
    print("  Instituto Jorge Müller - Sistema de Gestión")
    print("  PostgreSQL (Neon)")
    print("=" * 70)
    
    puerto = 5000
    
    if db:
        print(f"\n✅ Base de datos conectada")
    else:
        print(f"\n⚠️  Base de datos NO disponible - Modo testing (solo autenticación)")
    
    print(f"✅ Servidor iniciado en: http://localhost:{puerto}")
    print(f"   Google OAuth: {'✓' if GOOGLE_CLIENT_ID else '❌'}")
    print(f"\n📌 Para cerrar: Ctrl+C o cerrar esta ventana")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=puerto, debug=True)
