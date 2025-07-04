from datetime import datetime
import psycopg2
import os

def registrar_ingreso(monto):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("INSERT INTO movimientos (fecha, hora, monto, proveedor) VALUES (%s, %s, %s, %s)", 
                (datetime.now().date(), datetime.now().strftime("%H:%M"), monto, "cliente"))
    conn.commit()
    conn.close()

def registrar_egreso(proveedor, monto):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("INSERT INTO movimientos (fecha, hora, monto, proveedor) VALUES (%s, %s, %s, %s)", 
                (datetime.now().date(), datetime.now().strftime("%H:%M"), monto, proveedor))
    conn.commit()
    conn.close()
