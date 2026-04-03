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
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Cargar variables de entorno
load_dotenv()

# Importar módulo de base de datos
from database import Database, DatabaseError

# Importar autenticación OAuth
from auth import GoogleOAuth, login_required, GOOGLE_CLIENT_ID, ADMIN_EMAILS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.permanent_session_lifetime = timedelta(days=7)

# Inicializar base de datos
try:
    db = Database()
    print("✓ Conexión a base de datos establecida")
except DatabaseError as e:
    print(f"❌ Error de conexión: {e}")
    db = None

# ========== CONFIGURACIÓN TABS ==========
TABS = {
    0: {"id": "tab_0", "label": "Inicio", "icon": "🏠", "route": "dashboard"},
    1: {"id": "tab_1", "label": "Asistencia", "icon": "✅", "route": "asistencia"},
    2: {"id": "tab_2", "label": "Pagos", "icon": "💰", "route": "pagos"},
    3: {"id": "tab_3", "label": "Miembros", "icon": "👥", "route": "miembros"},
    4: {"id": "tab_4", "label": "Clases", "icon": "📚", "route": "clases"},
    5: {"id": "tab_5", "label": "Reportes", "icon": "📊", "route": "reportes"},
    6: {"id": "tab_6", "label": "Retiros", "icon": "💸", "route": "retiros"}
}

# ========== FUNCIONES AUXILIARES ==========

def check_db():
    """Verificar que la base de datos está disponible"""
    if not db:
        return None, {"status": "error", "message": "Conexión a base de datos no disponible"}, 503
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
        
        # Actualizar última conexión en base de datos
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
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        # Obtener usuario actual
        current_user = GoogleOAuth.get_session_user()
        
        # Obtener estadísticas de la base de datos
        miembros = db.get_miembros()
        miembros_regulares = db.get_miembros(tipo_asistencia='Regular')
        
        # Obtener pagos este mes
        start_date = date(date.today().year, date.today().month, 1)
        if date.today().month == 12:
            end_date = date(date.today().year + 1, 1, 1)
        else:
            end_date = date(date.today().year, date.today().month + 1, 1)
        
        pagos_mes = db.get_resumen_pagos(start_date, end_date)
        total_pagos = sum(float(p['total_pagos'] or 0) for p in pagos_mes)
        
        # Obtener clases de hoy
        clases_hoy = get_clase_hoy()
        
        return render_template('tab_0_dashboard.html',
                             tabs=TABS,
                             active_tab=0,
                             current_user=current_user,
                             stats={
                                 'miembros': len(miembros),
                                 'miembros_regulares': len(miembros_regulares),
                                 'clases': 0,  # Se puede obtener de otro lugar
                                 'pagos': total_pagos
                             },
                             clases_hoy=clases_hoy)
    
    except DatabaseError as e:
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
    db_check, error, code = check_db()
    if error:
        return error, code
    
    if tab_id not in TABS:
        return "Tab no encontrado", 404
    
    try:
        current_user = GoogleOAuth.get_session_user()
        tab_info = TABS[tab_id]
        template = f"tab_{tab_id}_{tab_info['route']}.html"
        
        # Cargar datos según el tab desde base de datos
        data = {}
        
        if tab_id == 1:  # Asistencia
            data['miembros'] = db.get_miembros()
            # Para clases, podríamos tener un endpoint para obtener todas las clases
            data['clases'] = []
            data['asistencia'] = db.get_asistencia_fecha(date.today())
            data['clases_hoy'] = get_clase_hoy()
        
        elif tab_id == 2:  # Pagos
            data['miembros'] = db.get_miembros(tipo_asistencia='Regular')
            # Se cargarán pagos vía API en el frontend
            data['pagos'] = []
        
        elif tab_id == 3:  # Miembros
            data['miembros'] = db.get_miembros()
        
        elif tab_id == 4:  # Clases
            data['clases'] = []
            data['oradores'] = []
        
        elif tab_id == 5:  # Reportes
            data['miembros'] = db.get_miembros(tipo_asistencia='Regular')
            data['reporte_pagos'] = db.get_reporte_pagos_por_mes()
            data['asistencia'] = []
            data['pagos'] = []
        
        elif tab_id == 6:  # Retiros
            data['retiros'] = []
        
        return render_template(template,
                             tabs=TABS,
                             active_tab=tab_id,
                             current_user=current_user,
                             **data)
    
    except DatabaseError as e:
        print(f"Error al cargar tab {tab_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - ASISTENCIA ==========

@app.route('/api/asistencia/save', methods=['POST'])
def save_asistencia():
    """Guardar asistencia en la base de datos"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        
        miembro_id = datos.get('id_miembro')
        fecha = datos.get('fecha', str(date.today()))
        asistio = datos.get('asistio', True)
        
        # La clase_id se obtendría de la clase para esa fecha
        # Por ahora usamos 1 como placeholder (deberías expandir esto)
        clase_id = datos.get('clase_id', 1)
        
        # Guardar en base de datos
        db.add_asistencia(miembro_id, clase_id, fecha, asistio)
        
        return jsonify({"status": "success", "message": "Asistencia guardada correctamente"})
    
    except DatabaseError as e:
        print(f"Error al guardar asistencia: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/asistencia/por-fecha/<fecha>', methods=['GET'])
def get_asistencia_fecha(fecha):
    """Obtener asistencia para una fecha específica"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        asistencia = db.get_asistencia_fecha(fecha)
        return jsonify({"status": "success", "asistencia": [dict(a) for a in asistencia]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== API ENDPOINTS - CLASES ==========

@app.route('/api/clases/por-fecha/<fecha>', methods=['GET'])
def get_clase_por_fecha(fecha):
    """Obtener clase para una fecha específica"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        clase = db.get_clase(1)  # Implementar búsqueda por fecha
        if clase:
            return jsonify({"status": "success", "clase": dict(clase)})
        else:
            return jsonify({"status": "success", "clase": None})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clases/hoy', methods=['GET'])
def get_clases_hoy_api():
    """Obtener clases de hoy (última, hoy, próxima)"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        clases = get_clase_hoy()
        return jsonify({"status": "success", "clases": [dict(c) for c in clases]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clases/update', methods=['POST'])
def update_clase():
    """Actualizar estado de una clase"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        clase_id = datos.get('id')
        nuevo_estado = datos.get('estado')
        
        db.update_clase_estado(clase_id, nuevo_estado)
        
        return jsonify({"status": "success", "message": "Clase actualizada correctamente"})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
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
        
        miembro_id = datos.get('id_miembro')
        monto = float(datos.get('monto', 0))
        fecha = datos.get('fecha', str(date.today()))
        mes = datos.get('mes', '')
        descripcion = datos.get('descripcion', '')
        metodo_pago = datos.get('metodo_pago', 'Efectivo')
        
        pago_id = db.add_pago(miembro_id, monto, fecha, mes, descripcion, metodo_pago)
        
        return jsonify({"status": "success", "message": "Pago registrado correctamente", "id": pago_id})
    
    except DatabaseError as e:
        print(f"Error al guardar pago: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/miembro/<int:miembro_id>', methods=['GET'])
def get_pagos_miembro(miembro_id):
    """Obtener pagos de un miembro"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        pagos = db.get_pagos_miembro(miembro_id)
        return jsonify({"status": "success", "pagos": [dict(p) for p in pagos]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/delete/<int:pago_id>', methods=['DELETE'])
def delete_pago(pago_id):
    """Eliminar un pago"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        db.delete_pago(pago_id)
        return jsonify({"status": "success", "message": "Pago eliminado correctamente"})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/update/<int:pago_id>', methods=['POST'])
def update_pago(pago_id):
    """Actualizar un pago"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        datos = request.json
        
        monto = float(datos.get('monto'))
        fecha = datos.get('fecha', str(date.today()))
        mes = datos.get('mes', '')
        descripcion = datos.get('descripcion', '')
        metodo_pago = datos.get('metodo_pago', 'Efectivo')
        
        db.update_pago(pago_id, monto, fecha, mes, descripcion, metodo_pago)
        
        return jsonify({"status": "success", "message": "Pago actualizado correctamente"})
    except DatabaseError as e:
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
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
        
        miembro_id = datos.get('id_miembro')
        monto = float(datos.get('monto', 0))
        fecha = datos.get('fecha', str(date.today()))
        razon = datos.get('razon', '')
        tipo_retiro = datos.get('tipo_retiro', 'Reembolso')
        
        retiro_id = db.add_retiro(miembro_id, monto, fecha, razon, tipo_retiro)
        
        return jsonify({"status": "success", "message": "Retiro registrado correctamente", "id": retiro_id})
    
    except DatabaseError as e:
        print(f"Error al guardar retiro: {e}")
        return jsonify({"status": "error", "message": f"Error de conexión: {str(e)}"}), 500
    except Exception as e:
        print(f"Error: {e}")
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
def get_all_miembros():
    """Obtener todos los miembros"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        miembros = db.get_miembros()
        return jsonify({"status": "success", "miembros": [dict(m) for m in miembros]})
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
        
        return jsonify({"status": "success", "message": "Miembro actualizado correctamente"})
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

# ========== API ENDPOINTS - EXPORTACIÓN ==========

@app.route('/api/export/excel/<tipo>', methods=['GET'])
def export_excel(tipo):
    """Exportar datos a Excel desde base de datos"""
    db_check, error, code = check_db()
    if error:
        return error, code
    
    try:
        wb = Workbook()
        ws = wb.active
        
        # Estilos
        header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        if tipo == 'miembros':
            ws.title = "Miembros"
            headers = ['ID', 'Nombre', 'Apellido', 'Email', 'Teléfono', 'Tipo', 'Matricula']
            ws.append(headers)
            
            miembros = db.get_miembros()
            for m in miembros:
                ws.append([
                    m['id'], m['nombre'], m['apellido'],
                    m.get('email', ''), m.get('telefono', ''),
                    m['tipo_asistencia'], m.get('matricula', '')
                ])
        
        elif tipo == 'pagos':
            ws.title = "Pagos"
            headers = ['ID', 'Miembro', 'Monto', 'Fecha', 'Mes', 'Método']
            ws.append(headers)
            
            reporte = db.get_reporte_pagos_por_mes()
            for r in reporte:
                ws.append([
                    r['miembro_id'], f"{r['nombre']} {r['apellido']}",
                    r.get('monto_total', 0), date.today(),
                    'Múltiples', 'Varios'
                ])
        
        elif tipo == 'asistencia':
            ws.title = "Asistencia"
            headers = ['Miembro', 'Clases', 'Asistidas', 'No Asistidas', 'Porcentaje']
            ws.append(headers)
            
            fecha_inicio = request.args.get('inicio', '2025-03-01')
            fecha_fin = request.args.get('fin', str(date.today()))
            reporte = db.get_reporte_asistencia(fecha_inicio, fecha_fin)
            
            for r in reporte:
                ws.append([
                    f"{r['nombre']} {r['apellido']}",
                    r['total_clases'],
                    r['clases_asistidas'],
                    r['clases_no_asistidas'],
                    f"{r.get('porcentaje_asistencia', 0)}%"
                ])
        
        # Aplicar estilos
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Ajustar anchos
        for column in ws.columns:
            max_length = 0
            column = list(column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column[0].column_letter].width = adjusted_width
        
        # Guardar en memoria
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Error al exportar: {e}")
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
    
    if not db:
        print("\n❌ ERROR: No hay conexión a la base de datos")
        print("   Verificar archivo .env con DATABASE_URL")
        print("   O ejecutar: python deploy_schema.py")
    else:
        puerto = 5000
        print(f"\n✅ Base de datos conectada")
        print(f"✅ Servidor iniciado en: http://localhost:{puerto}")
        print(f"\n📌 Para cerrar: Ctrl+C o cerrar esta ventana")
        print("=" * 70 + "\n")
        
        app.run(host='0.0.0.0', port=puerto, debug=False)
