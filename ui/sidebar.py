"""Componentes de la barra lateral (sidebar)."""
import streamlit as st
import db


def render_centers_management():
    """Renderiza la sección de gestión de centros en la barra lateral."""
    st.subheader("Centros")
    new_center = st.text_input("Nuevo Centro", key="sidebar_new_center")
    
    if st.button("Añadir Centro", key="add_center"):
        if new_center:
            db.add_center(new_center)
            st.success(f"Centro '{new_center}' añadido.")
            st.rerun()

    st.divider()

    centers = db.get_centers()
    center_names = [c[1] for c in centers]
    
    # Eliminar centro
    if center_names:
        del_center_name = st.selectbox("Centro a eliminar", center_names, key="center_del_select")
        if del_center_name in center_names:
            del_center_id = centers[center_names.index(del_center_name)][0]
        
        if st.button("Eliminar Centro", key="del_center_btn"):
            st.session_state.pending_center_delete = del_center_id
            st.session_state.pending_center_confirm = True

        if st.session_state.get('pending_center_confirm') and st.session_state.get('pending_center_delete'):
            c_matches = [c[1] for c in centers if c[0] == st.session_state.pending_center_delete]
            cname = c_matches[0] if c_matches else "Desconocido"
            
            st.warning(f"¿Eliminar el centro '{cname}'? Se borrarán empleados y vacaciones asociados.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirmar eliminación centro", key="confirm_del_center"):
                    db.remove_center(st.session_state.pending_center_delete)
                    st.success(f"Centro '{cname}' eliminado.")
                    st.session_state.pending_center_delete = None
                    st.session_state.pending_center_confirm = False
                    st.rerun()
            with c2:
                if st.button("Cancelar", key="cancel_del_center"):
                    st.session_state.pending_center_delete = None
                    st.session_state.pending_center_confirm = False
                    st.rerun()
    else:
        st.info("No hay centros.")
