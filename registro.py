from datetime import datetime
import sqlite3


DB_FILE = "movimientos.db"


def registrar_ingreso(monto):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO movimientos (fecha, hora, monto, proveedor) VALUES (?, ?, ?, ?)", 
                (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), monto, "cliente"))
    conn.commit()
    conn.close()


def registrar_egreso(proveedor, monto):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO movimientos (fecha, hora, monto, proveedor) VALUES (?, ?, ?, ?)", 
                (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), monto, proveedor))
    conn.commit()
    conn.close()
    
    
