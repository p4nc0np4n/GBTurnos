"""
Gestor de Jornada - GB Corporación
Control de Personal, Turnos y Vacaciones
"""
import streamlit as st
from datetime import date
import calendar
import db
from state import session
from ui import sidebar, tabs

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestor de Jornada", layout="wide")
st.title("🏢 GB turnos - Control de Personal y Jornada")
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1200px;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    .stButton>button {
        width: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. INICIALIZACIÓN ---
db.init_db()
session.init_session_state()

# Inicializar datos de ejemplo si no existen centros
centers = db.get_centers()
if not centers:
    db.add_center("Principal")
    centers = db.get_centers()
    if centers:
        center_id = centers[0][0]
        for name in ["Juan Pérez", "Maria Garcia", "Luis Torres"]:
            db.add_employee(name, center_id)

# --- 3. BARRA LATERAL (CONTROLES) ---
with st.sidebar:
    st.header("Gestión")
    if st.button("🏢 Gestión de Centros", key="toggle_centers"):
        st.session_state.show_centers = not st.session_state.get("show_centers", False)
    if st.session_state.get("show_centers", False):
        sidebar.render_centers_management()

    st.divider()
    section_options = [
        "Calendario y resumen anual",
        "Gestión de funciones",
        "Necesidades diarias del centro",
        "Gestión de empleados",
        "Generar turnos del centro",
    ]
    selected_section = st.radio("Secciones", section_options, key="sidebar_section")


# --- 4. PANEL PRINCIPAL (VISUALIZACIÓN) ---
# Selectores globales
centers = db.get_centers()
center_names = [c[1] for c in centers]
if center_names:
    sel_center_name = st.selectbox("Centro", center_names, key="center_select")
    sel_center_id = next((c[0] for c in centers if c[1] == sel_center_name), None)
else:
    st.info("No hay centros. Crea uno en la barra lateral.")
    sel_center_id = None

# Selector de Mes para visualizar
month_names_es = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
current_month_idx = st.session_state.get('selected_month', date.today().month) - 1
current_month_es = month_names_es[current_month_idx].capitalize()
st.subheader(f"Visualizando: {current_month_es} {st.session_state.get('selected_year', date.today().year)}")
col1, col2, col3 = st.columns([1,2,1])
with col1:
    if st.button("◀ Mes Anterior", key="prev_month"):
        if st.session_state.get('selected_month', date.today().month) == 1:
            st.session_state.selected_month = 12
            st.session_state.selected_year = st.session_state.get('selected_year', date.today().year) - 1
        else:
            st.session_state.selected_month = st.session_state.get('selected_month', date.today().month) - 1
        st.rerun()
with col2:
    years = list(range(st.session_state.get('selected_year', date.today().year) - 5, st.session_state.get('selected_year', date.today().year) + 6))
    selected_year = st.selectbox("Año", options=years, index=years.index(st.session_state.get('selected_year', date.today().year)))
    selected_month_name = st.selectbox("Mes", options=[m.capitalize() for m in month_names_es], index=st.session_state.get('selected_month', date.today().month) - 1)
    if selected_year != st.session_state.get('selected_year', date.today().year) or month_names_es.index(selected_month_name.lower()) + 1 != st.session_state.get('selected_month', date.today().month):
        st.session_state.selected_year = selected_year
        st.session_state.selected_month = month_names_es.index(selected_month_name.lower()) + 1
        st.rerun()
with col3:
    if st.button("Mes Siguiente ▶", key="next_month"):
        if st.session_state.get('selected_month', date.today().month) == 12:
            st.session_state.selected_month = 1
            st.session_state.selected_year = st.session_state.get('selected_year', date.today().year) + 1
        else:
            st.session_state.selected_month = st.session_state.get('selected_month', date.today().month) + 1
        st.rerun()

year = st.session_state.get('selected_year', date.today().year)
month = st.session_state.get('selected_month', date.today().month)

# Obtener empleados para las pestañas
employees = db.get_employees(sel_center_id) if sel_center_id else []

if selected_section == "Calendario y resumen anual":
    subtab1, subtab2, subtab3 = st.tabs([
        "Resumen mensual y calendario visual",
        "Calendario anual y resumen anual del centro",
        "Gestión de festivos",
    ])
    with subtab1:
        tabs.render_tab1_summary_and_calendar(year, month, sel_center_id, employees)
        st.divider()
        tabs.render_annual_summary(year, employees, sel_center_id)
    with subtab2:
        selected_year_annual = st.selectbox(
            "Año",
            options=list(range(date.today().year - 1, date.today().year + 2)),
            index=2,
            key="annual_year",
        )
        tabs.render_annual_calendar(selected_year_annual, sel_center_id)
    with subtab3:
        tabs.render_holiday_management(sel_center_id)

elif selected_section == "Gestión de funciones":
    tabs.render_tab2_functions(sel_center_id)

elif selected_section == "Necesidades diarias del centro":
    tabs.render_tab3_daily_needs(year, month, sel_center_id)

elif selected_section == "Gestión de empleados":
    tabs.render_tab4_employees(sel_center_id, employees)

elif selected_section == "Generar turnos del centro":
    tabs.render_tab5_shift_generation(year, month, sel_center_id)
