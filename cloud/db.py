import psycopg2
import os

def crear_tabla():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id SERIAL PRIMARY KEY,
            fecha DATE,
            hora TEXT,
            monto REAL,
            proveedor TEXT
        )
    """)
    conn.commit()
    conn.close()
