"""Componentes para visualización de calendarios."""
import streamlit as st
import pandas as pd
import calendar
from datetime import date
import db


def show_shifts_result_table(year, month, sel_center_id):
    """Muestra tabla con resultados de asignación de turnos."""
    all_assignments = db.get_assignments(center_id=sel_center_id)
    prefix = f"{year}-{month:02d}"
    month_assignments = [a for a in all_assignments if a[0].startswith(prefix)]

    if not month_assignments:
        st.info(f"No hay turnos registrados para {calendar.month_name[month]} {year}.")
    else:
        functions_list = [f[1] for f in db.get_functions(sel_center_id)]
        num_days_month = calendar.monthrange(year, month)[1]
        day_columns = [f"{d:02d}" for d in range(1, num_days_month + 1)]
        
        df_view = pd.DataFrame(index=functions_list, columns=day_columns).fillna("")

        for date_db, emp_name, func_name in month_assignments:
            d_str = date_db.split('-')[2]
            if func_name in df_view.index and d_str in df_view.columns:
                prev = df_view.at[func_name, d_str]
                df_view.at[func_name, d_str] = f"{prev}, {emp_name}".strip(", ")

        st.dataframe(df_view, use_container_width=True)


def show_annual_calendar(selected_year, sel_center_id):
    """Muestra calendario anual con festivos."""
    holidays = db.get_holidays(sel_center_id)
    holiday_dates = {h[0]: h[1] for h in holidays}
    
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
    st.dataframe(df_annual, use_container_width=True)


def show_annual_summary(selected_year, employees, sel_center_id):
    """Muestra resumen anual de horas y ausencias."""
    holidays = db.get_holidays(sel_center_id)
    holiday_dates = {h[0]: h[1] for h in holidays}
    
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
    st.dataframe(df_resumen, use_container_width=True)
