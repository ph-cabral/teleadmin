import os
import sqlite3
import pandas as pd
from db_sqlite import crear_tabla
from telegram import Update
from datetime import datetime

from calculos import calcular_total, mostrar_total
from registro import registrar_ingreso, registrar_egreso
from telegram_conect import mostrar_consultas, teclado_proveedores
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, filters, ContextTypes


from dotenv import load_dotenv
load_dotenv()


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_FILE = "movimientos.db"


operaciones = {}


def formatear_monto(monto):
    return format(float(monto), ",.2f").replace(",", "X").replace(".", ",").replace("X", ".")


# --- Mensajes entrantes ---
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if texto.replace(",", ".").replace(".", "", 1).isdigit():
        monto = float(texto.replace(",", "."))
        await update.message.reply_text("Seleccioná el destino del monto:", reply_markup=teclado_proveedores(monto))
        return
    await update.message.reply_text("📊 Elegí una opción:", reply_markup=mostrar_consultas())


async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("proveedor:"):
        _, proveedor, monto = data.split(":")
        monto = -abs(float(monto))  # egreso
        registrar_egreso(proveedor, monto)
        # await query.edit_message_text(f"📤 {proveedor}: ${abs(monto):,.2f} \n{mostrar_total(DB_FILE, formatear_monto)} ")
        total = mostrar_total(DB_FILE, formatear_monto)
        await query.edit_message_text(f"📤 {proveedor}: ${formatear_monto(abs(monto))} \n{total}")


    elif data.startswith("cliente:"):
        _, monto = data.split(":")
        registrar_ingreso(float(monto))  # ingreso
        await query.edit_message_text(f"💰 Ingreso: ${float(monto):,.2f} \n{mostrar_total(DB_FILE, formatear_monto)}")
    # 
    # elif data.startswith("consulta"):
    else:
        opcion = data.split(":")[1]
        # opcion = data
        df = pd.read_sql("SELECT * FROM movimientos", sqlite3.connect(DB_FILE))
        df["fecha"] = pd.to_datetime(df["fecha"])
        hoy = datetime.now().date()
        mes_actual = hoy.month
        anio_actual = hoy.year

        if opcion == "ingreso_hoy":
            total = df[(df["fecha"].dt.date == hoy) & (df["monto"] > 0)]["monto"].sum()
            mensaje = f"📥 Ingreso de hoy: ${formatear_monto(total)}"
        elif opcion == "egreso_hoy":
            total = df[(df["fecha"].dt.date == hoy) & (df["monto"] < 0)]["monto"].sum()
            mensaje = f"📤 Egreso de hoy: ${formatear_monto(abs(total))}"
        elif opcion == "ingreso_mes":
            total = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual) & (df["monto"] > 0)]["monto"].sum()
            mensaje = f"📆 Ingreso del mes: ${formatear_monto(total)}"
        elif opcion == "egreso_mes":
            total = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual) & (df["monto"] < 0)]["monto"].sum()
            mensaje = f"📉 Egreso del mes: ${formatear_monto(abs(total))}"
        elif opcion == "saldo_mes":
            total = df[(df["fecha"].dt.month == mes_actual) & (df["fecha"].dt.year == anio_actual)]["monto"].sum()
            mensaje = f"💰 Saldo del mes: ${formatear_monto(total)}"
        else:
            mensaje = "❌ Opción no reconocida."

        await query.edit_message_text(mensaje)
        return


# --- MAIN ---
if __name__ == "__main__":
    crear_tabla(DB_FILE)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(manejar_boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("🤖 Calculadora lista.")
    app.run_polling()