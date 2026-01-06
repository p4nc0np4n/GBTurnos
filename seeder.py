import calendar

import db


def seed_example_residencia():
    """Carga datos de ejemplo en el centro 'Residencia' para enero-2026."""
    conn = db.get_conn()
    c = conn.cursor()

    # Centro de ejemplo
    c.execute("INSERT OR IGNORE INTO centers(name) VALUES(?)", ("Residencia",))
    conn.commit()
    c.execute("SELECT id FROM centers WHERE name=?", ("Residencia",))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    center_id = row[0]

    # Empleados de ejemplo
    employees = [
        ("Ana Lopez", 1800, 8),
        ("Beatriz Ramos", 1750, 7.5),
        ("Carlos Medina", 1850, 8),
        ("Diego Suarez", 1700, 7),
        ("Elena Flores", 1800, 8),
    ]
    for name, max_horas, jornada in employees:
        c.execute(
            "INSERT OR IGNORE INTO employees(name, center_id, max_horas_anuales, horas_jornada_diaria) VALUES(?, ?, ?, ?)",
            (name, center_id, max_horas, jornada),
        )
        c.execute(
            "UPDATE employees SET max_horas_anuales=?, horas_jornada_diaria=? WHERE name=? AND center_id=?",
            (max_horas, jornada, name, center_id),
        )
    conn.commit()

    # Funciones de ejemplo
    function_names = ["Turno manana", "Turno tarde", "Turno noche", "Cocina", "Limpieza", "Recepcion"]
    for fname in function_names:
        c.execute("INSERT OR IGNORE INTO functions(name) VALUES(?)", (fname,))
    conn.commit()

    # Mapas auxiliares
    func_map = {name: fid for fid, name in c.execute("SELECT id, name FROM functions").fetchall()}
    emp_map = {name: eid for eid, name in c.execute("SELECT id, name FROM employees WHERE center_id=?", (center_id,)).fetchall()}

    # Asignar funciones a empleados (mayor numero = mas preferencia)
    emp_func_prefs = {
        "Ana Lopez": [("Turno manana", 3), ("Turno tarde", 2), ("Recepcion", 1)],
        "Beatriz Ramos": [("Turno tarde", 3), ("Cocina", 2), ("Limpieza", 1)],
        "Carlos Medina": [("Turno noche", 3), ("Turno tarde", 2)],
        "Diego Suarez": [("Cocina", 3), ("Turno manana", 2)],
        "Elena Flores": [("Limpieza", 3), ("Recepcion", 2), ("Turno noche", 1)],
    }
    for emp_name, prefs in emp_func_prefs.items():
        emp_id = emp_map.get(emp_name)
        if not emp_id:
            continue
        for func_name, priority in prefs:
            func_id = func_map.get(func_name)
            if func_id:
                c.execute(
                    "INSERT OR REPLACE INTO employee_functions(emp_id, func_id, priority) VALUES(?, ?, ?)",
                    (emp_id, func_id, priority),
                )
    conn.commit()

    # Vacaciones de enero 2026
    vacations = {
        "Ana Lopez": ["2026-01-02", "2026-01-03", "2026-01-04", "2026-01-15"],
        "Beatriz Ramos": ["2026-01-08", "2026-01-09", "2026-01-22", "2026-01-23"],
        "Carlos Medina": ["2026-01-12", "2026-01-13", "2026-01-26"],
        "Diego Suarez": ["2026-01-05", "2026-01-06", "2026-01-07"],
        "Elena Flores": ["2026-01-18", "2026-01-19"],
    }
    for emp_name, days in vacations.items():
        emp_id = emp_map.get(emp_name)
        if not emp_id:
            continue
        for day in days:
            c.execute(
                "INSERT OR IGNORE INTO vacations(emp_id, date, type) VALUES(?, ?, 'vacaciones')",
                (emp_id, day),
            )
    conn.commit()

    # Necesidades diarias para enero 2026
    days_in_month = calendar.monthrange(2026, 1)[1]
    for day in range(1, days_in_month + 1):
        weekday = calendar.weekday(2026, 1, day)
        date_str = f"2026-01-{day:02d}"
        if weekday < 5:
            needs = {
                "Turno manana": 2,
                "Turno tarde": 2,
                "Turno noche": 1,
                "Cocina": 1,
                "Limpieza": 1,
                "Recepcion": 1,
            }
        else:
            needs = {
                "Turno manana": 1,
                "Turno tarde": 1,
                "Turno noche": 1,
                "Cocina": 1,
                "Limpieza": 0,
                "Recepcion": 1,
            }
        for func_name, count in needs.items():
            func_id = func_map.get(func_name)
            if func_id is not None:
                c.execute(
                    "INSERT OR REPLACE INTO daily_needs(date, func_id, count, center_id) VALUES(?, ?, ?, ?)",
                    (date_str, func_id, count, center_id),
                )
    conn.commit()
    conn.close()


def unseed_example_residencia():
    """Elimina los datos de ejemplo del centro 'Residencia' y limpia funciones creadas si no se usan."""
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM centers WHERE name=?", ("Residencia",))
    row = c.fetchone()
    conn.close()

    if not row:
        return

    center_id = row[0]

    # Borra el centro y sus datos asociados
    db.remove_center(center_id)

    # Elimina funciones de ejemplo si quedaron sin referencias
    sample_functions = ["Turno manana", "Turno tarde", "Turno noche", "Cocina", "Limpieza", "Recepcion"]
    conn = db.get_conn()
    c = conn.cursor()
    for fname in sample_functions:
        c.execute("SELECT id FROM functions WHERE name=?", (fname,))
        frow = c.fetchone()
        if not frow:
            continue
        func_id = frow[0]
        c.execute("SELECT COUNT(*) FROM employee_functions WHERE func_id=?", (func_id,))
        ef_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM daily_needs WHERE func_id=?", (func_id,))
        dn_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM assignments WHERE func_id=?", (func_id,))
        as_count = c.fetchone()[0]
        if ef_count == 0 and dn_count == 0 and as_count == 0:
            c.execute("DELETE FROM functions WHERE id=?", (func_id,))
    conn.commit()
    conn.close()
