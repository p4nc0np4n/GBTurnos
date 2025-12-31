import streamlit as st
import pandas as pd
from datetime import date, timedelta
import db
import calendar

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestor de Jornada", layout="wide")
st.title("🏢 GB Corporación - Control de Personal y Jornada")
st.markdown(
    """
    <style>
    /* Limita el ancho del contenedor principal */
    .block-container {
        max-width: 1200px;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Hace que los botones no ocupen el 100% si no quieres */
    .stButton>button {
        width: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. BASE DE DATOS ---
db.init_db()

# Función auxiliar para recargar (Streamlit moderno usa st.rerun())
def rerun():
    st.rerun()

# Inicialización de Centros y Datos de ejemplo
centers = db.get_centers()
if not centers:
    db.add_center("Principal")
    centers = db.get_centers()
    if centers:
        center_id = centers[0][0]
        for name in ["Juan Pérez", "Maria Garcia", "Luis Torres"]:
            db.add_employee(name, center_id)

# Inicializar variables de estado (Session State)
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

# Asegurar selección de centro
centers = db.get_centers()
center_names = [c[1] for c in centers]
sel_center_name = st.session_state.get("center_select", center_names[0] if center_names else None)

if sel_center_name:
    # Busca el ID basado en el nombre seleccionado
    sel_center_id = next((c[0] for c in centers if c[1] == sel_center_name), None)
else:
    sel_center_id = None

# --- 3. BARRA LATERAL (CONTROLES) ---
with st.sidebar:
    st.header("Gestión")

    # Gestión de Centros
    st.subheader("Centros")
    new_center = st.text_input("Nuevo Centro", key="sidebar_new_center")
    
    if st.button("Añadir Centro", key="add_center"):
        if new_center:
            db.add_center(new_center)
            st.success(f"Centro '{new_center}' añadido.")
            rerun()

    st.divider()

    # Eliminar centro
    if center_names:
        del_center_name = st.selectbox("Centro a eliminar", center_names, key="center_del_select")
        # Encontrar ID
        if del_center_name in center_names:
            del_center_id = centers[center_names.index(del_center_name)][0]
        
        if st.button("Eliminar Centro", key="del_center_btn"):
            st.session_state.pending_center_delete = del_center_id
            st.session_state.pending_center_confirm = True

        if st.session_state.get('pending_center_confirm') and st.session_state.get('pending_center_delete'):
            # Buscar nombre seguro para mostrar
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
                    rerun()
            with c2:
                if st.button("Cancelar", key="cancel_del_center"):
                    st.session_state.pending_center_delete = None
                    st.session_state.pending_center_confirm = False
                    rerun()
    else:
        st.info("No hay centros.")

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
col1, col2 = st.columns(2)
with col1:
    current_year = date.today().year
    years = list(range(current_year - 5, current_year + 6))
    year = st.selectbox("Año", options=years, index=years.index(current_year))
with col2:
    month_names = list(calendar.month_name)[1:]
    selected_month_name = st.selectbox("Mes", options=month_names, index=date.today().month - 1)

month = month_names.index(selected_month_name) + 1

# Definición de pestañas principales
tab1, tab2, tab3 = st.tabs(["Calendario y Resumen", "Gestión de Funciones", "Gestión de Empleados"])

with tab1:

    # Lógica de cálculo de horas
    cal = calendar.monthcalendar(year, month)
    dias_laborables_mes = 0
    for semana in cal:
        for dia_idx in range(5): 
            if semana[dia_idx] != 0:
                dias_laborables_mes += 1

    horas_teoricas = dias_laborables_mes * 8
    st.metric(label=f"Horas Laborables Teóricas ({month}/{year})", value=f"{horas_teoricas} h")

    # Construir Tabla Resumen
    datos_resumen = []
    employees = db.get_employees(sel_center_id) if sel_center_id else []

    for emp in employees:
        emp_id, emp_name = emp[0], emp[1]
        # Contar vacaciones
        vacas_totales = db.get_vacations(emp_id)
        vacas_mes = 0
        for v in vacas_totales:
            v_date = pd.to_datetime(v[0])
            if v_date.year == year and v_date.month == month:
                vacas_mes += 1

        horas_realizadas = horas_teoricas - (vacas_mes * 8)
        balance = horas_realizadas - horas_teoricas

        datos_resumen.append({
            "Empleado": emp_name,
            "Días Ausencia": vacas_mes,
            "Horas Teóricas": horas_teoricas,
            "Horas Realizadas": horas_realizadas,
            "Balance Mes": balance
        })

    df = pd.DataFrame(datos_resumen)
    expected_cols = ["Empleado", "Días Ausencia", "Horas Teóricas", "Horas Realizadas", "Balance Mes"]
    
    if df.empty:
        df = pd.DataFrame(columns=expected_cols)

    # Mostrar tabla con formato
    if 'Balance Mes' in df.columns:
        # st.dataframe permite column_config en versiones nuevas, pero usaremos style.map para colores
        def color_balance(val):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        
        # map sustituye a applymap en pandas recientes
        styled = df.style.map(color_balance, subset=['Balance Mes'])
        st.dataframe(styled, width='stretch')
    else:
        st.dataframe(df, width='stretch')

    # Visualización de Calendario Simple (Matriz)
    st.subheader(f"Calendario Visual - {calendar.month_name[month]}")
    matriz_visual = []
    num_days = calendar.monthrange(year, month)[1]
    
    for emp in employees:
        emp_id, emp_name = emp[0], emp[1]
        fila = {"Empleado": emp_name}
        for d in range(1, num_days + 1):
            fecha_obj = date(year, month, d)
            fecha_actual = fecha_obj.strftime("%Y-%m-%d")
            dia_semana = fecha_obj.weekday()  # 0=Lun, 6=Dom

            estado = "Trabaja"
            vacs = db.get_vacations(emp_id)
            vac_dict = {v[0]: v[1] for v in vacs}
            
            if fecha_actual in vac_dict:
                estado = vac_dict[fecha_actual]
            elif dia_semana >= 5:
                estado = "Libra"

            fila[d] = estado
        matriz_visual.append(fila)

    df_cal = pd.DataFrame(matriz_visual)
    
    if not df_cal.empty:
        # Identificar columnas numéricas (días)
        day_cols = [c for c in df_cal.columns if isinstance(c, int)]

        def palette(v):
            if v == 'Trabaja':
                return 'background-color: #e6f7ff'  # azul clarito
            if v == 'Libra':
                return 'background-color: #f3f4f6'  # gris claro
            if v in ['vacaciones', 'ausencia', 'IT']:
                return 'background-color: #ffedd5'  # naranja claro
            return ''

        try:
            styled_cal = df_cal.style.map(palette, subset=day_cols)
            st.dataframe(styled_cal, width='stretch')
        except Exception:
            st.dataframe(df_cal, width='stretch')
    else:
        st.info("No hay datos para mostrar.")

# --- PESTAÑA 2: GESTIÓN DE FUNCIONES ---
with tab2:
    st.header("Gestión de Funciones y Asignaciones")

    # Subtabs
    subtab1, subtab2, subtab3 = st.tabs(["Funciones", "Asignaciones", "Necesidades Diarias"])

    with subtab1:
        st.subheader("Administrar Funciones")
        functions = db.get_functions()
        func_names = [f[1] for f in functions]

        # Mostrar funciones en tabla
        if functions:
            df_functions = pd.DataFrame(functions, columns=["ID", "Nombre"])
            df_functions = df_functions.drop(columns=["ID"])  # No mostrar ID
            st.dataframe(df_functions, width='stretch')
        else:
            st.info("No hay funciones definidas.")

        new_func = st.text_input("Nueva Función", key="new_func")
        if st.button("Añadir Función", key="add_func"):
            if new_func and new_func not in func_names:
                db.add_function(new_func)
                st.success(f"Función '{new_func}' añadida.")
                rerun()
            else:
                st.warning("Función ya existe o vacía.")

        st.divider()

        # Eliminar Función
        if func_names:
            del_func_name = st.selectbox("Función a eliminar", func_names, key="func_del_select")
            
            if st.button("Eliminar Función", key="del_func_btn"):
                st.session_state.pending_function_delete = functions[func_names.index(del_func_name)][0]
                st.session_state.pending_function_confirm = True

            if st.session_state.get('pending_function_confirm') and st.session_state.get('pending_function_delete'):
                # Buscar nombre seguro para mostrar
                f_matches = [f[1] for f in functions if f[0] == st.session_state.pending_function_delete]
                fname = f_matches[0] if f_matches else "Desconocida"
                
                st.warning(f"¿Eliminar la función '{fname}'? Se borrarán asignaciones y necesidades asociadas.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirmar eliminación función", key="confirm_del_func"):
                        db.remove_function(st.session_state.pending_function_delete)
                        st.success(f"Función '{fname}' eliminada.")
                        st.session_state.pending_function_delete = None
                        st.session_state.pending_function_confirm = False
                        rerun()
                with c2:
                    if st.button("Cancelar", key="cancel_del_func"):
                        st.session_state.pending_function_delete = None
                        st.session_state.pending_function_confirm = False
                        rerun()
        else:
            st.info("No hay funciones para eliminar.")

    with subtab2:
        st.subheader("Asignar Funciones a Empleados")
        employees = db.get_employees(sel_center_id) if sel_center_id else []
        emp_names = [e[1] for e in employees]
        
        if emp_names:
            emp_sel = st.selectbox("Seleccionar Empleado", emp_names, key="emp_func_select")
            emp_id = employees[emp_names.index(emp_sel)][0]

            functions = db.get_functions()
            func_dict = {f[0]: f[1] for f in functions}

            current_funcs = db.get_employee_functions(emp_id)
            # Mostrar funciones actuales en tabla
            if current_funcs:
                df_current = pd.DataFrame(current_funcs, columns=["Función", "Prioridad"])
                st.dataframe(df_current, width='stretch')
            else:
                st.info("No tiene funciones asignadas.")

            # Formulario
            func_options = [f[1] for f in functions]
            if func_options:
                selected_func = st.selectbox("Función", func_options, key="select_func")
                priority = st.number_input("Prioridad (mayor = más alta)", min_value=1, value=1, key="priority")
                
                if st.button("Asignar Función", key="assign_func"):
                    func_id = next(k for k, v in func_dict.items() if v == selected_func)
                    db.add_employee_function(emp_id, func_id, priority)
                    st.success("Asignada.")
                    rerun()
            else:
                st.info("Crea funciones en la pestaña anterior primero.")

            # Remover función
            if current_funcs:
                # current_funcs es [(name, priority), ...]
                func_names_curr = [f[0] for f in current_funcs] 
                remove_func_name = st.selectbox("Función a remover", func_names_curr, key="remove_func_select")
                
                if st.button("Remover Función", key="remove_func"):
                    # Necesitamos el ID de la función a borrar
                    # Buscamos en func_dict original el ID basado en el nombre
                    func_id_to_rem = next(k for k, v in func_dict.items() if v == remove_func_name)
                    db.remove_employee_function(emp_id, func_id_to_rem)
                    st.success("Removida.")
                    rerun()
        else:
            st.info("No hay empleados en este centro.")

    with subtab3:
        st.subheader("Establecer Necesidades Diarias")
        col1, col2 = st.columns(2)
        with col1:
            year_need = st.selectbox("Año", options=years, index=years.index(current_year), key="year_need")
        with col2:
            month_need = st.selectbox("Mes", options=month_names, index=date.today().month - 1, key="month_need")
            month_num = month_names.index(month_need) + 1

        functions = db.get_functions()
        func_names = [f[1] for f in functions]

        if func_names:
            num_days = calendar.monthrange(year_need, month_num)[1]
            days = list(range(1, num_days + 1))

            # Obtener datos existentes
            needs_data = {}
            for day in days:
                date_str = f"{year_need}-{month_num:02d}-{day:02d}"
                needs = db.get_daily_needs(date_str, sel_center_id)
                # Needs debe devolver [(func_name, count), ...]
                needs_data[day] = {n[0]: n[1] for n in needs}

            # Crear DataFrame editable
            df_needs = pd.DataFrame(index=func_names, columns=days)
            for func in func_names:
                for day in days:
                    df_needs.at[func, day] = needs_data[day].get(func, 0)

            st.write("Editar necesidades (personas necesarias por función y día):")
            edited_df = st.data_editor(df_needs, key="needs_editor")

            if st.button("Guardar Necesidades", key="save_needs"):
                # Asegurar que las columnas sean enteros
                edited_df.columns = edited_df.columns.astype(int)
                for func in func_names:
                    # Encontrar ID
                    func_id = next(f[0] for f in functions if f[1] == func)
                    for day in days:
                        count = edited_df.at[func, day]
                        date_str = f"{year_need}-{month_num:02d}-{day:02d}"
                        # Asumimos que set_daily_need maneja upsert (insertar o actualizar)
                        db.set_daily_need(date_str, func_id, int(count), sel_center_id)
                st.success("Guardado.")
        else:
            st.warning("No hay funciones definidas.")

    with tab3:
        st.header("Gestión de Empleados")

        # Alta de Empleado
        st.subheader("Alta de Empleado")
        nuevo_emp = st.text_input("Nuevo Empleado", key="tab3_new_emp")
        if st.button("Añadir Persona", key="tab3_add_emp"):
            if not sel_center_id:
                st.warning("Selecciona un centro primero.")
            elif nuevo_emp:
                db.add_employee(nuevo_emp, sel_center_id)
                st.success(f"{nuevo_emp} añadido al centro.")
                rerun()

        st.divider()

        # Registrar Vacaciones
        st.subheader("Registrar Ausencia/Vacaciones")
        employees = db.get_employees(sel_center_id) if sel_center_id else []
        emp_names = [e[1] for e in employees]
        
        if emp_names:
            emp_sel_name = st.selectbox("Empleado", emp_names, key="tab3_vac_emp_select")
            emp_sel_id = employees[emp_names.index(emp_sel_name)][0]
        else:
            emp_sel_name = None
            emp_sel_id = None

        fecha_vac = st.date_input("Fecha de ausencia", date.today(), key="tab3_vac_date")
        tipo_ausencia = st.selectbox("Tipo de ausencia", ["vacaciones", "ausencia", "IT"], key="tab3_tipo_ausencia")
        
        if st.button("Marcar Ausencia", key="tab3_mark_vac"):
            if not emp_sel_id:
                st.warning("Selecciona un empleado.")
            else:
                fecha_str = fecha_vac.strftime("%Y-%m-%d")
                db.add_vacation(emp_sel_id, fecha_str, tipo_ausencia)
                st.success("Guardado.")

        st.divider()

        # Eliminar Empleado
        st.subheader("Eliminar Empleado")
        if emp_names:
            emp_del_name = st.selectbox("Empleado a eliminar", emp_names, key="tab3_emp_del_select")
            emp_del_id = employees[emp_names.index(emp_del_name)][0]
            
            if st.button("Eliminar Empleado", key="tab3_start_delete"):
                st.session_state.pending_delete = emp_del_id
                st.session_state.pending_confirm = True

            if st.session_state.pending_confirm and st.session_state.pending_delete:
                matches = [e[1] for e in employees if e[0] == st.session_state.pending_delete]
                nombre = matches[0] if matches else "Desconocido"
                
                st.warning(f"¿Deseas eliminar a {nombre}? Esta acción no se puede deshacer.")
                colc1, colc2 = st.columns(2)
                with colc1:
                    if st.button("Confirmar Eliminación", key="tab3_confirm_delete"):
                        db.remove_employee(st.session_state.pending_delete)
                        st.success(f"{nombre} eliminado.")
                        st.session_state.pending_delete = None
                        st.session_state.pending_confirm = False
                        rerun()
                with colc2:
                    if st.button("Cancelar", key="tab3_cancel_delete"):
                        st.session_state.pending_delete = None
                        st.session_state.pending_confirm = False
                        rerun()
        else:
            st.info("No hay empleados para eliminar en este centro.")