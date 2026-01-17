"""Gestión del estado de sesión de Streamlit."""
import streamlit as st


def init_session_state():
    """Inicializa todas las variables necesarias en session_state."""
    if 'pending_delete' not in st.session_state:
        st.session_state.pending_delete = None
    if 'pending_confirm' not in st.session_state:
        st.session_state.pending_confirm = False
    if 'pending_center_delete' not in st.session_state:
        st.session_state.pending_center_delete = None
    if 'pending_center_confirm' not in st.session_state:
        st.session_state.pending_center_confirm = False
    if 'pending_function_delete' not in st.session_state:
        st.session_state.pending_function_delete = None
    if 'pending_function_confirm' not in st.session_state:
        st.session_state.pending_function_confirm = False
    if 'pending_clear' not in st.session_state:
        st.session_state.pending_clear = False
    if 'shift_alerts' not in st.session_state:
        st.session_state['shift_alerts'] = []
    if 'selected_month' not in st.session_state:
        from datetime import date
        st.session_state.selected_month = date.today().month
    if 'selected_year' not in st.session_state:
        from datetime import date
        st.session_state.selected_year = date.today().year


def get_month_year():
    """Retorna el mes y año seleccionados."""
    from datetime import date
    year = st.session_state.get('selected_year', date.today().year)
    month = st.session_state.get('selected_month', date.today().month)
    return month, year
