# DIAGRAMA DE DEPENDENCIAS DEL PROYECTO

Muestra cómo se relacionan los módulos entre sí.

---

## Árbol de Módulos

```text
┌─────────────────────────────────────────────────────────────────┐
│                         app.py (101 líneas)                     │
│                      Orquestador Principal                      │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌────────────┐  ┌────────────┐  ┌───────────┐
        │ db.py      │  │ state/     │  │ ui/       │
        │ (452 L)    │  │ session.py │  │ sidebar.py│
        │ Base de    │  │ (32 L)     │  │ (46 L)    │
        │ Datos      │  │            │  │           │
        └────────────┘  └────────────┘  └───────────┘
                                               │
                                        ┌──────┘
                                        ▼
                                   ┌────────────┐
                                   │ ui/tabs.py │
                                   │ (360 L)    │
                                   │ 6 Pestañas │
                                   └────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │ components/  │    │ logic/       │    │ db.py        │
            │ tables.py    │    │ shift_       │    │ (consultas)  │
            │ (117 L)      │    │ generation.py│    │              │
            │              │    │ (120 L)      │    │              │
            └──────────────┘    └──────────────┘    └──────────────┘
                    │                   │
                    └───────┬───────────┘
                            ▼
                    ┌──────────────┐
                    │ components/  │
                    │ calendar.py  │
                    │ (95 L)       │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ logic/       │
                    │ utils.py     │
                    │ (18 L)       │
                    └──────────────┘
```

---

## Flujo de Datos

1. `app.py` inicia y carga la configuración
2. `state/session.py` inicializa el estado de Streamlit
3. `ui/sidebar.py` renderiza la barra lateral
4. `ui/tabs.py` renderiza las 6 pestañas principales
5. Cada pestaña puede usar:
   - `components/tables.py` para mostrar tablas
   - `components/calendar.py` para mostrar calendarios
   - `logic/shift_generation.py` para lógica compleja
   - `db.py` para acceder a la base de datos
6. `logic/shift_generation.py` usa:
   - `db.py` para acceder a datos
   - `logic/utils.py` para funciones auxiliares

---

## Separación de Responsabilidades

```text
┌──────────────────────────────────┐
│  PRESENTACIÓN (ui/)              │
│  - Renderización de interfaz     │
│  - Gestión de eventos            │
│  - Flujo de usuario              │
└──────────────────────────────────┘
           ▲
           │ (consume)
           │
┌──────────────────────────────────┐
│  COMPONENTES (components/)       │
│  - Widgets reutilizables         │
│  - Visualización de datos        │
│  - Formateo de información       │
└──────────────────────────────────┘
           ▲
           │ (consume)
           │
┌──────────────────────────────────┐
│  LÓGICA (logic/)                 │
│  - Algoritmos                    │
│  - Procesamiento de datos        │
│  - Cálculos                      │
└──────────────────────────────────┘
           ▲
           │ (consume)
           │
┌──────────────────────────────────┐
│  ESTADO (state/)                 │
│  - Variables de sesión           │
│  - Estado de la aplicación       │
│  - Configuración                 │
└──────────────────────────────────┘
           ▲
           │ (consume)
           │
┌──────────────────────────────────┐
│  PERSISTENCIA (db.py)            │
│  - Base de datos                 │
│  - Consultas                     │
│  - Almacenamiento                │
└──────────────────────────────────┘
```

---

## Importaciones Cruzadas

```text
app.py
  ├── import streamlit as st
  ├── from state import session
  ├── from ui import sidebar
  ├── from ui import tabs
  ├── import db
  └── import calendar

state/session.py
  └── import streamlit as st

ui/sidebar.py
  ├── import streamlit as st
  └── import db

ui/tabs.py
  ├── import streamlit as st
  ├── import pandas as pd
  ├── import db
  ├── from components import tables
  ├── from components import calendar as cal_components
  └── from logic import shift_generation

components/tables.py
  ├── import streamlit as st
  ├── import pandas as pd
  ├── from datetime import date
  └── import db

components/calendar.py
  ├── import streamlit as st
  ├── import pandas as pd
  ├── import calendar
  ├── from datetime import date
  └── import db

logic/shift_generation.py
  ├── import calendar
  └── import db

logic/utils.py
  └── import random

seeder.py
  └── import db
```

---

## Métricas de Acoplamiento

- ❌ **Antes:** Altamente acoplado (todo en un archivo)
- ✅ **Después:** Bajo acoplamiento (módulos independientes)

| Módulo       | Dependencias propias               |
|--------------|------------------------------------|
| `app.py`     | 3 módulos propios + streamlit + db |
| `ui/`        | components, logic, db              |
| `components/`| db                                 |
| `logic/`     | db                                 |
| `state/`     | Independiente (solo streamlit)     |
