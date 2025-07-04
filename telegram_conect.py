from telegram import InlineKeyboardMarkup, InlineKeyboardButton


proveedores = ["Amiplast", "Anibal_Bonino(Pritty)", "Anselmi", "Bachilito", "Buon_Sapore(Jorge)", "Cafaratti(pepsi)", "Careglio",
               "Coca", "Demichelis", "Disbe", "Dutto", "DP(Paladini)", "Esperanza", "Fernando_Cavallo", "Freezo", "Glass", "GrupoM",
               "La_Esquina", "L&L(Secco)", "La_Bri", "Macellato", "Marzal", "Nono_Fidel", "Panero", "PyP", "Piamontesa", "Placeres_Naturales",
               "Region_Centro", "Santa_Maria", "Veneziana", "Verduleria", "Otro"]


# --- Teclados ---
def teclado_proveedores(monto):
    botones = [
        [InlineKeyboardButton(p.capitalize(), callback_data=f"proveedor:{p}:{monto}")]
        for p in proveedores
    ]
    # Agregamos botones adicionales
    botones.append([
        InlineKeyboardButton("🧾 Cliente", callback_data=f"cliente:{monto}"),
    ])
    return InlineKeyboardMarkup(botones)


def mostrar_consultas():
    botones = [
        [InlineKeyboardButton("📥 Ingreso hoy", callback_data="consulta:ingreso_hoy")],
        [InlineKeyboardButton("📤 Egreso hoy", callback_data="consulta:egreso_hoy")],
        [InlineKeyboardButton("📆 Ingreso mes", callback_data="consulta:ingreso_mes")],
        [InlineKeyboardButton("📉 Egreso mes", callback_data="consulta:egreso_mes")],
        [InlineKeyboardButton("💰 Saldo mes", callback_data="consulta:saldo_mes")]
    ]
    return InlineKeyboardMarkup(botones)