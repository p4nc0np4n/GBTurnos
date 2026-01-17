"""Funciones para renderizar las pestañas principales."""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
import db
from components import tables, calendar as cal_components
from logic import shift_generation


def render_tab1_summary_and_calendar(year, month, sel_center_id, employees):
    """Pestaña 1: Calendario y Resumen."""
    st.header("Resumen Mensual y Calendario Visual")
    
    tables.show_summary_table(employees, year, month, sel_center_id)
    
    st.subheader(f"Calendario Visual - {calendar.month_name[month]}")
    tables.show_calendar_matrix(employees, year, month, sel_center_id)


def render_tab2_functions(sel_center_id):
    """Pestaña 2: Gestión de Funciones y Asignaciones."""
    st.header("Gestión de Funciones y Asignaciones")

    subtab1, subtab2 = st.tabs(["Funciones", "Asignaciones"])

    with subtab1:
        st.subheader("Administrar Funciones")
        if not sel_center_id:
            st.warning("Selecciona un centro para gestionar sus funciones.")
        else:
            functions = db.get_functions(sel_center_id)
            func_names = [f[1] for f in functions]

            if functions:
                df_functions = pd.DataFrame(functions, columns=["ID", "Nombre"])
                df_functions = df_functions.drop(columns=["ID"])
                st.dataframe(df_functions, use_container_width=True)
            else:
                st.info("No hay funciones definidas.")

            new_func = st.text_input("Nueva Función", key="new_func")
            if st.button("Añadir Función", key="add_func"):
                if new_func and new_func not in func_names:
                    db.add_function(new_func, sel_center_id)
                    st.success(f"Función '{new_func}' añadida.")
                    st.rerun()
                else:
                    st.warning("Función ya existe o vacía.")

            st.divider()

            if func_names:
                del_func_name = st.selectbox("Función a eliminar", func_names, key="func_del_select")
                
                if st.button("Eliminar Función", key="del_func_btn"):
                    st.session_state.pending_function_delete = functions[func_names.index(del_func_name)][0]
                    st.session_state.pending_function_confirm = True

                if st.session_state.get('pending_function_confirm') and st.session_state.get('pending_function_delete'):
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
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key="cancel_del_func"):
                            st.session_state.pending_function_delete = None
                            st.session_state.pending_function_confirm = False
                            st.rerun()
            else:
                st.info("No hay funciones para eliminar.")

    with subtab2:
        st.subheader("Asignar Funciones a Empleados")
        employees = db.get_employees(sel_center_id) if sel_center_id else []
        emp_names = [e[1] for e in employees]
        
        if employees:
            summary_rows = []
            for emp_id, emp_name, _, _ in employees:
                funcs = db.get_employee_functions(emp_id)
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

            functions = db.get_functions(sel_center_id)
            func_dict = {f[0]: f[1] for f in functions}

            current_funcs = db.get_employee_functions(emp_id)
            if current_funcs:
                df_current = pd.DataFrame(current_funcs, columns=["Función", "Prioridad"])
                st.dataframe(df_current, use_container_width=True)
            else:
                st.info("No tiene funciones asignadas.")

            func_options = [f[1] for f in functions]
            if func_options:
                selected_func = st.selectbox("Función", func_options, key="select_func")
                priority = st.number_input("Prioridad (mayor = más alta)", min_value=1, value=1, key="priority")
                
                if st.button("Asignar Función", key="assign_func"):
                    func_id = next(k for k, v in func_dict.items() if v == selected_func)
                    db.add_employee_function(emp_id, func_id, priority)
                    st.success("Asignada.")
                    st.rerun()
            else:
                st.info("Crea funciones en la pestaña anterior primero.")

            if current_funcs:
                func_names_curr = [f[0] for f in current_funcs] 
                remove_func_name = st.selectbox("Función a remover", func_names_curr, key="remove_func_select")
                
                if st.button("Remover Función", key="remove_func"):
                    func_id_to_rem = next(k for k, v in func_dict.items() if v == remove_func_name)
                    db.remove_employee_function(emp_id, func_id_to_rem)
                    st.success("Removida.")
                    st.rerun()
        else:
            st.info("No hay empleados en este centro.")


def render_tab3_daily_needs(year, month, sel_center_id):
    """Pestaña 3: Necesidades Diarias."""
    st.header("Necesidades Diarias")
    st.subheader("Establecer Necesidades Diarias")
    st.info(f"Editando necesidades para {calendar.month_name[st.session_state.get('selected_month', date.today().month)]} {st.session_state.get('selected_year', date.today().year)}")
    
    if not sel_center_id:
        st.warning("Selecciona un centro primero.")
    else:
        functions = db.get_functions(sel_center_id)
        func_names = [f[1] for f in functions]

        if func_names:
            num_days = calendar.monthrange(year, month)[1]
            days = list(range(1, num_days + 1))

            needs_data = {}
            for day in days:
                date_str = f"{year}-{month:02d}-{day:02d}"
                needs = db.get_daily_needs(date_str, sel_center_id)
                needs_data[day] = {n[0]: n[1] for n in needs}

            df_needs = pd.DataFrame(index=func_names, columns=days)
            for func in func_names:
                for day in days:
                    df_needs.at[func, day] = needs_data[day].get(func, 0)

            st.write("Editar necesidades (personas necesarias por función y día):")
            edited_df = st.data_editor(df_needs, key="needs_editor")

            if st.button("Guardar Necesidades", key="save_needs"):
                with st.spinner("Guardando necesidades diarias..."):
                    edited_df.columns = edited_df.columns.astype(int)
                    changes = []
                    for func in func_names:
                        func_id = next(f[0] for f in functions if f[1] == func)
                        for day in days:
                            original_count = df_needs.at[func, day]
                            new_count = edited_df.at[func, day]
                            if original_count != new_count:
                                date_str = f"{year}-{month:02d}-{day:02d}"
                                changes.append((date_str, func_id, int(new_count), sel_center_id))
                    if changes:
                        db.batch_set_daily_needs(changes)
                        st.success(f"Necesidades guardadas exitosamente. Se actualizaron {len(changes)} entradas.")
                    else:
                        st.info("No se detectaron cambios.")
        else:
            st.warning("No hay funciones definidas.")


def render_tab4_employees(sel_center_id, employees):
    """Pestaña 4: Gestión de Empleados."""
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
            st.rerun()

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
            st.rerun()

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
        
        absences = db.get_vacations(emp_sel_id_remove)
        if absences:
            df_absences = pd.DataFrame(absences, columns=["Fecha", "Tipo"])
            df_absences["Fecha"] = pd.to_datetime(df_absences["Fecha"]).dt.strftime("%d/%m/%Y")
            st.dataframe(df_absences, use_container_width=True)
            
            absence_options = [f"{row['Fecha']} - {row['Tipo']}" for _, row in df_absences.iterrows()]
            selected_absence = st.selectbox("Ausencia a quitar", absence_options, key="tab3_remove_absence_select")
            
            if st.button("Quitar Ausencia", key="tab3_remove_vac"):
                fecha_str = selected_absence.split(" - ")[0]
                fecha_obj = pd.to_datetime(fecha_str, format="%d/%m/%Y")
                fecha_db = fecha_obj.strftime("%Y-%m-%d")
                db.remove_vacation(emp_sel_id_remove, fecha_db)
                st.success("Ausencia quitada.")
                st.rerun()
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
                    st.rerun()
            with colc2:
                if st.button("Cancelar", key="tab3_cancel_delete"):
                    st.session_state.pending_delete = None
                    st.session_state.pending_confirm = False
                    st.rerun()
    else:
        st.info("No hay empleados para eliminar en este centro.")


def render_tab5_shift_generation(year, month, sel_center_id):
    """Pestaña 5: Generar Calendario de Turnos."""
    st.header("Generar Calendario de Turnos")
    st.subheader(f"Gestión de turnos para {calendar.month_name[month]} {year}")
    
    # Mostrar alertas
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
        col_actions = st.columns(2)
        
        with col_actions[0]:
            if st.button("🚀 Generar Calendario de Turnos", key="generate_shifts"):
                with st.spinner("Calculando asignaciones óptimas..."):
                    alerts = shift_generation.generate_shifts(year, month, sel_center_id)
                    st.success("¡Calendario generado!")
                    if alerts:
                        st.session_state['shift_alerts'] = alerts
                    else:
                        st.session_state['shift_alerts'] = []
                    st.rerun()

        with col_actions[1]:
            if st.button("🗑️ Borrar Calendario del Mes", key="clear_shifts"):
                st.session_state.pending_clear = True

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

        st.subheader("Resultados de la Planificación")
        cal_components.show_shifts_result_table(year, month, sel_center_id)


def render_tab6_annual_summary(selected_year, sel_center_id, employees):
    """Pestaña 6: Calendario Anual y Resumen Anual."""
    st.header("Calendario Anual y Resumen Anual")

    if sel_center_id:
        holidays = db.get_holidays(sel_center_id)

        # Gestión de Festivos
        st.subheader("Gestión de Festivos")
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            new_holiday_date = st.date_input("Fecha del Festivo", key="new_holiday_date")
            new_holiday_name = st.text_input("Nombre del Festivo (opcional)", key="new_holiday_name")
            if st.button("Añadir Festivo", key="add_holiday"):
                db.add_holiday(new_holiday_date.strftime("%Y-%m-%d"), sel_center_id, new_holiday_name)
                st.success("Festivo añadido.")
                st.rerun()
        with col_h2:
            holiday_to_remove = st.selectbox("Festivo a eliminar", options=[f"{d} - {n or 'Sin nombre'}" for d, n in holidays], key="holiday_remove")
            if st.button("Eliminar Festivo", key="remove_holiday") and holiday_to_remove:
                date_str = holiday_to_remove.split(" - ")[0]
                db.remove_holiday(date_str, sel_center_id)
                st.success("Festivo eliminado.")
                st.rerun()

        # Calendario Anual
        st.subheader(f"Calendario Anual {selected_year}")
        cal_components.show_annual_calendar(selected_year, sel_center_id)

        # Resumen Anual
        st.subheader(f"Resumen Anual {selected_year}")
        cal_components.show_annual_summary(selected_year, employees, sel_center_id)
    else:
        st.info("Selecciona un centro.")
