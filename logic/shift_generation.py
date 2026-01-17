"""Lógica para generación automática de calendario de turnos."""
import calendar
import db


def generate_shifts(year, month, sel_center_id):
    """
    Genera automáticamente el calendario de turnos para un mes.
    
    Returns:
        list: Lista de alertas/problemas encontrados durante la generación
    """
    num_days = calendar.monthrange(year, month)[1]
    db.clear_assignments_for_month(year, month, sel_center_id)

    employees = db.get_employees(sel_center_id)
    emp_dict = {e[0]: e[1] for e in employees}
    emp_jornada = {e[0]: e[3] for e in employees}
    
    functions = db.get_functions(sel_center_id)
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

    return alerts
