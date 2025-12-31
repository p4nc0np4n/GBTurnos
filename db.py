import sqlite3
import os
import calendar

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS centers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS employees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            center_id INTEGER,
            max_horas_anuales REAL DEFAULT 1600,
            horas_jornada_diaria REAL DEFAULT 8,
            UNIQUE(name, center_id),
            FOREIGN KEY(center_id) REFERENCES centers(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS vacations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'ausencia',
            UNIQUE(emp_id, date),
            FOREIGN KEY(emp_id) REFERENCES employees(id)
        )
        """
    )
    # Add type column if it doesn't exist (for existing databases)
    try:
        c.execute("ALTER TABLE vacations ADD COLUMN type TEXT NOT NULL DEFAULT 'ausencia'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS functions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_functions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            func_id INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            UNIQUE(emp_id, func_id),
            FOREIGN KEY(emp_id) REFERENCES employees(id),
            FOREIGN KEY(func_id) REFERENCES functions(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS assignments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            emp_id INTEGER NOT NULL,
            func_id INTEGER NOT NULL,
            center_id INTEGER NOT NULL,
            UNIQUE(date, emp_id, center_id),
            FOREIGN KEY(emp_id) REFERENCES employees(id),
            FOREIGN KEY(func_id) REFERENCES functions(id),
            FOREIGN KEY(center_id) REFERENCES centers(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_needs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            func_id INTEGER NOT NULL,
            count INTEGER NOT NULL,
            center_id INTEGER NOT NULL,
            UNIQUE(date, func_id, center_id),
            FOREIGN KEY(func_id) REFERENCES functions(id),
            FOREIGN KEY(center_id) REFERENCES centers(id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS holidays(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            center_id INTEGER NOT NULL,
            name TEXT,
            UNIQUE(date, center_id),
            FOREIGN KEY(center_id) REFERENCES centers(id)
        )
        """
    )
    # Add center_id column if it doesn't exist (for existing databases)
    try:
        c.execute("ALTER TABLE daily_needs ADD COLUMN center_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Column already exists
    # Add new columns to employees
    try:
        c.execute("ALTER TABLE employees ADD COLUMN max_horas_anuales REAL DEFAULT 1800")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE employees ADD COLUMN horas_jornada_diaria REAL DEFAULT 8")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    # Populate initial functions if empty
    c.execute("SELECT COUNT(*) FROM functions")
    if c.fetchone()[0] == 0:
        functions = ["Ens", "prim c", "prim res", "seg", "diet col", "diet res", "exped", "2.0", "Putx"]
        for func in functions:
            c.execute("INSERT INTO functions(name) VALUES(?)", (func,))
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


def add_function(name):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO functions(name) VALUES(?)", (name,))
        conn.commit()
    except Exception:
        pass
    conn.close()


def get_functions():
    conn = get_conn()
    c = conn.cursor()
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
    c.execute("DELETE FROM daily_needs WHERE center_id=?", (center_id,))
    c.execute("DELETE FROM holidays WHERE center_id=?", (center_id,))
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
