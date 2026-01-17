"""Componentes para mostrar y editar tablas."""
import streamlit as st
import pandas as pd
from datetime import date
import db


def show_summary_table(employees, year, month, sel_center_id):
    """Muestra tabla resumen de horas y balance."""
    import calendar
    
    datos_resumen = []
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
        st.dataframe(styled, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)


def show_calendar_matrix(employees, year, month, sel_center_id):
    """Muestra matriz visual de calendario con estado diario."""
    import calendar
    
    matriz_visual = []
    num_days = calendar.monthrange(year, month)[1]
    holidays = db.get_holidays(sel_center_id) if sel_center_id else []
    holiday_dates = {h[0]: h[1] for h in holidays}
    
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
    df_cal.columns = df_cal.columns.astype(str)
    
    if not df_cal.empty:
        day_cols = [c for c in df_cal.columns if c.isdigit()]

        def palette(v):
            if v == 'Trabaja':
                return 'background-color: #e6f7ff'
            if v == 'Libra':
                return 'background-color: #f3f4f6'
            if v == 'Festivo':
                return 'background-color: #ffeaa7'
            if v in ['vacaciones', 'ausencia', 'IT']:
                return 'background-color: #ffedd5'
            return ''

        try:
            styled_cal = df_cal.style.map(palette, subset=day_cols)
            st.dataframe(styled_cal, use_container_width=True)
        except Exception:
            st.dataframe(df_cal, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")
