import openai
from datetime import datetime
import json
import os

client = openai.OpenAI()

def extraer_info_consulta(texto_usuario):
    hoy = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
Sos un asistente que interpreta preguntas sobre registros de ventas.

El usuario puede preguntar:

- Totales ("¿cuánto se recaudó hoy?", "¿cuánto esta semana?", "¿cuánto por la mañana?")
- Hora pico ("¿a qué hora se vendió más hoy?", "¿en qué hora se vendió más cada día esta semana?")
- Listados ("mostrame las ventas de ayer", "qué se vendió hoy")

Respondé SOLO en formato JSON. Por ejemplo:

### Para total:
{{
  "accion": "total",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD",
  "tipo": "ingreso" | "egreso" | "ambos",
  "franja_horaria": "mañana" | "tarde" | "noche" | null
}}

### Para hora pico:
{{
  "accion": "hora_pico",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD",
  "tipo": "ingreso" | "egreso" | "ambos",
  "por_dia": true | false
}}

### Para listado:
{{
  "accion": "listar",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD",
  "tipo": "ingreso" | "egreso" | "ambos"
}}

Si no se entiende bien, respondé con:
{{ "accion": "error" }}

La fecha actual es {hoy}.
Mensaje: "{texto_usuario}"
"""

    try:
        respuesta = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        contenido = respuesta.choices[0].message.content.strip()

        # Limpieza de bloque ```json
        if contenido.startswith("```"):
            contenido = contenido.split("```")[1]
            contenido = contenido.replace("json", "").strip()

        return json.loads(contenido)
    except Exception as e:
        print("❌ Error al interpretar:", e)
        return {"accion": "error"}
