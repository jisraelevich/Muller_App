#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instituto Jorge Müller - Sistema de Gestión
Servidor Flask para aplicación web local
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
import os
from datetime import datetime
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

DATA_DIR = 'data'

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

def load_json(filename):
    """Cargar archivo JSON desde data/"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_json(filename, data):
    """Guardar datos en archivo JSON"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_clase_hoy():
    """Obtener la clase de hoy o la próxima"""
    clases = load_json('clases.json')
    hoy = datetime.now().strftime('%Y-%m-%d')
    
    # Buscar clase de hoy
    for clase in clases:
        if clase.get('fecha') == hoy:
            return clase
    
    # Si no hay clase hoy, buscar la próxima
    for clase in clases:
        if clase.get('estado') == 'Programada':
            return clase
    
    return None

# ========== RUTAS PRINCIPALES ==========

@app.route('/')
def index():
    """Dashboard principal"""
    config = load_json('config.json')
    miembros = load_json('miembros.json')
    clases = load_json('clases.json')
    pagos = load_json('pagos.json')
    
    # Estadísticas
    total_miembros = len(miembros)
    total_clases = len(clases)
    total_pagos = sum(p.get('monto', 0) for p in pagos)
    
    clase_hoy = get_clase_hoy()
    
    return render_template('tab_0_dashboard.html',
                         config=config,
                         tabs=TABS,
                         active_tab=0,
                         stats={
                             'miembros': total_miembros,
                             'clases': total_clases,
                             'pagos': total_pagos
                         },
                         clase_hoy=clase_hoy)

@app.route('/tab/<int:tab_id>')
def render_tab(tab_id):
    """Renderizar tab específico"""
    if tab_id not in TABS:
        return "Tab no encontrado", 404
    
    config = load_json('config.json')
    tab_info = TABS[tab_id]
    template = f"tab_{tab_id}_{tab_info['route']}.html"
    
    # Cargar datos según el tab
    data = {}
    if tab_id == 1:  # Asistencia
        data['miembros'] = load_json('miembros.json')
        data['clases'] = load_json('clases.json')
        data['asistencia'] = load_json('asistencia.json')
        data['clase_hoy'] = get_clase_hoy()
    elif tab_id == 2:  # Pagos
        data['miembros'] = load_json('miembros.json')
        data['pagos'] = load_json('pagos.json')
    elif tab_id == 3:  # Miembros
        data['miembros'] = load_json('miembros.json')
    elif tab_id == 4:  # Clases
        data['clases'] = load_json('clases.json')
        data['oradores'] = load_json('oradores.json')
    elif tab_id == 5:  # Reportes
        data['miembros'] = load_json('miembros.json')
        data['asistencia'] = load_json('asistencia.json')
        data['pagos'] = load_json('pagos.json')
    elif tab_id == 6:  # Retiros
        data['retiros'] = load_json('retiros.json')
    
    return render_template(template,
                         config=config,
                         tabs=TABS,
                         active_tab=tab_id,
                         **data)

# ========== API ENDPOINTS ==========

@app.route('/api/asistencia/save', methods=['POST'])
def save_asistencia():
    """Guardar asistencia"""
    try:
        datos = request.json
        asistencia_actual = load_json('asistencia.json')
        
        # Agregar timestamp
        datos['fecha_registro'] = datetime.now().isoformat()
        
        # Agregar o actualizar
        asistencia_actual.append(datos)
        save_json('asistencia.json', asistencia_actual)
        
        return jsonify({"status": "success", "message": "Asistencia guardada correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clases/por-fecha/<fecha>', methods=['GET'])
def get_clases_por_fecha(fecha):
    """Obtener clase para una fecha específica"""
    try:
        clases = load_json('clases.json')
        clases_fecha = [c for c in clases if c.get('fecha') == fecha]
        
        if clases_fecha:
            return jsonify({"status": "success", "clase": clases_fecha[0]})
        else:
            return jsonify({"status": "success", "clase": None})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clases/todas', methods=['GET'])
def get_todas_clases():
    """Obtener todas las clases ordenadas por fecha"""
    try:
        clases = load_json('clases.json')
        # Ordenar por fecha (intentar parsear como YYYY-MM-DD primero, si falla usar como string)
        clases_ordenadas = sorted(clases, key=lambda c: c.get('fecha', ''))
        return jsonify({"status": "success", "clases": clases_ordenadas})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clases/update', methods=['POST'])
def update_clase():
    """Actualizar clase"""
    try:
        datos = request.json
        clase_id = datos.get('id')
        
        clases = load_json('clases.json')
        
        # Encontrar y actualizar la clase
        for clase in clases:
            if clase.get('id') == clase_id:
                if 'modalidad' in datos:
                    clase['modalidad'] = datos['modalidad']
                if 'estado' in datos:
                    clase['estado'] = datos['estado']
                break
        
        save_json('clases.json', clases)
        return jsonify({"status": "success", "message": "Clase actualizada correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pagos/save', methods=['POST'])
def save_pago():
    """Guardar pago"""
    try:
        datos = request.json
        pagos = load_json('pagos.json')
        
        # Agregar ID y timestamp
        nuevo_id = max([p.get('id', 0) for p in pagos], default=0) + 1
        datos['id'] = nuevo_id
        datos['fecha_registro'] = datetime.now().isoformat()
        
        pagos.append(datos)
        save_json('pagos.json', pagos)
        
        return jsonify({"status": "success", "message": "Pago registrado correctamente", "id": nuevo_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/retiros/save', methods=['POST'])
def save_retiro():
    """Guardar retiro"""
    try:
        datos = request.json
        retiros = load_json('retiros.json')
        
        # Agregar ID y timestamp
        nuevo_id = max([r.get('id', 0) for r in retiros], default=0) + 1
        datos['id'] = nuevo_id
        datos['fecha_registro'] = datetime.now().isoformat()
        
        retiros.append(datos)
        save_json('retiros.json', retiros)
        
        return jsonify({"status": "success", "message": "Retiro registrado correctamente", "id": nuevo_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/export/excel/<tipo>')
def export_excel(tipo):
    """Exportar datos a Excel"""
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
            headers = ['ID', 'Apellido', 'Nombre', 'Teléfono', 'Email', 'Congregación', 
                      'Localidad', 'Provincia', 'Tipo', 'Participa Exámenes']
            ws.append(headers)
            
            miembros = load_json('miembros.json')
            for m in miembros:
                ws.append([
                    m.get('id'), m.get('apellido'), m.get('nombre'),
                    m.get('telefono'), m.get('email'), m.get('congregacion'),
                    m.get('localidad'), m.get('provincia'),
                    m.get('tipo_asistencia'), m.get('participa_examenes')
                ])
        
        elif tipo == 'asistencia':
            ws.title = "Asistencia"
            headers = ['Fecha Clase', 'ID Miembro', 'Nombre Completo', 'Presente', 'Modalidad']
            ws.append(headers)
            
            asistencia = load_json('asistencia.json')
            for a in asistencia:
                ws.append([
                    a.get('fecha_clase'), a.get('id_miembro'),
                    a.get('nombre_completo'), a.get('presente'),
                    a.get('modalidad')
                ])
        
        elif tipo == 'pagos':
            ws.title = "Pagos"
            headers = ['ID', 'Fecha', 'ID Miembro', 'Nombre Completo', 'Monto', 'Concepto']
            ws.append(headers)
            
            pagos = load_json('pagos.json')
            for p in pagos:
                ws.append([
                    p.get('id'), p.get('fecha'), p.get('id_miembro'),
                    p.get('nombre_completo'), p.get('monto'), p.get('concepto')
                ])
        
        # Aplicar estilos a headers
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
                        max_length = len(cell.value)
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
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/miembros/update', methods=['POST'])
def update_miembro():
    """Actualizar datos de un miembro"""
    try:
        datos = request.json
        id_miembro = datos.get('id_miembro')
        tipo_asistencia = datos.get('tipo_asistencia')
        
        miembros = load_json('miembros.json')
        
        # Buscar y actualizar miembro
        for miembro in miembros:
            if miembro.get('id') == id_miembro:
                miembro['tipo_asistencia'] = tipo_asistencia
                break
        
        save_json('miembros.json', miembros)
        
        return jsonify({"status": "success", "message": "Miembro actualizado correctamente"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== INICIAR SERVIDOR ==========

if __name__ == '__main__':
    config = load_json('config.json')
    puerto = config.get('puerto', 5000)
    
    print("=" * 50)
    print(f"  {config.get('instituto', 'Instituto')}")
    print(f"  {config.get('ciudad', 'Salta')}")
    print("=" * 50)
    print(f"\n✅ Servidor iniciado en: http://localhost:{puerto}")
    print("\n📌 Para cerrar: Ctrl+C o cerrar esta ventana")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=puerto, debug=False)
