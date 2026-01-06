import streamlit as st
import pandas as pd
from datetime import date, timedelta
import db
import calendar
import random

def weighted_sample_without_replacement(items, weights, k):
    """Selección ponderada sin reemplazo."""
    if k >= len(items):
        return items
    selected = []
    remaining_items = items[:]
    remaining_weights = weights[:]
    for _ in range(k):
        if not remaining_items:
            break
        chosen = random.choices(remaining_items, weights=remaining_weights, k=1)[0]
        selected.append(chosen)
        idx = remaining_items.index(chosen)
        remaining_items.pop(idx)
        remaining_weights.pop(idx)
    return selected

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
if 'pending_clear' not in st.session_state:
    st.session_state.pending_clear = False
if 'shift_alerts' not in st.session_state:
    st.session_state['shift_alerts'] = []

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
st.subheader(f"Visualizando: {calendar.month_name[st.session_state.get('selected_month', date.today().month)]} {st.session_state.get('selected_year', date.today().year)}")
col1, col2, col3 = st.columns([1,2,1])
with col1:
    if st.button("◀ Mes Anterior", key="prev_month"):
        if st.session_state.get('selected_month', date.today().month) == 1:
            st.session_state.selected_month = 12
            st.session_state.selected_year = st.session_state.get('selected_year', date.today().year) - 1
        else:
            st.session_state.selected_month = st.session_state.get('selected_month', date.today().month) - 1
        rerun()
with col2:
    # Selectores directos si quieren cambiar manualmente
    years = list(range(st.session_state.get('selected_year', date.today().year) - 5, st.session_state.get('selected_year', date.today().year) + 6))
    selected_year = st.selectbox("Año", options=years, index=years.index(st.session_state.get('selected_year', date.today().year)))
    month_names = list(calendar.month_name)[1:]
    selected_month_name = st.selectbox("Mes", options=month_names, index=st.session_state.get('selected_month', date.today().month) - 1)
    # Actualizar session state si cambian los selectboxes
    if selected_year != st.session_state.get('selected_year', date.today().year) or month_names.index(selected_month_name) + 1 != st.session_state.get('selected_month', date.today().month):
        st.session_state.selected_year = selected_year
        st.session_state.selected_month = month_names.index(selected_month_name) + 1
        rerun()
with col3:
    if st.button("Mes Siguiente ▶", key="next_month"):
        if st.session_state.get('selected_month', date.today().month) == 12:
            st.session_state.selected_month = 1
            st.session_state.selected_year = st.session_state.get('selected_year', date.today().year) + 1
        else:
            st.session_state.selected_month = st.session_state.get('selected_month', date.today().month) + 1
        rerun()

year = st.session_state.get('selected_year', date.today().year)
month = st.session_state.get('selected_month', date.today().month)

# Definición de pestañas principales
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Calendario y Resumen", "Gestión de Funciones", "Necesidades Diarias", "Gestión de Empleados", "Generar Turnos", "Calendario Anual y Resumen Anual"])

with tab1:

    # Construir Tabla Resumen
    datos_resumen = []
    employees = db.get_employees(sel_center_id) if sel_center_id else []
    holidays = db.get_holidays(sel_center_id) if sel_center_id else []
    holiday_dates = {h[0]: h[1] for h in holidays}

    for emp in employees:
        emp_id, emp_name, max_horas, jornada = emp
        # Contar vacaciones
        vacas_totales = db.get_vacations(emp_id)
        vacas_mes = 0
        for v in vacas_totales:
            v_date = pd.to_datetime(v[0])
            if v_date.year == year and v_date.month == month:
                vacas_mes += 1

        # Días laborables del mes (lunes a viernes)
        dias_laborables_mes = 0
        cal = calendar.monthcalendar(year, month)
        for semana in cal:
            for dia_idx in range(5): 
                if semana[dia_idx] != 0:
                    dias_laborables_mes += 1

        # Restar festivos que caen en días laborables
        dias_festivos_mes = 0
        for h_date, _ in holidays:
            h_year, h_month, h_day = map(int, h_date.split('-'))
            if h_year == year and h_month == month:
                h_weekday = date(h_year, h_month, h_day).weekday()
                if h_weekday < 5:  # Lunes a viernes
                    dias_festivos_mes += 1

        dias_laborables_ajustados = dias_laborables_mes - dias_festivos_mes
        horas_teoricas = dias_laborables_ajustados * jornada
        dias_trabajados = dias_laborables_ajustados - vacas_mes
        horas_realizadas = dias_trabajados * jornada
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
        def color_balance(val):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        
        styled = df.style.format({
            'Horas Teóricas': '{:.2f}',
            'Horas Realizadas': '{:.2f}',
            'Balance Mes': '{:.2f}'
        }).map(color_balance, subset=['Balance Mes'])
        st.dataframe(styled, width='stretch')
    else:
        st.dataframe(df, width='stretch')

    # Visualización de Calendario Simple (Matriz)
    st.subheader(f"Calendario Visual - {calendar.month_name[month]}")
    matriz_visual = []
    num_days = calendar.monthrange(year, month)[1]
    
    for emp in employees:
        emp_id, emp_name, _, _ = emp
        fila = {"Empleado": emp_name}
        for d in range(1, num_days + 1):
            fecha_obj = date(year, month, d)
            fecha_actual = fecha_obj.strftime("%Y-%m-%d")
            dia_semana = fecha_obj.weekday()  # 0=Lun, 6=Dom

            estado = "Trabaja"
            vacs = db.get_vacations(emp_id)
            vac_dict = {v[0]: v[1] for v in vacs}
            
            if fecha_actual in holiday_dates:
                estado = "Festivo"
            elif fecha_actual in vac_dict:
                estado = vac_dict[fecha_actual]
            elif dia_semana >= 5:
                estado = "Libra"

            fila[d] = estado
        matriz_visual.append(fila)

    df_cal = pd.DataFrame(matriz_visual)
    
    # Convertir nombres de columnas a strings para evitar warnings
    df_cal.columns = df_cal.columns.astype(str)
    
    if not df_cal.empty:
        # Identificar columnas numéricas (días)
        day_cols = [c for c in df_cal.columns if c.isdigit()]

        def palette(v):
            if v == 'Trabaja':
                return 'background-color: #e6f7ff'  # azul clarito
            if v == 'Libra':
                return 'background-color: #f3f4f6'  # gris claro
            if v == 'Festivo':
                return 'background-color: #ffeaa7'  # amarillo claro
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
    subtab1, subtab2 = st.tabs(["Funciones", "Asignaciones"])

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
        
        # Resumen actual de asignaciones: Empleado y lista de funciones con prioridad
        if employees:
            summary_rows = []
            for emp_id, emp_name, _, _ in employees:
                funcs = db.get_employee_functions(emp_id)  # [(name, priority)] ordenado desc
                if funcs:
                    funcs_str = ", ".join([f"{name} ({prio})" for name, prio in funcs])
                else:
                    funcs_str = "—"
                summary_rows.append({"Empleado": emp_name, "Funciones": funcs_str})

            df_summary = pd.DataFrame(summary_rows)
            st.dataframe(df_summary, use_container_width=True)
        else:
            st.info("No hay empleados en este centro.")

        if emp_names:
            emp_sel = st.selectbox("Seleccionar Empleado", emp_names, key="emp_func_select")
            emp_id = employees[emp_names.index(emp_sel)][0]

            functions = db.get_functions()
            func_dict = {f[0]: f[1] for f in functions}

            current_funcs = db.get_employee_functions(emp_id)
            # Mostrar funciones actuales en tabla
            if current_funcs:
                df_current = pd.DataFrame(current_funcs, columns=["Función", "Prioridad"])
                st.dataframe(df_current, use_container_width=True)
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

    with tab3:
        st.header("Necesidades Diarias")

        st.subheader("Establecer Necesidades Diarias")
        st.info(f"Editando necesidades para {calendar.month_name[st.session_state.get('selected_month', date.today().month)]} {st.session_state.get('selected_year', date.today().year)}")
        
        year_need = st.session_state.get('selected_year', date.today().year)
        month_num = st.session_state.get('selected_month', date.today().month)

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
                with st.spinner("Guardando necesidades diarias..."):
                    # Asegurar que las columnas sean enteros
                    edited_df.columns = edited_df.columns.astype(int)
                    changes = []
                    for func in func_names:
                        # Encontrar ID
                        func_id = next(f[0] for f in functions if f[1] == func)
                        for day in days:
                            original_count = df_needs.at[func, day]
                            new_count = edited_df.at[func, day]
                            if original_count != new_count:
                                date_str = f"{year_need}-{month_num:02d}-{day:02d}"
                                changes.append((date_str, func_id, int(new_count), sel_center_id))
                    if changes:
                        db.batch_set_daily_needs(changes)
                        st.success(f"Necesidades guardadas exitosamente. Se actualizaron {len(changes)} entradas.")
                    else:
                        st.info("No se detectaron cambios.")
                # Actualizar df_needs para reflejar los cambios
                df_needs = edited_df.copy()
        else:
            st.warning("No hay funciones definidas.")

    with tab4:
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

        # Parámetros de empleados
        st.subheader("Parámetros de Empleados")
        for emp in employees:
            emp_id, emp_name, max_horas, jornada = emp
            st.write(f"**{emp_name}**")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_max_horas = st.number_input(f"Máx Horas Anuales para {emp_name}", value=float(max_horas), key=f"max_horas_{emp_id}")
            with col_p2:
                new_jornada = st.number_input(f"Horas Jornada Diaria para {emp_name}", value=float(jornada), key=f"jornada_{emp_id}")
            if st.button(f"Actualizar {emp_name}", key=f"update_{emp_id}"):
                db.update_employee_params(emp_id, new_max_horas, new_jornada)
                st.success("Parámetros actualizados.")
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

        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha inicio", date.today(), key="tab3_vac_start")
        with col2:
            fecha_fin = st.date_input("Fecha fin", fecha_inicio, key="tab3_vac_end")
        
        tipo_ausencia = st.selectbox("Tipo de ausencia", ["vacaciones", "ausencia", "IT"], key="tab3_tipo_ausencia")
        
        if st.button("Marcar Ausencia", key="tab3_mark_vac"):
            if not emp_sel_id:
                st.warning("Selecciona un empleado.")
            elif fecha_inicio > fecha_fin:
                st.warning("La fecha de inicio no puede ser posterior a la fecha de fin.")
            else:
                current_date = fecha_inicio
                added_count = 0
                while current_date <= fecha_fin:
                    fecha_str = current_date.strftime("%Y-%m-%d")
                    db.add_vacation(emp_sel_id, fecha_str, tipo_ausencia)
                    added_count += 1
                    current_date += timedelta(days=1)
                st.success(f"Ausencias guardadas: {added_count} días.")

        st.divider()

        # Quitar Ausencias
        st.subheader("Quitar Ausencias")
        if emp_names:
            emp_sel_name_remove = st.selectbox("Empleado", emp_names, key="tab3_remove_emp_select")
            emp_sel_id_remove = employees[emp_names.index(emp_sel_name_remove)][0]
            
            # Obtener ausencias del empleado
            absences = db.get_vacations(emp_sel_id_remove)
            if absences:
                # Mostrar en una tabla
                df_absences = pd.DataFrame(absences, columns=["Fecha", "Tipo"])
                df_absences["Fecha"] = pd.to_datetime(df_absences["Fecha"]).dt.strftime("%d/%m/%Y")
                st.dataframe(df_absences, width='stretch')
                
                # Selector para quitar
                absence_options = [f"{row['Fecha']} - {row['Tipo']}" for _, row in df_absences.iterrows()]
                selected_absence = st.selectbox("Ausencia a quitar", absence_options, key="tab3_remove_absence_select")
                
                if st.button("Quitar Ausencia", key="tab3_remove_vac"):
                    # Extraer fecha de la opción seleccionada
                    fecha_str = selected_absence.split(" - ")[0]
                    # Convertir de dd/mm/yyyy a yyyy-mm-dd
                    fecha_obj = pd.to_datetime(fecha_str, format="%d/%m/%Y")
                    fecha_db = fecha_obj.strftime("%Y-%m-%d")
                    db.remove_vacation(emp_sel_id_remove, fecha_db)
                    st.success("Ausencia quitada.")
                    rerun()
            else:
                st.info("No hay ausencias registradas para este empleado.")
        else:
            st.info("No hay empleados.")

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

    with tab5:
        st.header("Generar Calendario de Turnos")

        # 1. Parámetros de tiempo y centro
        year = st.session_state.get('selected_year', date.today().year)
        month = st.session_state.get('selected_month', date.today().month)
        
        st.subheader(f"Gestión de turnos para {calendar.month_name[month]} {year}")
        
        # Mostrar alertas de la última generación guardadas en session_state
        if st.session_state.get('shift_alerts'):
            n_alerts = len(st.session_state['shift_alerts'])
            st.warning(f"⚠️ {n_alerts} alerta(s) en la última generación. Despliega para ver detalles.")
            with st.expander("Detalles de alertas (última generación)", expanded=True):
                for a in st.session_state.get('shift_alerts', []):
                    st.warning(a)
                if st.button("Borrar alertas", key="clear_shift_alerts"):
                    st.session_state['shift_alerts'] = []
        if not sel_center_id:
            st.warning("Selecciona un centro primero.")
        else:
            # --- BOTONES DE ACCIÓN ---
            col_actions = st.columns(2)
            
            with col_actions[0]:
                if st.button("🚀 Generar Calendario de Turnos", key="generate_shifts"):
                    with st.spinner("Calculando asignaciones óptimas..."):
                        # Preparación inicial
                        num_days = calendar.monthrange(year, month)[1]
                        db.clear_assignments_for_month(year, month, sel_center_id)

                        employees = db.get_employees(sel_center_id)
                        emp_dict = {e[0]: e[1] for e in employees}
                        emp_jornada = {e[0]: e[3] for e in employees}
                        
                        functions = db.get_functions()
                        func_dict = {f[0]: f[1] for f in functions}
                        
                        # Cargar habilidades (funciones) y prioridades por empleado
                        emp_skills = {}
                        for emp_id in emp_dict:
                            funcs = db.get_employee_functions(emp_id)
                            emp_skills[emp_id] = {f[0]: f[1] for f in funcs}

                        # Cargar ausencias/vacaciones
                        emp_vacations = {}
                        for emp_id in emp_dict:
                            vacs = db.get_vacations(emp_id)
                            emp_vacations[emp_id] = {v[0] for v in vacs}

                        # Bolsa de horas mensual
                        remaining_hours = {}
                        for emp_id in emp_dict:
                            vacas_mes_count = sum(1 for v_date in emp_vacations[emp_id] 
                                                if v_date.startswith(f"{year}-{month:02d}"))
                            remaining_hours[emp_id] = (num_days - vacas_mes_count) * emp_jornada[emp_id]

                        alerts = []

                        # --- BUCLE DIARIO ---
                        for day in range(1, num_days + 1):
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            needs = db.get_daily_needs(date_str, sel_center_id)
                            
                            if not needs:
                                continue

                            # Traducir necesidades a lista de tareas
                            tasks_to_fill = []
                            for f_name, count in needs:
                                f_id = next((k for k, v in func_dict.items() if v == f_name), None)
                                if f_id:
                                    for _ in range(count):
                                        tasks_to_fill.append(f_id)

                            assigned_today = set()
                            
                            # --- OPTIMIZACIÓN POR ESCASEZ CON DIAGNÓSTICO ---
                            task_candidates_map = []
                            for f_id in tasks_to_fill:
                                f_name = func_dict[f_id]
                                candidates = []
                                
                                # Contadores para el diagnóstico
                                sin_habilidad = 0
                                en_vacaciones = 0
                                sin_horas = 0

                                for emp_id in emp_dict:
                                    # 1. Habilidad
                                    if f_name not in emp_skills[emp_id]:
                                        sin_habilidad += 1
                                        continue
                                    # 2. Vacaciones
                                    if date_str in emp_vacations[emp_id]:
                                        en_vacaciones += 1
                                        continue
                                    # 3. Horas
                                    if remaining_hours[emp_id] < emp_jornada[emp_id]:
                                        sin_horas += 1
                                        continue
                                    
                                    # Si pasa los filtros, es apto
                                    if emp_id not in assigned_today:
                                        candidates.append({
                                            'emp_id': emp_id,
                                            'priority': emp_skills[emp_id][f_name]
                                        })
                                
                                # Si no hay candidatos para función, alertamos con el motivo
                                if not candidates:
                                    motivo = ""
                                    if sin_habilidad == len(emp_dict): 
                                        motivo = "Nadie tiene esta función asignada en su ficha."
                                    elif (sin_habilidad + en_vacaciones + sin_horas) >= len(emp_dict):
                                        motivo = f"Indisponibilidad: {en_vacaciones} en vacac./baja y {sin_horas} sin horas."
                                    else:
                                        motivo = "Personal cualificado ya ocupado en otras tareas hoy."
                                    
                                    alerts.append(f"Día {day:02d}: No se pudo cubrir '{f_name}'. {motivo}")

                                task_candidates_map.append({
                                    'func_id': f_id,
                                    'candidates': candidates,
                                    'num_options': len(candidates)
                                })

                            # Ordenar: primero las tareas con menos opciones disponibles
                            task_candidates_map.sort(key=lambda x: x['num_options'])

                            # Asignación final
                            for item in task_candidates_map:
                                f_id = item['func_id']
                                available_now = [c for c in item['candidates'] if c['emp_id'] not in assigned_today]
                                
                                if available_now:
                                    # Maximizar prioridad
                                    available_now.sort(key=lambda x: x['priority'], reverse=True)
                                    best_candidate = available_now[0]
                                    emp_id = best_candidate['emp_id']
                                    
                                    db.set_assignment(date_str, emp_id, f_id, sel_center_id)
                                    assigned_today.add(emp_id)
                                    remaining_hours[emp_id] -= emp_jornada[emp_id]
                                else:
                                    # No quedó nadie disponible porque se usaron en tareas previas del día
                                    func_name = func_dict.get(f_id, "Función")
                                    alerts.append(f"Día {day:02d}: No se pudo cubrir '{func_name}'. Personal cualificado ya ocupado en otras tareas hoy.")

                        st.success("¡Calendario generado!")
                        # Guardar alertas en session_state antes de reiniciar para que persistan
                        if alerts:
                            st.session_state['shift_alerts'] = alerts
                        else:
                            st.session_state['shift_alerts'] = []
                        st.rerun()

            with col_actions[1]:
                if st.button("🗑️ Borrar Calendario del Mes", key="clear_shifts"):
                    st.session_state.pending_clear = True

            # --- LÓGICA DE BORRADO ---
            if st.session_state.get('pending_clear'):
                st.warning("¿Estás seguro de borrar todos los turnos de este mes?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirmar Borrado", key="confirm_clear_final"):
                        db.clear_assignments_for_month(year, month, sel_center_id)
                        st.session_state.pending_clear = False
                        st.rerun()
                with c2:
                    if st.button("Cancelar", key="cancel_clear_final"):
                        st.session_state.pending_clear = False
                        st.rerun()

            st.divider()

            # --- VISUALIZACIÓN DE RESULTADOS ---
            st.subheader("Resultados de la Planificación")
            
            # Obtener datos frescos de la BD
            all_assignments = db.get_assignments(center_id=sel_center_id)
            prefix = f"{year}-{month:02d}"
            month_assignments = [a for a in all_assignments if a[0].startswith(prefix)]

            if not month_assignments:
                st.info(f"No hay turnos registrados para {calendar.month_name[month]} {year}.")
            else:
                # Mostrar alertas de cobertura justo antes del calendario de resultados
                if st.session_state.get('shift_alerts'):
                    st.subheader("Alertas de Cobertura")
                    for a in st.session_state.get('shift_alerts', []):
                        st.warning(a)
                # Construcción del DataFrame para visualización
                functions_list = [f[1] for f in db.get_functions()]
                num_days_month = calendar.monthrange(year, month)[1]
                day_columns = [f"{d:02d}" for d in range(1, num_days_month + 1)]
                
                df_view = pd.DataFrame(index=functions_list, columns=day_columns).fillna("")

                for date_db, emp_name, func_name in month_assignments:
                    d_str = date_db.split('-')[2]
                    if func_name in df_view.index and d_str in df_view.columns:
                        prev = df_view.at[func_name, d_str]
                        df_view.at[func_name, d_str] = f"{prev}, {emp_name}".strip(", ")

                st.dataframe(df_view, use_container_width=True)

                

# --- PESTAÑA 6: CALENDARIO ANUAL Y RESUMEN ANUAL ---
with tab6:
    st.header("Calendario Anual y Resumen Anual")

    # Selector de año
    selected_year = st.selectbox("Año", options=list(range(date.today().year - 1, date.today().year + 2)), index=2, key="annual_year")

    if sel_center_id:
        # Obtener empleados
        employees = db.get_employees(sel_center_id)
        holidays = db.get_holidays(sel_center_id)
        holiday_dates = {h[0]: h[1] for h in holidays}

        # Gestión de Festivos
        st.subheader("Gestión de Festivos")
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            new_holiday_date = st.date_input("Fecha del Festivo", key="new_holiday_date")
            new_holiday_name = st.text_input("Nombre del Festivo (opcional)", key="new_holiday_name")
            if st.button("Añadir Festivo", key="add_holiday"):
                db.add_holiday(new_holiday_date.strftime("%Y-%m-%d"), sel_center_id, new_holiday_name)
                st.success("Festivo añadido.")
                rerun()
        with col_h2:
            holiday_to_remove = st.selectbox("Festivo a eliminar", options=[f"{d} - {n or 'Sin nombre'}" for d, n in holidays], key="holiday_remove")
            if st.button("Eliminar Festivo", key="remove_holiday") and holiday_to_remove:
                date_str = holiday_to_remove.split(" - ")[0]
                db.remove_holiday(date_str, sel_center_id)
                st.success("Festivo eliminado.")
                rerun()

        # Calendario Anual
        st.subheader(f"Calendario Anual {selected_year}")
        # Crear un calendario anual simple
        annual_cal = []
        for month in range(1, 13):
            month_name = calendar.month_name[month]
            cal = calendar.monthcalendar(selected_year, month)
            month_data = {"Mes": month_name}
            for week in cal:
                for day in week:
                    if day != 0:
                        date_str = f"{selected_year}-{month:02d}-{day:02d}"
                        if date_str in holiday_dates:
                            month_data[f"{day}"] = f"Festivo ({holiday_dates[date_str] or ''})"
                        else:
                            month_data[f"{day}"] = "Laborable"
            annual_cal.append(month_data)

        df_annual = pd.DataFrame(annual_cal)
        st.dataframe(df_annual, width='stretch')

        # Resumen Anual
        st.subheader(f"Resumen Anual {selected_year}")
        resumen_data = []
        for emp in employees:
            emp_id, emp_name, max_horas, jornada = emp
            # Obtener vacaciones
            vacs = db.get_vacations(emp_id)
            dias_vacaciones = 0
            dias_it = 0
            dias_ausencia = 0
            for v_date, v_type in vacs:
                v_year = int(v_date.split('-')[0])
                if v_year == selected_year:
                    if v_type == 'vacaciones':
                        dias_vacaciones += 1
                    elif v_type == 'IT':
                        dias_it += 1
                    else:
                        dias_ausencia += 1

            # Días trabajados: total días laborables - festivos - ausencias
            total_dias_laborables = 0
            for month in range(1, 13):
                cal = calendar.monthcalendar(selected_year, month)
                for week in cal:
                    for day in week:
                        if day != 0:
                            date_obj = date(selected_year, month, day)
                            if date_obj.weekday() < 5:  # Lunes a viernes
                                date_str = date_obj.strftime("%Y-%m-%d")
                                if date_str not in holiday_dates:
                                    total_dias_laborables += 1

            dias_trabajados = total_dias_laborables - dias_vacaciones - dias_it - dias_ausencia
            horas_trabajadas = dias_trabajados * jornada
            balance_horas = horas_trabajadas - max_horas

            resumen_data.append({
                "Empleado": emp_name,
                "Días Vacaciones": dias_vacaciones,
                "Días IT": dias_it,
                "Días Ausencia": dias_ausencia,
                "Días Trabajados": dias_trabajados,
                "Horas Trabajadas": horas_trabajadas,
                "Máx Horas Anuales": max_horas,
                "Balance Horas": balance_horas
            })

        df_resumen = pd.DataFrame(resumen_data)
        st.dataframe(df_resumen, width='stretch')
    else:
        st.info("Selecciona un centro.")