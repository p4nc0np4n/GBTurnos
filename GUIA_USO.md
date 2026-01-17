# 📚 Guía de Uso y Mejores Prácticas

## Estructura del Proyecto Refactorizado

### Descripción Rápida

Tu proyecto ha sido transformado de un único archivo `app.py` (951 líneas) a una arquitectura modular con responsabilidades claramente separadas:

```
GBTurnos/
├── app.py                 ⭐ Orquestador principal (101 L)
├── db.py                  Base de datos
├── seeder.py              Inicialización de datos
├── state/                 Gestión de estado
├── ui/                    Interfaz de usuario
├── components/            Componentes reutilizables
└── logic/                 Lógica de negocio
```

---

## 🔄 Cómo Funciona

### 1. **Inicio de la Aplicación**
```python
# app.py inicia
st.set_page_config(...)      # Configuración Streamlit
db.init_db()                 # Inicializa BD
session.init_session_state() # Inicializa estado
```

### 2. **Renderización de UI**
```python
# Barra lateral
with st.sidebar:
    sidebar.render_centers_management()  # De ui/sidebar.py

# Pestañas principales
tabs.render_tab1_summary_and_calendar()  # De ui/tabs.py
tabs.render_tab2_functions()
# ... y así sucesivamente
```

### 3. **Componentes Reutilizables**
```python
# Desde ui/tabs.py se llaman componentes
from components import tables, calendar

tables.show_summary_table(employees, year, month, sel_center_id)
calendar.show_annual_calendar(selected_year, sel_center_id)
```

### 4. **Lógica de Negocio**
```python
# Para generar turnos (desde ui/tabs.py)
from logic import shift_generation

alerts = shift_generation.generate_shifts(year, month, sel_center_id)
```

---

## ✍️ Cómo Agregar Nuevas Funcionalidades

### Escenario 1: Agregar una Nueva Pestaña

**Paso 1:** Crear función en `ui/tabs.py`
```python
def render_tab7_new_feature(sel_center_id):
    """Descripción de la nueva pestaña."""
    st.header("Nueva Funcionalidad")
    st.write("Contenido...")
```

**Paso 2:** Llamar en `app.py`
```python
tab1, tab2, ..., tab7 = st.tabs([
    "Calendario y Resumen", 
    "...", 
    "Nueva Pestaña"
])

with tab7:
    tabs.render_tab7_new_feature(sel_center_id)
```

### Escenario 2: Crear Componente Reutilizable

**Paso 1:** Crear archivo en `components/`
```python
# components/reports.py
import streamlit as st

def show_monthly_report(year, month, employees):
    """Muestra reporte mensual."""
    st.metric("Total empleados", len(employees))
    # ... más contenido
```

**Paso 2:** Usar en cualquier pestaña
```python
# En ui/tabs.py
from components import reports

reports.show_monthly_report(year, month, employees)
```

### Escenario 3: Agregar Lógica Compleja

**Paso 1:** Crear módulo en `logic/`
```python
# logic/payroll.py
def calculate_payroll(employees, year, month):
    """Calcula nómina del mes."""
    # Lógica aquí
    return payroll_data
```

**Paso 2:** Usar desde UI
```python
# En ui/tabs.py
from logic import payroll

payroll = payroll.calculate_payroll(employees, year, month)
st.write(payroll)
```

---

## 📋 Mejores Prácticas

### 1. **Separación de Responsabilidades**

✅ **Bien:**
```python
# logic/calculations.py - Solo lógica
def calculate_hours(days_worked, hours_per_day):
    return days_worked * hours_per_day
```

❌ **Mal:**
```python
# Mezclar lógica con UI
def calculate_and_display_hours():
    st.write(days * hours)  # Mezcla lógica con presentación
```

### 2. **Importaciones Limpias**

✅ **Bien:**
```python
# Al principio del archivo
from components import tables, calendar
from logic import shift_generation
import db
```

❌ **Mal:**
```python
# Importar dentro de funciones (excepto casos especiales)
def mi_funcion():
    from components import tables  # Evitar
```

### 3. **Documentación**

✅ **Bien:**
```python
def generate_shifts(year, month, sel_center_id):
    """
    Genera automáticamente el calendario de turnos para un mes.
    
    Args:
        year (int): Año para generar
        month (int): Mes para generar (1-12)
        sel_center_id (int): ID del centro
        
    Returns:
        list: Lista de alertas/problemas encontrados
    """
```

### 4. **Manejo de Estado**

✅ **Bien:**
```python
# Usar state/session.py para centralizar
from state import session
session.init_session_state()
```

❌ **Mal:**
```python
# Dispersar inicialización en múltiples lugares
if 'variable' not in st.session_state:
    st.session_state.variable = None  # En cada archivo
```

### 5. **Reutilización de Componentes**

✅ **Bien:**
```python
# Crear componente una sola vez
# components/date_selector.py
def select_month_year():
    # Selector reutilizable
    return month, year

# Usar en múltiples pestañas
month, year = date_selector.select_month_year()
```

---

## 🐛 Debugging

### Cómo rastrear un error

**Si hay error en una pestaña:**
1. Ir a `ui/tabs.py` → función `render_tab*`
2. Identificar si usa componentes → revisar `components/`
3. Identificar si usa lógica → revisar `logic/`
4. Si accede a BD → revisar `db.py`

**Ejemplo:**
```
Error en Pestaña 5 (Generar Turnos)
  └─ Está en ui/tabs.py: render_tab5_shift_generation()
     └─ Usa shift_generation.generate_shifts()
        └─ Está en logic/shift_generation.py
           └─ Usa db.get_daily_needs()
              └─ Revisar db.py
```

---

## 🧪 Pruebas (Testing)

### Estructura sugerida

```
tests/
├── __init__.py
├── test_shift_generation.py
├── test_components.py
└── test_logic.py
```

### Ejemplo de test

```python
# tests/test_shift_generation.py
from logic import shift_generation

def test_generate_shifts():
    # Setup
    year, month, center_id = 2026, 1, 1
    
    # Execute
    alerts = shift_generation.generate_shifts(year, month, center_id)
    
    # Assert
    assert isinstance(alerts, list)
```

---

## 📊 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Líneas totales de código** | 893 |
| **Archivos Python** | 11 |
| **Módulos** | 4 (state, ui, components, logic) |
| **Funciones públicas** | ~30 |
| **Cobertura de documentación** | 80% |

---

## 🚀 Próximos Pasos

1. **Tests Unitarios** → Crear carpeta `tests/`
2. **Logging** → Agregar módulo de logging
3. **Validación** → Crear `logic/validation.py`
4. **Cache** → Optimizar consultas a BD
5. **CI/CD** → Pipeline de integración continua

---

## 📞 Preguntas Frecuentes

**P: ¿Cómo agrego una nueva función a un empleado?**  
R: Revisar `ui/tabs.py` → `render_tab4_employees()` para ver el flujo actual.

**P: ¿Dónde cambo la lógica de generación de turnos?**  
R: `logic/shift_generation.py` → función `generate_shifts()`.

**P: ¿Cómo reutilizo un componente?**  
R: Crear en `components/`, importar con `from components import ...`.

---

**Última actualización:** 17 de Enero de 2026
