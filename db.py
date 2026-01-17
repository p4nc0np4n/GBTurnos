import sqlite3
import os
import calendar

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    conn.commit()
    conn.close()


def get_centers():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name FROM centers ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows


def add_center(name):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO centers(name) VALUES(?)", (name,))
        conn.commit()
    except Exception:
        pass
    conn.close()


def get_employees(center_id=None):
    conn = get_conn()
    c = conn.cursor()
    if center_id:
        c.execute("SELECT id, name, max_horas_anuales, horas_jornada_diaria FROM employees WHERE center_id=? ORDER BY name", (center_id,))
    else:
        c.execute("SELECT id, name, max_horas_anuales, horas_jornada_diaria FROM employees ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows


def add_employee(name, center_id=None):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO employees(name, center_id, max_horas_anuales, horas_jornada_diaria) VALUES(?, ?, 1600, 8)", (name, center_id)
        )
        conn.commit()
    except Exception:
        pass
    conn.close()


def remove_employee(emp_id):
    conn = get_conn()
    c = conn.cursor()
    # remove vacations and functions first
    c.execute("DELETE FROM vacations WHERE emp_id=?", (emp_id,))
    c.execute("DELETE FROM employee_functions WHERE emp_id=?", (emp_id,))
    c.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()


def add_vacation(emp_id, date_str, type_str='ausencia'):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO vacations(emp_id, date, type) VALUES(?, ?, ?)", (emp_id, date_str, type_str))
        conn.commit()
    except Exception:
        pass
    conn.close()


def remove_vacation(emp_id, date_str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM vacations WHERE emp_id=? AND date=?", (emp_id, date_str))
    conn.commit()
    conn.close()


def get_vacations(emp_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT date, type FROM vacations WHERE emp_id=?", (emp_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def add_function(name, center_id):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO functions(name, center_id) VALUES(?, ?)", (name, center_id))
        conn.commit()
    except Exception:
        pass
    conn.close()


def get_functions(center_id=None):
    conn = get_conn()
    c = conn.cursor()
    if center_id:
        c.execute("SELECT id, name FROM functions WHERE center_id=? ORDER BY id", (center_id,))
    else:
        c.execute("SELECT id, name FROM functions ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows


def remove_function(func_id):
    conn = get_conn()
    c = conn.cursor()
    # remove employee_functions and daily_needs first
    c.execute("DELETE FROM employee_functions WHERE func_id=?", (func_id,))
    c.execute("DELETE FROM daily_needs WHERE func_id=?", (func_id,))
    c.execute("DELETE FROM functions WHERE id=?", (func_id,))
    conn.commit()
    conn.close()


def add_employee_function(emp_id, func_id, priority):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO employee_functions(emp_id, func_id, priority) VALUES(?, ?, ?)", (emp_id, func_id, priority))
        conn.commit()
    except Exception:
        pass
    conn.close()


def get_employee_functions(emp_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT f.name, ef.priority
        FROM employee_functions ef
        JOIN functions f ON ef.func_id = f.id
        WHERE ef.emp_id = ?
        ORDER BY ef.priority DESC
    """, (emp_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def remove_employee_function(emp_id, func_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM employee_functions WHERE emp_id=? AND func_id=?", (emp_id, func_id))
    conn.commit()
    conn.close()


def set_daily_need(date_str, func_id, count, center_id):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO daily_needs(date, func_id, count, center_id) VALUES(?, ?, ?, ?)", (date_str, func_id, count, center_id))
        conn.commit()
    except Exception:
        pass
    conn.close()


def batch_set_daily_needs(needs_list):
    """
    needs_list: list of (date_str, func_id, count, center_id)
    """
    conn = get_conn()
    c = conn.cursor()
    try:
        c.executemany("INSERT OR REPLACE INTO daily_needs(date, func_id, count, center_id) VALUES(?, ?, ?, ?)", needs_list)
        conn.commit()
    except Exception as e:
        print(f"Error in batch_set_daily_needs: {e}")
    conn.close()


def get_daily_needs(date_str=None, center_id=None):
    conn = get_conn()
    c = conn.cursor()
    if date_str:
        if center_id:
            c.execute("""
                SELECT f.name, dn.count
                FROM daily_needs dn
                JOIN functions f ON dn.func_id = f.id
                WHERE dn.date = ? AND dn.center_id = ?
                ORDER BY f.name
            """, (date_str, center_id))
        else:
            c.execute("""
                SELECT f.name, dn.count
                FROM daily_needs dn
                JOIN functions f ON dn.func_id = f.id
                WHERE dn.date = ?
                ORDER BY f.name
            """, (date_str,))
    else:
        if center_id:
            c.execute("""
                SELECT dn.date, f.name, dn.count
                FROM daily_needs dn
                JOIN functions f ON dn.func_id = f.id
                WHERE dn.center_id = ?
                ORDER BY dn.date, f.name
            """, (center_id,))
        else:
            c.execute("""
                SELECT dn.date, f.name, dn.count
                FROM daily_needs dn
                JOIN functions f ON dn.func_id = f.id
                ORDER BY dn.date, f.name
            """)
    rows = c.fetchall()
    conn.close()
    return rows


def set_assignment(date_str, emp_id, func_id, center_id):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO assignments(date, emp_id, func_id, center_id) VALUES(?, ?, ?, ?)", (date_str, emp_id, func_id, center_id))
        conn.commit()
    except Exception:
        pass
    conn.close()


def get_assignments(date_str=None, center_id=None):
    conn = get_conn()
    c = conn.cursor()
    if date_str:
        if center_id:
            c.execute("""
                SELECT a.date, e.name, f.name
                FROM assignments a
                JOIN employees e ON a.emp_id = e.id
                JOIN functions f ON a.func_id = f.id
                WHERE a.date = ? AND a.center_id = ?
                ORDER BY f.name, e.name
            """, (date_str, center_id))
        else:
            c.execute("""
                SELECT a.date, e.name, f.name
                FROM assignments a
                JOIN employees e ON a.emp_id = e.id
                JOIN functions f ON a.func_id = f.id
                WHERE a.date = ?
                ORDER BY f.name, e.name
            """, (date_str,))
    else:
        if center_id:
            c.execute("""
                SELECT a.date, e.name, f.name
                FROM assignments a
                JOIN employees e ON a.emp_id = e.id
                JOIN functions f ON a.func_id = f.id
                WHERE a.center_id = ?
                ORDER BY a.date, f.name, e.name
            """, (center_id,))
        else:
            c.execute("""
                SELECT a.date, e.name, f.name
                FROM assignments a
                JOIN employees e ON a.emp_id = e.id
                JOIN functions f ON a.func_id = f.id
                ORDER BY a.date, f.name, e.name
            """)
    rows = c.fetchall()
    conn.close()
    return rows


def clear_assignments_for_month(year, month, center_id):
    conn = get_conn()
    c = conn.cursor()
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    c.execute("DELETE FROM assignments WHERE date >= ? AND date <= ? AND center_id = ?", (start_date, end_date, center_id))
    conn.commit()
    conn.close()


def remove_center(center_id):
    conn = get_conn()
    c = conn.cursor()
    # borrar vacaciones, funciones y empleados del centro
    c.execute("SELECT id FROM employees WHERE center_id=?", (center_id,))
    emp_ids = [r[0] for r in c.fetchall()]
    for eid in emp_ids:
        c.execute("DELETE FROM vacations WHERE emp_id=?", (eid,))
        c.execute("DELETE FROM employee_functions WHERE emp_id=?", (eid,))
    c.execute("DELETE FROM employees WHERE center_id=?", (center_id,))
    c.execute("DELETE FROM assignments WHERE center_id=?", (center_id,))
    c.execute("DELETE FROM daily_needs WHERE center_id=?", (center_id,))
    c.execute("DELETE FROM holidays WHERE center_id=?", (center_id,))
    c.execute("DELETE FROM functions WHERE center_id=?", (center_id,))
    c.execute("DELETE FROM centers WHERE id=?", (center_id,))
    conn.commit()
    conn.close()


def add_holiday(date_str, center_id, name=None):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO holidays(date, center_id, name) VALUES(?, ?, ?)", (date_str, center_id, name))
        conn.commit()
    except Exception:
        pass
    conn.close()


def remove_holiday(date_str, center_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM holidays WHERE date=? AND center_id=?", (date_str, center_id))
    conn.commit()
    conn.close()


def get_holidays(center_id=None):
    conn = get_conn()
    c = conn.cursor()
    if center_id:
        c.execute("SELECT date, name FROM holidays WHERE center_id=? ORDER BY date", (center_id,))
    else:
        c.execute("SELECT date, name FROM holidays ORDER BY date")
    rows = c.fetchall()
    conn.close()
    return rows


def update_employee_params(emp_id, max_horas_anuales, horas_jornada_diaria):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE employees SET max_horas_anuales=?, horas_jornada_diaria=? WHERE id=?", (max_horas_anuales, horas_jornada_diaria, emp_id))
    conn.commit()
    conn.close()


def get_employee_params(emp_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT max_horas_anuales, horas_jornada_diaria FROM employees WHERE id=?", (emp_id,))
    row = c.fetchone()
    conn.close()
    return row


def seed_example_residencia():
    """Carga datos de ejemplo en el centro 'Residencia' para enero-2026."""
    conn = get_conn()
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
        c.execute("INSERT OR IGNORE INTO functions(name, center_id) VALUES(?, ?)", (fname, center_id))
    conn.commit()

    # Mapas auxiliares (solo funciones del centro)
    func_map = {name: fid for fid, name in c.execute("SELECT id, name FROM functions WHERE center_id=?", (center_id,)).fetchall()}
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
    # Buscar el centro
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM centers WHERE name=?", ("Residencia",))
    row = c.fetchone()
    conn.close()

    if not row:
        return

    center_id = row[0]

    # Borra el centro y sus datos asociados
    remove_center(center_id)

    # Elimina funciones de ejemplo si quedaron sin referencias
    sample_functions = ["Turno manana", "Turno tarde", "Turno noche", "Cocina", "Limpieza", "Recepcion"]
    conn = get_conn()
    c = conn.cursor()
    for fname in sample_functions:
        c.execute("SELECT id FROM functions WHERE name=? AND center_id=?", (fname, center_id))
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
