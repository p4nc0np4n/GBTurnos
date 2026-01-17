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
st.title("🏢 GB Corporación - Control de Personal y Jornada")
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
    sidebar.render_centers_management()


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
st.subheader(f"Visualizando: {calendar.month_name[st.session_state.get('selected_month', date.today().month)]} {st.session_state.get('selected_year', date.today().year)}")
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
    month_names = list(calendar.month_name)[1:]
    selected_month_name = st.selectbox("Mes", options=month_names, index=st.session_state.get('selected_month', date.today().month) - 1)
    if selected_year != st.session_state.get('selected_year', date.today().year) or month_names.index(selected_month_name) + 1 != st.session_state.get('selected_month', date.today().month):
        st.session_state.selected_year = selected_year
        st.session_state.selected_month = month_names.index(selected_month_name) + 1
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

# Definición de pestañas principales
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Calendario y Resumen", "Gestión de Funciones", "Necesidades Diarias", "Gestión de Empleados", "Generar Turnos", "Calendario Anual y Resumen Anual"])

with tab1:
    tabs.render_tab1_summary_and_calendar(year, month, sel_center_id, employees)

with tab2:
    tabs.render_tab2_functions(sel_center_id)

with tab3:
    tabs.render_tab3_daily_needs(year, month, sel_center_id)

with tab4:
    tabs.render_tab4_employees(sel_center_id, employees)

with tab5:
    tabs.render_tab5_shift_generation(year, month, sel_center_id)

with tab6:
    selected_year_annual = st.selectbox("Año", options=list(range(date.today().year - 1, date.today().year + 2)), index=2, key="annual_year")
    tabs.render_tab6_annual_summary(selected_year_annual, sel_center_id, employees)
