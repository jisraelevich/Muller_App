/* ========================================
   INSTITUTO JORGE MÜLLER - JAVASCRIPT GLOBAL
   Archivo JS centralizado - Toda la lógica aquí
   ======================================== */

// ========== CONFIGURACIÓN GLOBAL ==========
const APP_CONFIG = {
    apiBase: '/api',
    tabs: {
        0: 'dashboard',
        1: 'asistencia',
        2: 'pagos',
        3: 'examenes',
        4: 'miembros',
        5: 'clases',
        6: 'reportes'
    }
};

// ========== UTILIDADES ==========

/**
 * Realizar petición fetch con manejo de errores
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error en fetchAPI:', error);
        mostrarAlerta('Error de conexión. Por favor intente nuevamente.', 'error');
        throw error;
    }
}

/**
 * Mostrar alerta en pantalla
 */
function mostrarAlerta(mensaje, tipo = 'info') {
    const alertContainer = document.getElementById('alert-container') || crearAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo}`;
    alertDiv.innerHTML = `
        <span style="font-size: 24px;">${getTipoIcon(tipo)}</span>
        <span>${mensaje}</span>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-ocultar después de 4 segundos
    setTimeout(() => {
        alertDiv.style.transition = 'opacity 0.3s ease';
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 4000);
}

function crearAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '100px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '500px';
    document.body.appendChild(container);
    return container;
}

function getTipoIcon(tipo) {
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    return icons[tipo] || 'ℹ️';
}

/**
 * Formatear fecha
 */
function formatearFecha(fecha) {
    if (!fecha) return '';
    const d = new Date(fecha);
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const anio = d.getFullYear();
    return `${dia}/${mes}/${anio}`;
}

/**
 * Formatear moneda
 */
function formatearMoneda(monto) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(monto);
}

// ========== NAVEGACIÓN ==========

/**
 * Navegar a un tab específico
 */
function navigateToTab(tabId) {
    window.location.href = `/tab/${tabId}`;
}

/**
 * Volver al inicio
 */
function volverInicio() {
    window.location.href = '/';
}

// ========== MÓDULO: ASISTENCIA ==========

const AsistenciaModule = {
    asistenciaActual: {},
    claseSeleccionada: null,
    clasesDisponibles: [],
    miembros: [],
    
    /**
     * Inicializar módulo de asistencia
     */
    init() {
        console.log('AsistenciaModule iniciado');
        this.asistenciaActual = {};
        this.claseSeleccionada = null;
        this.miembros = window.MIEMBROS_DATA || [];
        
        // Cargar clases disponibles
        this.cargarClasesDisponibles();
    },
    
    /**
     * Cargar todas las clases disponibles y llenar selector
     */
    async cargarClasesDisponibles() {
        try {
            const response = await fetchAPI(`${APP_CONFIG.apiBase}/clases/todas`);
            
            if (response.status === 'success' && response.clases) {
                this.clasesDisponibles = response.clases;
                
                // Llenar selector
                const selector = document.getElementById('selector-clase');
                if (selector) {
                    selector.innerHTML = '<option value="">-- Seleccionar Clase --</option>';
                    
                    response.clases.forEach(clase => {
                        const opcion = document.createElement('option');
                        opcion.value = clase.id;
                        opcion.textContent = `${clase.fecha} - ${clase.tema} (${clase.orador})`;
                        selector.appendChild(opcion);
                    });
                    
                    // Preseleccionar la siguiente clase programada
                    const siguienteClase = this.obtenerSiguienteClaseProgramada();
                    if (siguienteClase) {
                        selector.value = siguienteClase.id;
                        this.cargarClaseSeleccionada(siguienteClase.id);
                    }
                }
            }
        } catch (error) {
            console.error('Error cargando clases:', error);
        }
    },
    
    /**
     * Obtener la siguiente clase programada por fecha
     */
    obtenerSiguienteClaseProgramada() {
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        
        let proximaClase = null;
        let proximaFecha = null;
        
        this.clasesDisponibles.forEach(clase => {
            // Parsear fecha YYYY-MM-DD
            const partes = clase.fecha.split('-');
            const fechaClase = new Date(partes[0], partes[1] - 1, partes[2]);
            fechaClase.setHours(0, 0, 0, 0);
            
            // Buscar la próxima fecha
            if (fechaClase >= hoy && clase.estado !== 'Realizada') {
                if (!proximaFecha || fechaClase < proximaFecha) {
                    proximaFecha = fechaClase;
                    proximaClase = clase;
                }
            }
        });
        
        return proximaClase;
    },
    
    /**
     * Cargar clase seleccionada del selector
     */
    async cargarClaseSeleccionada(claseId) {
        if (!claseId) {
            document.getElementById('clase-info-container').style.display = 'none';
            document.getElementById('sin-clase-container').style.display = 'block';
            return;
        }
        
        const clase = this.clasesDisponibles.find(c => c.id == claseId);
        if (clase) {
            this.claseSeleccionada = clase;
            this.asistenciaActual = {};
            this.actualizarContador();
            
            // Actualizar información de la clase
            document.getElementById('clase-titulo').textContent = clase.tema || '-';
            
            // Generar cards de alumnos dinámicamente
            this.generarCardsAlumnos();
            
            // Mostrar contenedor
            document.getElementById('clase-info-container').style.display = 'block';
            document.getElementById('sin-clase-container').style.display = 'none';
        }
    },
    
    /**
     * Generar dinámicamente las cards de alumnos
     */
    generarCardsAlumnos() {
        const contenedor = document.getElementById('contenedor-alumnos');
        if (!contenedor) return;
        
        contenedor.innerHTML = '';
        
        this.miembros.forEach(miembro => {
            const card = document.createElement('div');
            card.className = 'item-card-asistencia';
            card.setAttribute('data-nombre', `${miembro.apellido}, ${miembro.nombre}`);
            
            const html = `
                <div style="text-align: center;">
                    <div style="font-size: 12px; font-weight: bold; color: #1f2937; margin-bottom: 4px;">
                        ${miembro.apellido}<br>${miembro.nombre}
                    </div>
                    <div style="font-size: 10px; color: #6b7280; margin-bottom: 6px;">
                        ${miembro.tipo_asistencia}
                    </div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button id="ausente-${miembro.id}" 
                            class="btn-action-small btn-ausente"
                            onclick="AsistenciaModule.toggleAsistencia(${miembro.id}, '${miembro.apellido}, ${miembro.nombre}')"
                            style="flex: 1; font-size: 10px; min-height: 32px;">
                        ✗
                    </button>
                    <button id="presente-${miembro.id}" 
                            class="btn-action-small btn-secondary"
                            onclick="AsistenciaModule.toggleAsistencia(${miembro.id}, '${miembro.apellido}, ${miembro.nombre}')"
                            style="flex: 1; font-size: 10px; min-height: 32px;">
                        ✓
                    </button>
                </div>
            `;
            
            card.innerHTML = html;
            contenedor.appendChild(card);
        });
    },
    
    /**
     * Cargar clases para una fecha especifica (DEPRECATED - mantener para compatibilidad)
     */
    async cargarClasesPorFecha(fecha) {
        // Esta función se mantiene por compatibilidad pero ya no se usa
        const clase = this.clasesDisponibles.find(c => c.fecha === fecha);
        if (clase) {
            this.cargarClaseSeleccionada(clase.id);
        } else {
            document.getElementById('clase-info-container').style.display = 'none';
            document.getElementById('sin-clase-container').style.display = 'block';
        }
    },
    
    /**
     * Marcar/desmarcar asistencia
     */
    toggleAsistencia(idMiembro, nombreCompleto) {
        const btnPresente = document.getElementById(`presente-${idMiembro}`);
        const btnAusente = document.getElementById(`ausente-${idMiembro}`);
        
        if (this.asistenciaActual[idMiembro]) {
            // Marcar como ausente
            delete this.asistenciaActual[idMiembro];
            btnPresente.classList.remove('btn-success');
            btnPresente.classList.add('btn-secondary');
            btnAusente.classList.remove('btn-secondary');
            btnAusente.classList.add('btn-ausente');
        } else {
            // Marcar como presente
            this.asistenciaActual[idMiembro] = {
                id_miembro: idMiembro,
                nombre_completo: nombreCompleto,
                presente: true
            };
            btnPresente.classList.remove('btn-secondary');
            btnPresente.classList.add('btn-success');
            btnAusente.classList.remove('btn-ausente');
            btnAusente.classList.add('btn-secondary');
        }
        
        this.actualizarContador();
    },
    
    /**
     * Actualizar contador de presentes
     */
    actualizarContador() {
        const contador = document.getElementById('contador-presentes');
        if (contador) {
            const presentes = Object.keys(this.asistenciaActual).length;
            contador.textContent = presentes;
        }
    },
    
    /**
     * Guardar asistencia (versión antigua - mantener para compatibilidad)
     */
    async guardar(fechaClase, idClase) {
        return this.guardarConFecha();
    },
    
    /**
     * Guardar asistencia con fecha seleccionada
     */
    async guardarConFecha() {
        if (!this.claseSeleccionada) {
            mostrarAlerta('Debe seleccionar una clase', 'warning');
            return;
        }
        
        if (Object.keys(this.asistenciaActual).length === 0) {
            mostrarAlerta('No hay asistencia registrada', 'warning');
            return;
        }
        
        const btnGuardar = document.getElementById('btn-guardar-asistencia');
        if (btnGuardar) {
            btnGuardar.disabled = true;
            btnGuardar.textContent = 'Guardando...';
        }
        
        try {
            const datos = {
                fecha_clase: this.claseSeleccionada.fecha,
                id_clase: this.claseSeleccionada.id,
                asistencias: Object.values(this.asistenciaActual)
            };
            
            const response = await fetchAPI(`${APP_CONFIG.apiBase}/asistencia/save`, {
                method: 'POST',
                body: JSON.stringify(datos)
            });
            
            if (response.status === 'success') {
                mostrarAlerta('✅ Asistencia guardada correctamente', 'success');
                setTimeout(() => {
                    volverInicio();
                }, 2000);
            }
        } catch (error) {
            console.error('Error guardando asistencia:', error);
            if (btnGuardar) {
                btnGuardar.disabled = false;
                btnGuardar.textContent = '✅ GUARDAR ASISTENCIA';
            }
        }
    },
    
    /**
     * Filtrar lista por búsqueda
     */
    filtrar(termino) {
        const items = document.querySelectorAll('.item-card-asistencia');
        const terminoLower = termino.toLowerCase();
        
        items.forEach(item => {
            const nombre = item.getAttribute('data-nombre').toLowerCase();
            if (nombre.includes(terminoLower)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
};

// ========== MÓDULO: PAGOS ==========

const PagosModule = {
    miembroSeleccionado: null,
    
    /**
     * Inicializar módulo de pagos
     */
    init() {
        console.log('PagosModule iniciado');
        this.miembroSeleccionado = null;
    },
    
    /**
     * Seleccionar miembro para pago
     */
    seleccionarMiembro(id, nombre) {
        this.miembroSeleccionado = { id, nombre };
        document.getElementById('miembro-seleccionado').textContent = nombre;
        
        // Inicializar fecha con la fecha actual
        const hoy = new Date().toISOString().split('T')[0];
        document.getElementById('fecha-pago').value = hoy;
        
        // Establecer tipo de pago por defecto
        document.getElementById('tipo-pago').value = 'Cuota';
        
        // Establecer método de pago por defecto
        document.getElementById('metodo-pago').value = 'Efectivo';
        
        document.getElementById('paso-1').classList.add('hidden');
        document.getElementById('paso-2').classList.remove('hidden');
    },
    
    /**
     * Agregar dígito al monto
     */
    agregarDigito(digito) {
        const input = document.getElementById('monto-pago');
        let valorActual = input.value.replace(/[^0-9]/g, '');
        
        if (digito === 'borrar') {
            valorActual = valorActual.slice(0, -1);
        } else {
            valorActual += digito;
        }
        
        input.value = valorActual ? `$ ${valorActual}` : '';
    },
    
    /**
     * Guardar pago
     */
    async guardar() {
        if (!this.miembroSeleccionado) {
            mostrarAlerta('Debe seleccionar un miembro', 'warning');
            return;
        }
        
        const montoStr = document.getElementById('monto-pago').value.replace(/[^0-9]/g, '');
        const monto = parseInt(montoStr);
        
        if (!monto || monto <= 0) {
            mostrarAlerta('Debe ingresar un monto válido', 'warning');
            return;
        }
        
        const fecha = document.getElementById('fecha-pago').value;
        if (!fecha) {
            mostrarAlerta('Debe seleccionar una fecha', 'warning');
            return;
        }
        
        const tipoPago = document.getElementById('tipo-pago').value;
        const metodoPago = document.getElementById('metodo-pago').value;
        
        const btnGuardar = document.getElementById('btn-guardar-pago');
        if (btnGuardar) {
            btnGuardar.disabled = true;
            btnGuardar.textContent = 'Guardando...';
        }
        
        try {
            const datos = {
                id_miembro: this.miembroSeleccionado.id,
                nombre_completo: this.miembroSeleccionado.nombre,
                monto: monto,
                concepto: tipoPago,
                metodo: metodoPago,
                fecha: fecha
            };
            
            const response = await fetchAPI(`${APP_CONFIG.apiBase}/pagos/save`, {
                method: 'POST',
                body: JSON.stringify(datos)
            });
            
            if (response.status === 'success') {
                mostrarAlerta(`✅ Pago de ${formatearMoneda(monto)} (${tipoPago} - ${metodoPago}) registrado correctamente`, 'success');
                setTimeout(() => {
                    volverInicio();
                }, 2000);
            }
        } catch (error) {
            console.error('Error guardando pago:', error);
            if (btnGuardar) {
                btnGuardar.disabled = false;
                btnGuardar.textContent = '💰 GUARDAR PAGO';
            }
        }
    },
    
    /**
     * Volver al paso 1
     */
    volverPaso1() {
        this.miembroSeleccionado = null;
        document.getElementById('paso-1').classList.remove('hidden');
        document.getElementById('paso-2').classList.add('hidden');
        document.getElementById('monto-pago').value = '';
        document.getElementById('fecha-pago').value = '';
        document.getElementById('tipo-pago').value = 'Cuota';
    },
    
    /**
     * Filtrar miembros
     */
    filtrar(termino) {
        const items = document.querySelectorAll('.item-card');
        const terminoLower = termino.toLowerCase();
        
        items.forEach(item => {
            const nombre = item.getAttribute('data-nombre').toLowerCase();
            if (nombre.includes(terminoLower)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
};

// ========== MÓDULO: RETIROS ==========

// ========== MÓDULO: RETIROS - Definido en tab_6_retiros.html ==========
// El RetirosModule se define directamente en tab_6_retiros.html para evitar conflictos

// ========== MÓDULO: EXÁMENES (ELIMINADO) ==========

// ========== MÓDULO: EXPORTAR EXCEL ==========

/**
 * Exportar a Excel
 */
async function exportarExcel(tipo) {
    const btnExportar = event.target;
    const textoOriginal = btnExportar.textContent;
    
    btnExportar.disabled = true;
    btnExportar.textContent = 'Exportando...';
    
    try {
        window.location.href = `${APP_CONFIG.apiBase}/export/excel/${tipo}`;
        
        setTimeout(() => {
            btnExportar.disabled = false;
            btnExportar.textContent = textoOriginal;
            mostrarAlerta('✅ Archivo Excel descargado', 'success');
        }, 2000);
    } catch (error) {
        console.error('Error exportando:', error);
        btnExportar.disabled = false;
        btnExportar.textContent = textoOriginal;
    }
}

// ========== INICIALIZACIÓN GLOBAL ==========

document.addEventListener('DOMContentLoaded', function() {
    console.log('App iniciada - Instituto Jorge Müller');
    
    // Inicializar módulos según la página actual
    const pageId = document.body.getAttribute('data-page');
    
    if (pageId === 'asistencia') {
        AsistenciaModule.init();
    } else if (pageId === 'pagos') {
        PagosModule.init();
    }
    // RetirosModule se inicializa en tab_6_retiros.html directamente
});
