from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime
import os
import math
from interprete_fecha import extraer_info_consulta
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DB_FILE = "movimientos.db"
operaciones = {}

def formatear_monto(monto):
    return format(float(monto), ",.2f").replace(",", "X").replace(".", ",").replace("X", ".")



# --- DB ---
def crear_tabla():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo TEXT,
            monto REAL,
            proveedor TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_ingreso(monto):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # cur.execute("INSERT INTO movimientos (fecha, tipo, monto) VALUES (?, ?, ?)", 
    #             (datetime.now().strftime("%Y-%m-%d"), "ingreso", monto))
    cur.execute("INSERT INTO movimientos (fecha, hora, monto, proveedor) VALUES (?, ?, ?, ?)", 
                (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), monto, "cliente"))
    conn.commit()
    conn.close()


def registrar_egreso(proveedor, monto):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # cur.execute("INSERT INTO movimientos (fecha, tipo, monto, proveedor) VALUES (?, ?, ?, ?)", 
    #             (datetime.now().strftime("%Y-%m-%d"), "egreso", monto, proveedor))
    cur.execute("INSERT INTO movimientos (fecha, hora, monto, proveedor) VALUES (?, ?, ?, ?, ?)", 
                (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), monto, proveedor))
    conn.commit()
    conn.close()

# --- Teclados ---
def teclado_calculadora(display):
    botones = [
        [InlineKeyboardButton(f"📟 {display}", callback_data="ignore")],
        [InlineKeyboardButton(txt, callback_data=txt) for txt in ["+", "-"]],
        [InlineKeyboardButton(txt, callback_data=txt) for txt in ["7", "8", "9"]],
        [InlineKeyboardButton(txt, callback_data=txt) for txt in ["4", "5", "6"]],
        [InlineKeyboardButton(txt, callback_data=txt) for txt in ["1", "2", "3"]],
        [InlineKeyboardButton(txt, callback_data=txt) for txt in ["0", "C"]],
        [InlineKeyboardButton(txt, callback_data=txt) for txt in ["=", "*"]],
    ]
    return InlineKeyboardMarkup(botones)

def teclado_confirmacion(resultado):
    botones = [
        [InlineKeyboardButton(f"📟 {float(resultado):,.2f}", callback_data="ignore")],
        [InlineKeyboardButton("✅ Aceptar", callback_data=f"aceptar:{resultado}"),
         InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    return InlineKeyboardMarkup(botones)

def calcular_total(texto_usuario):
    info = extraer_info_consulta(texto_usuario)

    if "fecha_inicio" not in info or "fecha_fin" not in info:
        return "❌ No pude entender la fecha. Probá de nuevo."

    df = pd.read_sql("SELECT * FROM movimientos", sqlite3.connect(DB_FILE))
    df["fecha"] = pd.to_datetime(df["fecha"])

    desde = pd.to_datetime(info["fecha_inicio"])
    hasta = pd.to_datetime(info["fecha_fin"])
    tipo = info["tipo"]
    print(tipo)
    filtrado = df[(df["fecha"] >= desde) & (df["fecha"] <= hasta)]

    # if tipo in ["ingreso", "egreso"]:
    #     filtrado = filtrado[filtrado["tipo"] == tipo]
    filtrado = filtrado[filtrado["proveedor"]== "cliente"]
    total = filtrado["monto"].sum()
    return f"📊 Total de {tipo} entre {desde.date()} y {hasta.date()}: ${formatear_monto(total)}"

# --- Botones presionados ---
async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    texto = query.data

    if texto == "ignore":
        return

    if user_id not in operaciones:
        operaciones[user_id] = ""

    # if texto == "C":
    #     operaciones[user_id] = ""
    #     await query.edit_message_reply_markup(reply_markup=teclado_calculadora("0"))

    elif texto == "=":
        try:
            resultado = eval(operaciones[user_id])
            operaciones[user_id] = str(resultado)
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                # [InlineKeyboardButton(f"📟 ####", callback_data="ignore")],
                [InlineKeyboardButton("🔁 +10% redondeado", callback_data=f"plus10:{resultado}")],
                [InlineKeyboardButton("✅ Aceptar", callback_data=f"aceptar:{resultado}"),
                 InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
            ]))
        except:
            return
            # operaciones[user_id] = ""
            # await query.edit_message_reply_markup(reply_markup=teclado_calculadora("Error"))

    elif texto.startswith("plus10:"):
        base = float(texto.split(":")[1])
        total = math.ceil(base * 0.9 / 100) * 100
        operaciones[user_id] = str(total)
        await query.edit_message_reply_markup(reply_markup=teclado_confirmacion(total))

    elif texto.startswith("aceptar:"):
        resultado = float(texto.split(":")[1])
        registrar_ingreso(resultado)
        operaciones.pop(user_id, None)
        await query.edit_message_text(f"💰 Ingreso registrado: ${resultado:,.2f}")

    elif texto == "cancelar":
        operaciones.pop(user_id, None)
        await query.edit_message_text("❌ Operación cancelada.")

    # else:
        # operaciones[user_id] += texto
        # await query.edit_message_reply_markup(reply_markup=teclado_calculadora(operaciones[user_id]))

# --- Mensajes entrantes ---
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    user_id = update.message.from_user.id
    partes = texto.split()

    # 🧾 Pregunta con lenguaje libre (GPT)
    if any(palabra in texto.lower() for palabra in ["cuánto", "total", "recaud", "hizo", "ganó"]):
        respuesta = calcular_total(texto)
        await update.message.reply_text(respuesta)
        return

    # ✅ Ingreso directo (solo número)
    if len(partes) == 1 and partes[0].replace(",", ".").replace(".", "", 1).isdigit():
        operaciones[user_id] = partes[0].replace(",", ".")
        await update.message.reply_text("🧮 Ingresá operación", reply_markup=teclado_confirmacion(operaciones[user_id]))
        return

    # 📤 Egreso: texto + número al final
    if len(partes) >= 2 and partes[-1].replace(",", ".").replace(".", "", 1).isdigit():
        proveedor = " ".join(partes[:-1])
        monto = float(partes[-1].replace(",", "."))
        registrar_egreso(proveedor, monto)
        await update.message.reply_text(f"📤 Egreso registrado: ${monto:,.2f} a {proveedor}")
        return


    # # Detectar ingreso directo (solo número)
    # if len(partes) == 1 and partes[0].replace(",", ".").replace(".", "", 1).isdigit():
    #     operaciones[user_id] = partes[0].replace(",", ".")
    #     await update.message.reply_text("🧮 Ingresá operación", reply_markup=teclado_confirmacion(operaciones[user_id]))

    # # Detectar egreso: texto + número al final
    # elif len(partes) >= 2 and partes[-1].replace(",", ".").replace(".", "", 1).isdigit():
    #     proveedor = " ".join(partes[:-1])
    #     monto = float(partes[-1].replace(",", "."))
    #     registrar_egreso(proveedor, monto)
    #     await update.message.reply_text(f"📤 Egreso registrado: ${monto:.2f} a {proveedor}")


# --- MAIN ---
if __name__ == "__main__":
    crear_tabla()
    # TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "PEGÁ_TU_TOKEN_ACÁ"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(manejar_boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("🤖 Calculadora lista.")
    app.run_polling()
