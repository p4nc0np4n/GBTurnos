# 📋 Estructura del Proyecto - Gestor de Jornada GB Corporación

## Resumen de la Refactorización

El proyecto original **`app.py` monolítico de 951 líneas** ha sido dividido en una **estructura modular y mantenible** con los siguientes componentes:

---

## 📁 Estructura de Directorios

```
GBTurnos/
├── app.py                 # ⭐ Archivo principal (118 líneas)
├── db.py                  # Módulo de base de datos
├── seeder.py              # Seed inicial de datos
│
├── state/                 # 🔧 Gestión de Estado
│   ├── __init__.py
│   └── session.py         # Inicialización de session_state
│
├── logic/                 # 🧠 Lógica de Negocio
│   ├── __init__.py
│   ├── utils.py           # Funciones auxiliares
│   └── shift_generation.py  # Generación de calendario de turnos
│
├── components/            # 🎨 Componentes Reutilizables
│   ├── __init__.py
│   ├── tables.py          # Tablas y editores de datos
│   └── calendar.py        # Visualización de calendarios
│
├── ui/                    # 🖥️ Interfaz de Usuario
│   ├── __init__.py
│   ├── sidebar.py         # Barra lateral
│   └── tabs.py            # Funciones para las 6 pestañas
│
└── venv/                  # Entorno virtual
```

---

## 📄 Descripción de Archivos

### **state/session.py**
Gestiona el estado de la aplicación Streamlit:
- Inicialización de variables de sesión
- Estados de confirmación/eliminación
- Alertas de generación de turnos

### **logic/utils.py**
Funciones auxiliares:
- `weighted_sample_without_replacement()` - Selección ponderada

### **logic/shift_generation.py**
Núcleo del algoritmo de generación de turnos:
- Genera automáticamente asignaciones optimizadas
- Gestiona restricciones (vacaciones, habilidades, horas)
- Produce alertas de problemas de cobertura

### **components/tables.py**
Componentes para visualización y edición de datos:
- Tabla resumen mensual de horas
- Matriz visual de calendario
- Gestión de funciones y empleados

### **components/calendar.py**
Visualización de calendarios:
- Calendario anual con festivos
- Tabla de resultados de turnos
- Resumen anual de empleados

### **ui/sidebar.py**
Barra lateral (sidebar):
- Gestión de centros
- Creación/eliminación de centros

### **ui/tabs.py**
Renderización de las 6 pestañas principales:
- `render_tab1_summary_and_calendar()` - Resumen y calendario
- `render_tab2_functions()` - Gestión de funciones
- `render_tab3_daily_needs()` - Necesidades diarias
- `render_tab4_employees()` - Gestión de empleados
- `render_tab5_shift_generation()` - Generación de turnos
- `render_tab6_annual_summary()` - Resumen anual

### **app.py**
Archivo principal simplificado:
- Configuración de Streamlit
- Inicialización de base de datos
- Selectores globales (centro, mes, año)
- Orquestación de componentes UI

---

## 🚀 Ventajas de la Nueva Estructura

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Líneas en app.py** | 951 | 118 |
| **Complejidad** | Monolítica | Modular |
| **Mantenibilidad** | Difícil | Fácil |
| **Reutilización** | Limitada | Excelente |
| **Testing** | Complejo | Unitario |

---

## 🔄 Flujo de Uso

1. **`app.py`** inicializa todo y orquesta la interfaz
2. **`state/session.py`** mantiene el estado de la sesión
3. **`ui/sidebar.py`** y **`ui/tabs.py`** renderizan la interfaz
4. **`components/`** proporciona componentes reutilizables
5. **`logic/`** contiene la lógica de negocio

---

## 📝 Cómo Agregar Nuevas Funcionalidades

### Agregar una nueva pestaña:

1. Crear función en `ui/tabs.py`: `render_tab7_new_feature()`
2. Agregar componentes en `components/` si es necesario
3. Llamar la función en `app.py`

### Agregar lógica compleja:

1. Crear archivo en `logic/`
2. Importar en `app.py` o donde sea necesario
3. Mantener separación de responsabilidades

### Agregar visualización reutilizable:

1. Crear función en `components/`
2. Importar donde sea necesario
3. Documentar parámetros

---

## 🛠️ Mejoras Futuras

- [ ] Agregar sistema de logging
- [ ] Implementar caching para consultas BD
- [ ] Crear tests unitarios
- [ ] Agregar validación de datos
- [ ] Mejorar visualización de gráficos

---

**Última actualización:** 17 de Enero de 2026
