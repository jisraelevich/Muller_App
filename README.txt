========================================
INSTITUTO JORGE MÜLLER - SISTEMA DE GESTIÓN
Salta, Argentina
========================================

DESCRIPCIÓN:
Sistema web local para gestión de asistencia, pagos, exámenes y reportes
del Instituto Bíblico Jorge Müller.

CARACTERÍSTICAS:
✅ Gestión de asistencia con pantalla táctil
✅ Registro de pagos con teclado numérico
✅ Control de exámenes por tema
✅ Exportación a Excel de todos los datos
✅ Interfaz optimizada para PC táctil
✅ Todos los datos guardados en JSON (sin base de datos)

========================================
INSTALACIÓN (PRIMERA VEZ)
========================================

1. INSTALAR PYTHON
   - Descargar desde: https://www.python.org/downloads/
   - Versión recomendada: Python 3.10 o superior
   - ⚠️ IMPORTANTE: Durante la instalación marcar:
     "Add Python to PATH"

2. VERIFICAR INSTALACIÓN
   - Abrir "Símbolo del sistema" (CMD)
   - Escribir: python --version
   - Debe mostrar: Python 3.x.x

========================================
USO DIARIO
========================================

1. INICIAR APLICACIÓN
   - Doble click en "iniciar.bat"
   - Esperar que se abra el navegador automáticamente
   - La primera vez instalará dependencias (1-2 minutos)

2. USAR LA APLICACIÓN
   - Navegar por los botones grandes
   - Marcar asistencia, registrar pagos, cargar exámenes
   - Todo se guarda automáticamente en la carpeta "data/"

3. CERRAR APLICACIÓN
   - Cerrar la ventana negra (consola)
   - O presionar Ctrl+C en la consola

========================================
ESTRUCTURA DE ARCHIVOS
========================================

Muller_App/
│
├── iniciar.bat          ← DOBLE CLICK AQUÍ PARA INICIAR
├── app.py               (Servidor Python)
├── requirements.txt     (Dependencias)
│
├── data/                ← TODOS LOS DATOS AQUÍ (JSON)
│   ├── miembros.json
│   ├── clases.json
│   ├── asistencia.json
│   ├── pagos.json
│   ├── examenes.json
│   └── config.json
│
├── static/
│   ├── css/
│   │   └── styles.css   ← TODO EL DISEÑO
│   └── js/
│       └── app.js       ← TODA LA LÓGICA
│
└── templates/           (Páginas HTML)
    ├── base.html
    ├── tab_0_dashboard.html
    ├── tab_1_asistencia.html
    ├── tab_2_pagos.html
    ├── tab_3_examenes.html
    ├── tab_4_miembros.html
    ├── tab_5_clases.html
    └── tab_6_reportes.html

========================================
BACKUP Y SEGURIDAD
========================================

HACER BACKUP:
- Copiar toda la carpeta "data/" a otra ubicación
- O usar exportaciones Excel desde la sección Reportes

RESTAURAR BACKUP:
- Reemplazar la carpeta "data/" con la copia guardada

DATOS IMPORTANTES:
- Los datos están en archivos JSON (texto plano)
- Se pueden abrir con Notepad si es necesario
- NO borrar los archivos JSON, siempre hacer copia primero

========================================
PERSONALIZACIÓN
========================================

CAMBIAR COLORES:
- Editar: static/css/styles.css
- Buscar la sección ":root" con las variables
- Modificar los valores hexadecimales

CAMBIAR TEXTOS:
- Editar los archivos .html en templates/

AGREGAR FUNCIONALIDADES:
- Modificar app.py (Python)
- Modificar static/js/app.js (JavaScript)

========================================
SOLUCIÓN DE PROBLEMAS
========================================

PROBLEMA: "Python no está instalado"
SOLUCIÓN: Instalar Python y marcar "Add to PATH"

PROBLEMA: El navegador no se abre
SOLUCIÓN: Abrir manualmente http://localhost:5000

PROBLEMA: Error "Puerto 5000 en uso"
SOLUCIÓN: 
- Cerrar otras aplicaciones que usen ese puerto
- O editar config.json y cambiar "puerto": 5001

PROBLEMA: No se guardan los datos
SOLUCIÓN:
- Verificar permisos de escritura en carpeta "data/"
- Revisar que los archivos JSON no estén abiertos

========================================
EXPORTAR A EXCEL
========================================

- Ir a "Reportes" en el menú principal
- Click en el tipo de datos a exportar
- El archivo se descarga automáticamente
- Ubicación: Carpeta "Descargas" de Windows

========================================
SOPORTE TÉCNICO
========================================

Para modificaciones o problemas:
- Revisar este archivo README
- Verificar que Python esté correctamente instalado
- Comprobar que todos los archivos estén presentes

========================================
VERSIÓN: 1.0
FECHA: Marzo 2026
========================================
